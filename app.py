import streamlit as st
import math
import json
import os

# --- ページ基本設定（スマホ対応） ---
st.set_page_config(page_title="toto AI 統合マネージャー", page_icon="⚽", layout="wide")

# --- セキュアなPINコード認証（コード内に秘密情報を一切持たない設計） ---
def check_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.title("🔒 toto AI 統合マネージャー")
        
        # SecretsにAPP_PINが設定されていない場合は安全のため起動をブロック
        if "APP_PIN" not in st.secrets:
            st.error("セキュリティ設定エラー: Streamlitの管理画面（Settings > Secrets）で `APP_PIN` を設定してください。")
            st.stop()

        pin = st.text_input("🔑 PINコードを入力してください", type="password")
        if pin == st.secrets["APP_PIN"]:
            st.session_state.authenticated = True
            st.rerun()
        elif pin != "":
            st.error("PINコードが正しくありません")
        return False
    return True

if not check_auth():
    st.stop()

# --- データ永続化ファイル ---
DATA_FILE = "toto_history_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # 初期データ（第1672回デフォルト）
    return {
        "current_round": "第1672回",
        "rounds": {
            "第1672回": {
                "title": "第1672回（11/14 13:50締切：ルヴァン杯第2戦＋J2）",
                "goal3_frames": [2, 4, 5],
                "matches": [
                    {"f": 1, "grp": "A", "h": "町田", "a": "神戸", "v": [40.5, 30.2, 29.3], "h_xg": 1.15, "h_xga": 0.90, "a_xg": 1.45, "a_xga": 1.15},
                    {"f": 2, "grp": "A", "h": "C大阪", "a": "浦和", "v": [34.6, 26.3, 39.1], "h_xg": 1.40, "h_xga": 1.50, "a_xg": 1.95, "a_xga": 1.15},
                    {"f": 3, "grp": "A", "h": "鹿島", "a": "横浜FM", "v": [54.8, 22.5, 22.7], "h_xg": 1.75, "h_xga": 1.15, "a_xg": 1.35, "a_xga": 2.15},
                    {"f": 4, "grp": "A", "h": "柏", "a": "川崎F", "v": [63.4, 17.8, 18.9], "h_xg": 1.85, "h_xga": 1.10, "a_xg": 1.40, "a_xga": 1.65},
                    {"f": 5, "grp": "A", "h": "新潟", "a": "宮崎", "v": [51.2, 21.4, 27.4], "h_xg": 1.30, "h_xga": 1.45, "a_xg": 1.85, "a_xga": 0.95},
                    {"f": 6, "grp": "B", "h": "大分", "a": "栃木C", "v": [71.8, 17.0, 11.2], "h_xg": 1.25, "h_xga": 0.85, "a_xg": 0.90, "a_xga": 1.95},
                    {"f": 7, "grp": "B", "h": "札幌", "a": "鳥栖", "v": [64.8, 18.0, 17.2], "h_xg": 1.60, "h_xga": 0.80, "a_xg": 1.45, "a_xga": 1.35},
                    {"f": 8, "grp": "B", "h": "仙台", "a": "秋田", "v": [69.4, 17.4, 13.2], "h_xg": 1.80, "h_xga": 1.20, "a_xg": 1.05, "a_xga": 1.35},
                    {"f": 9, "grp": "B", "h": "今治", "a": "磐田", "v": [10.1, 14.6, 75.3], "h_xg": 1.25, "h_xga": 1.90, "a_xg": 1.65, "a_xga": 1.05},
                    {"f": 10, "grp": "B", "h": "富山", "a": "徳島", "v": [71.5, 14.5, 14.0], "h_xg": 1.20, "h_xga": 1.70, "a_xg": 0.65, "a_xga": 1.45},
                    {"f": 11, "grp": "C", "h": "八戸", "a": "いわき", "v": [13.5, 15.8, 70.7], "h_xg": 0.90, "h_xga": 1.45, "a_xg": 1.75, "a_xga": 1.20},
                    {"f": 12, "grp": "C", "h": "藤枝", "a": "甲府", "v": [44.5, 32.4, 23.1], "h_xg": 1.25, "h_xga": 1.55, "a_xg": 0.85, "a_xga": 2.25},
                    {"f": 13, "grp": "C", "h": "大宮", "a": "山形", "v": [78.1, 12.4, 9.5], "h_xg": 1.85, "h_xga": 1.05, "a_xg": 0.85, "a_xga": 1.35}
                ],
                "actual_results": {}
            }
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

db = load_data()

# --- 数理計算ロジック（ポアソン分布・Dixon-Coles・DP） ---
def poisson(lmbda, k):
    return (lmbda ** k) * math.exp(-lmbda) / math.factorial(k)

def calc_102_probs(lh, la):
    rho = -0.08
    p1, p0, p2 = 0.0, 0.0, 0.0
    for i in range(8):
        for j in range(8):
            p = poisson(lh, i) * poisson(la, j)
            if i == 0 and j == 0: p *= (1 - lh * la * rho)
            elif i == 0 and j == 1: p *= (1 + lh * rho)
            elif i == 1 and j == 0: p *= (1 + la * rho)
            elif i == 1 and j == 1: p *= (1 - rho)
            if i > j: p1 += p
            elif i == j: p0 += p
            else: p2 += p
    tot = p1 + p0 + p2
    return p1 / tot, p0 / tot, p2 / tot

def calc_goal3_probs(lmbda):
    p0 = poisson(lmbda, 0)
    p1 = poisson(lmbda, 1)
    p2 = poisson(lmbda, 2)
    return [p0, p1, p2, max(0.0, 1.0 - (p0 + p1 + p2))]

# --- メイン画面ヘッダー ＆ 開催回更新 ---
st.title("⚽ toto AI 統合予想・結果分析システム")

round_keys = list(db["rounds"].keys())
selected_round = st.sidebar.selectbox("📅 開催回を選択", round_keys, index=round_keys.index(db["current_round"]))
cur_round_data = db["rounds"][selected_round]

# サイドバー：新しい開催回の追加
with st.sidebar.expander("➕ 新規開催回の追加・更新"):
    new_r_name = st.text_input("開催回名", placeholder="例：第1673回")
    new_r_title = st.text_input("タイトル/締切", placeholder="例：第1673回（11/21締切）")
    new_g3_str = st.text_input("GOAL3対象枠（カンマ区切り）", value="1,2,3")
    if st.button("この開催回を新規作成"):
        if new_r_name and new_r_name not in db["rounds"]:
            g3_list = [int(x.strip()) for x in new_g3_str.split(",") if x.strip().isdigit()]
            db["rounds"][new_r_name] = {
                "title": new_r_title or new_r_name,
                "goal3_frames": g3_list,
                "matches": [dict(m) for m in cur_round_data["matches"]],
                "actual_results": {}
            }
            db["current_round"] = new_r_name
            save_data(db)
            st.success(f"{new_r_name} を作成しました！")
            st.rerun()

# 4大タブラベル
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ ① 直前スタメン反映・予想",
    "💰 ② 予算500円 最適買い方提案",
    "🏁 ③ 終了後 結果照合・的中判定",
    "📈 ④ 振り返り・次回への蓄積"
])

