import streamlit as st
import os

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
        with st.spinner("🕵️ 正在攻克導向陷阱..."):
            try:
                raw_cookies = json.loads(cookie_str)
                fixed_cookies = []
                for ck in raw_cookies:
                    # 同時給予 .com 和 .net 的權限，防止跳轉時掉資訊
                    domain = ck.get("domain", "")
                    if "threads.com" in domain or "threads.net" in domain:
                        # 複製一份給 .net
                        ck_net = ck.copy()
                        ck_net["domain"] = domain.replace("threads.com", "threads.net")
                        if "sameSite" in ck_net:
                            ss = str(ck_net["sameSite"]).capitalize()
                            ck_net["sameSite"] = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                        fixed_cookies.append(ck_net)
                    fixed_cookies.append(ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # 模擬真實電腦的 User Agent
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        extra_http_headers={"Referer": "https://www.threads.net/"}
                    )
                    context.add_cookies(fixed_cookies)
                    page = context.new_page()

                    # 第一步：先去首頁「紮根」，讓系統認可你的 Cookie
                    page.goto("https://www.threads.net/", wait_until="networkidle")
                    time.sleep(5)
                    
                    # 第二步：直接進入收藏夾，並等待較長時間讓 Ajax 內容跑完
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    
                    # 滾動幾次以確保觸發內容加載
                    for _ in range(3):
                        page.mouse.wheel(0, 500)
                        time.sleep(2)

                    data_list = []
                    # 深度翻找：除了 span，也找 div 和 article 標籤
                    selectors = ['div[dir="auto"]', 'span[dir="auto"]', 'article']
                    
                    for selector in selectors:
                        elements = page.locator(selector).all()
                        for el in elements:
                            txt = el.inner_text().strip()
                            # 過濾掉雜訊
                            if len(txt) > 10 and not any(x in txt for x in ["Log in", "Forgot", "Policy", "Terms", "Instagram", "About"]):
                                if txt not in [d['內容'] for d in data_list]:
                                    data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_final.csv")
                    else:
                        # 失敗的話，看看到底跳轉到了哪裡
                        st.warning(f"⚠️ 目前停留在：{page.url}")
                        page.screenshot(path="final_debug.png")
                        with open("final_debug.png", "rb") as f:
                            st.download_button("📸 下載 Debug 截圖", f, "debug_view.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤：{str(e)}")
