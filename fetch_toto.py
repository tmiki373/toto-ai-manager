import json
import re
import datetime
import urllib.request
from bs4 import BeautifulSoup

DATA_FILE = "data.json"


def fetch_url(url, timeout=12):
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as res:
            raw = res.read()
            for enc in ["utf-8", "shift_jis", "cp932", "euc-jp"]:
                try:
                    txt = raw.decode(enc)
                    if len(txt) > 500:
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
                gf, ga = nums[6], nums[7]
                xg = round((gf / pl) * 0.75 + 0.325, 2)
                xga = round((ga / pl) * 0.75 + 0.325, 2)
                tr_str = "[{} {}位] 勝点{}/得失{:+d}".format(div, rk, pts, gf - ga)
                stats[t] = {"xg": xg, "xga": xga, "trend": tr_str}
    print("[Club Stats] Fetched:", len(stats))
    return stats


def calc_vote(h_xg, h_xga, a_xg, a_xga):
    hp = (h_xg / max(0.5, a_xga)) * 1.15
    ap = (a_xg / max(0.5, h_xga)) * 0.90
    tot = hp + ap + 0.75
    p1 = round((hp / tot) * 100, 1)
    p2 = round((ap / tot) * 100, 1)
    p0 = round(max(15.0, 100.0 - p1 - p2), 1)
    return [p1, p0, p2]


def get_future_matches(stats):
    jst = datetime.timezone(datetime.timedelta(hours=9))
    today = datetime.datetime.now(jst).date()
    wds = ["月", "火", "水", "木", "金", "土", "日"]
    games = []
    seen = set()

    for off in range(0, 15):
        td = today + datetime.timedelta(days=off)
        ymd = td.strftime("%Y%m%d")
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
                    games.append((td, d_str, teams[0], teams[1]))
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
        if g[1] not in udates:
            udates.append(g[1])
    d_label = "・".join(udates[:2])

    matches = []
    for i, (_, ds, hn, an) in enumerate(target, 1):
        hs = stats.get(hn, {"xg": 1.3, "xga": 1.3, "trend": ""})
        as_ = stats.get(an, {"xg": 1.3, "xga": 1.3, "trend": ""})
        grp = "A" if i <= 5 else ("B" if i <= 10 else "C")
        matches.append({
            "f": i, "grp": grp, "h": hn, "a": an,
            "v": calc_vote(hs["xg"], hs["xga"], as_["xg"], as_["xga"]),
            "h_xg": hs["xg"], "h_xga": hs["xga"],
            "a_xg": as_["xg"], "a_xga": as_["xga"],
            "analysis": "[{}] H:{} {} / A:{} {}".format(ds, hn, hs["trend"], an, as_["trend"])
        })

    rk = "次回toto対象節 ({})".format(d_label)
    return rk, {
        "title": "次回toto対象節 | 開催日: {} (全{}試合)".format(d_label, len(matches)),
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
    res = get_future_matches(data["club_stats"])
    if res:
        rk, obj = res
        data["rounds"][rk] = obj
        data["current_round"] = rk
        print("[SUCCESS]", rk, len(obj["matches"]))
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
