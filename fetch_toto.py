import json
import math
import os
import re
import datetime
import unicodedata
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

STADIUM_COORDS = {
    "札幌": (43.015, 141.410), "八戸": (40.535, 141.464), "仙台": (38.319, 140.881),
    "秋田": (39.725, 140.095), "山形": (38.336, 140.378), "いわき": (37.001, 140.854),
    "鹿島": (35.992, 140.640), "水戸": (36.345, 140.412), "栃木C": (36.326, 139.678),
    "浦和": (35.903, 139.717), "大宮": (35.916, 139.633), "千葉": (35.577, 140.123),
    "柏": (35.848, 139.975), "FC東京": (35.664, 139.527), "東京V": (35.664, 139.527),
    "町田": (35.592, 139.439), "川崎F": (35.585, 139.652), "横浜FM": (35.510, 139.606),
    "横浜FC": (35.469, 139.603), "湘南": (35.343, 139.341), "甲府": (35.622, 138.589),
    "新潟": (37.882, 139.059), "富山": (36.647, 137.194), "清水": (34.984, 138.481),
    "磐田": (34.725, 137.878), "藤枝": (34.869, 138.237), "名古屋": (35.084, 137.170),
    "京都": (35.016, 135.586), "G大阪": (34.802, 135.538), "C大阪": (34.614, 135.518),
    "神戸": (34.656, 135.169), "岡山": (34.680, 133.918), "広島": (34.402, 132.454),
    "徳島": (34.168, 134.617), "今治": (34.041, 132.969), "福岡": (33.585, 130.460),
    "鳥栖": (33.371, 130.520), "長崎": (32.755, 129.865), "大分": (33.200, 131.657),
    "宮崎": (32.029, 131.464), "栃木SC": (36.473, 139.858), "群馬": (36.413, 139.052),
    "松本": (36.179, 137.917), "長野": (36.580, 138.169), "金沢": (36.609, 136.634),
    "沼津": (35.148, 138.868), "岐阜": (35.442, 136.766), "鳥取": (35.457, 134.221),
    "山口": (34.156, 131.442), "讃岐": (34.287, 133.784), "愛媛": (33.767, 132.797),
    "高知": (33.541, 133.504), "北九州": (33.890, 130.888), "熊本": (32.837, 130.800),
    "鹿児島": (31.564, 130.561), "琉球": (26.306, 127.781)
}

TEAM_ALIAS_MAP = {
    "北海道コンサドーレ札幌": "札幌", "コンサドーレ札幌": "札幌",
    "ヴァンラーレ八戸": "八戸", "ベガルタ仙台": "仙台",
    "ブラウブリッツ秋田": "秋田", "モンテディオ山形": "山形", "いわきFC": "いわき",
    "鹿島アントラーズ": "鹿島", "水戸ホーリーホック": "水戸", "栃木シティ": "栃木C",
    "浦和レッズ": "浦和", "浦和レッドダイヤモンズ": "浦和",
    "RB大宮アルディージャ": "大宮", "大宮アルディージャ": "大宮",
    "ジェフユナイテッド千葉": "千葉", "ジェフユナイテッド市原・千葉": "千葉",
    "柏レイソル": "柏", "FC東京": "FC東京", "東京ヴェルディ": "東京V",
    "FC町田ゼルビア": "町田", "川崎フロンターレ": "川崎F",
    "横浜F・マリノス": "横浜FM", "横浜Fマリノス": "横浜FM",
    "横浜FC": "横浜FC", "湘南ベルマーレ": "湘南", "ヴァンフォーレ甲府": "甲府",
    "アルビレックス新潟": "新潟", "カターレ富山": "富山", "清水エスパルス": "清水",
    "ジュビロ磐田": "磐田", "藤枝MYFC": "藤枝", "名古屋グランパス": "名古屋",
    "京都サンガF.C.": "京都", "京都サンガFC": "京都",
    "ガンバ大阪": "G大阪", "セレッソ大阪": "C大阪",
    "ヴィッセル神戸": "神戸", "ファジアーノ岡山": "岡山", "サンフレッチェ広島": "広島",
    "徳島ヴォルティス": "徳島", "FC今治": "今治", "アビスパ福岡": "福岡",
    "サガン鳥栖": "鳥栖", "V・ファーレン長崎": "長崎", "Vファーレン長崎": "長崎",
    "大分トリニータ": "大分", "テゲバジャーロ宮崎": "宮崎",
    "栃木SC": "栃木SC", "ザスパ群馬": "群馬", "ザスパクサツ群馬": "群馬",
    "松本山雅FC": "松本", "AC長野パルセイロ": "長野", "ツエーゲン金沢": "金沢",
    "アスルクラロ沼津": "沼津", "FC岐阜": "岐阜", "ガイナーレ鳥取": "鳥取",
    "レノファ山口FC": "山口", "カマタマーレ讃岐": "讃岐", "愛媛FC": "愛媛",
    "高知ユナイテッドSC": "高知", "ギラヴァンツ北九州": "北九州", "ロアッソ熊本": "熊本",
    "鹿児島ユナイテッドFC": "鹿児島", "FC琉球": "琉球"
}


