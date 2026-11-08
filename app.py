from __future__ import annotations
import streamlit as st
from dataclasses import dataclass

# --- 記事より引用した試算前提（表7） ---------------------------------------

EXCHANGE_RATE = 155
PRICE_KWH = 31
DEPRECIATE_MONTHS = 36
HEAVY_RUN_CAP_H = 720
RAM_128GB_NOW = 514_800
PC_BODY_PRICE = 240_000

# --- データ構造 -----------------------------------------------------------

@dataclass(frozen=True)
class Profile:
    category: str
    name: str
    usage_key: str
    sensitive_hint: str | None
    wants_always_on: bool

PROFILES: list[Profile] = [
    # 開発・プログラミング
    Profile("開発・プログラミング", "アプリ・スクリプトを作りたい（コーディングエージェント）", "standard", None, False),
    Profile("開発・プログラミング", "複数のエージェントを常時走らせて開発したい", "heavy", None, True),
    
    # 専門業務（医療・法務・研究・ビジネス）
    Profile("専門業務（医療・法務・研究・ビジネス）", "院内の診療情報・社内機密文書を整理したい", "standard", "患者情報・社内機密を外部APIに送るわけにはいかない", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "係争中の裁判資料や未公開の契約書の要約・論点整理", "standard", "依頼者の秘密情報や係争関係の資料をクラウドに渡すことはできない", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "未公開の財務データやM&A検討資料の分析・レポート作成", "standard", "インサイダー情報や経営機密を外部APIに送るわけにはいかない", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "他人の未発表論文の査読（ピアレビュー）支援", "standard", "査読中原稿のクラウド送信は、ジャーナルの機密保持規定に抵触する恐れがある", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "自前のナレッジベース（電子カルテ・社内Wiki・判例集）と完全ローカルRAGを組みたい", "standard", "外部サーバーに一切インデックスやテキストを預けられない", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "顧客情報を扱う業務自動化（名簿・履歴書など）", "light", "個人情報を外部APIに送るわけにはいかない", False),
    Profile("専門業務（医療・法務・研究・ビジネス）", "公開済みの学術論文・公開判例の収集や、自分のドラフト推敲", "standard", None, False),
    
    # 日常利用・アイデア出し
    Profile("日常利用・アイデア出し", "翻訳・要約・ brainstorming の相棒が欲しい", "light", None, False),
    Profile("日常利用・アイデア出し", "深夜に制限なくモデルと壁打ち・雑談・アイデア出しをしたい", "light", None, False),
    
    # 野望・ロマン
    Profile("野望・ロマン", "APIの従量課金メーターに怯えず、無限にトークンを消費したい", "heavy", None, True),
    Profile("野望・ロマン", "「320Bクラスの怪物を自宅で飼っている」という圧倒的ロマンを感じたい", "standard", None, False),
]

@dataclass(frozen=True)
class Usage:
    name: str
    input_tokens: str
    output_tokens: str
    run_hours_std: int
    hours_factor: float
    cloud: dict[str, int]

USAGE: dict[str, Usage] = {
    "light": Usage("ライト", "2,000万", "10万", 11, 0.2, {
        "glm": 190, "sonnet": 2_500, "pro": 3_100, "max5x": 15_500, "max20x": 31_000,
    }),
    "standard": Usage("標準", "1.5億", "400万", 22, 1.0, {
        "glm": 1_426, "sonnet": 18_250, "pro": 3_100, "max5x": 15_500, "max20x": 31_000,
    }),
    "heavy": Usage("ヘビー", "15億", "1,500万", 720, 10.0, {
        "glm": 14_300, "sonnet": 70_000, "pro": 0, "max5x": 0, "max20x": 31_000,
    }),
}
USAGE_ORDER = ["light", "standard", "heavy"]

CLOUD_LABELS = {
    "glm": "GLM-5.3-Flash API",
    "sonnet": "Sonnet API（従量）",
    "pro": "Claude Pro（$20定額）",
    "max5x": "Claude Max 5x（$100定額）",
    "max20x": "Claude Max 20x（$200定額）",
}

@dataclass(frozen=True)
class Model:
    key: str
    name: str
    license_note: str
    vals_index: str
    min_memory_gb: int
    note: str

