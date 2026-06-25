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

# 2026年全年完整备用数据（广州·深圳·佛山，覆盖实物贸易展会）
BACKUP_EXHIBITIONS = [
    # ---------- 广州 ----------
    {"id":"bak_gz1","name":"广州国际智能制造技术与装备展览会","type":"国内","industry":"智能制造","location":"广州","venue":"广交会展馆","startDate":"2026-03-03","endDate":"2026-03-05","regLink":"https://www.mice-gz.org/hz/a/48/index.html?p=true","pastData":"2025年展商800家，专业观众3.2万人次，展出面积6万㎡","list":"西门子、ABB、汇川技术、埃斯顿、新松机器人","source":"备用数据"},
    {"id":"bak_gz2","name":"中国（广州）国际家具博览会（一期）","type":"国内","industry":"家具","location":"广州","venue":"广交会展馆","startDate":"2026-03-18","endDate":"2026-03-21","regLink":"https://www.mice-gz.org","pastData":"2025年展商1200家，参观人次超20万","list":"顾家家居、敏华控股、左右家私、喜临门","source":"备用数据"},
    {"id":"bak_gz3","name":"广州国际家具生产设备及配料展","type":"国内","industry":"家具制造","location":"广州","venue":"广交会展馆","startDate":"2026-03-28","endDate":"2026-03-31","regLink":"https://www.mice-gz.org","pastData":"上届展商900家，展示最新木工机械与面料","list":"金田豪迈、南兴装备、华剑智能","source":"备用数据"},
    {"id":"bak_gz4","name":"广州国际汽车零部件及售后展览会","type":"国内","industry":"汽车配件","location":"广州","venue":"保利世贸博览馆","startDate":"2026-04-06","endDate":"2026-04-08","regLink":"https://www.mice-gz.org","pastData":"2025年展商600家，覆盖全产业链","list":"博世、电装、法雷奥、均胜电子","source":"备用数据"},
    {"id":"bak_gz5","name":"第139届中国进出口商品交易会（广交会第一期）","type":"跨境","industry":"综合","location":"广州","venue":"广交会展馆","startDate":"2026-04-15","endDate":"2026-04-19","regLink":"https://www.cantonfair.org.cn","pastData":"2025年秋交会展商2.5万家，出口成交额约300亿美元","list":"海尔、美的、格力、TCL等多家中国品牌","source":"备用数据"},
    {"id":"bak_gz6","name":"广交会第二期","type":"跨境","industry":"综合","location":"广州","venue":"广交会展馆","startDate":"2026-04-23","endDate":"2026-04-27","regLink":"https://www.cantonfair.org.cn","pastData":"日用消费品、礼品、家居装饰品类展商为主","list":"星辉互动、邦宝益智、潮宏基珠宝","source":"备用数据"},
    {"id":"bak_gz7","name":"广交会第三期","type":"跨境","industry":"综合","location":"广州","venue":"广交会展馆","startDate":"2026-05-01","endDate":"2026-05-05","regLink":"https://www.cantonfair.org.cn","pastData":"纺织服装、鞋类、箱包等品类集中展出","list":"申洲国际、华利集团、开润股份","source":"备用数据"},
    {"id":"bak_gz8","name":"广州国际专业灯光音响展","type":"国内","industry":"灯光音响","location":"广州","venue":"广交会展馆","startDate":"2026-05-16","endDate":"2026-05-19","regLink":"https://www.mice-gz.org","pastData":"2025年展商1100家，亚洲规模最大的专业展","list":"森海塞尔、舒尔、雅马哈、哈曼","source":"备用数据"},
    {"id":"bak_gz9","name":"广州国际烘焙展览会","type":"国内","industry":"食品加工","location":"广州","venue":"保利世贸博览馆","startDate":"2026-05-20","endDate":"2026-05-22","regLink":"https://www.mice-gz.org","pastData":"华南地区最大烘焙展，上届展商800家","list":"安琪酵母、益海嘉里、中粮粮谷","source":"备用数据"},
    {"id":"bak_gz10","name":"广州国际包装工业展","type":"国内","industry":"包装","location":"广州","venue":"广交会展馆","startDate":"2026-06-02","endDate":"2026-06-04","regLink":"https://www.mice-gz.org","pastData":"2025年展商700家，展出智能包装设备","list":"华联机械、永创智能、中亚机械","source":"备用数据"},
    {"id":"bak_gz11","name":"广州国际照明展览会（光亚展）","type":"国内","industry":"照明","location":"广州","venue":"琶洲展馆","startDate":"2026-06-09","endDate":"2026-06-12","regLink":"https://www.mice-gz.org","pastData":"全球最大照明展，上届展商3000家","list":"欧普照明、雷士照明、三雄极光、佛山照明","source":"备用数据"},
    {"id":"bak_gz12","name":"广州国际建筑装饰博览会","type":"国内","industry":"建材","location":"广州","venue":"广交会展馆","startDate":"2026-07-08","endDate":"2026-07-11","regLink":"https://www.mice-gz.org","pastData":"2025年展商2200家，观众25万人次","list":"索菲亚、欧派、尚品宅配、志邦家居","source":"备用数据"},
    {"id":"bak_gz13","name":"广州国际纺织制衣及印花工业展","type":"国内","industry":"纺织","location":"广州","venue":"保利世贸博览馆","startDate":"2026-07-15","endDate":"2026-07-17","regLink":"https://www.mice-gz.org","pastData":"上届展商500家，覆盖缝制设备及面辅料","list":"杰克股份、标准股份、中捷资源","source":"备用数据"},
    {"id":"bak_gz14","name":"广州国际机器人及工业自动化展","type":"国内","industry":"自动化","location":"广州","venue":"保利世贸博览馆","startDate":"2026-08-16","endDate":"2026-08-18","regLink":"https://www.mice-gz.org","pastData":"2025年展商400家，展示最新协作机器人","list":"发那科、库卡、ABB、安川","source":"备用数据"},
    {"id":"bak_gz15","name":"广州国际塑料橡胶工业展","type":"国内","industry":"塑料橡胶","location":"广州","venue":"保利世贸博览馆","startDate":"2026-08-12","endDate":"2026-08-14","regLink":"https://www.mice-gz.org","pastData":"华南地区重要橡塑展，上届展商600家","list":"海天国际、伊之密、震雄集团","source":"备用数据"},
    {"id":"bak_gz16","name":"广州国际涂料展","type":"国内","industry":"化工","location":"广州","venue":"广交会展馆","startDate":"2026-12-02","endDate":"2026-12-04","regLink":"https://www.mice-gz.org","pastData":"2025年展商450家，国际品牌占比30%","list":"阿克苏诺贝尔、PPG、立邦","source":"备用数据"},
    # ---------- 深圳 ----------
    {"id":"bak_sz1","name":"深圳国际工业制造技术展(ITES)","type":"国内","industry":"机械制造","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-03-30","endDate":"2026-04-02","regLink":"https://www.szcec.com/szcec/cn-schedule/zl/index.html","pastData":"2025年展商1500家，专业观众12万人次","list":"马扎克、大族激光、发那科、西门子","source":"备用数据"},
    {"id":"bak_sz2","name":"深圳国际礼品及家居用品展","type":"国内","industry":"礼品家居","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-04-25","endDate":"2026-04-28","regLink":"https://www.szcec.com","pastData":"上届展商3000家，展会面积12万㎡","list":"小熊电器、名创优品、故宫文创","source":"备用数据"},
    {"id":"bak_sz3","name":"深圳国际家具展","type":"国内","industry":"家具","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-03-17","endDate":"2026-03-20","regLink":"https://www.szcec.com","pastData":"2025年展商600家，聚焦原创设计","list":"左右家私、雅兰、舒达、席梦思","source":"备用数据"},
    {"id":"bak_sz4","name":"深圳国际电子元器件及材料展","type":"国内","industry":"电子","location":"深圳","venue":"深圳会展中心","startDate":"2026-09-02","endDate":"2026-09-04","regLink":"https://www.szcec.com","pastData":"上届展商400家，涵盖被动元件与连接器","list":"村田、TDK、太阳诱电、立讯精密","source":"备用数据"},
    {"id":"bak_sz5","name":"中国（深圳）跨境电商展览会","type":"跨境","industry":"跨境电商","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-09-16","endDate":"2026-09-18","regLink":"https://www.szcec.com","pastData":"2025年展商1200家，亚马逊、eBay等平台到场","list":"安克创新、SHEIN、致欧科技","source":"备用数据"},
    {"id":"bak_sz6","name":"深圳国际光电博览会","type":"国内","industry":"光电","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-09-09","endDate":"2026-09-11","regLink":"https://www.szcec.com","pastData":"亚洲最大光电展，上届展商3000家","list":"华为、中兴、烽火通信、长飞光纤","source":"备用数据"},
    {"id":"bak_sz7","name":"深圳国际纺织面料及辅料博览会","type":"国内","industry":"纺织","location":"深圳","venue":"深圳会展中心","startDate":"2026-07-08","endDate":"2026-07-10","regLink":"https://www.szcec.com","pastData":"华南地区专业面辅料展，上届展商500家","list":"华孚时尚、新野纺织、鲁泰纺织","source":"备用数据"},
    {"id":"bak_sz8","name":"深圳国际珠宝展","type":"国内","industry":"珠宝","location":"深圳","venue":"深圳会展中心","startDate":"2026-09-10","endDate":"2026-09-14","regLink":"https://www.szcec.com","pastData":"中国最大珠宝展，上届展商800家","list":"周大福、周生生、老凤祥、六福珠宝","source":"备用数据"},
    {"id":"bak_sz9","name":"深圳国际智能家居展","type":"国内","industry":"智能家居","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-06-18","endDate":"2026-06-20","regLink":"https://www.szcec.com","pastData":"2025年展商350家，展示全屋智能方案","list":"华为、小米、海尔智家、欧瑞博","source":"备用数据"},
    {"id":"bak_sz10","name":"深圳国际汽车制造技术展","type":"国内","industry":"汽车制造","location":"深圳","venue":"深圳国际会展中心","startDate":"2026-06-25","endDate":"2026-06-27","regLink":"https://www.szcec.com","pastData":"上届展商200家，聚焦新能源汽车产线","list":"比亚迪、宁德时代、先导智能","source":"备用数据"},
    {"id":"bak_sz11","name":"深圳国际医疗器械展览会","type":"国内","industry":"医疗器械","location":"深圳","venue":"深圳会展中心","startDate":"2026-12-21","endDate":"2026-12-23","regLink":"https://www.szcec.com","pastData":"2025年展商300家，华南医疗设备集中采购","list":"迈瑞医疗、理邦仪器、开立医疗","source":"备用数据"},
    # ---------- 佛山 ----------
    {"id":"bak_fs1","name":"佛山（国际）陶瓷及卫浴博览交易会（春季）","type":"国内","industry":"陶瓷","location":"佛山","venue":"佛山国际会展中心","startDate":"2026-04-18","endDate":"2026-04-21","regLink":"https://www.cerambath.org","pastData":"2025年展商800家，参观商15万人次","list":"东鹏控股、新明珠集团、蒙娜丽莎、欧神诺","source":"备用数据"},
    {"id":"bak_fs2","name":"佛山国际机械装备展","type":"国内","industry":"机械","location":"佛山","venue":"顺德展览中心","startDate":"2026-10-20","endDate":"2026-10-23","regLink":"https://www.foshanexpo.com","pastData":"上届展商600家，展出数控机床及模具","list":"海天精工、创世纪、伊之密","source":"备用数据"},
    {"id":"bak_fs3","name":"佛山国际家具材料及制造展","type":"国内","industry":"家具","location":"佛山","venue":"顺德龙江前进会展中心","startDate":"2026-03-28","endDate":"2026-03-30","regLink":"https://www.foshanexpo.com","pastData":"2025年展商450家，以家具原辅材料为主","list":"联塑、联众、大自然家居","source":"备用数据"},
    {"id":"bak_fs4","name":"佛山不锈钢及五金制品展","type":"国内","industry":"五金","location":"佛山","venue":"佛山国际会议展览中心","startDate":"2026-06-18","endDate":"2026-06-20","regLink":"https://www.foshanexpo.com","pastData":"上届展商300家，涵盖不锈钢管材及五金件","list":"海利不锈钢、万佳泓、长城不锈钢","source":"备用数据"},
    {"id":"bak_fs5","name":"佛山国际智能家居博览会","type":"国内","industry":"智能家居","location":"佛山","venue":"潭洲国际会展中心","startDate":"2026-07-15","endDate":"2026-07-17","regLink":"https://www.foshanexpo.com","pastData":"2025年展商280家，聚焦智能家电与安防","list":"美的、碧桂园、睿住智能","source":"备用数据"},
    {"id":"bak_fs6","name":"佛山国际塑料橡胶工业展","type":"国内","industry":"塑料橡胶","location":"佛山","venue":"潭洲国际会展中心","startDate":"2026-06-05","endDate":"2026-06-07","regLink":"https://www.foshanexpo.com","pastData":"上届展商350家，展出注塑机及原料","list":"伊之密、震雄、海天","source":"备用数据"},
    {"id":"bak_fs7","name":"佛山国际门窗幕墙展","type":"国内","industry":"门窗","location":"佛山","venue":"佛山国际会议展览中心","startDate":"2026-07-22","endDate":"2026-07-24","regLink":"https://www.foshanexpo.com","pastData":"2025年展商200家，覆盖铝门窗及幕墙系统","list":"凤铝铝业、坚美铝业、华昌铝材","source":"备用数据"},
    {"id":"bak_fs8","name":"佛山（秋季）陶瓷及卫浴博览交易会","type":"国内","industry":"陶瓷","location":"佛山","venue":"佛山国际会展中心","startDate":"2026-10-18","endDate":"2026-10-21","regLink":"https://www.cerambath.org","pastData":"秋季陶博会，上届展商750家","list":"金意陶、欧文莱、简一","source":"备用数据"}
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9"
}