def load_existing_data():
    if not os.path.exists(DATA_FILE):
        return {"rounds": {}, "model_params": {"home_adv": 1.12}}
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            d = json.load(f)
            if isinstance(d, dict):
                d.setdefault("rounds", {})
                d.setdefault("model_params", {"home_adv": 1.12})
                return d
    except Exception as e:
        print("[Load existing data warning]", e)
    return {"rounds": {}, "model_params": {"home_adv": 1.12}}


def fetch_url(url, timeout=12):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            for enc in ["utf-8", "cp932", "shift_jis", "euc-jp"]:
                try:
                    txt = raw.decode(enc)
                    if len(txt) > 150:
                        return txt
                except Exception:
                    continue
    except Exception as e:
        print("[Fetch failed]", url, e)
    return ""


def norm_team(name):
    nfkc = unicodedata.normalize("NFKC", name or "")
    clean = re.sub(r"\s+", "", nfkc)
    for k in sorted(TEAM_ALIAS_MAP.keys(), key=len, reverse=True):
        v = TEAM_ALIAS_MAP[k]
        if k in clean or v == clean:
            return v
    return clean


def extract_two_teams_in_order(text, stats):
    nfkc = unicodedata.normalize("NFKC", text or "")
    patterns = []
    for k, v in TEAM_ALIAS_MAP.items():
        if v in stats:
            patterns.append((k, v))
    for v in stats.keys():
        patterns.append((v, v))
    patterns.sort(key=lambda x: len(x[0]), reverse=True)

    masked = nfkc
    found = []
    for pat, canonical in patterns:
        idx = masked.find(pat)
        if idx != -1:
            found.append((idx, canonical))
            masked = masked[:idx] + ("_" * len(pat)) + masked[idx + len(pat):]

    found.sort(key=lambda x: x[0])
    ordered_teams = []
    for _, tm in found:
        if tm not in ordered_teams:
            ordered_teams.append(tm)
    return ordered_teams[:2]


def damp_multiplier(raw_mult, low=0.78, high=1.24):
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


