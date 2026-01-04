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
        with st.spinner("🕵️ 正在處理並同步資料..."):
            try:
                # 1. 處理 JSON 格式
                raw_cookies = json.loads(cookie_str)
                fixed_cookies = []
                
                for ck in raw_cookies:
                    # 修正網域：統一使用 .threads.net 確保登入有效
                    if "domain" in ck:
                        ck["domain"] = ck["domain"].replace(".threads.com", ".threads.net")
                    
                    # 修正 SameSite：這是截圖報錯的主因
                    # Playwright 只接受 'Strict', 'Lax', 或 'None' (注意大小寫)
                    if "sameSite" in ck:
                        ss = str(ck["sameSite"]).capitalize()
                        if ss not in ["Strict", "Lax", "None"]:
                            ss = "Lax" # 預設安全值
                        ck["sameSite"] = ss
                    fixed_cookies.append(ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1"
                    )
                    context.add_cookies(fixed_cookies)

                    page = context.new_page()
                    # 嘗試前往收藏頁面
                    page.goto("https://www.threads.net/settings/saved", wait_until="domcontentloaded")
                    
                    # 雲端需多預留加載時間
                    time.sleep(15) 

                    data_list = []
                    # 抓取邏輯
                    for _ in range(5):
                        # 抓取包含文字的區塊
                        posts = page.locator('div[style*="white-space: pre-wrap"]').all()
                        if not posts:
                            posts = page.locator('span[dir="auto"]').all()
                            
                        for post in posts:
                            txt = post.inner_text()
                            if len(txt) > 2 and txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})
                        
                        page.keyboard.press("End")
                        time.sleep(3)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載檔案", df.to_csv(index=False).encode('utf-8-sig'), "threads_saved.csv")
                    else:
                        st.warning("⚠️ 抓不到內容，請確認 Cookie 是否仍有效（建議電腦重新整理後再次匯出）。")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
