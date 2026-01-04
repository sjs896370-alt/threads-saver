import streamlit as st
import os

# 初始化環境
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
    cookie_str = st.text_area("請貼入匯出的 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在同步收藏貼文..."):
            try:
                # 1. 徹底清洗並建立雙網域 Cookie
                raw_cookies = json.loads(cookie_str)
                final_cookies = []
                for ck in raw_cookies:
                    # 修正 SameSite 格式
                    ss = str(ck.get("sameSite", "Lax")).capitalize()
                    ss = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    
                    # 同時為 .com 和 .net 注入同一份 Cookie 權限
                    for d in [".threads.com", ".threads.net"]:
                        final_cookies.append({
                            "name": ck["name"],
                            "value": ck["value"],
                            "domain": d,
                            "path": "/",
                            "secure": True,
                            "sameSite": ss
                        })
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(final_cookies)
                    page = context.new_page()

                    # 2. 先前往首頁紮根，再轉向收藏夾
                    page.goto("https://www.threads.net/", wait_until="networkidle")
                    time.sleep(5)
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    
                    # 延長等待時間確保內容加載
                    time.sleep(20) 

                    data_list = []
                    # 3. 搜尋貼文內容
                    # Threads 的收藏內容通常在特定 dir="auto" 的 span 或 div 中
                    elements = page.locator('span[dir="auto"], div[style*="white-space: pre-wrap"]').all()
                    
                    for el in elements:
                        txt = el.inner_text().strip()
                        # 排除系統訊息，鎖定真正的收藏文字
                        if len(txt) > 5 and not any(x in txt for x in ["Not all", "wander", "working", "Terms", "Policy"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads.csv")
                    else:
                        # 失敗診斷
                        page.screenshot(path="debug.png")
                        st.warning("⚠️ 沒抓到貼文。請確認您在電腦端正開著『收藏夾』畫面並重新匯出 Cookie。")
                        with open("debug.png", "rb") as f:
                            st.download_button("📸 下載 Debug 截圖", f, "debug.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
