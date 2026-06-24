import requests
from bs4 import BeautifulSoup
import json
import re
import os
import time
from datetime import datetime
from playwright.sync_api import sync_playwright

# ====================== 配置区 ======================
GZ_LIST_URL = "https://www.mice-gz.org/hz/a/48/index.html?p=true"
SZ_LIST_URL = "https://www.szcec.com/szcec/cn-schedule/zl/index.html"

# 兜底备用数据
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
        "pastData": "2025年展商800家，展出面积6万㎡",
        "list": "西门子、ABB、汇川技术等",
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
        "pastData": "2025年展商1500家，专业观众12万人次",
        "list": "马扎克、大族激光、发那科等",
        "source": "备用数据"
    }
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 行业关键词库，自动匹配展会行业
INDUSTRY_MAP = {
    "智能制造": ["智能装备", "自动化", "机床", "工业机器人", "智能制造"],
    "电子半导体": ["电子", "半导体", "电路板", "元器件", "显示"],
    "新能源": ["光伏", "储能", "新能源汽车", "锂电"],
    "包装印刷": ["包装", "印刷", "标签"],
    "医疗器械": ["医疗", "器械", "医用"],
    "建材家居": ["家具", "建材", "卫浴", "门窗"],
    "综合展会": []
}

# ====================== 工具函数 ======================
def cn_date_to_std(date_raw: str) -> list:
    """中文日期字符串转 [startDate, endDate]"""
    clean_text = re.sub(r"\s|展出时间：|时间：", "", date_raw.strip())
    year_match = re.search(r"(\d{4})年", clean_text)
    md_matches = re.findall(r"(\d{1,2})月(\d{1,2})日", clean_text)

    if not md_matches:
        return ["", ""]
    base_year = year_match.group(1) if year_match else str(datetime.now().year)
    s_m, s_d = md_matches[0]
    start = f"{base_year}-{int(s_m):02d}-{int(s_d):02d}"
    if len(md_matches) >= 2:
        e_m, e_d = md_matches[1]
        end = f"{base_year}-{int(e_m):02d}-{int(e_d):02d}"
    else:
        end = start
    return [start, end]

def auto_match_industry(name: str) -> str:
    """根据展会名称自动匹配行业"""
    for industry, keywords in INDUSTRY_MAP.items():
        for kw in keywords:
            if kw in name:
                return industry
    return "综合展会"

def get_rendered_html(url: str, wait_second=3) -> str | None:
    """Playwright无头浏览器加载JS渲染后的完整HTML（适配GitHub Actions）"""
    try:
        with sync_playwright() as p:
            # 无头模式，无GPU，兼容CI环境
            browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-gpu"])
            context = browser.new_context(user_agent=HEADERS["User-Agent"])
            page = context.new_page()
            page.goto(url, timeout=20000)
            page.wait_for_timeout(wait_second * 1000)
            html = page.content()
            browser.close()
            return html
    except Exception as e:
        print(f"页面渲染失败 {url}: {str(e)}")
        return None