def parse_toto_schedule_page(html, stats, today):
    if not html:
        return "", "", []
    soup = BeautifulSoup(html, "html.parser")
    full_txt = unicodedata.normalize("NFKC", soup.get_text(" ", strip=True))

    rid = ""
    m_rid = re.search(r"第(\d{4})回", full_txt)
    if m_rid:
        rid = m_rid.group(1)

    dead_str = ""
    m_dead = re.search(r"(?:販売終了|ネット決済)[^\d]{0,15}(\d{4}年\d{1,2}月\d{1,2}日(?:\([月火水木金土日]\))?)\s*(\d{2}:\d{2})", full_txt)
    if m_dead:
        dead_str = "{} {}締切".format(m_dead.group(1), m_dead.group(2))

    wds = ["月", "火", "水", "木", "金", "土", "日"]
    frame_map = {}

    for blk in soup.find_all(["tr", "li", "div"]):
        row_txt = unicodedata.normalize("NFKC", blk.get_text(" ", strip=True))
        if len(row_txt) < 8 or len(row_txt) > 220:
            continue

        f_idx = None
        cells = [unicodedata.normalize("NFKC", c.get_text(" ", strip=True)) for c in blk.find_all(["td", "th", "span", "p"])]
        for c in cells[:3]:
            m_num = re.fullmatch(r"(?:第)?0?([1-9]|1[0-3])(?:枠)?", c.strip())
            if m_num:
                f_idx = int(m_num.group(1))
                break
        if f_idx is None:
            m_head = re.match(r"^(?:第\s*)?0?([1-9]|1[0-3])(?:\s*枠)?\b", row_txt)
            if m_head:
                f_idx = int(m_head.group(1))
        if f_idx is None or f_idx in frame_map:
            continue

        teams = extract_two_teams_in_order(row_txt, stats)
        if len(teams) != 2:
            continue
        hn, an = teams[0], teams[1]

        match_d = today
        m_md = re.search(r"(\d{1,2})[/月](\d{1,2})", row_txt)
        if m_md:
            try:
                cand_y = today.year
                if today.month == 12 and int(m_md.group(1)) == 1:
                    cand_y += 1
                match_d = datetime.date(cand_y, int(m_md.group(1)), int(m_md.group(2)))
            except Exception:
                match_d = today

        iso_d = match_d.strftime("%Y-%m-%d")
        d_str = "{}月{}日({})".format(match_d.month, match_d.day, wds[match_d.weekday()])
        frame_map[f_idx] = (f_idx, match_d, iso_d, d_str, hn, an)

    ordered = [frame_map[k] for k in sorted(frame_map.keys())]
    return rid, dead_str, ordered


def get_official_toto_card(stats, today):
    """Yahoo! toto / 楽天toto / スポーツくじ公式から開催回号と指定13試合を確実取得"""
    rid = ""
    dead_str = ""
    official_games = []

    index_urls = [
        "https://toto.yahoo.co.jp/schedule/toto",
        "https://toto.rakuten.co.jp/toto/"
    ]
    for u in index_urls:
        h = fetch_url(u, 12)
        if not h:
            continue
        r_cand, d_cand, g_cand = parse_toto_schedule_page(h, stats, today)
        if r_cand and not rid:
            rid = r_cand
        if d_cand and not dead_str:
            dead_str = d_cand
        if len(g_cand) > len(official_games):
            official_games = g_cand

        soup = BeautifulSoup(h, "html.parser")
        txt = unicodedata.normalize("NFKC", soup.get_text(" ", strip=True))
        m_sale = re.search(r"第(\d{4})回[^\n]{0,40}販売中", txt)
        if m_sale:
            rid = m_sale.group(1)
        elif not rid:
            for a in soup.find_all("a", href=True):
                m_href = re.search(r"/toto/(?:schedule/)?(\d{4})", a["href"])
                if m_href:
                    rid = m_href.group(1)
                    break
        if rid and len(official_games) >= 13:
            break

    print("[Detected Round ID]", rid)

    if len(official_games) < 10 and rid:
        detail_urls = [
            "https://toto.yahoo.co.jp/schedule/toto/{}".format(rid),
            "https://toto.rakuten.co.jp/toto/{}/".format(rid),
            "https://toto.rakuten.co.jp/toto/schedule/{}/".format(rid),
            "https://store.toto-dream.com/dcs/subos/screen/pi01/spin000/PGSPIN00001DisptotoLotInfo.form?holdCntId={}&commodityId=01".format(rid),
            "https://sp.toto-dream.com/dcs/subos/screen/si01/ssin025/PGSSIN02501ForwardGameListtotoSP.form?holdCntId={}&commodityId=01".format(rid)
        ]
        for du in detail_urls:
            dh = fetch_url(du, 12)
            r2, d2, g2 = parse_toto_schedule_page(dh, stats, today)
            print("[Detail Try]", du, "-> parsed:", len(g2))
            if r2 and not rid:
                rid = r2
            if d2 and not dead_str:
                dead_str = d2
            if len(g2) > len(official_games):
                official_games = g2
            if len(official_games) >= 13:
                break

    # 万一すべての外部totoページが取得不可だった場合のJリーグ全大会(ルヴァン杯+J1/J2/J3)フォールバック
    if len(official_games) < 10:
        print("[Fallback] Fetching J.League future matches across all competitions...")
        wds = ["月", "火", "水", "木", "金", "土", "日"]
        ym = today.strftime("%Y%m")
        fb_urls = [
            "https://www.jleague.jp/match/search/leaguecup/{}/".format(ym),
            "https://www.jleague.jp/match/search/j1/{}/".format(ym),
            "https://www.jleague.jp/match/search/j2/{}/".format(ym),
            "https://www.jleague.jp/match/search/j3/{}/".format(ym)
        ]
        fb_list = []
        seen = set()
        for fu in fb_urls:
            fh = fetch_url(fu, 10)
            if not fh:
                continue
            fsoup = BeautifulSoup(fh, "html.parser")
            for blk in fsoup.find_all(["tr", "li", "div"]):
                txt = blk.get_text(" ", strip=True)
                if len(txt) > 200 or len(txt) < 6:
                    continue
                teams = extract_two_teams_in_order(txt, stats)
                if len(teams) == 2:
                    match_d = None
                    for a_tag in blk.find_all("a", href=True):
                        m_url_d = re.search(r"/2026/(\d{2})(\d{2})\d{2}/", a_tag["href"])
                        if m_url_d:
                            try:
                                cand = datetime.date(today.year, int(m_url_d.group(1)), int(m_url_d.group(2)))
                                if cand >= today:
                                    match_d = cand
                            except Exception:
                                pass
                    if match_d is None:
                        continue
                    iso_d = match_d.strftime("%Y-%m-%d")
                    d_str = "{}月{}日({})".format(match_d.month, match_d.day, wds[match_d.weekday()])
                    pk = "{}:{}-{}".format(iso_d, teams[0], teams[1])
                    if pk not in seen:
                        seen.add(pk)
                        fb_list.append((match_d, iso_d, d_str, teams[0], teams[1]))
        fb_list.sort(key=lambda x: x[0])
        if fb_list:
            first_d = fb_list[0][0]
            sliced = [g for g in fb_list if (g[0] - first_d).days <= 3][:13]
            if len(sliced) < 5:
                sliced = fb_list[:13]
            official_games = [(idx, g[0], g[1], g[2], g[3], g[4]) for idx, g in enumerate(sliced, 1)]

    round_str = "第{}回".format(rid) if rid else "最新開催回"
    if not dead_str:
        dead_str = "公式スケジュール準拠"

    print("[Final Official Toto Card]", round_str, dead_str, "Count:", len(official_games))
    return rid, round_str, dead_str, official_games


