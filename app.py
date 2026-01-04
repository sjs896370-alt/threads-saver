import streamlit as st
import os

# --- 核心補丁：在啟動前強行安裝瀏覽器 ---
if "browser_fixed" not in st.session_state:
    with st.spinner("🔧 正在初始化雲端環境... 這大約需要一分鐘"):
        os.system("playwright install chromium")
    st.session_state.browser_fixed = True
# ---------------------------------------

import pandas as pd
from playwright.sync_api import sync_playwright
import time
import json

st.set_page_config(page_title="Threads 收藏管理員", page_icon="🧵")
st.title("🧵 Threads 收藏管理員")

with st.sidebar:
    st.header("🔑 登入設定")
    cookie_str = st.text_area("請貼入 Threads Cookies (JSON 格式)", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在抓取收藏內容..."):
            try:
                with sync_playwright() as p:
                    # 雲端必須 headless=True
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    
                    # 注入 Cookie
                    cookies = json.loads(cookie_str)
                    context.add_cookies(cookies)

                    page = context.new_page()
                    page.goto("https://www.threads.net/settings/saved", timeout=60000)
                    time.sleep(10) # 雲端多等一下

                    data_list = []
                    # 抓取前 3 頁試試
                    for _ in range(3):
                        posts = page.locator('div[style*="white-space: pre-wrap"]').all()
                        for post in posts:
                            txt = post.inner_text()
                            if txt and txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})
                        page.keyboard.press("End")
                        time.sleep(3)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df)
                    else:
                        st.warning("⚠️ 沒抓到內容。請確認 Cookie 是否為最新的 JSON 格式。")
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤：{str(e)}")
