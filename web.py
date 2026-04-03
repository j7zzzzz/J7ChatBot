# -*- coding: utf-8 -*-
"""
Created on Fri Apr  3 11:28:52 2026

@author: user
"""

import streamlit as st
import google.generativeai as genai
import os
import asyncio
from Tools import get_current_exchange_rate
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# 1. 頁面設定
st.set_page_config(page_title = "匯率查詢 AI 助手", page_icon="🤖")
st.title("💬 J7腦的匯率查詢機器人")

# 2. 載入金鑰
load_dotenv(dotenv_path = ".env")
api_key = os.getenv("GEMINI_API_KEY")
genai.configure(api_key = api_key)

# 3. 定義 MCP 工具轉換函式
@st.cache_resource
def get_cached_mcp_tools():
    """
    使用 st.cache_resource 確保工具清單只會抓取一次，
    之後直接從記憶體讀取，大幅提升反應速度。
    """
    return asyncio.run(get_mcp_tools())

async def get_mcp_tools():

    server_params = StdioServerParameters(
        command = "python",
        args = ["Tools.py"], # 確保 Tools.py 已經改寫成 FastMCP 版本
    )
    
    # 建立連線並抓取工具描述
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            mcp_tools_response = await session.list_tools()
            
            gemini_functions = []
            for tool in mcp_tools_response.tools:
                gemini_functions.append({
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema 
                })
            return gemini_functions
        
# ---------------------------------------------------------
# Streamlit 畫面開始
# ---------------------------------------------------------

# 4. 初始化「持久化」的聊天紀錄 (Session State)
if "chat_history" not in st.session_state:
    # 這裡存放給 Gemini 看的歷史紀錄
    st.session_state.chat_history = []

# 5. 側邊欄：處理文件知識庫
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

# 6. 顯示歷史對話畫面
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 7. 聊天輸入框
if prompt := st.chat_input("請輸入您的問題..."):
    # 顯示並存入使用者訊息 (只存一次) ---
    with st.chat_message("user"):
        st.markdown(prompt)
    # 注意：不要在這裡 append，統一在最後處理，或只存原始 prompt

    # 呼叫 Gemini 並帶入記憶與文件內容
    with st.chat_message("assistant"):
        try:
            # --- MCP 關鍵整合區 ---
            # 因為 Streamlit 不支援直接 await，我們用 asyncio.run 執行工具獲取
            with st.spinner("正在呼叫 MCP 工具..."):
                mcp_tools = get_cached_mcp_tools()
                
            # 將知識庫放入 system_instruction
            # 這樣 content 就會作為「背景設定」，不會重複出現在對話歷史中
            # 這裡我們使用 Gemini 的內建 ChatSession 功能
            model = genai.GenerativeModel(
                            model_name = "models/gemini-2.5-flash", 
                            tools = [{"function_declarations": mcp_tools}], # 把外部工具放進清單
                            system_instruction = f"你是一個助手。參考知識：{content}"
                            )        

            # 清理歷史紀錄格式
            formatted_history = []
            for m in st.session_state.chat_history:
                # 確保只傳送必要的內容，避免格式錯誤
                role = "user" if m["role"] == "user" else "model"
                formatted_history.append({"role": role, "parts": [m["content"]]})
            
            # Gemini 的歷史紀錄角色名稱是 "user" 和 "model" (不是 assistant)
            # 啟動對話會話，並帶入之前的歷史紀錄
            chat = model.start_chat(
                history = formatted_history, 
                enable_automatic_function_calling = True # 確保工具能自動跑
                )
            
            # 發送純問題，不重複發送知識庫
            # 使用 chat.send_message 發送問題，記憶才會串接
            response = chat.send_message(prompt)
            
            answer = response.text
            st.markdown(answer)
            
            # 將這對對話存入歷史紀錄
            # 存入原始的 prompt 與 answer，不含背景知識標籤
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            st.session_state.chat_history.append({"role": "model", "content": answer})
            
            # 選做：限制歷史紀錄長度 (例如只留最近 10 組對話) 以省 token
            # if len(st.session_state.chat_history) > 20:
                # st.session_state.chat_history = st.session_state.chat_history[-20:]
            
        except Exception as e:
            st.error(f"發生錯誤：{e}")        
