import json
import re
import datetime
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

def fetch_url_smart(target_url, timeout=15):
    """米国サーバーからでも通るJリーグ公式・公開ページを取得"""
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
    """Jリーグ公式順位表(J1/J2/J3)から全60クラブの最新成績を動的算出"""
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

def fetch_latest_round_id():
    """toto公式サイトトップから最新開催回号を取得"""
    html = fetch_url_smart("https://www.toto-dream.com/toto/index.html")
    ids = re.findall(r"第(\d{4})回", html) if html else []
    if ids:
        latest = sorted(list(set(ids)))[-1]
        print(f"[Latest toto ID] {latest}")
        return latest
    return "最新開催回"

def estimate_market_vote(h_xg, h_xga, a_xg, a_xga):
    """両クラブの実力値(xG/xGA)とホームアドバンテージから一般投票率(1/0/2)を自動推計"""
    h_pow = (h_xg / max(0.5, a_xga)) * 1.15
    a_pow = (a_xg / max(0.5, h_xga)) * 0.90
    d_pow = 0.75
    tot = h_pow + a_pow + d_pow
    p1 = round((h_pow / tot) * 100, 1)
    p2 = round((a_pow / tot) * 100, 1)
    p0 = round(max(15.0, 100.0 - p1 - p2), 1)
    return [p1, p0, p2]

def fetch_jleague_upcoming_matches(club_stats, round_id):
    """Jリーグ公式日程ページから取得できた試合をすべて保存（13試合未満でも保存する）"""
    match_urls = [
        "https://www.jleague.jp/match/",
        "https://www.jleague.jp/match/section/j1/latest/",
        "https://www.jleague.jp/match/section/j2/latest/",
        "https://www.jleague.jp/match/section/j3/latest/"
    ]

    raw_games = []
    seen_pairs = set()

    for m_url in match_urls:
        html = fetch_url_smart(m_url)
        if not html:
