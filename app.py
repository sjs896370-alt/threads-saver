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
    cookie_str = st.text_area("請貼入電腦端匯出的 JSON Cookies", height=200)

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先貼入 Cookies！")
    else:
        with st.spinner("🕵️ 正在攻克最後關卡，請稍候..."):
            try:
                # 1. 徹底清洗並強制網域同步
                raw_cookies = json.loads(cookie_str)
                final_cookies = []
                for ck in raw_cookies:
                    # 同時設定 .com 與 .net 的權限
                    for domain in [".threads.com", ".threads.net"]:
                        new_ck = {
                            "name": ck["name"],
                            "value": ck["value"],
                            "domain": domain,
                            "path": "/",
                            "secure": True
                        }
                        # 修正 SameSite 報錯
                        ss = str(ck.get("sameSite", "Lax")).capitalize()
                        new_ck["sameSite"] = ss if ss in ["Strict", "Lax", "None"] else "Lax"
                        final_cookies.append(new_ck)
                
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    context.add_cookies(final_cookies)
                    page = context.new_page()

                    # 2. 先前往首頁，確保登入狀態被系統認可
                    page.goto("https://www.threads.net/", wait_until="networkidle")
                    time.sleep(5)
                    
                    # 3. 前往收藏頁面 (嘗試官方正確路徑)
                    page.goto("https://www.threads.net/settings/saved", wait_until="networkidle")
                    time.sleep(15) 

                    data_list = []
                    # 4. 強力掃描：搜尋包含數字條列特徵的文字
                    # 這是抓取「1.北歐看極光」這類內容的最穩路徑
                    all_text_elements = page.locator('span[dir="auto"], div[style*="white-space: pre-wrap"]').all()
                    
                    for el in all_text_elements:
                        txt = el.inner_text().strip()
                        # 過濾掉錯誤訊息與短文字
                        if len(txt) > 10 and not any(x in txt for x in ["Not all who wander", "Log in", "Terms", "Policy"]):
                            if txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "抓取時間": time.strftime("%H:%M")})

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel (修正亂碼)", df.to_csv(index=False, encoding="utf-8-sig").encode('utf-8-sig'), "threads_saved.csv")
                    else:
                        st.warning("⚠️ 還是抓不到。請在電腦上點開『收藏』頁面，確保看得到內容後重新匯出一次 Cookie。")
                    
                    browser.close()
            except Exception as e:
                st.error(f"❌ 發生錯誤：{str(e)}")
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤：{str(e)}")
