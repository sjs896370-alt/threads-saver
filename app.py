import streamlit as st
import os
import random

if "browser_fixed" not in st.session_state:
    os.system("playwright install chromium")
    st.session_state.browser_fixed = True

import pandas as pd
from playwright.sync_api import sync_playwright
import time
import json

st.set_page_config(page_title="Threads 收藏全紀錄", page_icon="🧵")
st.title("🧵 Threads 收藏全紀錄同步")

with st.sidebar:
    st.header("🔑 登入設定")
    cookie_str = st.text_area("請貼入最新 JSON Cookies", height=200)
    scroll_times = st.slider("想要往下挖多深？(捲動次數)", 5, 50, 15)

if st.button("🚀 開始深度同步所有收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with sync_playwright() as p:
            try:
                # 1. 更加嚴謹的 Cookie 注入
                raw_cookies = json.loads(cookie_str)
                final_cookies = []
                for ck in raw_cookies:
                    ss = str(ck.get("sameSite", "Lax")).capitalize()
                    ss = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    for d in [".threads.net", ".threads.com"]:
                        final_cookies.append({
                            "name": ck["name"], "value": ck["value"],
                            "domain": d, "path": "/", "secure": True, "sameSite": ss
                        })

                browser = p.chromium.launch(headless=True)
                # 模擬更真實的視窗大小
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                )
                context.add_cookies(final_cookies)
                page = context.new_page()

                # 2. 繞路策略：先去首頁，再點進收藏 (模擬真人操作)
                status_text.text("🕵️ 正在通過門禁...")
                page.goto("https://www.threads.net/", wait_until="networkidle")
                time.sleep(random.uniform(3, 5))
                
                page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                time.sleep(8)

                all_posts_data = []
                seen_texts = set()

                # 3. 模擬人手捲動抓取
                for i in range(scroll_times):
                    # 抓取畫面中所有可能的貼文
                    # Threads 的貼文通常在具有特定屬性的 div 或 span 中
                    elements = page.locator('div[dir="auto"], span[dir="auto"]').all()
                    
                    current_page_count = 0
                    for el in elements:
                        txt = el.inner_text().strip()
                        # 排除掉長度太短或包含錯誤關鍵字的雜訊
                        if len(txt) > 15 and not any(x in txt for x in ["Not all", "Log in", "Terms", "Policy", "Back", "© 2026"]):
                            if txt not in seen_texts:
                                seen_texts.add(txt)
                                all_posts_data.append({"內容": txt, "抓取序號": len(all_posts_data)+1})
                                current_page_count += 1
                    
                    # 模擬真人滑動：有快有慢
                    page.mouse.wheel(0, random.randint(800, 1200))
                    time.sleep(random.uniform(1.5, 3.0))
                    
                    # 更新進度
                    progress = (i + 1) / scroll_times
                    progress_bar.progress(progress)
                    status_text.text(f"⏳ 正在同步中... 已捲動 {i+1} 次，累計抓到 {len(all_posts_data)} 則貼文")

                if all_posts_data:
                    df = pd.DataFrame(all_posts_data)
                    st.success(f"🎉 同步完成！共抓取 {len(df)} 則貼文")
                    st.dataframe(df, use_container_width=True)
                    st.download_button("📥 下載完整收藏 CSV", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_full_backup.csv")
                else:
                    st.error("⚠️ 偵測到讀取限制。請在電腦上重新整理 Threads 收藏頁面，並重新匯出 Cookie 後再試。")
                    page.screenshot(path="error_debug.png")
                    with open("error_debug.png", "rb") as f:
                        st.download_button("📸 下載 Debug 截圖", f, "debug.png")

                browser.close()
            except Exception as e:
                st.error(f"❌ 發生程式錯誤：{str(e)}")

