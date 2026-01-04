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
    cookie_str = st.text_area("請貼入 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在攻克最後關卡..."):
            try:
                # --- 1. 極度嚴格的 Cookie 清洗 ---
                raw_cookies = json.loads(cookie_str)
                cleaned_cookies = []
                for ck in raw_cookies:
                    # 修正網域：不管是 .com 還是 .net 全部支援
                    domain = ck.get("domain", "").replace("threads.com", "threads.net")
                    if not domain.startswith("."): domain = "." + domain
                    
                    # 建立乾淨的 Cookie 字典
                    new_ck = {
                        "name": ck["name"],
                        "value": ck["value"],
                        "domain": domain,
                        "path": ck.get("path", "/"),
                        "secure": True
                    }
                    
                    # 強制處理 SameSite (這是報錯主因)
                    ss = str(ck.get("sameSite", "Lax")).capitalize()
                    if ss in ["Strict", "Lax", "None"]:
                        new_ck["sameSite"] = ss
                    else:
                        new_ck["sameSite"] = "Lax" # 預設安全值
                        
                    cleaned_cookies.append(new_ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    # 模擬真實電腦環境，這是進入收藏夾的關鍵
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(cleaned_cookies)
                    page = context.new_page()

                    # 先去首頁「刷臉」
                    page.goto("https://www.threads.net/", wait_until="networkidle")
                    time.sleep(5)
                    
                    # 前往真正的收藏頁面
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    time.sleep(15) 

                    data_list = []
                    # 深度抓取包含「人生清單」的內容
                    potential_targets = page.locator('div[dir="auto"], span[dir="auto"]').all()
                    
                    for target in potential_targets:
                        txt = target.inner_text().strip()
                        # 排除掉法律條款雜訊，鎖定有意義的內容
                        if len(txt) > 10 and not any(x in txt for x in ["Policy", "Terms", "Instagram", "About"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載修正亂碼版 Excel", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_saved.csv")
                    else:
                        st.warning("⚠️ 抓不到內容。請在電腦上確認能否看到收藏，並重新匯出 Cookie。")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤：{str(e)}")
