import streamlit as st
import os

# 初始化 Playwright
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
    cookie_str = st.text_area("請貼入最新 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在同步收藏夾..."):
            try:
                # 1. 清洗並同步 .com 與 .net 的 Cookie
                raw_cookies = json.loads(cookie_str)
                final_cookies = []
                for ck in raw_cookies:
                    # 修正 SameSite 報錯
                    ss = str(ck.get("sameSite", "Lax")).capitalize()
                    ss = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    
                    # 強制為 .net 網域建立一份權限
                    new_ck = {
                        "name": ck["name"],
                        "value": ck["value"],
                        "domain": ".threads.net",
                        "path": "/",
                        "secure": True,
                        "sameSite": ss
                    }
                    final_cookies.append(new_ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(final_cookies)
                    page = context.new_page()

                    # 2. 直接進入 .net 的收藏頁面 (避開跳轉陷阱)
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle", timeout=60000)
                    
                    # 等待更長的時間讓你的「人生清單」跑出來
                    time.sleep(20) 
                    
                    # 滾動一下頁面觸發加載
                    page.mouse.wheel(0, 1000)
                    time.sleep(5)

                    data_list = []
                    # 3. 抓取包含「1. 北歐看極光」這種格式的文字
                    # 我們搜尋所有的文字區塊
                    elements = page.locator('span[dir="auto"], div[style*="pre-wrap"]').all()
                    
                    for el in elements:
                        txt = el.inner_text().strip()
                        # 過濾掉錯誤訊息與系統文字
                        if len(txt) > 8 and not any(x in txt for x in ["Not all", "wander", "working", "Report", "Policy"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                    
                    # 同時給予兩個網域相同的鑰匙
                    for domain in [".threads.com", ".threads.net"]:
                        new_ck = ck.copy()
                        new_ck["domain"] = domain
                        new_ck["sameSite"] = ss
                        if "id" in new_ck: del new_ck["id"] # 移除 Playwright 不認識的欄位
                        fixed_cookies.append(new_ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(fixed_cookies)
                    page = context.new_page()

                    # 2. 先去首頁「紮根」
                    page.goto("https://www.threads.net/", wait_until="networkidle")
                    time.sleep(5)
                    
                    # 3. 直接導向你的目標收藏頁
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    
                    # 4. 模擬人類捲動，確保「人生清單」內容被載入
                    for _ in range(3):
                        page.mouse.wheel(0, 1000)
                        time.sleep(3)

                    data_list = []
                    # 5. 精準抓取：尋找包含你截圖中「1.」這種條列格式的區塊
                    elements = page.locator('span[dir="auto"], div[style*="white-space: pre-wrap"]').all()
                    
                    for el in elements:
                        txt = el.inner_text().strip()
                        # 過濾掉雜訊文字，保留真正貼文
                        if len(txt) > 10 and not any(x in txt for x in ["Not all", "wander", "working", "Instagram", "Policy", "Terms"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel (修正亂碼)", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_final.csv")
                    else:
                        # 失敗的話，拍張照看看它在哪
                        page.screenshot(path="debug_final.png")
                        st.warning("⚠️ 還是沒抓到內容。請嘗試在電腦重新整理『收藏夾』後，再次匯出 Cookie 貼入。")
                        with open("debug_final.png", "rb") as f:
                            st.download_button("📸 下載 Debug 截圖", f, "debug.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
