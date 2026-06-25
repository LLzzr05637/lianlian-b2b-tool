import time
import json
import re
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

# ======= 配置区 =======
# 广州会展网 URL
GZ_URL = "https://www.mice-gz.org/hz/a/48/index.html?p=true"
# 深圳会展中心 URL
SZ_URL = "https://www.szcec.com/szcec/cn-schedule/zl/index.html"
# 备用展会数据
BACKUP_EXHIBITIONS = [
    {
        "id": "backup_1",
        "name": "广州国际智能制造技术与装备展览会",
        "type": "国内",
        "industry": "智能制造",
        "location": "广州",
        "venue": "广交会展馆",
        "startDate": "2026-03-03",
        "endDate": "2026-03-05",
        "regLink": "https://www.mice-gz.org/hz/a/48/index.html?p=true",
        "pastData": "2025年展商800家",
        "list": "西门子、ABB等",
        "source": "备用数据"
    },
    {
        "id": "backup_2",
        "name": "深圳国际工业制造技术展(ITES)",
        "type": "国内",
        "industry": "机械制造",
        "location": "深圳",
        "venue": "深圳国际会展中心",
        "startDate": "2026-03-30",
        "endDate": "2026-04-02",
        "regLink": "https://www.szcec.com/szcec/cn-schedule/zl/index.html",
        "pastData": "2025年展商1500家",
        "list": "马扎克、大族激光等",
        "source": "备用数据"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Referer": "https://www.baidu.com/",
    "Connection": "keep-alive"
}

def get_rendered_html(url, wait_second=3):
    """使用playwright加载JS动态页面，返回完整渲染后html，失败返回None"""
    try:
        with sync_playwright() as p:
            # 无头模式，不弹出浏览器窗口
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(extra_http_headers=HEADERS)
            page = context.new_page()
            page.goto(url, timeout=15000)
            # 等待页面展会列表加载完成
            time.sleep(wait_second)
            html = page.content()
            browser.close()
            print(f"✅ 页面加载成功: {url}")
            return html
    except Exception as e:
        print(f"❌ 页面加载失败 {url}: {str(e)}")
        return None

def parse_gz_exhibitions(html):
    """解析广州会展网"""
    soup = BeautifulSoup(html, 'html.parser')
    exhibitions = []
    # 适配官网最新DOM选择器
    items = soup.select('div.list-content ul li')
    print(f"广州页面匹配到列表条目: {len(items)} 个")

    for idx, item in enumerate(items):
        try:
            a_tag = item.select_one('a')
            name = a_tag.get_text(strip=True) if a_tag else ""
            date_span = item.select_one('span')
            date_text = date_span.get_text(strip=True) if date_span else ""

            # 正则匹配年月日
            date_res = re.findall(r"\d{4}-\d{2}-\d{2}", date_text)
            start_date = date_res[0] if date_res else ""
            end_date = date_res[1] if len(date_res) >= 2 else start_date

            exhibitions.append({
                "id": f"gz_{idx}",
                "name": name,
                "type": "国内",
                "industry": "",
                "location": "广州",
                "venue": "广交会展馆",
                "startDate": start_date,
                "endDate": end_date,
                "regLink": GZ_URL,
                "pastData": "",
                "list": "",
                "source": "广州会展网爬虫"
            })
        except Exception as e:
            print(f"广州单条解析异常: {str(e)}")
            continue
    return exhibitions

def parse_sz_exhibitions(html):
    """解析深圳会展中心"""
    soup = BeautifulSoup(html, 'html.parser')
    exhibitions = []
    items = soup.select('div.jiudian div.list')
    print(f"深圳页面匹配到列表条目: {len(items)} 个")

    for idx, item in enumerate(items):
        try:
            title_a = item.select_one('div.title a')
            name = title_a.get_text(strip=True) if title_a else ""
            time_div = item.select_one('div.time')
            date_text = time_div.get_text(strip=True) if time_div else ""

            date_res = re.findall(r"\d{4}-\d{2}-\d{2}", date_text)
            start_date = date_res[0] if date_res else ""
            end_date = date_res[1] if len(date_res) >= 2 else start_date

            exhibitions.append({
                "id": f"sz_{idx}",
                "name": name,
                "type": "国内",
                "industry": "",
                "location": "深圳",
                "venue": "深圳国际会展中心",
                "startDate": start_date,
                "endDate": end_date,
                "regLink": SZ_URL,
                "pastData": "",
                "list": "",
                "source": "深圳会展中心爬虫"
            })
        except Exception as e:
            print(f"深圳单条解析异常: {str(e)}")
            continue
    return exhibitions

def main():
    all_data = []

    # 抓取广州展会
    gz_html = get_rendered_html(GZ_URL)
    if gz_html:
        gz_list = parse_gz_exhibitions(gz_html)
        all_data.extend(gz_list)
        print(f"广州有效抓取 {len(gz_list)} 条展会\n")
    else:
        print("广州抓取失败，补充广州备用数据")
        all_data.append(BACKUP_EXHIBITIONS[0])

    time.sleep(2)

    # 抓取深圳展会
    sz_html = get_rendered_html(SZ_URL)
    if sz_html:
        sz_list = parse_sz_exhibitions(sz_html)
        all_data.extend(sz_list)
        print(f"深圳有效抓取 {len(sz_list)} 条展会\n")
    else:
        print("深圳抓取失败，补充深圳备用数据")
        all_data.append(BACKUP_EXHIBITIONS[1])

    # 双重兜底：如果抓取+单站点备用后依然为空，加载全部备用
    if not all_data:
        print("无任何抓取数据，加载全部备用展会数据")
        all_data = BACKUP_EXHIBITIONS

    # 输出JSON文件
    with open("exhibitions.json", "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"\n===================== 完成 =====================")
    print(f"共生成 {len(all_data)} 条展会数据，已保存至 exhibitions.json")

if __name__ == "__main__":
    main()
