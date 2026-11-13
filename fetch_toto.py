import json
import math
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


def damp_multiplier(raw_mult, low=0.78, high=1.24):
    """過剰適合防止のソフトクリッピング安全弁（極端な倍率膨張を対数減衰）"""
    if raw_mult >= 1.0:
        excess = raw_mult - 1.0
        span = high - 1.0
        return round(1.0 + span * math.tanh(excess / span), 4)
    deficit = 1.0 - raw_mult
    span = 1.0 - low
    return round(1.0 - span * math.tanh(deficit / span), 4)


def calc_travel_penalty(h_team, a_team):
    c1 = STADIUM_COORDS.get(h_team)
    c2 = STADIUM_COORDS.get(a_team)
    if not c1 or not c2:
        return 1.0, ""
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    km = int(2 * 6371.0 * math.asin(math.sqrt(a)))
    if km >= 800:
        return 0.92, "遠征{}km".format(km)
    if km >= 500:
        return 0.95, "遠征{}km".format(km)
    return 1.0, ""


def get_toto_schedule_and_votes():
    """最新販売回号・締切日時と、公開されている場合は各枠の一般投票率(集合知)を取得"""
    round_str = "最新開催回"
    dead_str = "公式スケジュール準拠"
    market_votes = {}

    html = fetch_url("https://toto.yahoo.co.jp/schedule/toto", 10)
    if html:
        soup = BeautifulSoup(html, "html.parser")
        txt = soup.get_text(" ", strip=True)
        m_sale = re.search(r"第(\d{4})回[（(]([^）)]+)[）)]\s*販売中", txt)
        if m_sale:
            rid, period = m_sale.group(1), m_sale.group(2)
            round_str = "第{}回".format(rid)
            dead_str = period
            sp_base = "https://sp.toto-dream.com/dcs/subos/screen/si01/ssin025/"
            sp_url = sp_base + "PGSSIN02501ForwardSalesTermtotoSP.form?holdCntId={}".format(rid)
            sp_html = fetch_url(sp_url, 10)
            if sp_html:
                sp_txt = BeautifulSoup(sp_html, "html.parser").get_text(" ", strip=True)
                pat = r"販売終了日\s*(\d{4}年\d{1,2}月\d{1,2}日\([月火水木金土日]\)).*?ネット決済\)\s*(\d{2}:\d{2})"
                m_end = re.search(pat, sp_txt)
                if m_end:
                    dead_str = "{} {}締切".format(m_end.group(1), m_end.group(2))
        else:
            m_next = re.findall(r"第(\d{4})回[（(]([^）)]+)[）)]\s*これから", txt)
            if m_next:
                rid, period = m_next[-1]
                round_str = "第{}回".format(rid)
                dead_str = period

    # Yahoo! toto投票状況ページから一般投票率(1/0/2)を取得試行（公開前なら空で安全にスキップ）
    v_html = fetch_url("https://toto.yahoo.co.jp/vote/toto", 10)
    if v_html:
        v_soup = BeautifulSoup(v_html, "html.parser")
        for tr in v_soup.find_all("tr"):
            row_txt = tr.get_text(" ", strip=True)
            m_f = re.match(r"^(\d{1,2})\b", row_txt)
            pcts = [float(x) for x in re.findall(r"(\d{1,2}(?:\.\d+)?)\s*%", row_txt)]
            if m_f and len(pcts) >= 3:
                f_idx = int(m_f.group(1))
                if 1 <= f_idx <= 13 and 95.0 <= sum(pcts[:3]) <= 105.0:
                    market_votes[f_idx] = [pcts[0], pcts[1], pcts[2]]

    print("[Schedule & Market Votes]", round_str, "Votes loaded:", len(market_votes))
    return round_str, dead_str, market_votes


def parse_recent_form_score(row_text):
    cleaned = re.sub(r"\s+", "", row_text)
    m = re.search(r"([WDL勝分敗○△●]{5})", cleaned)
    if not m:
        return 1.0, ""
    seq = m.group(1)
    pts = 0
    for ch in seq:
        if ch in ["W", "勝", "○"]:
            pts += 3
        elif ch in ["D", "分", "△"]:
            pts += 1
    mult = round(0.90 + (pts / 15.0) * 0.22, 3)
    return mult, "直近5戦{}/15pt".format(pts)