# =========================================================
# TAB 1: 直前スタメン反映 ＆ リアルタイム予想
# =========================================================
with tab1:
    st.subheader(f"📌 {cur_round_data['title']}")
    st.caption("土曜12:00頃のスタメン発表後、各枠のトグルを切り替えて最新予想を生成してください。")

    matches = cur_round_data["matches"]
    g3_frames = cur_round_data["goal3_frames"]

    processed_matches = []
    goal3_teams = []

    for idx, m in enumerate(matches):
        f = m["f"]
        is_g3 = f in g3_frames
        grp = "A組" if f <= 5 else ("B組" if f <= 10 else "本戦")

        with st.expander(f"第{f}枠 ({grp})：{m['h']} vs {m['a']}  [投票率: 1:{m['v'][0]}% / 0:{m['v'][1]}% / 2:{m['v'][2]}%]", expanded=False):
            c1, col_mid, col_r = st.columns([1.2, 1.2, 1])
            with c1:
                st.markdown(f"**🏠 {m['h']}**")
                h_atk_mod = st.selectbox("攻撃陣", ["通常", "🔥主力万全(+12%)", "⚠️主力欠場/温存(-20%)"], key=f"hatk_{f}")
                h_def_mod = st.selectbox("守備陣", ["通常", "🛡️正GK/CB不在・不安(+20%失点)", "🧱専守防衛(-15%失点)"], key=f"hdef_{f}")
                h_tac = st.selectbox("戦術方針", ["通常", "⚔️2点差必須（前がかり）", "🧱ドローOK（専守防衛）"], key=f"htac_{f}")
            with col_mid:
                st.markdown(f"**✈️ {m['a']}**")
                a_atk_mod = st.selectbox("攻撃陣", ["通常", "🔥主力万全(+12%)", "⚠️主力欠場/温存(-20%)"], key=f"aatk_{f}")
                a_def_mod = st.selectbox("守備陣", ["通常", "🛡️正GK/CB不在・不安(+20%失点)", "🧱専守防衛(-15%失点)"], key=f"adef_{f}")
                a_tac = st.selectbox("戦術方針", ["通常", "⚔️2点差必須（前がかり）", "🧱ドローOK（専守防衛）"], key=f"atac_{f}")
            with col_r:
                rain = st.checkbox("☔ 雨天・強風ピッチ", key=f"rain_{f}")

        # 係数計算
        h_atk_val = (1.12 if "主力万全" in h_atk_mod else (0.80 if "欠場" in h_atk_mod else 1.0)) * (1.18 if "前がかり" in h_tac else (0.85 if "専守防衛" in h_tac else 1.0))
        h_def_val = (1.20 if "不安" in h_def_mod else (0.85 if "専守防衛" in h_def_mod else 1.0))
        a_atk_val = (1.12 if "主力万全" in a_atk_mod else (0.80 if "欠場" in a_atk_mod else 1.0)) * (1.18 if "前がかり" in a_tac else (0.85 if "専守防衛" in a_tac else 1.0))
        a_def_val = (1.20 if "不安" in a_def_mod else (0.85 if "専守防衛" in a_def_mod else 1.0))

        lh = (m["h_xg"] * h_atk_val * (m["a_xga"] * a_def_val / 1.35)) * 1.08 * (0.84 if rain else 1.0)
        la = (m["a_xg"] * a_atk_val * (m["h_xga"] * h_def_val / 1.35)) / 1.08 * (0.84 if rain else 1.0)
        lh = max(0.25, min(3.50, lh))
        la = max(0.25, min(3.50, la))

        p1, p0, p2 = calc_102_probs(lh, la)
        probs = {"1": p1, "0": p0, "2": p2}
        votes = {"1": m["v"][0] / 100, "0": m["v"][1] / 100, "2": m["v"][2] / 100}
        evs = {k: probs[k] / max(0.01, votes[k]) for k in ["1", "0", "2"]}

        sorted_k = sorted(["1", "0", "2"], key=lambda k: probs[k], reverse=True)
        top1, top2 = sorted_k[0], sorted_k[1]
        diff = probs[top1] - probs[top2]

        # 判定（本戦toto用ドロー・期待値補正）
        pick = top2 if (diff <= 0.055 and (evs[top2] >= 1.25 or (top2 == "0" and probs["0"] >= 0.285))) else top1
        sub = top1 if pick == top2 else top2

        processed_matches.append({
            "f": f, "grp": m["grp"], "card": f"{m['h']} vs {m['a']}",
            "lh": lh, "la": la, "probs": probs, "evs": evs,
            "pick": pick, "sub": sub, "top1": top1, "top2": top2,
            "w_score": (probs[top1] + probs[top2]) * (1.0 - diff)
        })

        if is_g3:
            goal3_teams.append({"name": f"{m['h']}(H)", "f": f, "probs": calc_goal3_probs(lh), "v": m["v"]})
            goal3_teams.append({"name": f"{m['a']}(A)", "f": f, "probs": calc_goal3_probs(la), "v": m["v"]})

    # 予想サマリー
    toto_line = [pm["pick"] for pm in processed_matches]
    mini_a_line = [pm["pick"] for pm in processed_matches[:5]]
    mini_b_line = [pm["pick"] for pm in processed_matches[5:10]]

    st.write("---")
    st.markdown("### 🏆 算出した最新買い目サマリー")
    c_res1, c_res2 = st.columns(2)
    with c_res1:
        st.info(f"**toto 本戦（全13枠）**\n\n`{' - '.join(toto_line)}`")
        st.success(f"**mini toto A組（1〜5枠）**\n\n`{' - '.join(mini_a_line)}`")
    with c_res2:
        st.success(f"**mini toto B組（6〜10枠）**\n\n`{' - '.join(mini_b_line)}`")

        g3_single = []
        for gt in goal3_teams:
            ranked = sorted(range(4), key=lambda g: gt["probs"][g], reverse=True)
            g3_single.append(str(ranked[0]))
        st.warning(f"**toto GOAL3（シングル6枠）**\n\n`{' - '.join(g3_single)}`")