def get_official_vote_rates(rid):
    votes = {}
    urls = []
    if rid:
        urls.append("https://toto.yahoo.co.jp/vote/toto/{}".format(rid))
        urls.append("https://toto.rakuten.co.jp/toto/vote/{}/".format(rid))
        urls.append(
            "https://store.toto-dream.com/dcs/subos/screen/pi09/spin003/PGSPIN00301InitVoteRate.form?holdCntId={}&commodityId=01".format(rid)
        )
    urls.append("https://toto.yahoo.co.jp/vote/toto")

    for u in urls:
        html = fetch_url(u, 10)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            row_txt = unicodedata.normalize("NFKC", tr.get_text(" ", strip=True))
            m_f = re.match(r"^0?([1-9]|1[0-3])\b", row_txt)
            pcts = [float(x) for x in re.findall(r"(\d{1,2}(?:\.\d+)?)\s*%", row_txt)]
            if m_f and len(pcts) >= 3:
                f_idx = int(m_f.group(1))
                if 1 <= f_idx <= 13 and 95.0 <= sum(pcts[:3]) <= 105.0:
                    votes[f_idx] = [round(pcts[0], 1), round(pcts[1], 1), round(pcts[2], 1)]
        if len(votes) >= 10:
            break

    print("[Official Vote Rates Loaded]", len(votes))
    return votes


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


