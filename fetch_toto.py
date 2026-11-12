import json
import re
import datetime
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

STADIUM_COORDS = {
    "札幌": (43.015, 141.410), "八戸": (40.535, 141.464), "仙台": (38.319, 140.881),
    "秋田": (39.725, 140.095), "山形": (38.336, 140.378), "いわき": (37.001, 140.854),
    "鹿島": (35.992, 140.640), "水戸": (36.345, 140.412), "栃木C": (36.326, 139.678),
    "大宮": (35.916, 139.633), "千葉": (35.577, 140.123), "柏": (35.848, 139.975),
    "FC東京": (35.664, 139.527), "東京V": (35.664, 139.527), "町田": (35.592, 139.439),
    "川崎F": (35.585, 139.652), "横浜FM": (35.510, 139.606), "横浜FC": (35.469, 139.603),
    "湘南": (35.343, 139.341), "甲府": (35.622, 138.589), "新潟": (37.882, 139.059),
    "富山": (36.647, 137.194), "清水": (34.984, 138.481), "磐田": (34.725, 137.878),
    "藤枝": (34.869, 138.237), "名古屋": (35.084, 137.170), "京都": (35.016, 135.586),
    "G大阪": (34.802, 135.538), "C大阪": (34.614, 135.518), "神戸": (34.656, 135.169),
    "岡山": (34.680, 133.918), "広島": (34.402, 132.454), "徳島": (34.168, 134.617),
    "今治": (34.041, 132.969), "福岡": (33.585, 130.460), "鳥栖": (33.371, 130.520),
    "長崎": (32.755, 129.865), "大分": (33.200, 131.657), "宮崎": (32.029, 131.464),
    "栃木SC": (36.473, 139.858), "群馬": (36.413, 139.052), "松本": (36.179, 137.917),
    "長野": (36.580, 138.169), "金沢": (36.609, 136.634), "沼津": (35.148, 138.868),
    "岐阜": (35.442, 136.766), "鳥取": (35.457, 134.221), "山口": (34.156, 131.442),
    "讃岐": (34.287, 133.784), "愛媛": (33.767, 132.797), "高知": (33.541, 133.504),
    "北九州": (33.890, 130.888), "熊本": (32.837, 130.800), "鹿児島": (31.564, 130.561),
    "琉球": (26.306, 127.781)
}


def fetch_url(url, timeout=12):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            for enc in ["utf-8", "shift_jis", "cp932", "euc-jp"]:
                try:
                    txt = raw.decode(enc)
                    if len(txt) > 200:
                        return txt
                except Exception:
                    continue
    except Exception as e:
        print("[Fetch failed]", url, e)
    return ""


def norm_team(name):
    mp = {
        "北海道コンサドーレ札幌": "札幌", "コンサドーレ札幌": "札幌",
        "ヴァンラーレ八戸": "八戸", "ベガルタ仙台": "仙台",
        "ブラウブリッツ秋田": "秋田", "モンテディオ山形": "山形", "いわきFC": "いわき",
        "鹿島アントラーズ": "鹿島", "水戸ホーリーホック": "水戸", "栃木シティ": "栃木C",
        "RB大宮アルディージャ": "大宮", "大宮アルディージャ": "大宮", "ジェフユナイテッド千葉": "千葉",
        "柏レイソル": "柏", "FC東京": "FC東京", "東京ヴェルディ": "東京V",
        "FC町田ゼルビア": "町田", "川崎フロンターレ": "川崎F", "横浜F・マリノス": "横浜FM",
        "横浜FC": "横浜FC", "湘南ベルマーレ": "湘南", "ヴァンフォーレ甲府": "甲府",
        "アルビレックス新潟": "新潟", "カターレ富山": "富山", "清水エスパルス": "清水",
        "ジュビロ磐田": "磐田", "藤枝MYFC": "藤枝", "名古屋グランパス": "名古屋",
        "京都サンガF.C.": "京都", "ガンバ大阪": "G大阪", "セレッソ大阪": "C大阪",
        "ヴィッセル神戸": "神戸", "ファジアーノ岡山": "岡山", "サンフレッチェ広島": "広島",
        "徳島ヴォルティス": "徳島", "FC今治": "今治", "アビスパ福岡": "福岡",
        "サガン鳥栖": "鳥栖", "V・ファーレン長崎": "長崎", "大分トリニータ": "大分",
        "テゲバジャーロ宮崎": "宮崎", "栃木SC": "栃木SC", "ザスパ群馬": "群馬",
        "松本山雅FC": "松本", "AC長野パルセイロ": "長野", "ツエーゲン金沢": "金沢",
        "アスルクラロ沼津": "沼津", "FC岐阜": "岐阜", "ガイナーレ鳥取": "鳥取",
        "レノファ山口FC": "山口", "カマタマーレ讃岐": "讃岐", "愛媛FC": "愛媛",
        "高知ユナイテッドSC": "高知", "ギラヴァンツ北九州": "北九州", "ロアッソ熊本": "熊本",
        "鹿児島ユナイテッドFC": "鹿児島", "FC琉球": "琉球"
    }
    clean = re.sub(r"\s+", "", name)
    for k, v in mp.items():
        if k in clean or v == clean:
            return v
    return clean