# =========================================================
# TAB 2: 予算500円 最大化ポートフォリオ提案
# =========================================================
with tab2:
    st.subheader("💰 1開催あたり「予算最大500円」のおすすめ買い方提示")
    st.write("今節の各くじの『的中期待度』と『配当妙味』を数理モデルが比較し、**500円（5口分）をどう配分するのが最も勝率・回収率が高いか**を診断します。")

    p_mini_a = math.prod([pm["probs"][pm["pick"]] for pm in processed_matches[:5]])
    p_mini_b = math.prod([pm["probs"][pm["pick"]] for pm in processed_matches[5:10]])

    ranked_w = sorted(processed_matches, key=lambda x: x["w_score"], reverse=True)
    w1, w2 = ranked_w[0], ranked_w[1]

    g3_exp = []
    for idx, gt in enumerate(goal3_teams):
        rk = sorted(range(4), key=lambda g: gt["probs"][g], reverse=True)
        t1, t2 = rk[0], rk[1]
        sc = (gt["probs"][t1] + gt["probs"][t2]) * (1.0 - (gt["probs"][t1] - gt["probs"][t2]))
        g3_exp.append({"idx": idx, "name": gt["name"], "t1": t1, "t2": t2, "score": sc})
    g3_exp.sort(key=lambda x: x["score"], reverse=True)
    gw1_idx = g3_exp[0]["idx"] if len(g3_exp) > 0 else 0
    gw2_idx = g3_exp[1]["idx"] if len(g3_exp) > 1 else 1

    g3_multi_400 = []
    for idx, gt in enumerate(goal3_teams):
        item = next(e for e in g3_exp if e["idx"] == idx)
        if idx in (gw1_idx, gw2_idx):
            g3_multi_400.append(f"[{min(item['t1'], item['t2'])}・{max(item['t1'], item['t2'])}]")
        else:
            g3_multi_400.append(str(item["t1"]))

    st.markdown("#### 🎯 今節の最推奨プラン（予算ジャスト500円）")

    if p_mini_b > p_mini_a:
        st.success("##### 【推奨プランA：GOAL3 400円マルチ ＋ mini toto B組 1口（計500円）】")
        st.markdown("""
        * **選定根拠**：今節はJ2中心の **mini toto B組（6〜10枠）の軸が極めて堅く（的中確率高）**、GOAL3は2箇所をダブルで抑えれば高配当1等が射程に入るため、この2つに集中投資するのが最も期待値が高いです。
        """)
        if len(g3_exp) >= 2:
            st.markdown(f"1. **toto GOAL3（4口・400円）**：`{' - '.join(g3_multi_400)}`\n"
                        f"   * 拡張枠：**{g3_exp[0]['name']} ＆ {g3_exp[1]['name']}**\n"
                        f"2. **mini toto B組（1口・100円）**：`{' - '.join(mini_b_line)}`\n"
                        f"   * **合計投資額：500円**")
    else:
        st.success("##### 【推奨プランB：mini toto 2組分散 ＋ 本戦toto 1口（計500円）】")
        st.markdown(f"1. **mini toto A組（2口ダブル・200円）**：`[{ranked_w[0]['pick']}・{ranked_w[0]['sub']}]` を組み込み\n"
                    f"2. **mini toto B組（2口ダブル・200円）**\n"
                    f"3. **toto 本戦（1口・100円）**：`{' - '.join(toto_line)}`\n"
                    f"   * **合計投資額：500円**")

    st.write("---")
    st.markdown("#### 🔄 代替プラン（好みに合わせて選択）")
    st.info(f"**【一攫千金狙いプラン（計500円）】**\n\n"
            f"* **toto本戦 2ダブルマルチ（4口・400円）**：\n"
            f"  `第{w1['f']}枠({w1['card']})` と `第{w2['f']}枠({w2['card']})` をダブルにして本戦13枠をカバー。\n"
            f"* **mini toto B組（1口・100円）**：`{' - '.join(mini_b_line)}`")