# 行业关键词库
INDUSTRY_MAP = {
    "智能制造": ["智能装备", "自动化", "机床", "工业机器人", "智能制造"],
    "电子半导体": ["电子", "半导体", "电路板", "元器件", "显示"],
    "新能源": ["光伏", "储能", "新能源汽车", "锂电"],
    "包装印刷": ["包装", "印刷", "标签"],
    "医疗器械": ["医疗", "器械", "医用"],
    "建材家居": ["家具", "建材", "卫浴", "门窗"],
    "综合展会": []
}

def cn_date_to_std(date_raw: str) -> list:
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
    for industry, keywords in INDUSTRY_MAP.items():
        for kw in keywords:
            if kw in name:
                return industry
    return "综合展会"

def get_rendered_html(url: str, wait_second=3) -> str | None:
    try:
        with sync_playwright() as p:
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

def parse_gz_all(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("ul.list li")
    print(f"【广州】列表页匹配到展会数量：{len(items)}")
    res = []
    for idx, item in enumerate(items):
        try:
            a_tag = item.select_one("a")
            if not a_tag: continue
            exh_name = a_tag.get_text(strip=True)
            detail_href = a_tag.get("href", "")
            detail_url = f"https://www.mice-gz.org{detail_href}" if detail_href.startswith("/") else detail_href
            date_text = item.select_one("span.date").get_text(strip=True) if item.select_one("span.date") else ""
            venue_text = item.select_one("span.address").get_text(strip=True) if item.select_one("span.address") else "广交会展馆"
            start_dt, end_dt = cn_date_to_std(date_text)
            industry = auto_match_industry(exh_name)
            past_data, exhib_list, reg_link = "", "", detail_url
            detail_html = get_rendered_html(detail_url, wait_second=2)
            if detail_html:
                d_soup = BeautifulSoup(detail_html, "html.parser")
                past_node = d_soup.select_one(".history-data, .past-info")
                if past_node: past_data = past_node.get_text(strip=True)
                exhib_node = d_soup.select_one(".brand-list, .exhibitor")
                if exhib_node: exhib_list = exhib_node.get_text(strip=True)
                reg_a = d_soup.select_one("a.register-btn")
                if reg_a and reg_a.get("href"): reg_link = reg_a["href"]
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

def parse_sz_all(html: str) -> list:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select("div.list-item")
    print(f"【深圳】列表页匹配到展会数量：{len(items)}")
    res = []
    for idx, item in enumerate(items):
        try:
            title_a = item.select_one("div.title a")
            if not title_a: continue
            exh_name = title_a.get_text(strip=True)
            detail_href = title_a.get("href", "")
            detail_url = f"https://www.szcec.com{detail_href}" if detail_href.startswith("/") else detail_href
            date_text = item.select_one("div.time").get_text(strip=True) if item.select_one("div.time") else ""
            venue_text = item.select_one("div.address").get_text(strip=True) if item.select_one("div.address") else "深圳国际会展中心"
            start_dt, end_dt = cn_date_to_std(date_text)
            industry = auto_match_industry(exh_name)
            past_data, exhib_list, reg_link = "", "", detail_url
            detail_html = get_rendered_html(detail_url, wait_second=2)
            if detail_html:
                d_soup = BeautifulSoup(detail_html, "html.parser")
                past_node = d_soup.select_one(".history, .past-stat")
                if past_node: past_data = past_node.get_text(strip=True)
                exhib_node = d_soup.select_one(".exhibitor-name, .brand")
                if exhib_node: exhib_list = exhib_node.get_text(strip=True)
                reg_btn = d_soup.select_one("a.sign-up")
                if reg_btn and reg_btn.get("href"): reg_link = reg_btn["href"]
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
    if len(total_data) == 0:
        print("警告：线上未抓到任何展会，加载备用兜底数据（包含全年展会）")
        output = BACKUP_EXHIBITIONS
    else:
        print("使用线上实时抓取数据，覆盖备用数据")
        output = total_data

    output_file = "exhibitions.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    if os.path.exists(output_file):
        file_size = os.stat(output_file).st_size
        print(f"\n文件写入完成 | 路径: {output_file} | 文件大小: {file_size} Byte | 最终展会总数: {len(output)}")
    else:
        raise Exception("JSON文件写入失败，文件不存在！")

if __name__ == "__main__":
    main()
