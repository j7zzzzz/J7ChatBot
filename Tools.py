# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 11:59:34 2026

@author: user
"""

import requests

def get_current_exchange_rate(currency: str):
    """查詢即時匯率，例如 USD, JPY"""
    # 這裡使用外部公開 API
    url = "https://api.exchangerate-api.com/v4/latest/TWD"
    response = requests.get(url)
    data = response.json()
    return f"目前的 1 台幣 (TWD) 可兌換 {data['rates'][currency.upper()]} {currency.upper()}"
