import json
import math
import os
import re
import hashlib
import datetime
import unicodedata
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"
HTML_FILE = "index.html"

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
    except Exception:
        pass
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


def calc_travel_penalty(h_team, a_team):
    c1 = STADIUM_COORDS.get(h_team)
    c2 = STADIUM_COORDS.get(a_team)
    if not c1 or not c2:
        return 1.0, ""
    lat1, lon1 = math.radians(c1[0]), math.radians(c1[1])
    lat2, lon2 = math.radians(c2[0]), math.radians(c2[1])
    a = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
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


def fetch_card_for_round_id(rid, stats, today):
    detail_urls = [
        "https://toto.yahoo.co.jp/schedule/toto/{}".format(rid),
        "https://toto.rakuten.co.jp/toto/{}/".format(rid),
        "https://toto.rakuten.co.jp/toto/schedule/{}/".format(rid),
        "https://store.toto-dream.com/dcs/subos/screen/pi01/spin000/PGSPIN00001DisptotoLotInfo.form?holdCntId={}&commodityId=01".format(rid),
        "https://sp.toto-dream.com/dcs/subos/screen/si01/ssin025/PGSSIN02501ForwardGameListtotoSP.form?holdCntId={}&commodityId=01".format(rid)
    ]
    best_games = []
    dead_str = "公式スケジュール準拠"
    for du in detail_urls:
        dh = fetch_url(du, 12)
        r2, d2, g2 = parse_toto_schedule_page(dh, stats, today)
        if d2 and dead_str == "公式スケジュール準拠":
            dead_str = d2
        if len(g2) > len(best_games):
            best_games = g2
        if len(best_games) >= 13:
            break
    return dead_str, best_games


def get_official_toto_rounds(stats, today):
    rids = []
    for u in ["https://toto.yahoo.co.jp/schedule/toto", "https://toto.rakuten.co.jp/toto/"]:
        h = fetch_url(u, 12)
        if not h:
            continue
        txt = unicodedata.normalize("NFKC", BeautifulSoup(h, "html.parser").get_text(" ", strip=True))
        for m in re.findall(r"第(\d{4})回", txt):
            if m not in rids:
                rids.append(m)

    if rids:
        base_id = int(rids[0])
        for cand_id in [base_id - 1, base_id, base_id + 1, base_id + 2]:
            s_id = str(cand_id)
            if s_id not in rids:
                rids.append(s_id)
        rids = sorted(rids)

    results = []
    for rid in rids:
        dead_str, games = fetch_card_for_round_id(rid, stats, today)
        if len(games) >= 10:
            min_game_date = min(g[1] for g in games)
            max_game_date = max(g[1] for g in games)
            if max_game_date >= today - datetime.timedelta(days=1):
                results.append((rid, "第{}回".format(rid), dead_str, games, min_game_date, max_game_date))

    # 今日以降で最も開催日が近い順にソート（第1672回 → 第1673回 → 第1674回...）
    results.sort(key=lambda x: (x[4], int(x[0])))
    return results


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
    return votes


