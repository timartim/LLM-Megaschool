import time
import asyncio
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from pydantic import HttpUrl

from schemas.request import PredictionRequest, PredictionResponse
from utils.logger import setup_logger
from fastapi.middleware.cors import CORSMiddleware

from search_itmo.services import (
    transform_query_for_google,
    check_is_multiple_choice,
    search_google,
    fetch_page_texts,
    compress_pages_for_itmo,
    ask_which_variant,
    ask_explanation,
)

app = FastAPI()
logger = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8081", "http://51.250.74.4:8081"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    global logger
    logger = await setup_logger()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    body = await request.body()
    await logger.info(f"Incoming request: {request.method} {request.url}\nRequest body: {body.decode()}")
    response = await call_next(request)
    process_time = time.time() - start_time
    response_body = b""
    async for chunk in response.body_iterator:
        response_body += chunk
    await logger.info(
        f"Request completed: {request.method} {request.url}\n"
        f"Status: {response.status_code}\n"
        f"Response body: {response_body.decode()}\n"
        f"Duration: {process_time:.3f}s"
    )
    return Response(
        content=response_body,
        status_code=response.status_code,
        headers=dict(response.headers),
        media_type=response.media_type,
    )


@app.post("/api/request", response_model=PredictionResponse)
async def predict(body: PredictionRequest):
    try:
        await logger.info(f"Processing prediction request with id: {body.id}, query='{body.query}'")

        # Шаг 1: параллельно:
        # (a) Получаем гугл-запрос
        # (b) Проверяем, есть ли multiple-choice
        tasks = [
            transform_query_for_google(body.query),
            check_is_multiple_choice(body.query),
        ]
        refined_query, is_multi = await asyncio.gather(*tasks)

        await logger.info(f"Refined query: {refined_query}, is_multi={is_multi}")

        # Шаг 2: Идём в Google
        links = await search_google(refined_query)
        await logger.info(f"Got links: {links}")

        # Шаг 3: Скачиваем тексты, сжимаем до нужных частей
        raw_pages = await fetch_page_texts(links)
        big_context = await compress_pages_for_itmo(raw_pages)

        # Шаг 4: если multiple-choice => спрашиваем модель, какой вариант правильный
        chosen_variant: Optional[int] = None
        if is_multi:
            chosen_variant = await ask_which_variant(body.query, big_context)
            await logger.info(f"chosen_variant = {chosen_variant}")

        # Шаг 5: всегда спрашиваем "пояснение"
        explanation = await ask_explanation(body.query, big_context, chosen_variant)

        # Формируем ответ
        final_answer = chosen_variant if chosen_variant is not None else None

        # Список источников
        sources: List[HttpUrl] = []
        for link in links:
            sources.append(HttpUrl(link))

        resp = PredictionResponse(
            id=body.id,
            answer=final_answer,
            reasoning=explanation,
            sources=sources
        )
        await logger.info(f"Final response: {resp}")
        return resp

    except ValueError as e:
        await logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        await logger.error(f"Internal error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