def get_club_stats():
    stats = {}
    urls = [
        ("https://www.jleague.jp/standings/j1/", "J1"),
        ("https://www.jleague.jp/standings/j2/", "J2"),
        ("https://www.jleague.jp/standings/j3/", "J3")
    ]
    for url, div in urls:
        html = fetch_url(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            nums = [int(x) for x in cells if re.fullmatch(r"-?\d+", x)]
            txts = [x for x in cells if len(x) >= 2 and not re.fullmatch(r"-?\d+", x)]
            if len(nums) >= 8 and len(txts) >= 1:
                t = norm_team(txts[0])
                if t in stats:
                    continue
                rk, pts, pl = nums[0], nums[1], max(1, nums[2])
                w, d, l = nums[3], nums[4], nums[5]
                gf, ga = nums[6], nums[7]
                form_mult = round(0.92 + ((w / pl) * 0.22), 3)
                xg = round(((gf / pl) * 0.75 + 0.325) * form_mult, 2)
                xga = round(((ga / pl) * 0.75 + 0.325) / form_mult, 2)
                tr_str = "[{} {}位] 勝点{}/{}勝{}分{}敗".format(div, rk, pts, w, d, l)
                stats[t] = {"xg": xg, "xga": xga, "trend": tr_str}
    print("[Club Stats] Fetched:", len(stats))
    return stats


def get_toto_round_num():
    html = fetch_url("https://www.toto-dream.com/toto/index.html", 10)
    ids = [int(x) for x in re.findall(r"第(\d{4})回", html)] if html else []
    if ids:
        max_id = max(ids)
        if "結果" in html and "第{}回".format(max_id) in html:
            return "第{}回".format(max_id + 1)
        return "第{}回".format(max_id)
    return "第1663回"


def get_top_scorers():
    scorers = set()
    for div in ["j1", "j2", "j3"]:
        html = fetch_url("https://www.jleague.jp/stats/{}/goal.html".format(div), 10)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr")[:35]:
            for a in tr.find_all("a"):
                nm = re.sub(r"\s+", "", a.get_text(strip=True))
                if 2 <= len(nm) <= 12 and not any(x in nm for x in ["J1", "J2", "J3", "詳細", "順位"]):
                    scorers.add(nm)
    return scorers


def check_weather_rain(home_team, target_date_iso):
    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        return False, "晴/曇"
    lat, lon = coords
    api = (
        "https://api.open-meteo.com/v1/forecast?latitude={}&longitude={}"
        "&daily=precipitation_sum&timezone=Asia%2FTokyo&start_date={}&end_date={}"
    ).format(lat, lon, target_date_iso, target_date_iso)
    raw = fetch_url(api, 8)
    if not raw:
        return False, "予報取得中"
    try:
        js = json.loads(raw)
        prec = js.get("daily", {}).get("precipitation_sum", [0])[0] or 0
        if prec >= 2.0:
            return True, "雨({}mm)".format(prec)
        return False, "晴/曇"
    except Exception:
        return False,