def get_club_stats():
    """シーズン基礎力＋直近5戦フォーム＋ホーム/アウェイ別傾き＋終盤モチベーションを算出"""
    raw_rows = []
    total_gf = 0
    total_played = 0

    urls = [
        ("https://www.jleague.jp/standings/j1/", "J1"),
        ("https://www.jleague.jp/standings/j2/", "J2"),
        ("https://www.jleague.jp/standings/j3/", "J3")
    ]
    seen_teams = set()
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
                if t in seen_teams:
                    continue
                seen_teams.add(t)
                rk, pts, pl = nums[0], nums[1], max(1, nums[2])
                w, d, l = nums[3], nums[4], nums[5]
                gf, ga = nums[6], nums[7]
                total_gf += gf
                total_played += pl

                # テーブル内にホーム/アウェイ別戦績列が含まれている場合は会場別傾きを抽出
                home_tilt = 1.0
                away_tilt = 1.0
                if len(nums) >= 16:
                    h_w, h_l = nums[9], nums[11]
                    a_w, a_l = nums[13], nums[15]
                    home_tilt = round(max(0.92, min(1.08, 1.0 + (h_w - h_l) * 0.012)), 3)
                    away_tilt = round(max(0.92, min(1.08, 1.0 + (a_w - a_l) * 0.012)), 3)

                recent_mult, recent_tag = parse_recent_form_score("".join(cells))
                raw_rows.append((t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, home_tilt, away_tilt))

    dyn_avg = round(total_gf / max(1, total_played), 3) if total_played > 0 else 1.30
    print("[Dynamic League Avg Goals]", dyn_avg)

    stats = {}
    for (t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, h_tilt, a_tilt) in raw_rows:
        atk_base = ((gf / pl) * 0.80) + (dyn_avg * 0.20)
        def_base = ((ga / pl) * 0.80) + (dyn_avg * 0.20)

        gd_per_game = (gf - ga) / pl
        season_mult = 0.94 + ((w / pl) * 0.14) + max(-0.06, min(0.06, gd_per_game * 0.04))
        blended_form = (season_mult * 0.65) + (recent_mult * 0.35)

        motive_mult = 1.0
        motive_tag = ""
        if (div == "J1" and rk <= 3) or (div in ["J2", "J3"] and rk <= 6):
            motive_mult = 1.05
            motive_tag = "・優勝/昇格圏"
        elif rk >= 17:
            motive_mult = 1.04
            motive_tag = "・残留争い"

        extra = "・" + recent_tag if recent_tag else ""
        tr_str = "[{} {}位{}{}] 勝点{}/{}勝{}分{}敗".format(div, rk, motive_tag, extra, pts, w, d, l)
        stats[t] = {
            "atk": round(atk_base * blended_form * motive_mult, 3),
            "def_v": round(def_base / (blended_form * motive_mult), 3),
            "h_tilt": h_tilt,
            "a_tilt": a_tilt,
            "trend": tr_str,
            "rk": rk
        }

    print("[Club Stats] Fetched:", len(stats))
    return stats, dyn_avg


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


def check_weather(home_team, target_date_iso):
    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        return 1.0, "晴/曇"
    lat, lon = coords
    api = (
        "https://api.open-meteo.com/v1/forecast?latitude={}&longitude={}"
        "&daily=precipitation_sum,wind_speed_10m_max&timezone=Asia%2FTokyo"
        "&start_date={}&end_date={}"
    ).format(lat, lon, target_date_iso, target_date_iso)
    raw = fetch_url(api, 8)
    if not raw:
        return 1.0, "晴/曇"
    try:
        js = json.loads(raw)
        daily = js.get("daily", {})
        prec = (daily.get("precipitation_sum") or [0])[0] or 0
        wind = (daily.get("wind_speed_10m_max") or [0])[0] or 0
        if prec >= 2.0 and wind >= 36.0:
            return 0.80, "荒天(雨{}mm/強風)".format(prec)
        if prec >= 2.0:
            return 0.86, "雨({}mm)".format(prec)
        if wind >= 36.0:
            return 0.90, "強風({}km/h)".format(round(wind))
        return 1.0, "晴/曇"
    except Exception:
        return 1.0, "晴/曇"


def check_lineup_status(match_url, top_scorers):
    if not match_url:
        return 1.0, 1.0, "スタメン発表前"
    html = fetch_url(match_url, 10)
    if not html:
        return 1.0, 1.0, "スタメン発表前"
    soup = BeautifulSoup(html, "html.parser")
    txt = soup.get_text(" ", strip=True)
    if "先発" not in txt and "スターティング" not in txt:
        return 1.0, 1.0, "スタメン発表前"
    clean_txt = re.sub(r"\s+", "", txt)
    hits = [p for p in top_scorers if p in clean_txt]
    if len(hits) >= 2:
        return 1.07, 1.07, "スタメン確定(主力出場:{}ほか)".format(hits[0])
    elif len(hits) == 1:
        return 1.03, 0.96, "スタメン確定(主力出場:{})".format(hits[0])
    return 0.91, 0.91, "スタメン確定(ターンオーバー傾向)"


