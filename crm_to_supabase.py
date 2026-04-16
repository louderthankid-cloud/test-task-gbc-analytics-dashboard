import os
import requests
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# Ключи RetailCRM
CRM_URL = os.getenv("RETAILCRM_URL").rstrip("/")
CRM_API_KEY = os.getenv("RETAILCRM_API_KEY")

# Ключи Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def fetch_orders_from_crm():
    print("Запрос заказов из RetailCRM")
    url = f"{CRM_URL}/api/v5/orders"
    params = {"apiKey": CRM_API_KEY, "limit": 100}

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get("success"):
            orders = data.get("orders", [])
            print(f"Получено {len(orders)} заказов. Начало загрузки в базу данных")
            return orders
        else:
            print(f"Ошибка CRM: {data.get('errorMsg')}")
            return []
    else:
        print(f"Ошибка сети: {response.status_code}")
        return []


def transform_and_upsert(orders):
    success_count = 0

    for order in orders:
        try:
            crm_id = order.get("id")
            total_sum = float(order.get("totalSumm") or 0)

            city = "Не указан"
            delivery = order.get("delivery")
            if isinstance(delivery, dict):
                address = delivery.get("address")
                if isinstance(address, dict):
                    city = address.get("city", "Не указан")

            utm_source = "direct"
            custom_fields = order.get("customFields")
            if isinstance(custom_fields, dict) and custom_fields.get("utm_source"):
                utm_source = custom_fields.get("utm_source")

            db_payload = {
                "crm_id": crm_id,
                "total_sum": total_sum,
                "city": city,
                "utm_source": utm_source,
                "status": order.get("status"),
                "created_at": order.get("createdAt"),
                "raw_data": order,
            }

            response = (
                supabase.table("orders")
                .upsert(db_payload, on_conflict="crm_id")
                .execute()
            )

            if response.data:
                success_count += 1

        except Exception as e:
            print(f"Ошибка обработки заказа ID {order.get('id', 'Unknown')}: {e}")

    print(
        f"Успешно синхронизировано {success_count} из {len(orders)} заказов в Supabase"
    )


if __name__ == "__main__":
    orders_data = fetch_orders_from_crm()
    if orders_data:
        transform_and_upsert(orders_data)
