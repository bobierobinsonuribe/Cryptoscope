import requests
from datetime import datetime, timedelta
import time

ETHERSCAN_API_KEY = "YourApiKeyHere"
ETHERSCAN_API_URL = "https://api.etherscan.io/api"


class CryptoTracker:
    def __init__(self, address: str):
        self.address = address.lower()
        self.session = requests.Session()

    def get_transactions(self):
        params = {
            "module": "account",
            "action": "txlist",
            "address": self.address,
            "startblock": 0,
            "endblock": 99999999,
            "sort": "desc",
            "apikey": ETHERSCAN_API_KEY,
        }
        response = self.session.get(ETHERSCAN_API_URL, params=params)
        data = response.json()
        if data["status"] != "1":
            raise ValueError("Ошибка получения данных:", data.get("message"))
        return data["result"]

    def analyze(self, transactions):
        alerts = []

        for tx in transactions:
            to_addr = tx["to"].lower()
            from_addr = tx["from"].lower()
            gas_price = int(tx["gasPrice"]) / 1e9  # в Gwei
            is_contract = tx["input"] != "0x"
            timestamp = datetime.fromtimestamp(int(tx["timeStamp"]))

            # 1. Быстрая пересылка между адресами
            if from_addr == self.address and to_addr != self.address:
                delay = datetime.now() - timestamp
                if delay < timedelta(minutes=5):
                    alerts.append(f"⚠ Быстрая пересылка в течение {delay.seconds} секунд на {to_addr}")

            # 2. Слишком высокая комиссия
            if gas_price > 300:
                alerts.append(f"⚠ Аномальная комиссия: {gas_price:.2f} Gwei")

            # 3. Деньги получены от нового адреса
            if to_addr == self.address:
                txs_from_sender = [t for t in transactions if t["from"].lower() == from_addr]
                if len(txs_from_sender) == 1:
                    alerts.append(f"⚠ Средства от свежего адреса: {from_addr}")

            # 4. Вызов смарт-контракта
            if is_contract:
                alerts.append(f"⚠ Обнаружено взаимодействие с контрактом. Hash: {tx['hash']}")

        return alerts


def scan_wallet(address):
    tracker = CryptoTracker(address)
    print(f"📡 Анализ кошелька {address}...")
    txs = tracker.get_transactions()
    issues = tracker.analyze(txs)
    if not issues:
        print("✅ Ничего подозрительного не обнаружено.")
    else:
        print("\n".join(issues))