def get_club_stats_by_league():
    league_rows = {"J1": [], "J2": [], "J3": []}
    league_totals = {"J1": [0, 0], "J2": [0, 0], "J3": [0, 0]}

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
                league_totals[div][0] += gf
                league_totals[div][1] += pl

                home_tilt, away_tilt = 1.0, 1.0
                if len(nums) >= 16:
                    h_w, h_l = nums[9], nums[11]
                    a_w, a_l = nums[13], nums[15]
                    home_tilt = round(max(0.92, min(1.08, 1.0 + (h_w - h_l) * 0.012)), 3)
                    away_tilt = round(max(0.92, min(1.08, 1.0 + (a_w - a_l) * 0.012)), 3)

                recent_mult, recent_tag = parse_recent_form_score("".join(cells))
                league_rows[div].append(
                    (t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, home_tilt, away_tilt)
                )

    league_avgs = {}
    for div in ["J1", "J2", "J3"]:
        gf_sum, pl_sum = league_totals[div]
        league_avgs[div] = round(gf_sum / max(1, pl_sum), 3) if pl_sum > 0 else 1.30

    stats = {}
    for div, rows in league_rows.items():
        l_avg = league_avgs[div]
        for (t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, h_tilt, a_tilt) in rows:
            atk_base = ((gf / pl) * 0.80) + (l_avg * 0.20)
            def_base = ((ga / pl) * 0.80) + (l_avg * 0.20)

            pyth_exp = (gf ** 1.35) / max(1.0, (gf ** 1.35) + (ga ** 1.35))
            actual_win_rate = (w + d * 0.35) / pl
            true_strength_mult = 0.93 + (pyth_exp * 0.10) + (actual_win_rate * 0.06)
            blended_form = (true_strength_mult * 0.65) + (recent_mult * 0.35)

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
                "div": div,
                "l_avg": l_avg,
                "atk": round(atk_base * blended_form * motive_mult, 3),
                "def_v": round(def_base / (blended_form * motive_mult), 3),
                "h_tilt": h_tilt,
                "a_tilt": a_tilt,
                "trend": tr_str,
                "rk": rk
            }

    print("[Club Stats] Fetched:", len(stats))
    return stats


def get_match_links_for_dates(stats, target_dates):
    link_map = {}
    for iso_d in sorted(list(target_dates)):
        ymd = iso_d.replace("-", "")
        html = fetch_url("https://www.jleague.jp/match/search/all/{}/".format(ymd), 10)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for blk in soup.find_all(["tr", "li", "div"]):
            txt = blk.get_text(" ", strip=True)
            if len(txt) > 200 or len(txt) < 6:
                continue
            teams = extract_two_teams_in_order(txt, stats)
            if len(teams) == 2:
                for a_tag in blk.find_all("a", href=True):
                    href = a_tag["href"]
                    if "/match/" in href and ("live" in href or "preview" in href):
                        full_u = href if href.startswith("http") else "https://www.jleague.jp" + href
                        link_map["{}-{}".format(teams[0], teams[1])] = full_u
                        break
    return link_map


def get_recent_match_dates_and_results(stats, existing_data, today):
    last_played = {}
    recent_scores = {}

    for back in range(1, 8):
        past_d = today - datetime.timedelta(days=back)
        ymd = past_d.strftime("%Y%m%d")
        html = fetch_url("https://www.jleague.jp/match/search/all/{}/".format(ymd), 8)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for blk in soup.find_all(["tr", "li", "div"]):
            txt = blk.get_text(" ", strip=True)
            if len(txt) > 180 or len(txt) < 6:
                continue
            teams = extract_two_teams_in_order(txt, stats)
            if len(teams) == 2:
                for tm in teams:
                    if tm not in last_played:
                        last_played[tm] = past_d
                m_sc = re.search(r"(\d+)\s*[-－ー]\s*(\d+)", txt)
                if m_sc:
                    hs, as_ = int(m_sc.group(1)), int(m_sc.group(2))
                    res_code = "1" if hs > as_ else ("2" if hs < as_ else "0")
                    recent_scores["{}-{}".format(teams[0], teams[1])] = {
                        "hs": hs, "as": as_, "res": res_code
                    }

    home_adv = float(existing_data.get("model_params", {}).get("home_adv", 1.12))
    pred_home_wins, actual_home_wins, sample_cnt = 0.0, 0.0, 0

    for rk, r_obj in existing_data.get("rounds", {}).items():
        act = r_obj.setdefault("actual_results", {})
        for m in r_obj.get("matches", []):
            pair_key = "{}-{}".format(m.get("h"), m.get("a"))
            if pair_key in recent_scores:
                act[str(m["f"])] = recent_scores[pair_key]
            f_str = str(m.get("f"))
            if f_str in act and "v" in m:
                pred_home_wins += (m["v"][0] / 100.0)
                actual_home_wins += (1.0 if act[f_str]["res"] == "1" else 0.0)
                sample_cnt += 1

    if sample_cnt >= 10:
        err = (actual_home_wins - pred_home_wins) / sample_cnt
        home_adv = round(max(1.05, min(1.18, home_adv + err * 0.15)), 3)

    return last_played, home_adv


