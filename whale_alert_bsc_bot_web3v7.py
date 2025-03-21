import requests
import time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from telegram import Bot
from datetime import datetime

# Dados reais da Gabi
TELEGRAM_BOT_TOKEN = "7769613471:AAHBTFcZ70mCiYFLhrK3zlyOeYUJh0yztZM"
CHAT_ID = 6781248598
MIN_USD_AMOUNT = 10000
BSC_NODE = "https://bsc-dataseed.binance.org"
INTERVAL = 2

def get_bnb_price():
    try:
        response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=binancecoin&vs_currencies=usd")
        return response.json()["binancecoin"]["usd"]
    except Exception as e:
        print("Erro ao buscar preço do BNB:", e)
        return None

def format_bnb(wei_value):
    return Web3.from_wei(wei_value, 'ether')

def send_alert(bot, tx, bnb_amount, usd_amount):
    message = f"🐋 [ALERTA - TRANSAÇÃO ALTA NA BSC]\n\n" \
              f"🔁 Hash: {tx['hash'].hex()}\n" \
              f"📤 De: {tx['from']}\n" \
              f"📥 Para: {tx['to']}\n" \
              f"💸 Valor: {bnb_amount:.2f} BNB (~${usd_amount:,.2f})\n" \
              f"🔗 https://bscscan.com/tx/{tx['hash'].hex()}"
    bot.send_message(chat_id=CHAT_ID, text=message)

def monitor_bsc_transactions():
    web3 = Web3(Web3.HTTPProvider(BSC_NODE))
    web3.middleware_onion.inject(geth_poa_middleware, layer=0)

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bnb_price = get_bnb_price()

    if not bnb_price:
        print("Não foi possível obter o preço do BNB.")
        return

    latest = web3.eth.block_number
    print(f"🎯 Iniciando monitoramento de transações na BSC acima de ${MIN_USD_AMOUNT:,}...")
    print(f"⛓️  Começando a partir do bloco #{latest}")

    while True:
        try:
            block = web3.eth.get_block(latest, full_transactions=True)
            print(f"🕓 {datetime.now().strftime('%H:%M:%S')} - 📦 Bloco #{latest} com {len(block.transactions)} transações...")

            for tx in block.transactions:
                from_is_contract = web3.eth.get_code(tx["from"]) != b''
                to_is_contract = web3.eth.get_code(tx["to"]) != b'' if tx["to"] else False

                if from_is_contract or to_is_contract:
                    continue

                bnb_amount = float(format_bnb(tx["value"]))
                usd_amount = bnb_amount * bnb_price

                if usd_amount >= MIN_USD_AMOUNT:
                    send_alert(bot, tx, bnb_amount, usd_amount)
                    print(f"🔔 Alerta enviado: {bnb_amount:.2f} BNB / ${usd_amount:,.2f}")

            latest += 1
        except Exception as e:
            print("Erro ao processar bloco:", e)

        time.sleep(INTERVAL)

if __name__ == "__main__":
    monitor_bsc_transactions()