def parse_recent_form_score(row_text):
    cleaned = re.sub(r"\s+", "", row_text)
    m = re.search(r"([WDL勝分敗○△●]{5})", cleaned)
    if not m:
        return 1.0, ""
    seq = m.group(1)
    pts = sum(3 if ch in ["W", "勝", "○"] else (1 if ch in ["D", "分", "△"] else 0) for ch in seq)
    return round(0.90 + (pts / 15.0) * 0.22, 3), "直近5戦{}/15pt".format(pts)


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
                w, d, l, gf, ga = nums[3], nums[4], nums[5], nums[6], nums[7]
                league_totals[div][0] += gf
                league_totals[div][1] += pl
                home_tilt, away_tilt = 1.0, 1.0
                if len(nums) >= 16:
                    home_tilt = round(max(0.92, min(1.08, 1.0 + (nums[9] - nums[11]) * 0.012)), 3)
                    away_tilt = round(max(0.92, min(1.08, 1.0 + (nums[13] - nums[15]) * 0.012)), 3)
                recent_mult, recent_tag = parse_recent_form_score("".join(cells))
                league_rows[div].append((t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, home_tilt, away_tilt))

    stats = {}
    for div, rows in league_rows.items():
        gf_sum, pl_sum = league_totals[div]
        l_avg = round(gf_sum / max(1, pl_sum), 3) if pl_sum > 0 else 1.30
        for (t, div, rk, pts, pl, w, d, l, gf, ga, recent_mult, recent_tag, h_tilt, a_tilt) in rows:
            atk_base = ((gf / pl) * 0.80) + (l_avg * 0.20)
            def_base = ((ga / pl) * 0.80) + (l_avg * 0.20)
            pyth_exp = (gf ** 1.35) / max(1.0, (gf ** 1.35) + (ga ** 1.35))
            actual_win_rate = (w + d * 0.35) / pl
            blended_form = ((0.93 + (pyth_exp * 0.10) + (actual_win_rate * 0.06)) * 0.65) + (recent_mult * 0.35)
            motive_mult = 1.05 if ((div == "J1" and rk <= 3) or (div in ["J2", "J3"] and rk <= 6)) else (1.04 if rk >= 17 else 1.0)
            motive_tag = "・優勝/昇格圏" if motive_mult == 1.05 else ("・残留争い" if motive_mult == 1.04 else "")
            extra = "・" + recent_tag if recent_tag else ""
            stats[t] = {
                "div": div, "l_avg": l_avg,
                "atk": round(atk_base * blended_form * motive_mult, 3),
                "def_v": round(def_base / (blended_form * motive_mult), 3),
                "h_tilt": h_tilt, "a_tilt": a_tilt,
                "trend": "[{} {}位{}{}] 勝点{}/{}勝{}分{}敗".format(div, rk, motive_tag, extra, pts, w, d, l),
                "rk": rk
            }
    return stats


def check_weather(home_team, target_date_iso):
    coords = STADIUM_COORDS.get(home_team)
    if not coords:
        return 1.0, "晴/曇"
    api = (
        "https://api.open-meteo.com/v1/forecast?latitude={}&longitude={}"
        "&daily=precipitation_sum,wind_speed_10m_max&timezone=Asia%2FTokyo&start_date={}&end_date={}"
    ).format(coords[0], coords[1], target_date_iso, target_date_iso)
    raw = fetch_url(api, 8)
    if not raw:
        return 1.0, "晴/曇"
    try:
        daily = json.loads(raw).get("daily", {})
        prec = (daily.get("precipitation_sum") or [0])[0] or 0
        wind = (daily.get("wind_speed_10m_max") or [0])[0] or 0
        if prec >= 2.0:
            return 0.86, "雨({}mm)".format(prec)
        if wind >= 36.0:
            return 0.90, "強風({}km/h)".format(round(wind))
    except Exception:
        pass
    return 1.0, "晴/曇"


def calc_vote_league_dc(h_lam, a_lam):
    def pois(k, lam):
        return (lam ** k) * math.exp(-lam) / math.factorial(k)
    p1, p0, p2 = 0.0, 0.0, 0.0
    for i in range(6):
        for j in range(6):
            p = pois(i, h_lam) * pois(j, a_lam)
            if i > j:
                p1 += p
            elif i == j:
                p0 += p
            else:
                p2 += p
    tot = max(1e-6, p1 + p0 + p2)
    r1 = round((p1 / tot) * 100, 1)
    r2 = round((p2 / tot) * 100, 1)
    return [r1, round(max(12.0, 100.0 - r1 - r2), 1), r2]


