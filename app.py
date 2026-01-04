import streamlit as st
import pandas as pd
from playwright.sync_api import sync_playwright
import time
import json

# 設定頁面標題
st.set_page_config(page_title="Threads 收藏管理員", page_icon="🧵")
st.title("🧵 Threads 收藏管理員")

# 側邊欄設定
with st.sidebar:
    st.header("🔑 登入設定")
    cookie_str = st.text_area("請貼入 Threads Cookies (JSON 格式)", help="在電腦使用 EditThisCookie 匯出")
    st.info("雲端版需要 Cookie 才能繞過登入驗證。")

# 主功能按鈕
if st.button("🚀 開始同步收藏"):
    if not cookie_str:
        st.error("請先在左側貼入 Cookies！")
    else:
        with st.spinner("正在啟動雲端瀏覽器並載入資料..."):
            try:
                with sync_playwright() as p:
                    # 啟動無頭瀏覽器
                    browser = p.chromium.launch(headless=True)
                    context = browser.new_context()
                    
                    # 注入 Cookie
                    cookies = json.loads(cookie_str)
                    context.add_cookies(cookies)

                    page = context.new_page()
                    # 直接前往收藏頁面
                    page.goto("https://www.threads.net/settings/saved")
                    time.sleep(5) # 等待頁面加載

                    data_list = []
                    # 模擬捲動並抓取
                    for i in range(5):
                        # 抓取文字內容
                        posts = page.locator('div[style*="white-space: pre-wrap"]').all()
                        for post in posts:
                            txt = post.inner_text()
                            if txt and txt not in [d['內容'] for d in data_list]:
                                data_list.append({"內容": txt, "抓取時間": time.strftime("%H:%M:%S")})
                        
                        page.keyboard.press("End")
                        time.sleep(2)

                    if data_list:
                        df = pd.DataFrame(data_list)
                        st.success(f"成功抓取 {len(df)} 則貼文！")
                        st.dataframe(df, use_container_width=True)
                        
                        # 導出 CSV
                        csv = df.to_csv(index=False, encoding="utf-8-sig")
                        st.download_button(
                            label="📥 下載 Excel (CSV)",
                            data=csv,
                            file_name="threads_saved.csv",
                            mime="text/csv",
                        )
                    else:
                        st.warning("沒抓到內容，請檢查 Cookie 是否失效或收藏夾是否為空。")
                    
                    browser.close()
            except Exception as e:
                st.error(f"發生錯誤：{str(e)}")
