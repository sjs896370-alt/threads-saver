import streamlit as st
import os

# 環境初始化
if "browser_fixed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.browser_fixed = True

import pandas as pd
from playwright.sync_api import sync_playwright
import time
import json

st.set_page_config(page_title="Threads 收藏管理員", page_icon="🧵")
st.title("🧵 Threads 收藏管理員")

with st.sidebar:
    st.header("🔑 登入設定")
    cookie_str = st.text_area("請貼入最新匯出的 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在同步收藏夾..."):
            try:
                # 處理並過濾 Cookie
                raw_cookies = json.loads(cookie_str)
                fixed_cookies = []
                for ck in raw_cookies:
                    # 強制修正網域與屬性
                    if "domain" in ck:
                        ck["domain"] = ck["domain"].replace(".threads.com", ".threads.net")
                    if "sameSite" in ck:
                        ss = str(ck["sameSite"]).capitalize()
                        ck["sameSite"] = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    fixed_cookies.append(ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # 模擬電腦版寬螢幕
                    context = browser.new_context(viewport={'width': 1280, 'height': 800})
                    context.add_cookies(fixed_cookies)

                    page = context.new_page()
                    # 直接前往目標網址
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle", timeout=60000)
                    
                    # 等待內容載入
                    time.sleep(15) 

                    data_list = []
                    # 抓取貼文，並避開頁底條款
                    elements = page.query_selector_all('div[dir="auto"], span[dir="auto"]')
                    for el in elements:
                        txt = el.inner_text().strip()
                        # 過濾掉法律條款與短字
                        if len(txt) > 5 and not any(x in txt for x in ["Policy", "Terms", "Cookies", "Report"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel (修正亂碼)", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads.csv")
                    else:
                        # 這是診斷關鍵：如果抓不到，拍一張目前的畫面
                        page.screenshot(path="debug.png")
                        st.warning("⚠️ 沒抓到貼文。可能被擋在登入頁面了。")
                        with open("debug.png", "rb") as f:
                            st.download_button("📸 查看程式現在看到的畫面 (Debug)", f, "debug.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
