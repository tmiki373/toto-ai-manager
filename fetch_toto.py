import json
import re
import datetime
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

def fetch_html(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=12) as res:
        return res.read().decode("utf-8", errors="ignore")

def normalize_team_name(raw_name):
    """クラブ名の表記ゆれ（正式名称と略称）を統一"""
    mapping = {
        "北海道コンサドーレ札幌": "札幌", "ヴァンラーレ八戸": "八戸", "ベガルタ仙台": "仙台",
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
        "テゲバジャーロ宮崎": "宮崎"
    }
    clean = raw_name.strip()
    for full, short in mapping.items():
        if full in clean or short == clean:
            return short
    return clean

def fetch_dynamic_club_stats():
    """Jリーグ公式順位表(J1/J2/J3)から全クラブの最新得点力・守備力・トレンドを動的算出"""
    stats = {}
    urls = [
        "https://www.jleague.jp/standings/j1/",
        "https://www.jleague.jp/standings/j2/",
        "https://www.jleague.jp/standings/j3/"
    ]
    for url in urls:
        try:
            soup = BeautifulSoup(fetch_html(url), "html.parser")
            for tr in soup.find_all("tr"):
                tds = [td.get_text(strip=True) for td in tr.find_all("td")]
                # 順位表行（順位, チーム名, 勝点, 試合, 勝, 分, 敗, 得点, 失点, 得失点差）の解析
                nums = [int(x) for x in tds if re.fullmatch(r"-?\d+", x)]
                texts = [x for x in tds if len(x) >= 2 and not re.fullmatch(r"-?\d+", x)]
                if len(nums) >= 8 and len(texts) >= 1:
                    team_short = normalize_team_name(texts[0])
                    rank = nums[0]
                    pts = nums[1]
                    played = max(1, nums[2])
                    gf = nums[6]
                    ga = nums[7]
                    gd = gf - ga

                    avg_gf = round(gf / played, 2)
                    avg_ga = round(ga / played, 2)
                    # リーグ平均(1.30)との回帰ブレンドで基礎期待値(xg, xga)を動的算出
                    dyn_xg = round(avg_gf * 0.75 + 1.30 * 0.25, 2)
                    dyn_xga = round(avg_ga * 0.75 + 1.30 * 0.25, 2)

                    # トレンド文の動的生成
                    atk_eval = "得点力上位" if avg_gf >= 1.50 else ("得点力不足" if avg_gf <= 0.95 else "標準的攻撃力")
                    def_eval = "鉄壁守備" if avg_ga <= 0.95 else ("失点過多" if avg_ga >= 1.65 else "標準的守備")
                    trend = f"{rank}位(勝点{pts}/得失{gd:+d})・1試合平均{avg_gf:.2f}得点/{avg_ga:.2f}失点[{atk_eval}・{def_eval}]"

                    stats[team_short] = {
                        "xg": dyn_xg,
                        "xga": dyn_xga,
                        "trend": trend
                    }
        except Exception:
            continue
    return stats

def discover_active_hold_ids():
    """toto公式サイトから現在販売中・直近のholdCntIdを動的抽出"""
    ids = set()
    urls = [
        "https://store.toto-dream.com/dcs/subos/screen/si01/ssin020/LOTOPNoticeList01.form",
        "https://store.toto-dream.com/dcs/subos/screen/pi04/spin010/PGSPIN01001In.form"
    ]
    for u in urls:
        try:
            html = fetch_html(u)
            for m in re.findall(r"holdCntId=(\d{4})", html):
                ids.add(m)
        except Exception:
            continue
    return sorted(list(ids))