def calc_vote_dynamic_dc(h_lam, a_lam):
    """試合ペース(合計得点期待値)連動型の動的Dixon-Coles補正付き勝率算出"""
    tot_lam = h_lam + a_lam
    # ロースコア予想(tot_lam < 2.2)ほど引き分け相関を強め、撃ち合い予想では弱める
    rho = max(-0.16, min(-0.06, -0.12 + (tot_lam - 2.4) * 0.03))

    def pois(k, lam):
        return (lam ** k) * math.exp(-lam) / math.factorial(k)

    p1, p0, p2 = 0.0, 0.0, 0.0
    for i in range(6):
        for j in range(6):
            p = pois(i, h_lam) * pois(j, a_lam)
            if i == 0 and j == 0:
                p *= max(0.1, 1.0 - h_lam * a_lam * rho)
            elif i == 1 and j == 0:
                p *= max(0.1, 1.0 + a_lam * rho)
            elif i == 0 and j == 1:
                p *= max(0.1, 1.0 + h_lam * rho)
            elif i == 1 and j == 1:
                p *= max(0.1, 1.0 - rho)

            if i > j:
                p1 += p
            elif i == j:
                p0 += p
            else:
                p2 += p

    tot = max(1e-6, p1 + p0 + p2)
    r1 = round((p1 / tot) * 100, 1)
    r2 = round((p2 / tot) * 100, 1)
    r0 = round(max(12.0, 100.0 - r1 - r2), 1)
    return [r1, r0, r2]


def blend_with_market_wisdom(h_lam, a_lam, mkt_v):
    """一般投票率(集合知)が取得できた場合、人気偏重を除去した上で25%ベイズ統合する"""
    if not mkt_v or len(mkt_v) < 3:
        return h_lam, a_lam, ""
    # フェイバリット・ロングショットバイアス除去 (累乗0.85で正規化)
    debiased = [max(1.0, x) ** 0.85 for x in mkt_v]
    s = sum(debiased)
    m_p1, m_p2 = debiased[0] / s, debiased[2] / s

    stat_v = calc_vote_dynamic_dc(h_lam, a_lam)
    s_p1, s_p2 = stat_v[0] / 100.0, stat_v[2] / 100.0

    # 統計75% + 集合知25% の比率シフトをλへ穏やかに反映 (最大±8%以内に制限)
    h_shift = damp_multiplier(1.0 + (m_p1 - s_p1) * 0.25, 0.92, 1.08)
    a_shift = damp_multiplier(1.0 + (m_p2 - s_p2) * 0.25, 0.92, 1.08)
    return round(h_lam * h_shift, 2), round(a_lam * a_shift, 2), " / 集合知融合済"


