import os
import json
import re
import asyncio
import tkinter as tk           # 新增：导入 tkinter
from tkinter import filedialog # 新增：导入文件选择对话框
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

# --- 1. 弹出窗口让用户选择目标文件夹 ---
root = tk.Tk()
root.withdraw() # 隐藏多余的主窗口
print("请在弹出的窗口中选择要处理的数据库文件夹 (例如 data 文件夹)...")
BASE_DIR = filedialog.askdirectory(title="选择要处理的数据库文件夹 (如 data)")

if not BASE_DIR:
    print("未选择任何文件夹，程序退出。")
    exit()

# --- 2. 根据用户选择的文件夹，动态生成路径 ---
HTML_DIR = os.path.join(BASE_DIR, 'html')
PREVIEW_DIR = os.path.join(BASE_DIR, 'previews')
INDEX_FILE = os.path.join(BASE_DIR, 'index.json')

if not os.path.exists(PREVIEW_DIR):
    os.makedirs(PREVIEW_DIR)


async def process_files():
    index_data = []

    async with async_playwright() as p:
        # 启动浏览器
        browser = await p.chromium.launch()
        # 建议使用深色模式截图，更符合 X 的原生质感
        context = await browser.new_context(viewport={'width': 600, 'height': 800}, color_scheme='dark')
        page = await context.new_page()

        files = [f for f in os.listdir(HTML_DIR) if f.endswith('.html')]
        print(f"检测到 {len(files)} 个文件，开始处理...")

        for filename in files:
            path = os.path.join(HTML_DIR, filename)

            with open(path, 'r', encoding='utf-8') as f:
                html_content = f.read()

                # --- 核心改进：通过正则表达式提取精确日期 ---
                # 匹配 var dateString = "2026-04-04T21:35:38.000Z";
                date_match = re.search(r'var dateString = "([^"]+)"', html_content)
                if date_match:
                    # 提取出的格式是 ISO 字符串，我们取 T 之前的部分（日期）
                    full_date = date_match.group(1)
                    date_only = full_date.split('T')[0]
                else:
                    date_only = "未知日期"

                # --- 提取正文用于搜索 ---
                soup = BeautifulSoup(html_content, 'html.parser')
                # 尝试抓取 X 的正文容器，如果抓不到则抓取全文文本
                text_el = soup.find('div', {'data-testid': 'tweetText'}) or soup.find('article')
                text = text_el.get_text() if text_el else soup.get_text()

            # --- 生成预览图 ---
            preview_name = f"{filename}.jpg"
            preview_path = os.path.join(PREVIEW_DIR, preview_name)
            abs_url = "file://" + os.path.abspath(path)

            try:
                await page.goto(abs_url, wait_until="networkidle")

                # --- 强制注入暗黑模式样式 ---
                dark_style = """
                            html, body, .tweet-container, .embedded-tweet-container, #nonjsonview { 
                                background-color: #000000 !important; 
                                color: #e7e9ea !important; 
                                border-color: #2f3336 !important; 
                            }
                            .tweet-content, .tweet-author-name { color: #e7e9ea !important; }
                            .tweet-author-username, .date, .date a { color: #71767b !important; }
                            a { color: #1d9bf0 !important; }
                            * { box-shadow: none !important; }
                            """
                await page.add_style_tag(content=dark_style)
                await asyncio.sleep(0.5)

                # --- 核心修改：精准定位你样本中的推文容器 ---
                # 优先寻找 .tweet-container，找不到再找官方的 article
                tweet_element = await page.query_selector('.tweet-container') or \
                                await page.query_selector('article') or \
                                await page.query_selector('[data-testid="tweet"]')

                if tweet_element:
                    # 只截取这个容器的实际大小，彻底消除多余黑边
                    await tweet_element.screenshot(path=preview_path, type="jpeg", quality=75)
                else:
                    # 极少数情况下的保底机制
                    await page.screenshot(path=preview_path, full_page=True, type="jpeg", quality=75)
            except Exception as e:
                print(f"截图出错 {filename}: {e}")

            index_data.append({
                "id": filename,
                "date": date_only,
                "text": text[:300].replace('\n', ' '),  # 存入索引，方便搜索
                "preview": preview_name
            })
            print(f"已完成: {filename} | 抓取日期: {date_only}")

        await browser.close()

    # 按照日期降序排列（最新的在最前）
    index_data.sort(key=lambda x: x['date'], reverse=True)

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, ensure_ascii=False, indent=2)

    print("\n--- 处理完毕 ---")
    print(f"索引已保存至 {INDEX_FILE}")


asyncio.run(process_files())