import requests
from bs4 import BeautifulSoup
import json
import re
import os

# ======= 配置区 =======
# 广州会展网 URL
GZ_URL = "https://www.mice-gz.org/hz/a/48/index.html?p=true"
# 深圳会展中心 URL
SZ_URL = "https://www.szcec.com/szcec/cn-schedule/zl/index.html"
# 备用展会数据 (如果网站抓取失败，则使用这些数据)
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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def get_html(url, timeout=10):
    """获取页面HTML，失败返回None"""
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding
        return resp.text
    except Exception as e:
        print(f"请求失败 {url}: {e}")
        return None

def parse_gz_exhibitions(html):
    """解析广州会展网页面，返回展会列表"""
    soup = BeautifulSoup(html, 'html.parser')
    exhibitions = []
    # --- 请根据实际页面结构调整选择器 ---
    # 示例：假设展会在 class="exh-item" 的div中
    items = soup.select('.exh-item')
    for item in items:
        try:
            name = item.select_one('.title').get_text(strip=True)
            date_text = item.select_one('.date').get_text(strip=True)
            # 简单提取日期
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', date_text)
            start_date = dates[0] if dates else ''
            end_date = dates[1] if len(dates) > 1 else start_date
            # 其他字段暂时留空，可自行扩展
            exhibitions.append({
                "id": f"gz_{len(exhibitions)}",
                "name": name,
                "type": "国内",
                "industry": "",
                "location": "广州",
                "venue": "",
                "startDate": start_date,
                "endDate": end_date,
                "regLink": GZ_URL,
                "pastData": "",
                "list": "",
                "source": "广州会展网爬虫"
            })
        except Exception as e:
            print(f"解析广州展会条目出错: {e}")
    return exhibitions

def parse_sz_exhibitions(html):
    """解析深圳会展中心页面，返回展会列表"""
    soup = BeautifulSoup(html, 'html.parser')
    exhibitions = []
    # --- 请根据实际页面结构调整选择器 ---
    # 示例：假设展会在 class="event-item" 中
    items = soup.select('.event-item')
    for item in items:
        try:
            name = item.select_one('.event-title').get_text(strip=True)
            date_text = item.select_one('.event-date').get_text(strip=True)
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', date_text)
            start_date = dates[0] if dates else ''
            end_date = dates[1] if len(dates) > 1 else start_date
            exhibitions.append({
                "id": f"sz_{len(exhibitions)}",
                "name": name,
                "type": "国内",
                "industry": "",
                "location": "深圳",
                "venue": "",
                "startDate": start_date,
                "endDate": end_date,
                "regLink": SZ_URL,
                "pastData": "",
                "list": "",
                "source": "深圳会展中心爬虫"
            })
        except Exception as e:
            print(f"解析深圳展会条目出错: {e}")
    return exhibitions

def main():
    all_exhibitions = []

    # 尝试抓取广州
    gz_html = get_html(GZ_URL)
    if gz_html:
        gz_exh = parse_gz_exhibitions(gz_html)
        all_exhibitions.extend(gz_exh)
        print(f"广州抓取成功：{len(gz_exh)} 条")
    else:
        print("广州抓取失败，将使用备用数据")

    # 尝试抓取深圳
    sz_html = get_html(SZ_URL)
    if sz_html:
        sz_exh = parse_sz_exhibitions(sz_html)
        all_exhibitions.extend(sz_exh)
        print(f"深圳抓取成功：{len(sz_exh)} 条")
    else:
        print("深圳抓取失败，将使用备用数据")

    # 如果所有抓取都失败（或抓取结果为空），则使用备用数据
    if not all_exhibitions:
        print("所有抓取未获取到数据，启用备用展会列表")
        all_exhibitions = BACKUP_EXHIBITIONS

    # 保存为 JSON 文件
    with open('exhibitions.json', 'w', encoding='utf-8') as f:
        json.dump(all_exhibitions, f, ensure_ascii=False, indent=2)

    print(f"成功生成 exhibitions.json，共 {len(all_exhibitions)} 条展会")

if __name__ == "__main__":
    main()