def build_round_predictions(official_games, stats, home_adv, round_num_str, deadline_str, market_votes):
    if not official_games:
        return None
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
        l_avg = hs.get("l_avg", 1.30)
        w_mult, w_label = check_weather(hn, iso_d)
        travel_mult, travel_tag = calc_travel_penalty(hn, an)

        away_adv = round(2.04 - home_adv, 3)
        h_rel = hs["atk"] * (as_["def_v"] / l_avg) * home_adv * hs["h_tilt"] * w_mult
        a_rel = as_["atk"] * (hs["def_v"] / l_avg) * away_adv * as_["a_tilt"] * w_mult * travel_mult

        final_h_lam = round(max(0.30, min(3.30, h_rel)), 2)
        final_a_lam = round(max(0.25, min(3.10, a_rel)), 2)
        mkt_v = market_votes.get(f_idx)
        display_v = mkt_v if mkt_v else calc_vote_league_dc(final_h_lam, final_a_lam)

        grp = "A" if f_idx <= 5 else ("B" if f_idx <= 10 else "C")
        tr_note = " / {}".format(travel_tag) if travel_tag else ""
        matches.append({
            "f": f_idx, "grp": grp, "h": hn, "a": an, "v": display_v,
            "h_xg": final_h_lam, "h_xga": final_a_lam, "a_xg": final_a_lam, "a_xga": final_h_lam,
            "analysis": "[{} | 天候:{}{}] H:{} {} / A:{} {}".format(ds, w_label, tr_note, hn, hs["trend"], an, as_["trend"])
        })

    rk = "{} (開催: {} / {})".format(round_num_str, d_label, deadline_str)
    return rk, {
        "title": "{} | 開催日: {} | 締切: {} (公式指定全{}試合)".format(round_num_str, d_label, deadline_str, len(matches)),
        "goal3_frames": [1, 2, 3],
        "matches": matches,
        "actual_results": {}
    }


def embed_data_into_html(out_data):
    if not os.path.exists(HTML_FILE):
        return
    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html = f.read()

    pin = os.environ.get("APP_PIN", "").strip()
    if pin and "__INJECTED_PIN_HASH__" in html:
        h = hashlib.sha256(pin.encode("utf-8")).hexdigest()
        html = html.replace("__INJECTED_PIN_HASH__", h)

    json_str = json.dumps(out_data, ensure_ascii=False)
    replacement = (
        "<!-- EMBEDDED_DATA_START -->\n"
        "  <script id=\"embedded-toto-data\">window.__EMBEDDED_TOTO_DATA__ = " + json_str + ";</script>\n"
        "  <!-- EMBEDDED_DATA_END -->"
    )
    if "<!-- EMBEDDED_DATA_START -->" in html and "<!-- EMBEDDED_DATA_END -->" in html:
        html = re.sub(
            r"<!-- EMBEDDED_DATA_START -->.*?<!-- EMBEDDED_DATA_END -->",
            lambda _: replacement,
            html,
            flags=re.DOTALL
        )
    with open(HTML_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print("[EMBEDDED] Current round set to:", out_data.get("current_round"))


def main():
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(jst)
    today = now_jst.date()

    existing_data = load_existing_data()
    home_adv = float(existing_data.get("model_params", {}).get("home_adv", 1.12))
    st = get_club_stats_by_league()

    official_rounds = get_official_toto_rounds(st, today)
    rounds = {}
    most_recent_rk = ""
    fallback_rk = ""

    for (rid, r_num, deadline_str, official_games, min_d, max_d) in official_rounds:
        mkt_votes = get_official_vote_rates(rid)
        res = build_round_predictions(
            official_games, st, home_adv, r_num, deadline_str, mkt_votes
        )
        if res:
            rk, obj = res
            rounds[rk] = obj
            if not fallback_rk:
                fallback_rk = rk
            # 今日以降に最終試合がある回の中で、最も開催が近い回を優先選択
            if not most_recent_rk and max_d >= today:
                most_recent_rk = rk

    current_rk = most_recent_rk or fallback_rk

    if not rounds:
        rounds = existing_data.get("rounds", {})
        current_rk = existing_data.get("current_round", "")

    out_data = {
        "current_round": current_rk,
        "last_updated": now_jst.strftime("%Y-%m-%d %H:%M JST"),
        "model_params": {"home_adv": home_adv},
        "club_stats": st,
        "rounds": rounds
    }
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(out_data, f, ensure_ascii=False, indent=2)

    embed_data_into_html(out_data)


if __name__ == "__main__":
    main()
