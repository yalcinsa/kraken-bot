# Profi-Krypto-Bot (BTC, ETH, SOL, LINK, DOT, AVAX) mit RSI, Stop-Loss & Take-Profit

import time
import requests
import numpy as np
from datetime import datetime
import krakenex
import os

# ============ KONFIGURATION ============

API_KEY = "HIER_DEIN_API_KEY"
API_SECRET = "HIER_DEIN_API_SECRET"

coins = ["BTCEUR", "ETHEUR", "SOLEUR", "LINKEUR", "DOTEUR", "AVAXEUR"]
weights = {
    "BTCEUR": 0.35,
    "ETHEUR": 0.25,
    "SOLEUR": 0.15,
    "LINKEUR": 0.10,
    "DOTEUR": 0.10,
    "AVAXEUR": 0.05
}

max_daily_invest = 50.0         # EUR pro Tag
profit_target_pct = 0.20        # 20 % Gewinnziel
stop_loss_pct = 0.10            # 10 % Stop Loss
rsi_period = 14
price_check_interval = 300      # Alle 5 Minuten

api = krakenex.API()
api.key = API_KEY
api.secret = API_SECRET

portfolio = {}

# ============ FUNKTIONEN ============

def fetch_ohlc(coin, interval="5"):
    try:
        resp = api.query_public("OHLC", {"pair": coin, "interval": interval})
        ohlc = resp["result"]
        pair_data = next(iter({k: v for k, v in ohlc.items() if k != "last"}))
        closes = [float(x[4]) for x in ohlc[pair_data]]
        return closes
    except Exception as e:
        print(f"[{coin}] Fehler beim Abrufen der OHLC-Daten:", e)
        return []

def calculate_rsi(prices, period=14):
    if len(prices) < period + 1:
        return None
    deltas = np.diff(prices)
    gains = np.maximum(deltas, 0)
    losses = np.maximum(-deltas, 0)
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    if avg_loss == 0:
        return 100
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def fetch_price(pair):
    try:
        res = api.query_public("Ticker", {"pair": pair})
        return float(res["result"][next(iter(res["result"]))]["c"][0])
    except:
        return None

def place_market_order(pair, type_, volume):
    try:
        order = {
            "pair": pair,
            "type": type_,
            "ordertype": "market",
            "volume": volume
        }
        res = api.query_private("AddOrder", order)
        return res
    except Exception as e:
        print("Fehler bei Order:", e)

# ============ MAIN LOOP ============

def run_bot():
    global portfolio

    print("🚀 Trading-Bot läuft mit RSI, TP/SL & 6 Coins")
    invested_today = 0
    last_day = datetime.now().day

    while True:
        if datetime.now().day != last_day:
            invested_today = 0
            last_day = datetime.now().day

        for coin in coins:
            weight = weights[coin]
            budget = max_daily_invest * weight

            closes = fetch_ohlc(coin)
            if not closes:
                continue

            rsi = calculate_rsi(closes, rsi_period)
            if rsi is None:
                continue

            price = fetch_price(coin)
            if price is None:
                continue

            print(f"[{coin}] RSI: {rsi:.2f} | Preis: {price:.2f} EUR")

            # Kaufentscheidung
            if rsi < 30 and invested_today + budget <= max_daily_invest:
                volume = round(budget / price, 6)
                place_market_order(coin, "buy", volume)
                print(f"[🟢 Kauf] {volume} {coin} zu {price:.2f} EUR")
                portfolio[coin] = {"price": price, "amount": volume}
                invested_today += budget

            # Verkaufsentscheidung
            if coin in portfolio:
                buy_price = portfolio[coin]["price"]
                amount = portfolio[coin]["amount"]
                gain = (price - buy_price) / buy_price

                if gain >= profit_target_pct or gain <= -stop_loss_pct or rsi > 70:
                    place_market_order(coin, "sell", amount)
                    print(f"[🔴 Verkauf] {amount} {coin} zu {price:.2f} EUR | Gewinn: {gain*100:.2f}%")
                    del portfolio[coin]

        print("-" * 40)
        time.sleep(price_check_interval)

run_bot()