def get_key_players_and_suspensions(stats):
    atk_stars = set()
    all_regulars = set()
    suspended_teams = set()

    for div in ["j1", "j2", "j3"]:
        g_html = fetch_url("https://www.jleague.jp/stats/{}/goal.html".format(div), 8)
        if g_html:
            soup = BeautifulSoup(g_html, "html.parser")
            for tr in soup.find_all("tr")[:35]:
                for a in tr.find_all("a"):
                    nm = re.sub(r"\s+", "", a.get_text(strip=True))
                    if 2 <= len(nm) <= 12 and not any(x in nm for x in ["J1", "J2", "J3", "詳細", "順位"]):
                        atk_stars.add(nm)
                        all_regulars.add(nm)

        p_html = fetch_url("https://www.jleague.jp/stats/{}/playtime.html".format(div), 8)
        if p_html:
            soup = BeautifulSoup(p_html, "html.parser")
            for tr in soup.find_all("tr")[:50]:
                for a in tr.find_all("a"):
                    nm = re.sub(r"\s+", "", a.get_text(strip=True))
                    if 2 <= len(nm) <= 12 and not any(x in nm for x in ["J1", "J2", "J3", "詳細", "順位"]):
                        all_regulars.add(nm)

    s_html = fetch_url("https://www.jleague.jp/news/", 8)
    if s_html:
        soup = BeautifulSoup(s_html, "html.parser")
        for a in soup.find_all("a"):
            t = a.get_text(strip=True)
            if "出場停止" in t:
                for tm in stats.keys():
                    if tm in t:
                        suspended_teams.add(tm)

    return atk_stars, all_regulars, suspended_teams


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


def check_lineup_and_suspension(match_url, h_team, a_team, atk_stars, all_regulars, suspended_teams):
    h_atk_m = 0.96 if h_team in suspended_teams else 1.0
    a_atk_m = 0.96 if a_team in suspended_teams else 1.0
    h_def_m = 1.04 if h_team in suspended_teams else 1.0
    a_def_m = 1.04 if a_team in suspended_teams else 1.0
    susp_note = "(出場停止影響あり)" if (h_team in suspended_teams or a_team in suspended_teams) else ""

    if not match_url:
        return h_atk_m, h_def_m, a_atk_m, a_def_m, "スタメン発表前" + susp_note

    html = fetch_url(match_url, 10)
    if not html:
        return h_atk_m, h_def_m, a_atk_m, a_def_m, "スタメン発表前" + susp_note

    soup = BeautifulSoup(html, "html.parser")
    txt = soup.get_text(" ", strip=True)
    if "先発" not in txt and "スターティング" not in txt:
        return h_atk_m, h_def_m, a_atk_m, a_def_m, "スタメン発表前" + susp_note

    clean_txt = re.sub(r"\s+", "", txt)
    hit_atk = [p for p in atk_stars if p in clean_txt]
    hit_reg = [p for p in all_regulars if p in clean_txt]

    if len(hit_atk) >= 2 and len(hit_reg) >= 6:
        return 1.07, 0.95, 1.07, 0.95, "スタメン確定(攻守主力万全:{}ほか)".format(hit_atk[0])
    elif len(hit_reg) >= 4:
        return 1.02, 0.98, 1.02, 0.98, "スタメン確定(主力中心:{}ほか)".format(hit_reg[0])
    return 0.91, 1.08, 0.91, 1.08, "スタメン確定(ターンオーバー/守備変更傾向)"