def get_future_matches(stats, dyn_avg, top_scorers, round_num_str, deadline_str, market_votes):
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    wds = ["月", "火", "水", "木", "金", "土", "日"]
    ym = today.strftime("%Y%m")
    urls = [
        "https://www.jleague.jp/match/section/j1/latest/",
        "https://www.jleague.jp/match/section/j2/latest/",
        "https://www.jleague.jp/match/section/j3/latest/",
        "https://www.jleague.jp/match/search/j1/{}/".format(ym),
        "https://www.jleague.jp/match/search/j2/{}/".format(ym),
        "https://www.jleague.jp/match/search/j3/{}/".format(ym)
    ]

    games = []
    seen = set()

    for url in urls:
        html = fetch_url(url, 10)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for blk in soup.find_all(["tr", "li", "div"]):
            txt = blk.get_text(" ", strip=True)
            if len(txt) > 200 or len(txt) < 6:
                continue
            teams = []
            for sub in blk.find_all(["td", "span", "p", "a", "div"]):
                s = sub.get_text(strip=True)
                if 2 <= len(s) <= 16:
                    nm = norm_team(s)
                    if nm in stats and nm not in teams:
                        teams.append(nm)
            if len(teams) == 2:
                m_link = ""
                match_d = None
                for a_tag in blk.find_all("a", href=True):
                    href = a_tag["href"]
                    m_url_d = re.search(r"/2026/(\d{2})(\d{2})\d{2}/", href)
                    if m_url_d:
                        try:
                            cand = datetime.date(today.year, int(m_url_d.group(1)), int(m_url_d.group(2)))
                            if cand >= today:
                                match_d = cand
                        except Exception:
                            pass
                    if "/match/" in href and ("live" in href or "preview" in href):
                        m_link = href if href.startswith("http") else "https://www.jleague.jp" + href
                if match_d is None:
                    continue
                iso_d = match_d.strftime("%Y-%m-%d")
                d_str = "{}月{}日({})".format(match_d.month, match_d.day, wds[match_d.weekday()])
                pk = "{}:{}-{}".format(iso_d, teams[0], teams[1])
                if pk not in seen:
                    seen.add(pk)
                    games.append((match_d, iso_d, d_str, teams[0], teams[1], m_link))

    games.sort(key=lambda x: x[0])
    print("[Valid Future Games]", len(games))
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
        hs = stats.get(hn, {"atk": dyn_avg, "def_v": dyn_avg, "h_tilt": 1.0, "a_tilt": 1.0, "trend": ""})
        as_ = stats.get(an, {"atk": dyn_avg, "def_v": dyn_avg, "h_tilt": 1.0, "a_tilt": 1.0, "trend": ""})

        w_mult, w_label = check_weather(hn, iso_d)
        hm_lu, am_lu, lu_label = check_lineup_status(m_link, top_scorers)
        travel_mult, travel_tag = calc_travel_penalty(hn, an)

        # 相対マッチアップ基礎値（会場別傾き含む）
        h_base = hs["atk"] * (as_["def_v"] / dyn_avg) * 1.12 * hs["h_tilt"]
        a_base = as_["atk"] * (hs["def_v"] / dyn_avg) * 0.92 * as_["a_tilt"]

        # 環境・コンディション合成倍率に対数ダンピング安全弁を適用（暴走防止）
        h_env_mult = damp_multiplier(w_mult * hm_lu)
        a_env_mult = damp_multiplier(w_mult * am_lu * travel_mult)

        h_rel = h_base * h_env_mult
        a_rel = a_base * a_env_mult

        # 戦力差による完封（クリーンシート）バイアス補正
        lam_gap = h_rel - a_rel
        cs_tag = ""
        if lam_gap >= 0.45:
            a_rel *= 0.89
            cs_tag = " / H完封優位"
        elif lam_gap <= -0.45:
            h_rel *= 0.89
            cs_tag = " / A完封優位"

        # 市場投票率（集合知）とのアンサンブル統合
        mkt_v = market_votes.get(i)
        final_h_lam, final_a_lam, mkt_tag = blend_with_market_wisdom(h_rel, a_rel, mkt_v)

        final_h_lam = round(max(0.30, min(3.30, final_h_lam)), 2)
        final_a_lam = round(max(0.25, min(3.10, final_a_lam)), 2)

        model_v = calc_vote_dynamic_dc(final_h_lam, final_a_lam)
        display_v = mkt_v if mkt_v else model_v

        grp = "A" if i <= 5 else ("B" if i <= 10 else "C")
        tr_note = " / {}".format(travel_tag) if travel_tag else ""
        auto_note = "天候:{} / {}{}{}{}".format(w_label, lu_label, tr_note, cs_tag, mkt_tag)
        matches.append({
            "f": i, "grp": grp, "h": hn, "a": an,
            "v": display_v,
            "h_xg": final_h_lam, "h_xga": final_a_lam,
            "a_xg": final_a_lam, "a_xga": final_h_lam,
            "analysis": "[{} | {}] H:{} {} / A:{} {}".format(ds, auto_note, hn, hs["trend"], an, as_["trend"])
        })

    rk = "{} (開催: {} / {})".format(round_num_str, d_label, deadline_str)
    return rk, {
        "title": "{} | 開催日: {} | 締切: {} (全{}試合・アンサンブル推論モデル適用済)".format(
            round_num_str, d_label, deadline_str, len(matches)
        ),
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
    st, dyn_avg = get_club_stats()
    if st:
        data["club_stats"] = st
    r_num, deadline_str, mkt_votes = get_toto_schedule_and_votes()
    scorers = get_top_scorers()
    res = get_future_matches(data["club_stats"], dyn_avg, scorers, r_num, deadline_str, mkt_votes)
    if res:
        rk, obj = res
        data["rounds"][rk] = obj
        data["current_round"] = rk
        print("[SUCCESS]", rk, len(obj["matches"]))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
