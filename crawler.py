import requests
from bs4 import BeautifulSoup
import json
import re

def crawl_gz_exhibitions():
    url = "https://www.mice-gz.org/hz/a/48/index.html?p=true"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.encoding = 'utf-8'
        soup = BeautifulSoup(resp.text, 'html.parser')
        exhibitions = []
        # 根据实际页面结构调整选择器（示例，需按F12查看元素）
        for item in soup.select('.exh-item'):
            name = item.select_one('.title').text.strip()
            date_text = item.select_one('.date').text.strip()
            # 简单日期解析（示例）
            dates = re.findall(r'\d{4}-\d{2}-\d{2}', date_text)
            start_date = dates[0] if len(dates) > 0 else ''
            end_date = dates[1] if len(dates) > 1 else start_date
            # 其他字段自行补充
            exhibitions.append({
                "id": f"gz_{len(exhibitions)}",
                "name": name,
                "industry": "",
                "location": "广州",
                "startDate": start_date,
                "endDate": end_date,
                "regLink": "",
                "pastData": "",
                "list": "",
                "source": "广州会展网自动抓取"
            })
        return exhibitions
    except Exception as e:
        print(f"广州爬取失败: {e}")
        return []

def crawl_sz_exhibitions():
    url = "https://www.szcec.com/szcec/cn-schedule/zl/index.html"
    # 类似结构，解析深圳展会
    return []  # 暂时留空

def main():
    all_exhibitions = []
    all_exhibitions.extend(crawl_gz_exhibitions())
    all_exhibitions.extend(crawl_sz_exhibitions())
    # 保存为 JSON 文件
    with open('exhibitions.json', 'w', encoding='utf-8') as f:
        json.dump(all_exhibitions, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
