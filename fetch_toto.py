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


def estimate_market_vote(h_xg, h_xga, a_xg, a_xga):
    h_pow = (h_xg / max(0.5, a_xga)) * 1.15
    a_pow = (a_xg / max(0.5, h_xga)) * 0.90
    d_pow = 0.75
    tot = h_pow + a_pow + d_pow
    p1 = round((h_pow / tot) * 100, 1)
    p2 = round((a_pow / tot) * 100, 1)
    p0 = round(max(15.0, 100.0 - p1 - p2), 1)
    return [p1, p0, p2]


def fetch_future_jleague_matches(club_stats):
    """今日（JST現在日付）以降に開催される今月・来月のJ1/J2/J3公式日程のみを抽出"""
    jst = datetime.timezone(datetime.timedelta(hours=9))
    now_jst = datetime.datetime.now(jst)
    today_date = now_jst.date()

    # 今月と来月のYYYYMMを生成
    y1, m1 = now_jst.year, now_jst.month
    y2, m2 = (y1 + 1, 1) if m1 == 12 else (y1, m1 + 1)
    ym_list = [f"{y1}{m1:02d}", f"{y2}{m2:02d}"]

    match_urls = []
    for ym in ym_list:
        for div in ["j1", "j2", "j3"]:
            match_urls.append(f"https://www.jleague.jp/match/search/{div}/{ym}/")

    upcoming_games = []  # (date_obj, date_str, h_name, a_name, act)
    seen_pairs = set()

    for m_url in match_urls:
        html = fetch_url_smart(m_url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")

        # ページ内の日付見出しと試合要素を上から順に走査
        current_date_obj = None
        current_date_str = ""

        for elem in soup.find_all(["h2", "h3", "h4", "p", "div", "tr", "li"]):
            txt = elem.get_text(" ", strip=True)
            if len(txt) > 200 or len(txt) < 4:
                continue

            # 日付見出しの更新 (例: 2026年11月14日(土) や 11月14日(土))
            m_d = re.search(r"(?:(\d{4})年)?(\d{1,2})月(\d{1,2})日\s*[（(]([月火水木金土日])[）)]", txt)
            if m_d and len(txt) <= 35:
                yr = int(m_d.group(1)) if m_d.group(1) else y1
                mo, dy, wd = int(m_d.group(2)), int(m_d.group(3)), m_d.group(4)
                try:
                    current_date_obj = datetime.date(yr, mo, dy)
                    current_date_str = f"{mo}月{dy}日({wd})"
                except Exception:
                    pass
                continue

            # 今日より前の過去の試合は完全にスキップ
            if current_date_obj is None or current_date_obj < today_date:
                continue

            found_teams = []
            for sub in elem.find_all(["td", "span", "p", "a", "div"]):
                t_str = sub.get_text(strip=True)
                if 2 <= len(t_str) <= 16:
                    norm = normalize_team_name(t_str)
                    if norm in club_stats and norm not in found_teams:
                        found_teams.append(norm)

            if len(found_teams) == 2:
                pair_key = f"{current_date_str}:{found_teams[0]}-{found_teams[1]}"
                if pair_key not in seen_pairs:
                    seen_pairs.add(pair_key)
                    upcoming_games.append((current_date_obj, current_date_str, found_teams[0], found_teams[1], None))

    # 日付の早い順（直近の週末開催節）にソート
    upcoming_games.sort(key=lambda x: x[0])
    print(f"[Future Matches >= {today_date}] Found {len(upcoming_games)} upcoming games.")

    if not upcoming_games:
        return None

    # 直近開催日（または連続する2日間＝週末の1節分）の試合を最大13試合抽出
    first_date = upcoming_games[0][0]
    target_games = [g for g in upcoming_games if (g[0] - first_date).days <= 3][:13]
    if len(target_games) < 5:
        target_games = upcoming_games[:13]

    unique_dates = []
    for g in target_games:
        if g[1] not in unique_dates:
            unique_dates.append(g[1])
    date_label = "・".join(unique_dates[:2])

    matches = []
    for idx, (_, d_str, h_name, a_name, act) in enumerate(target_games, start=1):
        hs = club_stats.get(h_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ計算済"})
        as_ = club_stats.get(a_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ計算済"})
        grp = "A" if idx <= 5 else ("B" if idx <= 10 else "C")
        v_rates = estimate_market_vote(hs["xg"], hs["xga"], as_["xg"], as_["xga"])

        matches.append({
            "f": idx, "grp": grp, "h": h_name, "a": a_name,
            "v": v_rates,
            "h_xg": hs["xg"], "h_xga": hs["xga"],
            "a_xg": as_["xg"], "a_xga": as_["xga"],
            "analysis": f"[{d_str}] 【H:{h_name}】{hs['trend']} ／ 【A:{a_name}】{as_['trend']}"
        })

    r_key = f"次回開催節 ({date_label})"
    return r_key, {
        "title": f"次回toto対象節｜開催日: {date_label}（全{len(matches)}試合・今日以降の最新日程）",
        "goal3_frames": [i for i in [1, 2, 3] if i <= len(matches)],
        "matches": matches,
        "actual_results": {}
    }


def main():
    # 古い過去開催回キャッシュが残らないよう毎回クリーンに最新化
    data = {"current_round": "", "last_updated": "", "club_stats": {}, "rounds": {}}

    jst = datetime.timezone(datetime.timedelta(hours=9))
    data["last_updated"] = datetime.datetime.now(jst).strftime("%Y-%m-%d %H:%M JST")

    live_stats = fetch_dynamic_club_stats()
    if live_stats:
        data["club_stats"] = live_stats

    res = fetch_future_jleague_matches(data.get("club_stats", {}))
    if res:
        r_key, round_obj = res
        data["rounds"][r_key] = round_obj
        data["current_round"] = r_key
        print(f"[SUCCESS] Saved {len(round_obj['matches'])} future matches for {r_key}.")

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
