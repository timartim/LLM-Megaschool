import logging
import re

import aiohttp
import asyncio
from bs4 import BeautifulSoup
from typing import List, Optional

from .config import SEARCH_API_KEY, CX
from .model import run_model

logger = logging.getLogger("uvicorn")
SEARCH_URL = "https://www.googleapis.com/customsearch/v1"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger(__name__)


async def transform_query_for_google(original_query: str) -> str:
    system_msg = {
        "role": "system",
        "text": (
            "Преобразуй вопрос пользователя в короткий поисковый запрос (1 строка), "
            "чтобы Google мог легко найти информацию, связанную с Университетом ИТМО. "
            "Не добавляй варианты ответа (1., 2. и т.д.)."
        )
    }
    user_msg = {"role": "user", "text": original_query}
    messages = [system_msg, user_msg]
    result = await run_model(messages)
    return result.strip() or original_query


async def check_is_multiple_choice(query: str) -> bool:
    """
    Запрашиваем у LLM, есть ли варианты (yes/no).
    """
    system_msg = {
        "role": "system",
        "text": "Есть ли в отправленном тебе запросе варианты ответа на него? ответь строго да или нет и только это."
    }
    user_msg = {"role": "user", "text": query}
    messages = [system_msg, user_msg]
    raw = await run_model(messages)

    return (raw.strip().lower() == "да")


async def search_google(query: str) -> List[str]:
    logger.info(f"search_google: query='{query}'")
    params = {"key": SEARCH_API_KEY, "cx": CX, "q": query, "num": 5}
    async with aiohttp.ClientSession() as session:
        async with session.get(SEARCH_URL, params=params) as resp:
            logger.info(f"search_google status={resp.status}")
            if resp.status == 200:
                data = await resp.json()
                items = data.get("items", [])
                links = [it.get("link") for it in items if "link" in it]
                logger.info(f"search_google found {len(links)} links: {links}")
                return links[:3]
            else:
                txt = await resp.text()
                logger.warning(f"search_google error {resp.status}: {txt}")
    return []


async def fetch_page_content(session: aiohttp.ClientSession, link: str) -> str:
    try:
        logger.info(f"Начинаю загрузку страницы: {link}")
        async with session.get(link) as resp:
            # Таймаут 1 секунда на всю операцию
            content = await asyncio.wait_for(resp.text(), timeout=1.0)
            text = BeautifulSoup(content, "html.parser").get_text()
            logger.info(f"Страница {link} загружена, размер: {len(text)} символов")
            return text
    except Exception as e:
        logger.error(f"Ошибка при загрузке {link}: {type(e).__name__}")
        return ""


async def fetch_page_texts(links: List[str]) -> List[str]:
    logger.info(f"Начинаю загрузку списка ссылок: {links}")
    async with aiohttp.ClientSession() as session:
        # Создаем задачи как объекты Task
        tasks = [
            asyncio.create_task(
                asyncio.wait_for(fetch_page_content(session, link), timeout=1.0)
            )
            for link in links[:5]
        ]

        results = []
        for future in asyncio.as_completed(tasks):
            try:
                result = await future
                if result:
                    results.append(result)
                    if len(results) >= 3:
                        break
            except Exception as e:
                logger.error(f"Ошибка в задаче: {type(e).__name__}")

        # Отменяем оставшиеся задачи
        for task in tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        logger.info(f"Успешно загружено {len(results)} страниц")
        return results[:3]


async def compress_pages_for_itmo(raw_texts: List[str]) -> str:
    """
    Для каждого текста:
      1. Убираем HTML-теги
      2. Удаляем любые пробелы/переносы строк
      3. Оставляем первые 10000 символов
      4. Вызываем LLM (run_model) с просьбой выделить сведения про ИТМО
    """
    logger.info(f"Запускаю compress_pages_for_itmo для {len(raw_texts)} страниц")

    system_msg = {
        "role": "system",
        "text": (
            "Тебе дан текст страницы. Оставь только то, что связано с "
            "Университетом ИТМО. Если нет упоминаний, напиши 'нет информации'."
        ),
    }

    summaries = []
    for idx, txt in enumerate(raw_texts):
        text_no_html = BeautifulSoup(txt, "html.parser").get_text()

        # 2. Удаляем все whitespace-символы
        text_one_space = re.sub(r"\s+", " ", text_no_html).strip()

        # 3. Оставляем только первые 400 символов (нужна скорость)
        text_truncated = text_one_space[:400]

        # 4. Готовим запрос для модели
        user_msg = {"role": "user", "text": text_truncated}
        messages = [system_msg, user_msg]

        # Вызываем вашу LLM/модель
        summary = await run_model(messages)

        logger.info(f"Page #{idx} summary (first 100 chars): {summary[:100]}...")
        summaries.append(summary.strip())

    # Объединяем сжатую информацию со всех страниц
    big_context = "\n\n".join(summaries)
    return big_context


async def ask_which_variant(user_query: str, big_context: str) -> Optional[int]:
    """
    Спросить модель: 'Какой вариант правильный?' (1 строка = цифра или null),
    Вторая строка - мини-пояснение (можно игнорировать).
    """
    system_msg = {
        "role": "system",
        "text": (
            "У пользователя есть вопрос с вариантами ответа. Опираясь на контекст, в первой строке напиши номер сделай это как можно быстрее. "
            "правильного варианта (1..N). Если нельзя определить — напиши null."
        )
    }
    user_msg = {
        "role": "user",
        "text": f"Вопрос: {user_query}\n\nКонтекст:\n{big_context}"
    }
    messages = [system_msg, user_msg]
    raw = await run_model(messages)
    lines = raw.strip().split("\n", 1)
    first_line = lines[0].strip().lower() if lines else "null"

    if first_line.isdigit():
        return int(first_line)
    return None


async def ask_explanation(user_query: str, big_context: str, chosen_variant: Optional[int]) -> str:
    """
    Спросить у модели пояснение. Если вариант выбран, можно подмешать его.
    """
    sys_msg = {
        "role": "system",
        "text": (
            "Объясни ответ на вопрос. Учитывай контекст про ИТМО. Сделай 2 предложения и как можно быстрее. Скажи откуда ты взял эту информацию"
            "Если есть выбранный вариант, упомяни почему именно он верен."
        )
    }
    variant_str = f"(Выбранный вариант: {chosen_variant})" if chosen_variant else ""
    user_msg = {
        "role": "user",
        "text": f"{user_query}\n\nКонтекст:\n{big_context}\n\n{variant_str}"
    }
    messages = [sys_msg, user_msg]
    explanation = await run_model(messages)
    return explanation.strip()
