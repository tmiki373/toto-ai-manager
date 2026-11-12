import json
import re
import datetime
import requests
from bs4 import BeautifulSoup

DATA_FILE = "data.json"

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ja,en-US;q=0.9,en;q=0.8"
})

def get_html(url):
    try:
        res = SESSION.get(url, timeout=15)
        res.raise_for_status()
        res.encoding = res.apparent_encoding
        return res.text
    except Exception as e:
        print(f"[GET Error] {url}: {e}")
        return ""

def normalize_team_name(raw_name):
    mapping = {
        "北海道コンサドーレ札幌": "札幌", "コンサドーレ札幌": "札幌", "ヴァンラーレ八戸": "八戸",
        "ベガルタ仙台": "仙台", "ブラウブリッツ秋田": "秋田", "モンテディオ山形": "山形",
        "いわきFC": "いわき", "鹿島アントラーズ": "鹿島", "水戸ホーリーホック": "水戸",
        "栃木シティ": "栃木C", "RB大宮アルディージャ": "大宮", "大宮アルディージャ": "大宮",
        "ジェフユナイテッド千葉": "千葉", "柏レイソル": "柏", "FC東京": "FC東京",
        "東京ヴェルディ": "東京V", "FC町田ゼルビア": "町田", "川崎フロンターレ": "川崎F",
        "横浜F・マリノス": "横浜FM", "横浜Ｆ・マリノス": "横浜FM", "横浜FC": "横浜FC",
        "湘南ベルマーレ": "湘南", "ヴァンフォーレ甲府": "甲府", "アルビレックス新潟": "新潟",
        "カターレ富山": "富山", "清水エスパルス": "清水", "ジュビロ磐田": "磐田",
        "藤枝MYFC": "藤枝", "名古屋グランパス": "名古屋", "京都サンガF.C.": "京都",
        "ガンバ大阪": "G大阪", "セレッソ大阪": "C大阪", "ヴィッセル神戸": "神戸",
        "ファジアーノ岡山": "岡山", "サンフレッチェ広島": "広島", "徳島ヴォルティス": "徳島",
        "FC今治": "今治", "アビスパ福岡": "福岡", "サガン鳥栖": "鳥栖",
        "V・ファーレン長崎": "長崎", "大分トリニータ": "大分", "テゲバジャーロ宮崎": "宮崎",
        "栃木SC": "栃木SC", "ザスパ群馬": "群馬", "松本山雅FC": "松本",
        "AC長野パルセイロ": "長野", "ツエーゲン金沢": "金沢", "アスルクラロ沼津": "沼津",
        "FC岐阜": "岐阜", "ガイナーレ鳥取": "鳥取", "レノファ山口FC": "山口",
        "カマタマーレ讃岐": "讃岐", "愛媛FC": "愛媛", "高知ユナイテッドSC": "高知",
        "ギラヴァンツ北九州": "北九州", "ロアッソ熊本": "熊本", "鹿児島ユナイテッドFC": "鹿児島",
        "FC琉球": "琉球"
    }
    clean = re.sub(r"\s+", "", raw_name)
    for full, short in mapping.items():
        if full in clean or short == clean:
            return short
    return clean

def fetch_club_stats():
    """Yahoo!スポーツナビ J1/J2/J3順位表から最新スタッツを動的取得"""
    stats = {}
    urls = [
        ("https://soccer.yahoo.co.jp/jleague/category/j1/standings", "J1"),
        ("https://soccer.yahoo.co.jp/jleague/category/j2/standings", "J2"),
        ("https://soccer.yahoo.co.jp/jleague/category/j3/standings", "J3")
    ]
    for url, div in urls:
        html = get_html(url)
        if not html:
            continue
        soup = BeautifulSoup(html, "html.parser")
        for tr in soup.find_all("tr"):
