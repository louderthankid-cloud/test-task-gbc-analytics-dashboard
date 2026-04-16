import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

CRM_URL = os.getenv("RETAILCRM_URL")
CRM_API_KEY = os.getenv("RETAILCRM_API_KEY")


def upload_orders():
    if not CRM_URL or not CRM_API_KEY:
        print("Ошибка: Не указаны ключи RETAILCRM в .env")
        return

    try:
        with open("mock_orders.json", "r", encoding="utf-8") as file:
            orders = json.load(file)
    except FileNotFoundError:
        print("Ошибка: Файл mock_orders.json не найден")
        return

    url = f"{CRM_URL}/api/v5/orders/create"

    print(f"Загрузка {len(orders)} заказов в RetailCRM")

    success_count = 0

    for i, order_data in enumerate(orders):
        order_data.pop("orderType", None)
        order_data.pop("orderMethod", None)
        order_data.pop("status", None)

        payload = {"apiKey": CRM_API_KEY, "order": json.dumps(order_data)}

        url = f"{CRM_URL.rstrip('/')}/api/v5/orders/create"
        response = requests.post(url, data=payload)

        if response.status_code in (200, 201):
            res_json = response.json()
            if res_json.get("success"):
                crm_id = res_json.get("id")
                print(f"[{i+1}/{len(orders)}] Заказ успешно создан, CRM ID: {crm_id}")
                success_count += 1
            else:
                print(
                    f"[{i+1}/{len(orders)}] CRM вернула ошибку: {res_json.get('errorMsg')} - {res_json.get('errors')}"
                )
        else:
            print(
                f"[{i+1}/{len(orders)}] Ошибка сети: {response.status_code} - {response.text}"
            )

        time.sleep(0.3)

    print(f"\nКонец загрузки. Успешно загружено: {success_count}/{len(orders)}")


if __name__ == "__main__":
    upload_orders()