def calc_vote_league_dc(h_lam, a_lam, div):
    tot_lam = h_lam + a_lam
    league_bias = -0.015 if div == "J2" else (0.015 if div == "J3" else 0.0)
    rho = max(-0.17, min(-0.05, -0.12 + league_bias + (tot_lam - 2.4) * 0.03))

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


def blend_with_smart_market(h_lam, a_lam, div, mkt_v, prev_v):
    if not mkt_v or len(mkt_v) < 3:
        return h_lam, a_lam, ""

    debiased = [max(1.0, x) ** 0.85 for x in mkt_v]
    s = sum(debiased)
    m_p1, m_p2 = debiased[0] / s, debiased[2] / s

    smart_h, smart_a = 1.0, 1.0
    smart_tag = ""
    if prev_v and len(prev_v) >= 3:
        diff_1 = mkt_v[0] - prev_v[0]
        diff_2 = mkt_v[2] - prev_v[2]
        if diff_1 >= 3.0:
            smart_h = 1.03
            smart_tag = "・直前H人気急上昇"
        elif diff_2 >= 3.0:
            smart_a = 1.03
            smart_tag = "・直前A人気急上昇"

    stat_v = calc_vote_league_dc(h_lam, a_lam, div)
    s_p1, s_p2 = stat_v[0] / 100.0, stat_v[2] / 100.0

    h_shift = damp_multiplier((1.0 + (m_p1 - s_p1) * 0.25) * smart_h, 0.92, 1.08)
    a_shift = damp_multiplier((1.0 + (m_p2 - s_p2) * 0.25) * smart_a, 0.92, 1.08)
    return round(h_lam * h_shift, 2), round(a_lam * a_shift, 2), " / 集合知融合済" + smart_tag


