import logging
from yandex_cloud_ml_sdk import YCloudML
from .config import MODEL_AUTH_KEY

logger = logging.getLogger("uvicorn")

sdk = YCloudML(folder_id="b1gensvl1uk7ugci74r7", auth=MODEL_AUTH_KEY)
model = sdk.models.completions("yandexgpt-32k", model_version="rc").configure(temperature=0.5)

async def run_model(messages: list[dict]) -> str:
    """
    Принимает список сообщений в формате:
    [
      {"role": "system", "text": "..."},
      {"role": "user",   "text": "..."},
      ...
    ]
    Возвращает текст первого ответа модели.
    """
    logger.info(f"Отправляем сообщения в модель: {messages}")
    result = model.run(messages)
    if result and result.alternatives:
        text = result.alternatives[0].text
        logger.info(f"Модель вернула:\n{text}")
        return text
    return "no model information"
