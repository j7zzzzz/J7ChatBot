# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 11:28:52 2026

@author: user
"""

import streamlit as st
import google.generativeai as genai
import os
from Tools import get_current_exchange_rate
from dotenv import load_dotenv

# 1. 頁面設定
st.set_page_config(page_title = "有記憶的 AI 助手", page_icon="🤖")
st.title("💬 J7的有腦 RAG 對話機器人")

# 2. 載入金鑰
load_dotenv(dotenv_path = ".env")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key = api_key)

# 3. 初始化「持久化」的聊天紀錄 (Session State)
if "chat_history" not in st.session_state:
    # 這裡存放給 Gemini 看的歷史紀錄
    st.session_state.chat_history = []

# 4. 側邊欄：處理文件知識庫
with st.sidebar:
    st.header("文件中心")
    uploaded_file = st.file_uploader("上傳你的知識文件 (.txt)", type = ("txt"))
    if uploaded_file:
        content = uploaded_file.read().decode("utf-8")
        st.success("檔案已掛載至 AI 記憶中")
    else:
        content = "目前沒有參考文件。"
        
    if st.button("清除對話紀錄"):
        st.session_state.chat_history = []
        st.rerun()

# 5. 顯示歷史對話畫面
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. 聊天輸入框
if prompt := st.chat_input("請輸入您的問題..."):
    # 顯示使用者的訊息
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 呼叫 Gemini 並帶入記憶
    with st.chat_message("assistant"):
        try:
            # 這裡我們使用 Gemini 的內建 ChatSession 功能
            model = genai.GenerativeModel(
                            model_name = "models/gemini-2.5-flash", 
                            tools = [get_current_exchange_rate] # 把外部工具放進清單
                            )        

            # 啟動對話會話，並帶入之前的歷史紀錄
            chat = model.start_chat(
                history=[
                    {"role": m["role"], "parts": [m["content"]]} 
                    for m in st.session_state.chat_history
                    ], 
                enable_automatic_function_calling = True # 確保工具能自動跑
                )
            
            # 將知識庫內容作為「系統設定」或是「第一則指令」
            # 為了讓記憶最準確，我們每次把知識庫放在 Prompt 最前面
            # 使用 chat.send_message 發送問題，記憶才會串接
            full_query = f"【背景知識】：{content}\n\n【使用者問題】：{prompt}"   
            response = chat.send_message(full_query)
            
            answer = response.text
            st.markdown(answer)
            
            # 將這對對話存入歷史紀錄
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "model", "content": answer})
            
        except Exception as e:
            st.error(f"發生錯誤：{e}")        