MODELS: dict[str, Model] = {
    "glm": Model("glm", "GLM-5.3-Flash", "MIT", "50.9%", 100,
                 "320B/活性18B。量子化でも最小87GB。Terminal-Bench等に強い"),
    "qwen": Model("qwen", "Qwen3.8-Flash-Next", "オープン", "-", 48,
                  "小さくて速い。同じ機種でGLMの約2〜3倍速。Mac mini 64GBでも動く"),
    "deepseek": Model("deepseek", "DeepSeek V4.1 Flash-1017", "オープン", "61.3%", 240,
                      "総合評価は最高だが巨大。実質256GB級でないと動かない"),
}
MODEL_ORDER = ["glm", "qwen", "deepseek"]

@dataclass
class Machine:
    name: str
    base_price: int
    needs_ram_kit: bool
    capacity_gb: int
    speeds: dict[str, int | None]
    base_speed_key: str
    base_hours: int
    power_w: int
    note: str

def nvidia(gpu_price: int) -> int:
    return PC_BODY_PRICE + gpu_price

MACHINES: list[Machine] = [
    Machine("Mac mini M5 Pro 64GB", 480_000, False, 64,
            {"glm": None, "qwen": 38, "deepseek": None},
            "qwen", 87, 60, "統合メモリ64GB。GLMは脱落、Qwenなら動く"),
    Machine("Mac Studio M5 Max 128GB", 887_800, False, 128,
            {"glm": 45, "qwen": 97, "deepseek": None},
            "glm", 34, 180, "費用対効果が突出。GLM約45tok/s・月34h"),
    Machine("Mac Studio M5 Ultra 256GB", 1_669_800, False, 256,
            {"glm": 55, "qwen": 115, "deepseek": 33},
            "glm", 28, 220, "DeepSeek V4.1を動かせる実質唯一級"),
    Machine("RTX 3060 12GB + RAM128GB", nvidia(60_000), True, 140,
            {"glm": 3, "qwen": 8, "deepseek": None},
            "glm", 105, 300, "RAM所有済みなら最安クラス"),
    Machine("RTX 4080 SUPER 32GB + RAM128GB", nvidia(315_000), True, 160,
            {"glm": 6, "qwen": 15, "deepseek": None},
            "glm", 60, 400, "VRAM32GB。RAM代高騰の直撃を受ける"),
    Machine("RTX 5090 32GB + RAM128GB", nvidia(1_010_000), True, 160,
            {"glm": 12, "qwen": 30, "deepseek": None},
            "glm", 40, 500, "GPU単体で101万円。リファレンス環境"),
    Machine("RTX PRO 6000 96GB + RAM128GB", nvidia(3_000_000), True, 224,
            {"glm": 25, "qwen": 60, "deepseek": 28},
            "glm", 20, 550, "VRAM96GBで一気に速くなる構成"),
    Machine("DGX Spark 128GB", 620_000, False, 128,
            {"glm": 12, "qwen": 30, "deepseek": None},
            "glm", 90, 170, "メモリ帯域の壁で初期費用の割に速度が出ない"),
]

BUDGET_OPTIONS: list[tuple[str, int | None]] = [
    ("50万円前後まで（まずは手堅く）", 500_000),
    ("90万円前後まで（本命の武器を求めて）", 900_000),
    ("150万円前後まで（伝説の装備を）", 1_500_000),
    ("予算は気にしない（無制限）", None),
]

# --- 計算関数 ----------------------------------------------------------------

def machine_price(m: Machine, ram_owned: bool) -> tuple[int, str]:
    if not m.needs_ram_kit:
        return m.base_price, "本体込み（Unified Memory）"
    if ram_owned:
        return m.base_price, "RAM所有済みのためRAM代0円"
    return (m.base_price + RAM_128GB_NOW,
            f"GPU+本体 {m.base_price:,}円 + 128GB RAM {RAM_128GB_NOW:,}円")

def run_hours(m: Machine, model_key: str, usage: Usage) -> int:
    base_speed = m.speeds.get(m.base_speed_key) or 1
    speed = m.speeds.get(model_key) or 1
    hours = m.base_hours * (base_speed / speed) * usage.hours_factor
    return min(HEAVY_RUN_CAP_H, round(hours))

