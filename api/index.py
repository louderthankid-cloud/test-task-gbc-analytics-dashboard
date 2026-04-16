import os
import json
import httpx
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)
from supabase import create_async_client
from dotenv import load_dotenv

from api.schemas.order import OrderSchema

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


async def get_supabase():
    return await create_async_client(
        os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY")
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
)
async def send_telegram_notification(msg: str):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT_ID, "text": msg, "parse_mode": "Markdown"},
            timeout=10.0,
        )
        response.raise_for_status()


async def process_webhook(order_data: dict):
    try:
        order = OrderSchema.model_validate(order_data)

        city = (
            order.delivery.address.city
            if order.delivery and order.delivery.address
            else "Не указан"
        )
        utm = order.customFields.utm_source if order.customFields else "direct"

        db_payload = {
            "crm_id": order.id,
            "total_sum": order.totalSumm,
            "city": city,
            "utm_source": utm,
            "status": order.status,
            "raw_data": order_data,
        }

        supabase = await get_supabase()
        await supabase.table("orders").upsert(
            db_payload, on_conflict="crm_id"
        ).execute()
        print(f"[Webhook] Заказ {order.id} сохранен/обновлен.")

        if order.totalSumm > 50000:
            msg = f"**Заказ больше 50000₸**\nID: {order.id}\nСумма: {order.totalSumm:,.0f} ₸\nГород: {city}"
            await send_telegram_notification(msg)
            print(f"[Webhook] ТГ уведомление отправлено для {order.id}")

    except ValidationError as e:
        print(f"[Webhook Error] Ошибка валидации структуры Pydantic: {e}")
    except Exception as e:
        print(f"[Webhook Error] Неожиданная ошибка: {e}")


@app.get("/api/dashboard")
async def get_dashboard_data():
    supabase = await get_supabase()
    response = await supabase.rpc("get_dashboard_metrics").execute()

    metrics = response.data

    widgets = [
        {
            "id": "1",
            "type": "MetricCard",
            "title": "Общая выручка",
            "data": {"value": f"{metrics.get('total_revenue', 0):,.0f} ₸"},
        },
        {
            "id": "2",
            "type": "MetricCard",
            "title": "Количество заказов",
            "data": {"value": str(metrics.get("orders_count", 0))},
        },
        {
            "id": "3",
            "type": "MetricCard",
            "title": "Средний чек",
            "data": {"value": f"{metrics.get('avg_check', 0):,.0f} ₸"},
        },
        {
            "id": "4",
            "type": "BarChart",
            "title": "Выручка по городам",
            "data": metrics.get("city_data", []),
        },
        {
            "id": "5",
            "type": "PieChart",
            "title": "Источники трафика (UTM)",
            "data": metrics.get("utm_data", []),
        },
        {
            "id": "6",
            "type": "ProductList",
            "title": "Топ продаваемых товаров (шт)",
            "data": metrics.get("top_products", []),
        },
    ]
    return widgets


@app.post("/api/webhook")
async def retailcrm_webhook(request: Request):
    try:
        content_type = request.headers.get("content-type", "")

        if "application/json" in content_type:
            payload = await request.json()
            order_data = payload.get("order", payload)

        elif (
            "application/x-www-form-urlencoded" in content_type
            or "multipart/form-data" in content_type
        ):
            form_data = await request.form()
            raw = form_data.get("order") if "order" in form_data else None
            order_data = json.loads(raw) if raw else dict(form_data)

        else:
            raw = await request.body()
            payload = json.loads(raw.decode("utf-8"))
            order_data = payload.get("order", payload)

        await process_webhook(order_data)
        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook error: {e}")
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