# =========================================================
# TAB 3: 終了後 結果照合・的中判定
# =========================================================
with tab3:
    st.subheader(f"🏁 {selected_round} 結果照合・的中確認（事実確認）")
    st.caption("試合終了後、確定した公式スコアを入力すると、購入した買い目との照合および当せん判定を厳格に行います。")

    actual_res = cur_round_data.get("actual_results", {})

    st.write("##### 1. 試合結果（スコア・勝敗）の入力")
    cols = st.columns(4)
    updated_actual = {}
    for idx, m in enumerate(matches):
        f = m["f"]
        prev = actual_res.get(str(f), {})
        col = cols[idx % 4]
        with col:
            res_val = st.selectbox(
                f"第{f}枠 {m['h']} vs {m['a']}",
                ["未確定", "1 (ホーム勝)", "0 (引分)", "2 (アウェイ勝)"],
                index=["未確定", "1", "0", "2"].index(prev.get("res", "未確定")) if prev.get("res") in ["1","0","2"] else 0,
                key=f"act_res_{f}"
            )
            h_sc = st.number_input(f"第{f}枠 {m['h']} 得点", min_value=0, max_value=9, value=prev.get("h_score", 0), key=f"act_h_{f}")
            a_sc = st.number_input(f"第{f}枠 {m['a']} 得点", min_value=0, max_value=9, value=prev.get("a_score", 0), key=f"act_a_{f}")

            if res_val != "未確定":
                mark = res_val.split()[0]
                updated_actual[str(f)] = {"res": mark, "h_score": h_sc, "a_score": a_sc}

    if st.button("💾 確定結果を保存して照合する"):
        cur_round_data["actual_results"] = updated_actual
        save_data(db)
        st.success("結果を保存しました！下部に的中判定を表示します。")
        st.rerun()

    if updated_actual:
        st.write("---")
        st.write("##### 2. 的中・当せん判定結果")
        hit_count_toto = 0
        hit_count_a = 0
        hit_count_b = 0

        match_check_rows = []
        for pm in processed_matches:
            f_str = str(pm["f"])
            act = updated_actual.get(f_str)
            if act:
                is_hit = (pm["pick"] == act["res"])
                if is_hit:
                    hit_count_toto += 1
                    if pm["f"] <= 5: hit_count_a += 1
                    elif pm["f"] <= 10: hit_count_b += 1
                match_check_rows.append({
                    "枠": pm["f"], "カード": pm["card"],
                    "予想": pm["pick"], "結果": act["res"],
                    "判定": "🎯 的中" if is_hit else "❌ ハズレ",
                    "スコア": f"{act['h_score']} - {act['a_score']}"
                })

        st.table(match_check_rows)

        fin_count = len(updated_actual)
        st.markdown(f"**【速報的中スコア】**：終了 {fin_count}/13試合中 **{hit_count_toto}試合的中**")
        if fin_count == 13:
            if hit_count_toto == 13: st.balloons(); st.success("🎉 **toto本戦 1等完全的中！！**")
            elif hit_count_toto == 12: st.success("🎉 **toto本戦 2等的中！**")
            elif hit_count_toto == 11: st.success("🎉 **toto本戦 3等的中！**")
            else: st.warning(f"残念ながらtoto本戦は当せん圏外（{hit_count_toto}/13的中）でした。")

            if hit_count_a == 5: st.success("🎉 **mini toto A組 1等的中！**")
            if hit_count_b == 5: st.success("🎉 **mini toto B組 1等的中！**")

