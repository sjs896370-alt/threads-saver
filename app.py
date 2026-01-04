import streamlit as st
import os

# 強制安裝瀏覽器零件
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
    cookie_str = st.text_area("請貼入 Threads Cookies (JSON 格式)", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在同步資料，請耐心等待約 30 秒..."):
            try:
                # 修正網域錯誤：將 .com 替換為 .net
                fixed_cookie_str = cookie_str.replace(".threads.com", ".threads.net")
                cookies = json.loads(fixed_cookie_str)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    context.add_cookies(cookies)

                    page = context.new_page()
                    # 直接前往收藏夾
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    time.sleep(10) # 雲端加載較慢

                    data_list = []
                    # 抓取邏輯
                    for _ in range(5):
                        # 抓取貼文文字
                        posts = page.locator('div[style*="white-space: pre-wrap"]').all()
                        for post in posts:
                            txt = post.inner_text()
                            if txt and txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})
                        page.keyboard.press("End")
                        time.sleep(3)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df)
                        st.download_button("📥 下載檔案", df.to_csv(index=False).encode('utf-8-sig'), "threads.csv")
                    else:
                        st.warning("⚠️ 抓不到內容。請確認您在電腦上是否能正常開啟 Threads 收藏頁面。")
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤：{str(e)}")
