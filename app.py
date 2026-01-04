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
    cookie_str = st.text_area("請貼入電腦端匯出的 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在抓取你的『人生清單』，請稍候..."):
            try:
                # 1. 處理 Cookie：強制鎖定網域為 .threads.net
                raw_cookies = json.loads(cookie_str)
                fixed_cookies = []
                for ck in raw_cookies:
                    # 統一將 SameSite 轉為規範格式，防止報錯
                    ss = str(ck.get("sameSite", "Lax")).capitalize()
                    ss = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                    
                    fixed_cookies.append({
                        "name": ck["name"],
                        "value": ck["value"],
                        "domain": ".threads.net",
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
                    context.add_cookies(fixed_cookies)
                    page = context.new_page()

                    # 2. 直接攻入收藏夾路徑
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle", timeout=60000)
                    
                    # 給予充足時間加載內容（你的清單很長，需要時間）
                    time.sleep(20) 
                    
                    # 滾動一下確保所有內容都浮現
                    page.mouse.wheel(0, 1000)
                    time.sleep(5)

                    data_list = []
                    # 3. 搜尋包含「1.北歐看極光」這類特徵的文字
                    # 我們鎖定所有可能的文字標籤
                    all_text = page.locator('span[dir="auto"], div[dir="auto"]').all()
                    
                    for el in all_text:
                        txt = el.inner_text().strip()
                        # 過濾掉錯誤訊息與短字，鎖定真正的清單內容
                        if len(txt) > 10 and not any(x in txt for x in ["Not all", "wander", "Policy", "Terms", "Report"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功同步 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        # 提供 Excel 下載
                        csv = df.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button("📥 下載 Excel (修正亂碼)", csv, file_name="threads_saved.csv")
                    else:
                        # 拍張照看看為什麼沒抓到
                        page.screenshot(path="debug.png")
                        st.warning("⚠️ 目前沒抓到內容。請在電腦上確認能否看到清單。")
                        with open("debug.png", "rb") as f:
                            st.download_button("📸 下載 Debug 截圖", f, "debug.png")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
