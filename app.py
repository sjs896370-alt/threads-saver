import streamlit as st
import os

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
    scroll_times = st.slider("想要往下挖多深？(捲動次數)", 1, 30, 10)

if st.button("🚀 開始深度同步所有收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在深挖收藏夾，這可能需要一分鐘..."):
            try:
                raw_cookies = json.loads(cookie_str)
                cleaned_cookies = []
                for ck in raw_cookies:
                    for d in [".threads.com", ".threads.net"]:
                        new_ck = {
                            "name": ck["name"], "value": ck["value"],
                            "domain": d, "path": "/", "secure": True
                        }
                        ss = str(ck.get("sameSite", "Lax")).capitalize()
                        new_ck["sameSite"] = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                        cleaned_cookies.append(new_ck)

                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(cleaned_cookies)
                    page = context.new_page()

                    # 前往收藏夾
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    time.sleep(10)

                    all_posts = set() # 使用集合來去重
                    
                    # --- 深度捲動邏輯 ---
                    for i in range(scroll_times):
                        # 抓取當前畫面所有文字區塊
                        elements = page.locator('span[dir="auto"], div[dir="auto"]').all()
                        for el in elements:
                            txt = el.inner_text().strip()
                            # 過濾雜訊：長度大於10，且不是系統按鈕文字
                            if len(txt) > 10 and not any(x in txt for x in ["Not all", "Log in", "Terms", "Policy", "Back"]):
                                all_posts.add(txt)
                        
                        # 執行向下滑動
                        page.mouse.wheel(0, 2000)
                        time.sleep(2) # 等待新內容加載
                        st.write(f"正在掃描第 {i+1} 頁內容...")

                    if all_posts:
                        data_list = [{"內容": p, "同步序號": i+1} for i, p in enumerate(list(all_posts))]
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 大功告成！總共抓到 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載完整收藏清單", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_full_backup.csv")
                    else:
                        st.error("⚠️ 掃描完成但沒抓到內容，請確認您的 Cookie 是否已過期。")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
