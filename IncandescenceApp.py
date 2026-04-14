import os
import re
import json
import tkinter as tk
from tkinter import filedialog
import webbrowser
from bs4 import BeautifulSoup

# ==========================================
# 前端阅读器模板 (纯本地、动态挂载、极致性能)
# ==========================================
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>IncandescenceReader</title>
    <style>
        :root { --border: #2f3336; --text-gray: #71767b; --x-blue: #1d9bf0; }
        body { background: #000; color: #e7e9ea; font-family: -apple-system, sans-serif; margin: 0; overflow-x: hidden; }
        .app { max-width: 600px; margin: 0 auto; border-left: 1px solid var(--border); border-right: 1px solid var(--border); min-height: 100vh; position: relative; background: #000; }
        .sidebar { position: fixed; top: 100px; width: 220px; color: var(--text-gray); font-size: 14px; line-height: 1.6; }
        .sidebar h3 { color: #fff; font-size: 16px; margin-bottom: 10px; }
        .sidebar-left { left: calc(50% - 300px - 250px); text-align: right; border-right: 2px solid var(--border); padding-right: 20px; }
        .sidebar-right { right: calc(50% - 300px - 250px); text-align: left; border-left: 2px solid var(--border); padding-left: 20px; }
        .sidebar img { width: 100%; border-radius: 8px; margin-top: 10px; border: 1px solid var(--border); }
        .profile-header { border-bottom: 1px solid var(--border); }
        .banner { width: 100%; height: 200px; background: #333; object-fit: cover; }
        .profile-info { padding: 12px 16px; position: relative; }
        .avatar-img { width: 80px; height: 80px; border-radius: 50%; border: 4px solid #000; position: absolute; top: -45px; background: #222; }
        .profile-names { margin-top: 40px; }
        .p-name { font-size: 20px; font-weight: 800; display: block; }
        .p-user { color: var(--text-gray); font-size: 15px; }
        .p-bio { margin: 12px 0; font-size: 15px; white-space: pre-wrap; }
        .p-meta { color: var(--text-gray); font-size: 14px; display: flex; gap: 15px; flex-wrap: wrap; }
        .p-meta span { display: flex; align-items: center; gap: 4px; }
        .p-meta a { color: var(--x-blue); text-decoration: none; }
        .p-meta a:hover { text-decoration: underline; }
        .search-area { padding: 10px 16px; border-bottom: 1px solid var(--border); position: sticky; top: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(12px); z-index: 10; }
        .search-inner { background: #202327; border-radius: 999px; padding: 8px 16px; }
        #search { background: transparent; border: none; color: #fff; width: 100%; outline: none; }

        /* 虚拟列表卡片容器：增加鼠标悬浮反馈 */
        .virtual-item { border-bottom: 1px solid var(--border); width: 100%; cursor: pointer; transition: background 0.2s; }
        .virtual-item:hover { background-color: rgba(255, 255, 255, 0.03); }

        /* 强行覆盖注入的 HTML 的暗黑样式 */
        .tweet-container, .embedded-tweet-container, #nonjsonview { 
            background-color: transparent !important; 
            color: #e7e9ea !important; 
            border-color: #2f3336 !important; 
            margin: 0 !important;
            padding: 16px 16px 8px 16px !important;
            border-radius: 0 !important;
            border: none !important;
            width: auto !important;
            max-width: 100% !important;
        }
        .embedded-tweet-container { border: 1px solid #2f3336 !important; border-radius: 12px !important; margin-bottom: 8px !important; padding: 12px !important; }
        .tweet-content, .tweet-author-name { color: #e7e9ea !important; }
        .tweet-author-username, .date a { color: #71767b !important; }
        a { color: #1d9bf0 !important; }
        * { box-shadow: none !important; }

        /* 【核心修复：补齐丢失的原网页 Flex 排版样式】 */
        .tweet-author { display: flex; flex-direction: row; align-items: center; margin-bottom: 10px; }
        .tweet-author-info { display: flex; flex-direction: column; justify-content: center; }
        .tweet-author-profile-image { display: flex; align-items: center; }

        /* 限制配图并保护头像 */
        .tweet-image, .tweet-content img, video { max-width: 100%; border-radius: 12px; margin-top: 10px; display: block; }
        .tweet-author-profile-image img { width: 48px !important; height: 48px !important; border-radius: 50% !important; margin-right: 12px; margin-top: 0 !important; }

        /* 隐藏原网页自带的底部时间戳，使用独立数据 */
        p.date { display: none !important; }

        /* 恢复弹窗详情页样式 */
        #detail-view { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: #000; z-index: 100; }
        iframe { width: 100%; height: calc(100% - 60px); border: none; background: #fff; }
        .back-btn { height: 60px; line-height: 60px; padding: 0 20px; color: var(--x-blue); cursor: pointer; font-weight: bold; border-bottom: 1px solid var(--border); background: #000; }
    </style>
</head>
<body>
    <div class="sidebar sidebar-left">
        <h3>IncandescenceReader</h3>
        <h3>「白炽阅读器」</h3>
        <p style="margin-top:20px;"><b>By Kiriakigawa Nozomi</b><br>AKA 芝士灵狐</p>
        <p>谨以此工具纪念@AnIncandescence</p>
        <p>在此对向本项目作出贡献的协助者<br>致以最崇高的敬意与诚挚的感谢</p>
        <p>特别致谢:<br>本项目基于@sjshb57的<br>基础建设与技术标准</p>
    </div>
    <div class="sidebar sidebar-right">
        <h3>使用指南</h3>
        <p>1. <b>检索</b>：支持按关键词或日期<br>[yyyy mm dd]搜索<br>
           2. <b>详情</b>：点击对应帖文即展开原始HTML文件<br>
    </div>
    <div class="app">
        <div class="profile-header">
            <img class="banner" id="p-banner">
            <div class="profile-info">
                <img class="avatar-img" id="p-avatar">
                <div class="profile-names">
                    <span class="p-name" id="p-name">Loading...</span>
                    <span class="p-user" id="p-username">@handle</span>
                </div>
                <div class="p-bio" id="p-bio"></div>
                <div class="p-meta"><span id="p-loc"></span><span id="p-link"></span></div>
            </div>
        </div>
        <div class="search-area">
            <div class="search-inner"><input type="text" id="search" placeholder="搜索关键词或日期..."></div>
        </div>
        <div id="list"></div>
    </div>

    <div id="detail-view">
        <div class="back-btn" onclick="closeDetail()">← 返回</div>
        <iframe id="viewer"></iframe>
    </div>

<script src="profile.js"></script>
<script src="archive_data.js"></script>

<script>
    let lastScrollY = 0;

    // 1. 渲染资料栏
    if (typeof profileData !== 'undefined') {
        document.getElementById('p-name').innerText = profileData.name;
        document.getElementById('p-username').innerText = profileData.username;
        document.getElementById('p-bio').innerText = profileData.bio;
        document.getElementById('p-avatar').src = profileData.avatar;
        document.getElementById('p-banner').src = profileData.banner;
        if(profileData.location) document.getElementById('p-loc').innerHTML = `📍 ${profileData.location}`;
        if(profileData.link) document.getElementById('p-link').innerHTML = `🔗 <a href="${profileData.link}" target="_blank">${profileData.link.replace(/^https?:\\/\\//, '')}</a>`;
    }

    // 2. 交叉观察器 (Intersection Observer)
    const listEl = document.getElementById('list');
    let itemHeights = {}; 

    function renderList(items) {
        listEl.innerHTML = items.map(item => `
            <div class="virtual-item" id="item-${item.id}" style="min-height: 150px;" onclick="openDetail('${item.id}')">
                <div class="content-box"></div>
                <div class="post-date" style="padding: 0 16px 16px 16px; font-size: 13px; color: var(--text-gray);">发布于: ${item.date}</div>
            </div>
        `).join('');

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                const id = entry.target.id.replace('item-', '');
                const itemData = items.find(i => i.id === id);
                const contentBox = entry.target.querySelector('.content-box');

                if (entry.isIntersecting) {
                    if (!contentBox.hasChildNodes()) {
                        contentBox.innerHTML = itemData.html;
                        entry.target.style.height = 'auto'; 
                    }
                } else {
                    if (contentBox.hasChildNodes()) {
                        const rect = entry.target.getBoundingClientRect();
                        itemHeights[id] = rect.height;
                        entry.target.style.height = rect.height + 'px';
                        contentBox.innerHTML = ''; 
                    }
                }
            });
        }, { rootMargin: '1000px 0px' });

        document.querySelectorAll('.virtual-item').forEach(el => observer.observe(el));
    }

    // 打开与关闭详情页
    function openDetail(id) {
        lastScrollY = window.scrollY;
        document.getElementById('viewer').src = 'html/' + id;
        document.getElementById('detail-view').style.display = 'block';
        document.body.style.overflow = 'hidden';
    }

    function closeDetail() {
        document.getElementById('detail-view').style.display = 'none';
        document.getElementById('viewer').src = '';
        document.body.style.overflow = 'auto';
        window.scrollTo(0, lastScrollY);
    }

    if (typeof archiveData !== 'undefined') {
        renderList(archiveData);

        document.getElementById('search').oninput = (e) => {
            const kw = e.target.value.toLowerCase();
            const filtered = archiveData.filter(i => (i.text && i.text.toLowerCase().includes(kw)) || i.date.includes(kw));
            renderList(filtered);
        };
    }
</script>
</body>
</html>
"""


def main():
    root = tk.Tk()
    root.withdraw()
    print("=== 白炽阅读器 ===")

    target_dir = filedialog.askdirectory(title="选择档案根目录 (html目录的上一级)")
    if not target_dir:
        print("未选择目录，程序退出。")
        return

    html_dir = os.path.join(target_dir, 'html')
    if not os.path.exists(html_dir):
        print(f"错误：未找到 'html' 文件夹！")
        input("按回车键退出...")
        return

    data_js_path = os.path.join(target_dir, 'archive_data.js')
    profile_json_path = os.path.join(target_dir, 'profile.json')
    profile_js_path = os.path.join(target_dir, 'profile.js')

    # ========== 1. 修复读取个人资料 (profile.json -> profile.js) ==========
    print("\n[系统提示] 正在同步个人资料...")
    profile_data = {
        "name": "待完善的资料",
        "username": "@Username",
        "bio": "请在 profile.json中\n修改这些信息。",
        "location": "未知位置",
        "link": "----",
        "avatar": "avatar/dummy_avatar.jpg",
        "banner": "avatar/dummy_banner.jpg"
    }

    if os.path.exists(profile_json_path):
        try:
            with open(profile_json_path, 'r', encoding='utf-8') as f:
                user_profile = json.load(f)
                profile_data.update(user_profile)
        except Exception as e:
            print(f"读取旧 profile.json 失败: {e}")
    else:
        with open(profile_json_path, 'w', encoding='utf-8') as f:
            json.dump(profile_data, f, ensure_ascii=False, indent=2)

    with open(profile_js_path, 'w', encoding='utf-8') as f:
        f.write("const profileData = ")
        json.dump(profile_data, f, ensure_ascii=False, indent=2)
        f.write(";")

    # ========== 2. 强力提取并修复推文内部图片路径 ==========
    print("[系统提示] 正在提取HTML内容并刷新缓存(这只需几秒钟)...")
    archive_data = []
    files = [f for f in os.listdir(html_dir) if f.endswith('.html')]

    for filename in files:
        path = os.path.join(html_dir, filename)
        with open(path, 'r', encoding='utf-8') as f:
            html_content = f.read()

            date_match = re.search(r'var dateString = "([^"]+)"', html_content)
            date_only = date_match.group(1).split('T')[0] if date_match else "未知时间"

            soup = BeautifulSoup(html_content, 'html.parser')
            container = soup.find('div', class_='tweet-container') or soup.find('article')

            text = ""
            html_str = ""
            if container:
                text_el = container.find('div', {'data-testid': 'tweetText'})
                text = text_el.get_text() if text_el else container.get_text()

                for tag in container.find_all(['img', 'video', 'source']):
                    src_attr = 'src' if tag.has_attr('src') else ('data-src' if tag.has_attr('data-src') else None)
                    if src_attr:
                        val = tag[src_attr]
                        if '../' in val:
                            tag[src_attr] = val.replace('../', '')
                        elif val.startswith('/'):
                            tag[src_attr] = val[1:]

                html_str = str(container)

            archive_data.append({
                "id": filename,
                "date": date_only,
                "text": text[:300].replace('\n', ' '),
                "html": html_str
            })

    archive_data.sort(key=lambda x: x['date'], reverse=True)
    with open(data_js_path, 'w', encoding='utf-8') as f:
        f.write("const archiveData = ")
        json.dump(archive_data, f, ensure_ascii=False)
        f.write(";")

    # ========== 3. 生成并打开阅读器 ==========
    reader_path = os.path.join(target_dir, 'Reader.html')
    with open(reader_path, 'w', encoding='utf-8') as f:
        f.write(HTML_TEMPLATE)

    print("\n✅ 所有数据及修复已完成！")
    print("正在唤起您的浏览器加载本地档...")

    webbrowser.open(f"file://{os.path.abspath(reader_path)}")


if __name__ == "__main__":
    main()