def scrape_round_detail(hold_id, club_stats):
    """指定holdCntIdの投票状況・GOAL3対象・確定結果を動的取得"""
    vote_url = f"https://store.toto-dream.com/dcs/subos/screen/si01/ssin026/PGSSIN02601In.form?holdCntId={hold_id}&commodityId=01"
    g3_url = f"https://store.toto-dream.com/dcs/subos/screen/si01/ssin026/PGSSIN02601In.form?holdCntId={hold_id}&commodityId=03"
    res_url = f"https://store.toto-dream.com/dcs/subos/screen/pi04/spin011/PGSPIN01101LnkHoldCntLotResultLst.form?holdCntId={hold_id}"

    g3_teams = set()
    try:
        g3_soup = BeautifulSoup(fetch_html(g3_url), "html.parser")
        for td in g3_soup.find_all("td"):
            txt = normalize_team_name(td.get_text(strip=True))
            if len(txt) >= 2:
                g3_teams.add(txt)
    except Exception:
        pass

    matches = []
    title = f"第{hold_id}回"
    try:
        soup = BeautifulSoup(fetch_html(vote_url), "html.parser")
        full_text = soup.get_text(" ", strip=True)
        m_dead = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日.*?\d{2}:\d{2})", full_text)
        if m_dead:
            title = f"第{hold_id}回（{m_dead.group(1)}締切）"

        for tr in soup.find_all("tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            row_str = " ".join(tds)
            pcts = re.findall(r"(\d{1,2}(?:\.\d+)?)\s*%", row_str)
            if len(pcts) >= 3:
                teams = [t for t in tds if len(t) >= 2 and not re.search(r"\d+%|\d{2}:\d{2}|^\d+$|vs|VS", t)]
                if len(teams) >= 2:
                    h_name = normalize_team_name(teams[0])
                    a_name = normalize_team_name(teams[1])
                    hs = club_stats.get(h_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ取得待ち"})
                    as_ = club_stats.get(a_name, {"xg": 1.30, "xga": 1.30, "trend": "最新データ取得待ち"})
                    f_no = len(matches) + 1
                    grp = "A" if f_no <= 5 else ("B" if f_no <= 10 else "C")
                    matches.append({
                        "f": f_no, "grp": grp, "h": h_name, "a": a_name,
                        "v": [float(pcts[0]), float(pcts[1]), float(pcts[2])],
                        "h_xg": hs["xg"], "h_xga": hs["xga"],
                        "a_xg": as_["xg"], "a_xga": as_["xga"],
                        "analysis": f"【H:{h_name}】{hs['trend']} ／ 【A:{a_name}】{as_['trend']}"
                    })
            if len(matches) == 13:
                break
    except Exception:
        pass

    actual_results = {}
    try:
        r_soup = BeautifulSoup(fetch_html(res_url), "html.parser")
        f_idx = 1
        for tr in r_soup.find_all("tr"):
            tds = [td.get_text(strip=True) for td in tr.find_all("td")]
            score_match = re.search(r"(\d+)\s*[-－]\s*(\d+)", " ".join(tds))
            if score_match and f_idx <= 13:
                hs, as_ = int(score_match.group(1)), int(score_match.group(2))
                res_mark = "1" if hs > as_ else ("2" if as_ > hs else "0")
                actual_results[str(f_idx)] = {"res": res_mark, "hs": hs, "as": as_}
                f_idx += 1
    except Exception:
        pass

    if len(matches) != 13:
        return None

    g3_frames = [m["f"] for m in matches if m["h"] in g3_teams or m["a"] in g3_teams][:3]
    if len(g3_frames) != 3:
        g3_frames = [1, 2, 3]

    return {
        "title": title,
        "goal3_frames": g3_frames,
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

    # 1. Jリーグ公式順位表から全クラブの最新スタッツを動的取得
    live_stats = fetch_dynamic_club_stats()
    if live_stats:
        data["club_stats"] = live_stats

    # 2. toto公式から現在有効な全開催回を動的取得
    hold_ids = discover_active_hold_ids()
    for hid in hold_ids:
        r_key = f"第{hid}回"
        scraped = scrape_round_detail(hid, data.get("club_stats", {}))
        if scraped:
            data["rounds"][r_key] = scraped
            data["current_round"] = r_key

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    main()