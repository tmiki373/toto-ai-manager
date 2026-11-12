import json
import re
import datetime
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"


def fetch_url_smart(target_url, timeout=15):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
    }
    try:
        req = urllib.request.Request(target_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            for enc in ["utf-8", "shift_jis", "cp932", "euc-jp"]:
                try:
                    text = raw.decode(enc)
                    if len(text) > 500:
                        return text
                except Exception:
                    continue
    except Exception as e:
        print(f"[Fetch failed] {target_url} -> {e}")
    return ""


def normalize_team_name(raw_name):
    mapping = {
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
    clean = re.sub(r"\s+", "", raw_name)
    for full, short in mapping.items():
        if full in clean or short == clean:
            return short
    return clean


def fetch_dynamic_club_stats():
    stats = {}
    sources = [
        ("https://www.jleague.jp/standings/j1/", "J1"),
        ("https://www.jleague.jp/standings/j2/", "J2"),
        ("https://www.jleague.jp/standings/j3/", "J3")
    ]
    for url, div in sources:
        html = fetch_url_smart(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
            cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
            nums = [int(x) for x in cells if re.fullmatch(r"-?\d+", x)]
            texts = [x for x in cells if len(x) >= 2 and not re.fullmatch(r"-?\d+", x)]
            if len(nums) >= 8 and len(texts) >= 1:
                team_short = normalize_team_name(texts[0])
                if team_short in stats:
                    continue
                rank, pts, played = nums[0], nums[1], max(1, nums[2])
                gf, ga = nums[6], nums[7]
                gd = gf - ga
                avg_gf = round(gf / played, 2)
                avg_ga = round(ga / played, 2)
                dyn_xg = round(avg_gf * 0.75 + 1.30 * 0.25, 2)
                dyn_xga = round(avg_ga * 0.75 + 1.30 * 0.25, 2)

                atk_eval = "得点力上位" if avg_gf >= 1.50 else ("得点力不足" if avg_gf <= 0.95 else "標準的攻撃力")
                def_eval = "鉄壁守備" if avg_ga <= 0.95 else ("失点過多" if avg_ga >= 1.65 else "標準的守備")
                trend = f"[{div} {rank}位] 勝点{pts}/得失{gd:+d}・平均{avg_gf:.2f}得点/{avg_ga:.2f}失点({atk_eval}・{def_eval})"
                stats[team_short] = {"xg": dyn_xg, "xga": dyn_xga, "trend": trend, "div": div, "rank": rank}
    print(f"[Club Stats] Fetched {len(stats)} clubs dynamically.")
    return stats


def fetch_latest_round_info():
    """toto公式サイトトップから最新開催回号と開催日・締切日時を抽出"""
    html = fetch_url_smart("https://www.toto-dream.com/toto/index.html")
    round_id = "最新開催回"
    date_label = ""
    if html:
        ids = re.findall(r"第(\d{4})回", html)
        if ids:
            round_id = sorted(list(set(ids)))[-1]
        soup = BeautifulSoup(html, "html.parser")
        txt = soup.get_text(" ", strip=True)
        # 開催日・販売締切日の日付パターンを抽出 (例: 11月14日(土) / 2026年11月14日)
        m_dates = re.findall(r"(?:\d{4}年)?\d{1,2}月\d{1,2}日(?:\s*[（(][月火水木金土日][）)])?", txt)
        if m_dates:
            unique_dates = []
            for d in m_dates:
                d_clean = re.sub(r"\s+", "", d)
                if d_clean not in unique_dates:
                    unique_dates.append(d_clean)
            date_label = "・".join(unique_dates[:2])
    print(f"[Latest toto Info] ID={round_id}, Date={date_label}")
    return round_id, date_label


def estimate_market_vote(h_xg, h_xga, a_xg, a_xga):
    h_pow = (h_xg / max(0.5, a_xga)) * 1.15
    a_pow = (a_xg / max(0.5, h_xga)) * 0.90
    d_pow = 0.75
    tot = h_pow + a_pow + d_pow
    p1 = round((h_pow / tot) * 100, 1)
    p2 = round((a_pow / tot) * 100, 1)
    p0 = round(max(15.0, 100.0 - p1 - p2), 1)
    return [p1, p0, p2]


def fetch_jleague_upcoming_matches(club_stats, round_id, toto_date_label):
    match_urls = [
        "https://www.jleague.jp/match/",
        "https://www.jleague.jp/match/section/j1/latest/",
        "https://www.jleague.jp/match/section/j2/latest/",
        "https://www.jleague.jp/match/section/j3/latest/"
    ]

    raw_games = []
    seen_pairs = set()
    extracted_dates = []

    for m_url in match_urls:
        html = fetch_url_smart(m_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        page_txt = soup.get_text(" ", strip=True)
        for d_m in re.findall(r"\d{1,2}月\d{1,2}日\s*[（(][月火水木金土日][）)]", page_txt):
            d_clean = re.sub(r"\s+", "", d_m)
            if d_clean not in extracted_dates:
                extracted_dates.append(d_clean)

        for block in soup.find_all(["tr", "li", "div"]):
            txt = block.get_text(" ", strip=True)
            if len(txt) > 180 or len(txt) < 6:
                continue
            found_teams = []
            for elem in block.find_all(["td", "span", "p", "a", "div"]):
                t_str = elem.get_text(strip=True)
                if 2 <= len(t_str) <= 16:
                    norm = normalize_team_name(t_str)
                    if norm in club_stats and norm not in found_teams:
                        found_teams.append(norm)
            if len(found_teams) == 2:
                pair_key = f"{found_teams[0]}-{found_teams[1]}"
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    sc = re.search(r"(\d+)\s*[-－]\s*(\d+)", txt)
                    act = None
                    if sc and ("試合終了" in txt or "FT" in txt or re.search(r"\b\d+\s*-\s*\d+\b", txt)):
                        hs_v, as_v = int(sc.group(1)), int(sc.group(2))
                        if hs_v <= 9 and as_v <= 9:
                            mark = "1" if hs_v > as_v else ("2" if as_v > hs_v else "0")
                            act = {"res": mark, "hs": hs_v, "as": as_v}
                    raw_games.append((found_teams[0], found_teams[1], act))

    print(f"[J-League Match Pages] Extracted {len(raw_games)} unique matches total.")
    if len(raw_games) == 0:
        return None

    selected = raw_games[:13]
    matches = []
    actual_results = {}

    for idx, (h_name, a_name, act) in enumerate(selected, start=1):
        hs = club_stats.get(h_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ計算済"})
        as_ = club_stats.get(a_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ計算済"})
        grp = "A" if idx <= 5 else ("B" if idx <= 10 else "C")
        v_rates = estimate_market_vote(hs["xg"], hs["xga"], as_["xg"], as_["xga"])

        matches.append({
            "f": idx, "grp": grp, "h": h_name, "a": a_name,
            "v": v_rates,
            "h_xg": hs["xg"], "h_xga": hs["xga"],
            "a_xg": as_["xg"], "a_xga": as_["xga"],
            "analysis": f"【H:{h_name}】{hs['trend']} ／ 【A:{a_name}】{as_['trend']}"
        })
        if act:
            actual_results[str(idx)] = act

    jst = datetime.timezone(datetime.timedelta(hours=9))
    today_str = datetime.datetime.now(jst).strftime("%Y/%m/%d")

    # 開催日ラベルの組み立て（Jリーグ試合開催日 or toto公式日付）
    final_date = "・".join(extracted_dates[:2]) if extracted_dates else (toto_date_label or today_str)
    base_round = f"第{round_id}回" if round_id.isdigit() else "最新節"
    r_key = f"{base_round} ({final_date})"

    return r_key, {
        "title": f"{base_round}｜開催日: {final_date}（全{len(matches)}試合・最新順位スタッツ反映）",
        "goal3_frames": [i for i in [1, 2, 3] if i <= len(matches)],
        "matches": matches,
        "actual_results": actual_results
    }


def main():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {"current_round": "", "last_updated": "", "club_stats": {}, "rounds": {}}

    jst = datetime.timezone(datetime.timedelta(hours=9))
    data["last_updated"] = datetime.datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")

    live_stats = fetch_dynamic_club_stats()
    if live_stats:
        data["club_stats"] = live_stats

    round_id, toto_date_label = fetch_latest_round_info()
    res = fetch_jleague_upcoming_matches(data.get("club_stats", {}), round_id, toto_date_label)
    if res:
        r_key, round_obj = res
        # 古い日付なしキーがあれば整理して最新キーをセット
        old_plain_key = f"第{round_id}回"
        if old_plain_key in data["rounds"] and old_plain_key != r_key:
            del data["rounds"][old_plain_key]
        data["rounds"][r_key] = round_obj
        data["current_round"] = r_key
        print(f"[SUCCESS] Saved {len(round_obj['matches'])} matches for {r_key} into {DATA_FILE}.")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
