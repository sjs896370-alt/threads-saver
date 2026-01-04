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
    cookie_str = st.text_area("請貼入匯出的 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在攻克網址陷阱，抓取貼文中..."):
            try:
                # 1. 處理並統一 Cookie 網域
                raw_cookies = json.loads(cookie_str)
                fixed_cookies = []
                for ck in raw_cookies:
                    # 不管是 .com 還是 .net，全部給予 .net 網域權限
                    if "domain" in ck:
                        domain = ck["domain"].replace("threads.com", "threads.net")
                        ck["domain"] = domain if domain.startswith(".") else "." + domain
                    if "sameSite" in ck:
                        ss = str(ck["sameSite"]).capitalize()
                        ck["sameSite"] = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    fixed_cookies.append(ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(viewport={'width': 1280, 'height': 800})
                    context.add_cookies(fixed_cookies)
                    page = context.new_page()

                    # 2. 嘗試三個可能的路徑，直到抓到內容為止
                    urls = [
                        "https://www.threads.net/settings/saved",
                        "https://www.threads.net/saved",
                        "https://www.threads.com/saved"
                    ]
                    
                    data_list = []
                    for target_url in urls:
                        if len(data_list) > 0: break # 抓到了就跳出
                        
                        page.goto(target_url, wait_until="networkidle", timeout=60000)
                        time.sleep(15) # 等待渲染

                        # 3. 深度搜索貼文內容 (使用包含 '人生清單' 這種格式的選擇器)
                        # 嘗試抓取所有可能包含內文的層級
                        potential_posts = page.locator('span[dir="auto"], div[dir="auto"]').all()
                        
                        for post in potential_posts:
                            txt = post.inner_text().strip()
                            # 過濾條件：長度要夠、排除系統文字、排除重複
                            if len(txt) > 10 and not any(x in txt for x in ["Policy", "Terms", "Report", "working", "lost"]):
                                if txt not in [d['內容'] for d in data_list]:
                                    data_list.append({"內容": txt, "抓取時間": time.strftime("%H:%M")})
                        
                        # 往下滾動一點點再抓一次
                        page.mouse.wheel(0, 1000)
                        time.sleep(3)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        csv = df.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button("📥 下載 Excel (修正亂碼)", data=csv, file_name="threads_saved.csv", mime="text/csv")
                    else:
                        page.screenshot(path="debug.png")
                        st.warning("⚠️ 還是抓不到。這通常是 Cookie 權限不足，請確保在電腦『看到貼文』時匯出。")
                        with open("debug.png", "rb") as f:
                            st.download_button("📸 下載 Debug 截圖看原因", f, "debug.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
