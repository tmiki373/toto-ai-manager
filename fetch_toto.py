import json
import re
import datetime
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

# 主要クラブ本拠地スタジアム緯度経度（天候自動取得用）
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
    """シーズン順位・得失点＋直近フォームの自動取得"""
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
                win_rate = w / pl
                # 勝率による調子補正係数 (0.90 ~ 1.12)
                form_mult = round(0.92 + (win_rate * 0.22), 3)
                xg = round(((gf / pl) * 0.75 + 0.325) * form_mult, 2)
                xga = round(((ga / pl) * 0.75 + 0.325) / form_mult, 2)
                tr_str = "[{} {}位] 勝点{}/{}勝{}分{}敗".format(div, rk, pts, w, d, l)
                stats[t] = {"xg": xg, "xga": xga, "trend": tr_str, "div": div}
    print("[Club Stats] Fetched:", len(stats))
    return stats


def get_top_scorers():
    """J1/J2/J3得点ランキング上位選手を自動取得（スタメン主力判定の基準）"""
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
    print("[Top Scorers] Loaded:", len(scorers))
    return scorers


def check_weather_rain(home_team, target_date_iso):
    """Open-Meteo無料気象APIで本拠地の当日降水量を自動判定"""
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
        return False, "晴/曇"


def check_lineup_status(match_url, h_team, a_team, top_scorers):
    """試合速報ページからスタメン公開有無と主力出場状況を自動判定"""
    if not match_url:
        return 1.0, 1.0, "スタメン発表前"
    html = fetch_url(match_url, 10)
    if not html:
        return 1.0, 1.0, "スタメン発表前"
    soup = BeautifulSoup(html, "html.parser")
    txt = soup.get_text(" ", strip=True)
    if "先発" not in txt and "スターティング" not in txt:
        return 1.0, 1.0, "スタメン発表前"

    # スタメン発表済の場合、主力得点源の名前がページ内にあるか判定
    clean_txt = re.sub(r"\s+", "", txt)
    hit_players = [p for p in top_scorers if p in clean_txt]
    if len(hit_players) >= 2:
        return 1.06, 1.06, "スタメン確定(主力出場:{}ほか)".format(hit_players[0])
    elif len(hit_players) == 1:
        return 1.02, 0.96, "スタメン確定(主力出場:{})".format(hit_players[0])
    else:
        return 0.92, 0.92, "スタメン確定(ターンオーバー傾向)"


def calc_vote(h_xg, h_xga, a_xg, a_xga):
    hp = (h_xg / max(0.5, a_xga)) * 1.15
    ap = (a_xg / max(0.5, h_xga)) * 0.90
    tot = hp + ap + 0.75
    p1 = round((hp / tot) * 100, 1)
    p2 = round((ap / tot) * 100, 1)
    p0 = round(max(15.0, 100.0 - p1 - p2), 1)
    return [p1, p0, p2]


def get_future_matches(stats, top_scorers):
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    wds = ["月", "火", "水", "木", "金", "土", "日"]
    games = []
    seen = set()

    for off in range(0, 15):
        td = today + datetime.timedelta(days=off)
        ymd = td.strftime("%Y%m%d")
        iso_d = td.strftime("%Y-%m-%d")
        d_str = "{}月{}日({})".format(td.month, td.day, wds[td.weekday()])
        url = "https://www.jleague.jp/match/search/all/{}/".format(ymd)
        html = fetch_url(url, 10)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        cnt = 0
        for blk in soup.find_all(["tr", "li", "div"]):
            txt = blk.get_text(" ", strip=True)
            if len(txt) > 180 or len(txt) < 6:
                continue
            teams = []
            for sub in blk.find_all(["td", "span", "p", "a", "div"]):
                s = sub.get_text(strip=True)
                if 2 <= len(s) <= 16:
                    nm = norm_team(s)
                    if nm in stats and nm not in teams:
                        teams.append(nm)
            if len(teams) == 2:
                pk = "{}:{}-{}".format(ymd, teams[0], teams[1])
                if pk not in seen:
                    seen.add(pk)
                    m_link = ""
                    for a_tag in blk.find_all("a", href=True):
                        if "/match/" in a_tag["href"] and ("live" in a_tag["href"] or "preview" in a_tag["href"]):
                            href = a_tag["href"]
                            m_link = href if href.startswith("http") else "https://www.jleague.jp" + href
                            break
                    games.append((td, iso_d, d_str, teams[0], teams[1], m_link))
                    cnt += 1
        if cnt > 0:
            print("[Date]", ymd, d_str, "Matches:", cnt)

    print("[Total Future Matches]", len(games))
    if not games:
        return None

    first_d = games[0][0]
    target = [g for g in games if (g[0] - first_d).days <= 3][:13]
    if len(target) < 5:
        target = games[:13]

    udates = []
    for g in target:
        if g[2] not in udates:
            udates.append(g[2])
    d_label = "・".join(udates[:2])

    matches = []
    for i, (_, iso_d, ds, hn, an, m_link) in enumerate(target, 1):
        hs = stats.get(hn, {"xg": 1.3, "xga": 1.3, "trend": ""})
        as_ = stats.get(an, {"xg": 1.3, "xga": 1.3, "trend": ""})

        # 1. 自動天候補正
        is_rain, w_label = check_weather_rain(hn, iso_d)
        rain_mult = 0.86 if is_rain else 1.0

        # 2. 自動スタメン主力判定補正
        hm_lineup, am_lineup, lineup_label = check_lineup_status(m_link, hn, an, top_scorers)

        final_h_xg = round(hs["xg"] * rain_mult * hm_lineup, 2)
        final_h_xga = round(hs["xga"] * rain_mult, 2)
        final_a_xg = round(as_["xg"] * rain_mult * am_lineup, 2)
        final_a_xga = round(as_["xga"] * rain_mult, 2)

        grp = "A" if i <= 5 else ("B" if i <= 10 else "C")
        auto_note = "天候:{} / {}".format(w_label, lineup_label)
        matches.append({
            "f": i, "grp": grp, "h": hn, "a": an,
            "v": calc_vote(final_h_xg, final_h_xga, final_a_xg, final_a_xga),
            "h_xg": final_h_xg, "h_xga": final_h_xga,
            "a_xg": final_a_xg, "a_xga": final_a_xga,
            "analysis": "[{} | {}] H:{} {} / A:{} {}".format(ds, auto_note, hn, hs["trend"], an, as_["trend"])
        })

    rk = "次回toto対象節 ({})".format(d_label)
    return rk, {
        "title": "次回toto対象節 | 開催日: {} (全{}試合・天候/スタメン自動補正済)".format(d_label, len(matches)),
        "goal3_frames": [x for x in [1, 2, 3] if x <= len(matches)],
        "matches": matches,
        "actual_results": {}
    }


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    data = {
        "current_round": "",
        "last_updated": datetime.datetime.now(jst).strftime("%Y-%m-%d %H:%M JST"),
        "club_stats": {},
        "rounds": {}
    }
    st = get_club_stats()
    if st:
        data["club_stats"] = st
    scorers = get_top_scorers()
    res = get_future_matches(data["club_stats"], scorers)
    if res:
        rk, obj = res
        data["rounds"][rk] = obj
        data["current_round"] = rk
        print("[SUCCESS]", rk, len(obj["matches"]))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