# ====================== 广州展会解析（列表+详情） ======================
def parse_gz_all(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("ul.list li")
    print(f"【广州】列表页匹配到展会数量：{len(items)}")
    res = []
    for idx, item in enumerate(items):
        try:
            a_tag = item.select_one("a")
            if not a_tag:
                continue
            exh_name = a_tag.get_text(strip=True)
            detail_href = a_tag.get("href", "")
            detail_url = f"https://www.mice-gz.org{detail_href}" if detail_href.startswith("/") else detail_href

            # 列表页基础信息
            date_text = item.select_one("span.date").get_text(strip=True) if item.select_one("span.date") else ""
            venue_text = item.select_one("span.address").get_text(strip=True) if item.select_one("span.address") else "广交会展馆"
            start_dt, end_dt = cn_date_to_std(date_text)
            industry = auto_match_industry(exh_name)

            # 进入详情页抓取：往届数据、参展商、官方报名链接
            past_data = ""
            exhib_list = ""
            reg_link = detail_url
            detail_html = get_rendered_html(detail_url, wait_second=2)
            if detail_html:
                d_soup = BeautifulSoup(detail_html, "html.parser")
                # 往届数据
                past_node = d_soup.select_one(".history-data, .past-info")
                if past_node:
                    past_data = past_node.get_text(strip=True)
                # 参展商列表
                exhib_node = d_soup.select_one(".brand-list, .exhibitor")
                if exhib_node:
                    exhib_list = exhib_node.get_text(strip=True)
                # 官方报名链接
                reg_a = d_soup.select_one("a.register-btn")
                if reg_a and reg_a.get("href"):
                    reg_link = reg_a["href"]

            res.append({
                "id": f"gz_{idx}",
                "name": exh_name,
                "type": "国内",
                "industry": industry,
                "location": "广州",
                "venue": venue_text,
                "startDate": start_dt,
                "endDate": end_dt,
                "regLink": reg_link,
                "pastData": past_data,
                "list": exhib_list,
                "source": "广州会展网爬虫"
            })
            time.sleep(0.5)
        except Exception as e:
            print(f"【广州】第{idx}条展会解析异常：{str(e)}")
    return res

# ====================== 深圳展会解析（列表+详情） ======================
def parse_sz_all(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.list-item")
    print(f"【深圳】列表页匹配到展会数量：{len(items)}")
    res = []
    for idx, item in enumerate(items):
        try:
            title_a = item.select_one("div.title a")
            if not title_a:
                continue
            exh_name = title_a.get_text(strip=True)
            detail_href = title_a.get("href", "")
            detail_url = f"https://www.szcec.com{detail_href}" if detail_href.startswith("/") else detail_href

            # 列表基础信息
            date_text = item.select_one("div.time").get_text(strip=True) if item.select_one("div.time") else ""
            venue_text = item.select_one("div.address").get_text(strip=True) if item.select_one("div.address") else "深圳国际会展中心"
            start_dt, end_dt = cn_date_to_std(date_text)
            industry = auto_match_industry(exh_name)

            # 详情页拓展字段
            past_data = ""
            exhib_list = ""
            reg_link = detail_url
            detail_html = get_rendered_html(detail_url, wait_second=2)
            if detail_html:
                d_soup = BeautifulSoup(detail_html, "html.parser")
                past_node = d_soup.select_one(".history, .past-stat")
                if past_node:
                    past_data = past_node.get_text(strip=True)
                exhib_node = d_soup.select_one(".exhibitor-name, .brand")
                if exhib_node:
                    exhib_list = exhib_node.get_text(strip=True)
                reg_btn = d_soup.select_one("a.sign-up")
                if reg_btn and reg_btn.get("href"):
                    reg_link = reg_btn["href"]

            res.append({
                "id": f"sz_{idx}",
                "name": exh_name,
                "type": "国内",
                "industry": industry,
                "location": "深圳",
                "venue": venue_text,
                "startDate": start_dt,
                "endDate": end_dt,
                "regLink": reg_link,
                "pastData": past_data,
                "list": exhib_list,
                "source": "深圳会展中心爬虫"
            })
            time.sleep(0.5)
        except Exception as e:
            print(f"【深圳】第{idx}条展会解析异常：{str(e)}")
    return res

# ====================== 主程序 ======================
def main():
    total_data = []
    print("====== 开始抓取广州展会列表 ======")
    gz_html = get_rendered_html(GZ_LIST_URL, wait_second=4)
    if gz_html:
        gz_data = parse_gz_all(gz_html)
        total_data.extend(gz_data)
        print(f"广州成功抓取 {len(gz_data)} 条完整展会数据")
    else:
        print("广州列表页面渲染失败，无数据")

    print("\n====== 开始抓取深圳展会列表 ======")
    sz_html = get_rendered_html(SZ_LIST_URL, wait_second=4)
    if sz_html:
        sz_data = parse_sz_all(sz_html)
        total_data.extend(sz_data)
        print(f"深圳成功抓取 {len(sz_data)} 条完整展会数据")
    else:
        print("深圳列表页面渲染失败，无数据")

    print(f"\n线上爬虫合计抓取：{len(total_data)} 条")
    # 无线上数据则启用备用数据
    if len(total_data) == 0:
        print("警告：线上未抓到任何展会，加载备用兜底数据")
        output = BACKUP_EXHIBITIONS
    else:
        print("使用线上实时抓取数据，覆盖备用数据")
        output = total_data

    # 强制写入JSON，覆盖旧文件
    output_file = "exhibitions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 校验文件写入结果
    if os.path.exists(output_file):
        file_size = os.stat(output_file).st_size
        print(f"\n文件写入完成 | 路径: {output_file} | 文件大小: {file_size} Byte | 最终展会总数: {len(output)}")
    else:
        raise Exception("JSON文件写入失败，文件不存在！")

if __name__ == "__main__":
    main()
