import json
import re
import datetime
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

def fetch_url_smart(target_url, timeout=15):
    """直接アクセスを試み、失敗した場合はリレー経由で取得する"""
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
        print(f"[Direct fetch failed] {target_url} -> {e}")

    encoded = urllib.parse.quote(target_url, safe="")
    for p_url in [f"https://api.allorigins.win/raw?url={encoded}"]:
        try:
            req = urllib.request.Request(p_url, headers=headers)
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
            print(f"[Proxy fetch failed] {p_url} -> {e}")
    return ""

def normalize_team_name(raw_name):
    """クラブ名の表記ゆれを統一"""
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
    """Jリーグ公式順位表(J1/J2/J3)から全80クラブの最新成績を動的算出"""
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
                stats[team_short] = {"xg": dyn_xg, "xga": dyn_xga, "trend": trend}
    print(f"[Club Stats] Fetched {len(stats)} clubs dynamically.")
    return stats

def fetch_latest_toto_rounds(club_stats):
    """スポーツナビ(Yahoo! toto)およびtoto公式の現行URLから最新開催回・13枠・投票率・結果を動的取得"""
    rounds_found = {}

    # 1. スポーツナビ totoトップ＆投票状況ページから開催回リンクを探索
    base_urls = [
        "https://sports.yahoo.co.jp/toto/",
        "https://www.toto-dream.com/toto/index.html"
    ]
    round_links = {}
    for b_url in base_urls:
        html = fetch_url_smart(b_url)
        if not html:
            continue
        # スポーツナビ形式の開催回リンク (/toto/1672/ 等)
        for m in re.finditer(r'href=["\']([^"\']*/toto/(\d{4})/?[^"\']*)["\']', html):
            path, rid = m.group(1), m.group(2)
            full_u = urllib.parse.urljoin(b_url, path)
            round_links[rid] = full_u
        # テキストから最新回号も検出
        for rid in re.findall(r"第(\d{4})回", html):
            if rid not in round_links:
                round_links[rid] = f"https://sports.yahoo.co.jp/toto/{rid}/"

    target_ids = sorted(list(round_links.keys()))[-3:]
    print(f"[Target Round IDs] {target_ids}")

    for rid in target_ids:
        # 投票状況URLと結果URLの両方をチェック
        candidate_urls = [
            f"https://sports.yahoo.co.jp/toto/{rid}/vote",
            f"https://sports.yahoo.co.jp/toto/{rid}/",
            f"https://sports.yahoo.co.jp/toto/{rid}/result",
            round_links[rid]
        ]
        matches = []
        actual_results = {}
        title = f"第{rid}回"

        for u in candidate_urls:
            html = fetch_url_smart(u)
            if not html:
                continue
            soup = BeautifulSoup(html, "html.parser")
            page_text = soup.get_text(" ", strip=True)

            m_dead = re.search(r"(\d{1,2}月\d{1,2}日.*?\d{2}:\d{2})", page_text)
            if m_dead and "締切" not in title:
                title = f"第{rid}回（{m_dead.group(1)}締切）"

            # テーブル行から対戦カードと投票率(またはスコア)を抽出
            if len(matches) < 13:
                temp_matches = []
                for tr in soup.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                    row_str = " ".join(cells)
                    pcts = re.findall(r"(\d{1,2}(?:\.\d+)?)\s*%", row_str)
                    # クラブ名候補（club_statsに存在するチーム名を優先マッチング）
                    matched_teams = []
                    for c in cells:
                        norm_c = normalize_team_name(c)
                        if norm_c in club_stats and norm_c not in matched_teams:
                            matched_teams.append(norm_c)
                    if len(matched_teams) >= 2:
                        h_name, a_name = matched_teams[0], matched_teams[1]
                        v_rates = [float(pcts[0]), float(pcts[1]), float(pcts[2])] if len(pcts) >= 3 else [40.0, 30.0, 30.0]
                        hs = club_stats.get(h_name, {"xg": 1.30, "xga": 1.30, "trend": "最新スタッツ計算済"})
                        as_ = club_stats.get(a_name, {"xg": 1.30, "xga": 1.30, "trend": "最新スタッツ計算済"})
                        f_no = len(temp_matches) + 1
                        grp = "A" if f_no <= 5 else ("B" if f_no <= 10 else "C")
                        temp_matches.append({
                            "f": f_no, "grp": grp, "h": h_name, "a": a_name,
                            "v": v_rates,
                            "h_xg": hs["xg"], "h_xga": hs["xga"],
                            "a_xg": as_["xg"], "a_xga": as_["xga"],
                            "analysis": f"【H:{h_name}】{hs['trend']} ／ 【A:{a_name}】{as_['trend']}"
                        })
                    if len(temp_matches) == 13:
                        break
                if len(temp_matches) == 13:
                    matches = temp_matches

            # 確定スコア抽出
            if len(actual_results) < 13:
                f_idx = 1
                for tr in soup.find_all("tr"):
                    cells = [c.get_text(strip=True) for c in tr.find_all(["td", "th"])]
                    sc = re.search(r"(\d+)\s*[-－]\s*(\d+)", " ".join(cells))
                    if sc and f_idx <= 13:
                        hs_val, as_val = int(sc.group(1)), int(sc.group(2))
                        mark = "1" if hs_val > as_val else ("2" if as_val > hs_val else "0")
                        actual_results[str(f_idx)] = {"res": mark, "hs": hs_val, "as": as_val}
                        f_idx += 1

        print(f"[Round {rid}] Parsed matches: {len(matches)}/13, Results: {len(actual_results)}/13")
        if len(matches) == 13:
            r_key = f"第{rid}回"
            rounds_found[r_key] = {
                "title": title,
                "goal3_frames": [1, 2, 3],
                "matches": matches,
                "actual_results": actual_results
            }

    return rounds_found

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

    new_rounds = fetch_latest_toto_rounds(data.get("club_stats", {}))
    for rk, rv in new_rounds.items():
        data["rounds"][rk] = rv
        data["current_round"] = rk

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()
