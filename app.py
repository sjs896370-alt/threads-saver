import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import json

st.set_page_config(page_title="Threads 收藏管理員", page_icon="🧵")
st.title("🧵 Threads 收藏管理員")

with st.sidebar:
    st.header("🔑 登入設定")
    cookie_str = st.text_area("請貼入 Threads Cookies (JSON 格式)", height=200)
    st.info("💡 提示：請在電腦使用 EditThisCookie 匯出 JSON 後貼到這裡。")

if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("❌ 請先在左側選單貼入 Cookies！")
    else:
        with st.spinner("正在啟動雲端瀏覽器..."):
            try:
                with sync_playwright() as p:
                    # 使用預裝的 chromium
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    
                    # 注入 Cookie
                    cookies = json.loads(cookie_str)
                    context.add_cookies(cookies)

                    page = context.new_page()
                    page.goto("https://www.threads.net/settings/saved")
                    time.sleep(7) # 雲端網路較慢，多等兩秒

                    data_list = []
                    for i in range(5):
                        posts = page.locator('div[style*="white-space: pre-wrap"]').all()
                        for post in posts:
                            txt = post.inner_text()
                            if txt and txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "時間": time.strftime("%H:%M")})
                        page.keyboard.press("End")
                        time.sleep(2)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"✅ 成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        st.download_button("📥 下載 Excel", df.to_csv(index=False).encode('utf-8-sig'), "threads.csv")
                    else:
                        st.warning("⚠️ 沒抓到內容，請檢查 Cookie 是否貼對。")
                    browser.close()
            except Exception as e:
                st.error(f"❌ 錯誤訊息：{str(e)}")
                st.info("提示：如果還是顯示 Executable doesn't exist，請嘗試重啟 App (Reboot)。")