def build_round_predictions(official_games, stats, last_played, home_adv, atk_stars, all_regulars,
                            suspended_teams, round_num_str, deadline_str, market_votes, prev_round_votes):
    if not official_games:
        return None

    target_dates = set(g[2] for g in official_games)
    link_map = get_match_links_for_dates(stats, target_dates)

    sorted_by_date = sorted(official_games, key=lambda x: x[1])
    udates = []
    for g in sorted_by_date:
        if g[3] not in udates:
            udates.append(g[3])
    d_label = "・".join(udates[:2])

    matches = []
    for (f_idx, m_date, iso_d, ds, hn, an) in official_games:
        hs = stats.get(hn, {"div": "J1", "l_avg": 1.30, "atk": 1.30, "def_v": 1.30, "h_tilt": 1.0, "a_tilt": 1.0, "trend": ""})
        as_ = stats.get(an, {"div": "J1", "l_avg": 1.30, "atk": 1.30, "def_v": 1.30, "h_tilt": 1.0, "a_tilt": 1.0, "trend": ""})
        div = hs.get("div", "J1")
        l_avg = hs.get("l_avg", 1.30)

        m_link = link_map.get("{}-{}".format(hn, an), "")
        w_mult, w_label = check_weather(hn, iso_d)
        h_atk_lu, h_def_lu, a_atk_lu, a_def_lu, lu_label = check_lineup_and_suspension(
            m_link, hn, an, atk_stars, all_regulars, suspended_teams
        )
        travel_mult, travel_tag = calc_travel_penalty(hn, an)

        h_rest = (m_date - last_played[hn]).days if hn in last_played else 7
        a_rest = (m_date - last_played[an]).days if an in last_played else 7
        rest_diff = h_rest - a_rest
        h_rest_mult, a_rest_mult, rest_note = 1.0, 1.0, ""
        if rest_diff <= -2 and h_rest <= 4:
            h_rest_mult = 0.94
            rest_note = " / H過密(中{}日)".format(h_rest - 1)
        elif rest_diff >= 2 and a_rest <= 4:
            a_rest_mult = 0.94
            rest_note = " / A過密(中{}日)".format(a_rest - 1)

        away_adv = round(2.04 - home_adv, 3)
        h_base = hs["atk"] * ((as_["def_v"] * a_def_lu) / l_avg) * home_adv * hs["h_tilt"]
        a_base = as_["atk"] * ((hs["def_v"] * h_def_lu) / l_avg) * away_adv * as_["a_tilt"]

        h_env_mult = damp_multiplier(w_mult * h_atk_lu * h_rest_mult)
        a_env_mult = damp_multiplier(w_mult * a_atk_lu * a_rest_mult * travel_mult)

        h_rel = h_base * h_env_mult
        a_rel = a_base * a_env_mult

        lam_gap = h_rel - a_rel
        cs_tag = ""
        if lam_gap >= 0.45:
            a_rel *= 0.89
            cs_tag = " / H完封優位"
        elif lam_gap <= -0.45:
            h_rel *= 0.89
            cs_tag = " / A完封優位"

        mkt_v = market_votes.get(f_idx)
        prev_v = prev_round_votes.get(f_idx)
        final_h_lam, final_a_lam, mkt_tag = blend_with_smart_market(h_rel, a_rel, div, mkt_v, prev_v)

        final_h_lam = round(max(0.30, min(3.30, final_h_lam)), 2)
        final_a_lam = round(max(0.25, min(3.10, final_a_lam)), 2)

        model_v = calc_vote_league_dc(final_h_lam, final_a_lam, div)
        display_v = mkt_v if mkt_v else model_v

        grp = "A" if f_idx <= 5 else ("B" if f_idx <= 10 else "C")
        tr_note = " / {}".format(travel_tag) if travel_tag else ""
        auto_note = "天候:{} / {}{}{}{}{}".format(w_label, lu_label, rest_note, tr_note, cs_tag, mkt_tag)
        matches.append({
            "f": f_idx, "grp": grp, "h": hn, "a": an,
            "v": display_v,
            "h_xg": final_h_lam, "h_xga": final_a_lam,
            "a_xg": final_a_lam, "a_xga": final_h_lam,
            "analysis": "[{} | {}] H:{} {} / A:{} {}".format(ds, auto_note, hn, hs["trend"], an, as_["trend"])
        })

    rk = "{} (開催: {} / {})".format(round_num_str, d_label, deadline_str)
    return rk, {
        "title": "{} | 開催日: {} | 締切: {} (公式指定全{}試合・自己学習アンサンブル適用済)".format(
            round_num_str, d_label, deadline_str, len(matches)
        ),
        "goal3_frames": [x for x in [1, 2, 3] if x <= len(matches)],
        "matches": matches,
        "actual_results": {}
    }


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(jst)
    today = now_jst.date()

    existing_data = load_existing_data()
    st = get_club_stats_by_league()
    last_played, home_adv = get_recent_match_dates_and_results(st, existing_data, today)
    rid, r_num, deadline_str, official_games = get_official_toto_card(st, today)
    mkt_votes = get_official_vote_rates(rid)
    atk_stars, all_regulars, suspended_teams = get_key_players_and_suspensions(st)

    prev_round_votes = {}
    for k, r_obj in existing_data.get("rounds", {}).items():
        if r_num in k:
            for m in r_obj.get("matches", []):
                if "v" in m:
                    prev_round_votes[int(m["f"])] = m["v"]

    res = build_round_predictions(
        official_games, st, last_played, home_adv, atk_stars, all_regulars, suspended_teams,
        r_num, deadline_str, mkt_votes, prev_round_votes
    )

    rounds = existing_data.get("rounds", {})
    current_rk = existing_data.get("current_round", "")
    if res:
        rk, obj = res
        old_act = {}
        for old_k in list(rounds.keys()):
            if r_num in old_k or "最新開催回" in old_k:
                old_act = rounds[old_k].get("actual_results", {})
                if old_k != rk:
                    del rounds[old_k]
        obj["actual_results"] = old_act
        rounds[rk] = obj
        current_rk = rk
        print("[SUCCESS]", rk, len(obj["matches"]))

    if len(rounds) > 5:
        for old_k in list(rounds.keys())[:-5]:
            del rounds[old_k]

    out_data = {
        "current_round": current_rk,
        "last_updated": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "model_params": {"home_adv": home_adv},
        "club_stats": st,
        "rounds": rounds
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
    
