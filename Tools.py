# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 11:59:34 2026

@author: user
"""
import os
import requests

def get_current_exchange_rate(base_currency: str, target_currency: str):
    """
    獲取指定貨幣之間的最新匯率。
    例如：base_currency='USD', target_currency='TWD'
    """
    # 這裡使用外部公開 API
    # url = "https://api.exchangerate-api.com/v4/latest/TWD"
    api_key = os.getenv("EXCHANGE_RATE_API_KEY")
    url = f"https://v6.exchangerate-api.com/v6/{api_key}/pair/{base_currency}/{target_currency}"
    
    try:
        response = requests.get(url)
        data = response.json()
        if data["result"] == "success":
            rate = data["conversion_rate"]
            return f"目前的匯率是 1 {base_currency} = {rate} {target_currency}"
        else:
            return "暫時無法取得匯率資訊，請檢查貨幣代碼是否正確。"
    except Exception as e:
        return f"連線錯誤：{e}"