def monthly_cost(m: Machine, model_key: str, usage: Usage, ram_owned: bool) -> tuple[int, int, int]:
    price, _ = machine_price(m, ram_owned)
    depreciation = round(price / DEPRECIATE_MONTHS)
    hours = run_hours(m, model_key, usage)
    electricity = round(hours * m.power_w / 1000 * PRICE_KWH)
    return price, depreciation, electricity

def break_even_months(price: int, local_monthly: int, cloud_monthly: int) -> int | None:
    if cloud_monthly <= local_monthly:
        return None
    return -(-price // (cloud_monthly - local_monthly))

def viable_machines(model_key: str, budget: int | None, ram_owned: bool) -> list[Machine]:
    ok = []
    for m in MACHINES:
        if not m.speeds.get(model_key):
            continue
        price, _ = machine_price(m, ram_owned)
        if budget is not None and price > budget:
            continue
        ok.append(m)
    ok.sort(key=lambda m: -(m.speeds[model_key] or 0))
    return ok


# --- Streamlit アプリ本体 ----------------------------------------------------

st.set_page_config(page_title="ローカルAI導入診断", page_icon="🗡️", layout="centered")

# Wizardry-style Retro CSS + ヘッダー非表示
st.markdown("""
<style>

    /* ヘッダー完全非表示 */
    header {
        display: none !important;
    }
    .stAppHeader {
        display: none !important;
    }
    
    /* 余白調整 */
    .block-container {
        padding: 2rem !important;
        margin-top: 1rem !important;
        background-color: #050505 !important;
        max-width: 800px !important;
    }
    
    /* Streamlit Community Cloud 等で付与されるiframeやデコレーション枠の非表示化 */
    iframe {
        border: none !important;
    }
    .stApp {
        border: none !important;
    }

    
    /* セレクトボックスの文字切れ対策（内部要素の高さを確保） */
    div[data-baseweb="select"] > div {
        min-height: 48px !important;
        height: auto !important;
        padding-top: 5px !important;
        padding-bottom: 5px !important;
    }
    div[data-baseweb="select"] span {
        white-space: normal !important;
        line-height: 1.4 !important;
        display: block !important;
    }
    
    /* カスタムステータスウィンドウ（st.metricの代わり） */
    .status-card {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 15px;
        margin-bottom: 10px;
    }
    .status-label {
        color: #aaaaaa;
        font-size: 0.9rem;
        margin-bottom: 5px;
    }
    .status-value {
        color: #ffcc00;
        font-size: clamp(1.2rem, 3.5vw, 1.8rem);
        line-height: 1.3;
        word-break: break-word;
    }


    /* ボタンをレトロ風に */
    .stButton > button {
        background-color: #000000;
        color: #ffffff;
        border: 2px solid #ffffff;
        border-radius: 0;
        width: 100%;
        padding: 10px;
        font-size: 1.2rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #ffffff;
        color: #000000;
        border-color: #ffffff;
    }
    hr {
        border-top: 1px dashed #ffffff;
    }
    
    /* 画面切り替え時の暗転フェードイン */
    .retro-flash {
        position: fixed;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background-color: #000000;
        z-index: 9999999;
        pointer-events: none;
        animation: fade-in-black 0.6s ease-out forwards;
    }
    @keyframes fade-in-black {
        0% { opacity: 1; }
        40% { opacity: 1; }
        100% { opacity: 0; visibility: hidden; }
    }
    </style>
""", unsafe_allow_html=True)


# --- 状態管理 ----------------------------------------------------------------
if 'step' not in st.session_state:
    st.session_state.step = 0

# 各ステップのコールバック関数。ウィジェットの状態が消える前に保存する。
def to_step_1():
    st.session_state.step = 1

def to_step_2():
    st.session_state.saved_profile = st.session_state.q1_profile
    st.session_state.saved_data = st.session_state.q2_data
    st.session_state.step = 2

def to_step_3():
    st.session_state.saved_usage = st.session_state.q3_usage
    st.session_state.saved_model = st.session_state.q4_model
    st.session_state.step = 3

def to_step_4():
    st.session_state.saved_budget = st.session_state.q5_budget
    st.session_state.saved_ram = st.session_state.q6_ram
    st.session_state.step = 4

def to_step_5():
    st.session_state.step = 5

def reset_step():
    st.session_state.step = 0

# --- 場面切り替えアニメーション（Stepが変わるたびにIDが変わり再発火する） ---
st.markdown(f'<div class="retro-flash" id="flash_step_{st.session_state.step}"></div>', unsafe_allow_html=True)



# --- ステップ表示 ------------------------------------------------------------
if st.session_state.step == 0:
    
    st.markdown("<h1 style='text-align: center; color: #ffcc00 !important;'>地下迷宮と100万円の魔法陣</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>〜オープンモデルの時代・本当のコスト診断〜</p>", unsafe_allow_html=True)
    st.image('Gemini_Generated_Image_jpwpqwjpwpqwjpwp.jpg', use_container_width=True)
    st.markdown("---")
    st.markdown("""
    それは西暦2026年。  
    あなたは「320Bクラスの怪物が家庭用PCで動く」という噂を聞きつけ、薄暗いPCショップの地下迷宮に足を踏み入れた。
    
    しかし、遥か彼方の塔（クラウドAPI）は月額1,400円で魔法を貸してくれるという。  
    果たして、100万円の剣（Mac Studio）を自腹で買う価値はあるのだろうか？
    
    あなたの選択が、運命を決める……。
    """)
    st.button("＞ 迷宮へ足を踏み入れる", on_click=to_step_1)
    


elif st.session_state.step == 1:
    
    st.subheader("B1F：冒険者の魂")
    st.image('Gemini_Generated_Image_1fu7vu1fu7vu1fu7.jpg', use_container_width=True)
    
    categories = list(dict.fromkeys(p.category for p in PROFILES))
    chosen_cat = st.selectbox("問1-1. 汝が求める力の方向性（分野）はどれか？", categories, key="q1_cat")
    
    filtered_profiles = [p.name for p in PROFILES if p.category == chosen_cat]
    chosen_profile_name = st.selectbox("問1-2. 具体的な望みを選べ", filtered_profiles, key="q1_profile")
    profile = next(p for p in PROFILES if p.name == chosen_profile_name)

    st.markdown("---")
    data_choices = ["外に出せる（クラウドAPIへの送信を許可）", "外に出せない（完全ローカルに幽閉する）"]
    default_data_idx = 1 if profile.sensitive_hint else 0
    st.radio("問2. その任務のデータは、城の外へ持ち出せるか？", data_choices, index=default_data_idx, key="q2_data")
    
    if profile.sensitive_hint:
        st.warning(f"🛡️ 賢者の助言: {profile.sensitive_hint}。「外に出せない」を選ぶのが命のためだ。")

    # 機密データなのに外に出そうとした場合のブロック処理
    if profile.sensitive_hint and st.session_state.q2_data == data_choices[0]:
        st.error("💀 【呪い】機密データを外に持ち出そうとしたため、魔法陣の扉が封印された！「外に出せない」を選び直すのだ。")
        st.button("＞ 次の階層へ進む", disabled=True)
    else:
        st.button("＞ 次の階層へ進む", on_click=to_step_2)
    


elif st.session_state.step == 2:
    
    st.subheader("B2F：召喚の儀式")
    st.image('Gemini_Generated_Image_sw4d22sw4d22sw4d.jpg', use_container_width=True)
    
    # B1Fで保存した状態を使用
    profile = next(p for p in PROFILES if p.name == st.session_state.saved_profile)
    usage_default_idx = USAGE_ORDER.index(profile.usage_key)
    
    st.radio(
        "問3. 魔法陣はどれほど酷使するつもりか？",
        options=USAGE_ORDER,
        index=usage_default_idx,
        format_func=lambda k: f"{USAGE[k].name}（入力 {USAGE[k].input_tokens} tok ≒ 文庫本 {int(float(USAGE[k].input_tokens.replace(',', '').replace('万','e4').replace('億','e8'))/100000):,} 冊分/月）",
        key="q3_usage"
    )
    
    st.markdown("---")
    model_choices = [MODELS[k].name for k in MODEL_ORDER] + ["おまかせ（推奨：Qwen3.8-Flash-Next）"]
    st.selectbox(
        "問4. どの怪物を相棒に選ぶか？",
        model_choices,
        index=len(MODEL_ORDER),
        key="q4_model"
    )
    
    st.button("＞ さらに奥へ進む", on_click=to_step_3)
    


elif st.session_state.step == 3:
    
    st.subheader("B3F：財宝の間")
    st.image('Gemini_Generated_Image_h2z318h2z318h2z3.jpg', use_container_width=True)
    
    st.selectbox(
        "問5. 旅の資金（初期予算）はいかほどか？",
        range(len(BUDGET_OPTIONS)),
        format_func=lambda i: BUDGET_OPTIONS[i][0],
        index=1,
        key="q5_budget"
    )
    
    st.markdown("---")
    st.markdown("「NVIDIA構成は既に大容量RAMを持っている人向け」。所有済みならRAM代が浮く。")
    st.checkbox("DDR5 64GB以上のRAMを既に所持している", value=False, key="q6_ram")
    
    st.button("＞ 運命の扉を開く（診断する）", on_click=to_step_4)
    


elif st.session_state.step == 4:
    # --- 保存した状態を使ってロジック計算 ---
    profile_name = st.session_state.saved_profile
    profile = next(p for p in PROFILES if p.name == profile_name)
    cloud_ok = (st.session_state.saved_data == "外に出せる（クラウドAPIへの送信を許可）")
    usage = USAGE[st.session_state.saved_usage]
    
    model_str = st.session_state.saved_model
    model_choice_idx = [MODELS[k].name for k in MODEL_ORDER].index(model_str) if model_str != "おまかせ（推奨：Qwen3.8-Flash-Next）" else len(MODEL_ORDER)
    model_key = None if model_choice_idx == len(MODEL_ORDER) else MODEL_ORDER[model_choice_idx]
    
    budget = BUDGET_OPTIONS[st.session_state.saved_budget][1]
    ram_owned = st.session_state.saved_ram

    should_report_cloud = False
    is_hybrid_case = False

    chosen_model = model_key or "qwen"
    swap_note = "おまかせ選択により **Qwen3.8-Flash-Next** を召喚した（GLMの約2〜3倍速）" if model_key is None else ""

    candidates = viable_machines(chosen_model, budget, ram_owned)

    if not candidates:
        
        st.markdown("<h2 style='color: #ff4444 !important;'>💀 冒険失敗（Game Over）</h2>", unsafe_allow_html=True)
        st.markdown(f"所持金 {f'{budget:,}円' if budget else '無限'} / RAM {'あり' if ram_owned else 'なし'} では、"
                 f"**{MODELS[chosen_model].name}** を召喚できる魔法陣が存在しない！")
        st.markdown("> **【酒場の噂】** GLMは合計メモリ100GB以上、DeepSeekは256GB級が必須だ。資金を貯めるか、モデルをQwenに落として出直してきな。")
        st.button("＞ 最初からやり直す", on_click=reset_step)
        
        st.stop()

    machine = candidates[0]
    price, depreciation, electricity = monthly_cost(machine, chosen_model, usage, ram_owned)
    local_monthly = depreciation + electricity
    cheapest_cloud = min((v for v in usage.cloud.values() if v > 0), default=10**18)
    sonnet_heavy_zone = usage.cloud["sonnet"] >= 70_000

    if cloud_ok:
        if local_monthly >= cheapest_cloud and not sonnet_heavy_zone:
            should_report_cloud = True
        elif sonnet_heavy_zone and local_monthly >= cheapest_cloud:
            is_hybrid_case = True

    
    
    if should_report_cloud:
        st.markdown("<h2 style='color: #ff4444 !important;'>🏰 結末：遥か彼方の塔（クラウドAPI）</h2>", unsafe_allow_html=True)
        st.markdown("""
        主人公は剣を買わず、月々の宿代だけで旅を続けることを選んだ。  
        記事の検証では、**GLM-5.3-Flash API（標準利用で月約1,426円）より安いローカル構成は1つも存在しなかった**——賢明な判断だ。
        """)
        plan_key, plan_price = min(((k, v) for k, v in usage.cloud.items() if v > 0), key=lambda x: x[1])
        st.info(f"🏆 **賢者の助言:** {CLOUD_LABELS[plan_key]} （月額 約 {plan_price:,} 円）を契約せよ。")
        st.caption("※ データを外に出さずに済む方法ではない。機密性を求めるなら『外に出せない』を選んでやり直すのだ。")
    
    else:
        if is_hybrid_case:
            st.markdown("<h2 style='color: #aa88ff !important;'>⚖️ 結末：双剣使い（ハイブリッド領域）</h2>", unsafe_allow_html=True)
            st.markdown("""**【図7の予言】** Claude換算で月7万円以上を使う主人公へ:  
*「Max 20xかMac Studio M5 Maxか、3年でほぼ同額。どちらでも同じ」*""")
        else:
            st.markdown("<h2 style='color: #44ff44 !important;'>📜 結末：城に巨人を宿す（完全ローカル）</h2>", unsafe_allow_html=True)
        st.image('Gemini_Generated_Image_5uy0tb5uy0tb5uy0.jpg', use_container_width=True)

        st.markdown(f'''
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
            <div class="status-card" style="flex: 1 1 45%;">
                <div class="status-label">🛠️ 授けられし名刀</div>
                <div class="status-value">{machine.name}</div>
            </div>
            <div class="status-card" style="flex: 1 1 45%;">
                <div class="status-label">💰 初期投資額</div>
                <div class="status-value">{price:,} 円</div>
            </div>
            <div class="status-card" style="flex: 1 1 45%;">
                <div class="status-label">🕯️ 維持費 (償却+電気代)</div>
                <div class="status-value">{local_monthly:,} 円/月</div>
            </div>
            <div class="status-card" style="flex: 1 1 45%;">
                <div class="status-label">⚡ 詠唱速度</div>
                <div class="status-value">{machine.speeds[chosen_model]} tok/s</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)
        
        st.markdown(f"> *{machine.note}*")
        if swap_note:
            st.markdown(f"> *{swap_note}*")

        st.markdown("---")
        st.subheader("⚔️ クラウドとの決闘判定")
        glm_cloud = usage.cloud["glm"]
        if local_monthly < glm_cloud:
            st.markdown(f"<p style='color: #44ff44 !important;'>🎉 <b>完全勝利！</b> 維持費（{local_monthly:,}円）が GLM API（月{glm_cloud:,}円）を下回る稀有な構成を引き当てた！</p>", unsafe_allow_html=True)
        else:
            st.markdown(f"<p style='color: #ff4444 !important;'>💀 <b>敗北…</b> 維持費（{local_monthly:,}円）は GLM API（月{glm_cloud:,}円）に勝てない。</p>", unsafe_allow_html=True)
            st.caption("記事の結論: 『GLM-5.3-FlashをAPIで使うと月約1,400円。これより安くなるマシンは1台もなかった』")

        st.markdown("---")
        st.subheader("⏳ 3年間の総コストと損益分岐")
        
        # 3年間の総コスト計算（初期費用 ＋ 月額維持費×36ヶ月）
        sonnet = usage.cloud["sonnet"]
        total_3y_local = price + (electricity * DEPRECIATE_MONTHS)
        total_3y_cloud_sonnet = sonnet * DEPRECIATE_MONTHS
        total_3y_cloud_glm = glm_cloud * DEPRECIATE_MONTHS
        
        st.markdown(f'''
        <div style="display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 15px;">
            <div class="status-card" style="flex: 1 1 30%;">
                <div class="status-label">城に巨人を宿す（ローカル3年総額）</div>
                <div class="status-value">{total_3y_local:,} 円</div>
            </div>
            <div class="status-card" style="flex: 1 1 30%;">
                <div class="status-label">Sonnet API（クラウド3年総額）</div>
                <div class="status-value">{total_3y_cloud_sonnet:,} 円</div>
            </div>
            <div class="status-card" style="flex: 1 1 30%;">
                <div class="status-label">GLM API（クラウド3年総額）</div>
                <div class="status-value">{total_3y_cloud_glm:,} 円</div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

        be_sonnet = break_even_months(price, local_monthly, sonnet)
        be_max20x = break_even_months(price, local_monthly, 31_000)

        c_be1, c_be2 = st.columns(2)
        with c_be1:
            if be_sonnet:
                st.info(f"**vs Sonnet API（月{sonnet:,}円）**\n\n👉 **{be_sonnet} か月** で逆転！")
            else:
                st.warning(f"**vs Sonnet API（月{sonnet:,}円）**\n\n👉 維持費のほうが高いため、元は取れない。")
        with c_be2:
            if be_max20x:
                st.info(f"**vs Claude Max 20x（月31,000円）**\n\n👉 **{be_max20x} か月** で逆転！")
            else:
                st.warning(f"**vs Claude Max 20x（月31,000円）**\n\n👉 元は取れない。")

        if cloud_ok:
            hybrid_extra = 5_500
            st.markdown(f"""
            #### 🔀 裏ルート：ハイブリッド構成
            - **設計・最終レビュー:** 塔の賢者（Claude 3割: 月約{hybrid_extra:,}円）
            - **実装・テスト修正:** 城の巨人（ローカル 7割）
            - **合計月額:** **{local_monthly + hybrid_extra:,} 円**  
            *「回数を気にせずエージェントを回せる自由度」こそが本当の買い物である（記事談）。*
            """)

    st.markdown("---")
    st.subheader("📊 あなたの使い方におけるクラウド参考月額")
    cloud_data = []
    for k in ["glm", "sonnet", "pro", "max5x", "max20x"]:
        cost = usage.cloud[k]
        cloud_data.append({
            "プラン名": CLOUD_LABELS[k],
            "月額費用": f"{cost:,} 円" if cost > 0 else "利用上限オーバー（不可）"
        })
    st.dataframe(cloud_data, use_container_width=True)

    st.markdown("---")
    st.subheader("📜 エピローグ")
    if not cloud_ok:
        st.markdown("> *主人公はデータを外に出さぬ誓いとともに、自分の城でモデルを走らせた。*  \n> *ローカルを選ぶ本当の理由は「データを外に出さないこと」と「回数を気にしないこと」である。*")
    else:
        st.markdown("> *もし元を取れる気がしないなら、クラウドのままでも構わない。*  \n> *エピローグはあなたの使い方次第だ。*")


    st.button("＞ 冒険の記録（あとがき）を読む", on_click=to_step_5)
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == 5:
    st.markdown('<div class="retro-box">', unsafe_allow_html=True)
    st.markdown("<h2 style='color: #ffcc00 !important;'>📜 あとがき：現実世界への帰還</h2>", unsafe_allow_html=True)
    
    st.markdown('''
ここまで遊んでいただき、ありがとうございます！  
このアプリは、以下の検証記事のデータを元に、<b style='color:#ffcc00;'>「あなたにとって本当に必要なAI環境のコスト」</b>をシミュレーションするためのツールです。

> **【出典記事】**  
> **[月1,400円のAPIに、100万円のPCは勝てるか？ Sonnet級オープンモデルを自宅で動かす本当のコスト](https://x.com/poporacchi/article/2118836220403040753)**

### 📊 現状のローカルAI事情（2026年秋）
- <b style='color:#ffcc00;'>モデルの巨大化</b>: GLM-5.3-FlashやDeepSeek V4.1など、非常に優秀なオープンモデルが登場していますが、それに伴い必要なメモリ容量も100GB〜250GB級へと跳ね上がっています。
- <b style='color:#ffcc00;'>メモリ価格の高騰</b>: DDR5大容量キットの価格が1年で8倍以上に高騰したことで、NVIDIA GPUを用いた自作PCのコストパフォーマンスが大きく悪化しました。
- <b style='color:#ffcc00;'>Macの台頭</b>: メモリ帯域と大容量ユニファイドメモリを兼ね備えた **Mac Studio** が、巨大なモデルを動かす上での「コスパ最強マシン」として注目を集めています。

### ⚙️ 試算のカスタマイズについて
AIハードウェアの価格や為替は日々変動します。
もしご自身で最新の相場に合わせて計算し直したい場合は、プログラム（`app.py`）の冒頭にある以下の数値を書き換えるだけで、すべての計算が自動で更新されます。
- `EXCHANGE_RATE`（為替レート）
- `RAM_128GB_NOW`（DDR5メモリの価格）
- `MACHINES`（各PCの本体価格や生成速度）

それでは、良きAIライフ（冒険）を！
''', unsafe_allow_html=True)
    
    st.markdown("---")
    st.button("＞ もう一度冒険に出る", on_click=reset_step)
    