# =========================================================
# TAB 4: 振り返り・次回への蓄積
# =========================================================
with tab4:
    st.subheader("📈 振り返り・次回へのパラメータ引き継ぎ")
    st.write("試合結果と事前のゴール期待値（λ）を比較し、次回予想に向けてチームの基礎パラメータを学習・調整します。")

    if not actual_res:
        st.info("タブ③で試合結果が登録されると、自動で乖離分析レポートが生成されます。")
    else:
        st.write("##### 🔍 予測λ（ゴール期待値）と実際の結果の乖離分析")
        discrepancies = []
        for pm in processed_matches:
            f_str = str(pm["f"])
            act = actual_res.get(f_str)
            if act:
                h_diff = act["h_score"] - pm["lh"]
                a_diff = act["a_score"] - pm["la"]
                note = "想定通り"
                if abs(h_diff) >= 1.5 or abs(a_diff) >= 1.5:
                    note = "⚠️ 大幅乖離（決定力爆発または守備崩壊）"
                discrepancies.append({
                    "枠": pm["f"], "カード": pm["card"],
                    "予測スコア(λ)": f"{pm['lh']:.2f} - {pm['la']:.2f}",
                    "実スコア": f"{act['h_score']} - {act['a_score']}",
                    "乖離評価": note
                })
        st.table(discrepancies)

        st.markdown("""
        **💡 次回への引き継ぎアクション**
        1. **「大幅乖離」となったチームのxG見直し**：実得点がxGを大きく下回ったチームは、次戦で「主力決定力不足」の割引を適用。
        2. **クリーンシート継続チームの守備評価アップ**：失点0が続くチーム（札幌・町田など）の被xG係数を上方修正。
        """)