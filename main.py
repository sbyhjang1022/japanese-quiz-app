import streamlit as st
import random
import pandas as pd
from PIL import Image, ImageDraw, ImageFont
import io

st.set_page_config(page_title="일본어 동사 퀴즈", layout="centered")

# 단어 데이터 (일본어, 읽는 방법, 한국어 뜻)
WORDS = [
    ("買う", "かう", "사다"),
    ("行く", "いく", "가다"),
    ("話す", "はなす", "말하다"),
    ("あそぶ", "あそぶ", "놀다"),
    ("飲む", "のむ", "마시다"),
    ("すわる", "すわる", "앉다"),
    ("つくる", "つくる", "만들다"),
    ("のぼる", "のぼる", "오르다"),
    ("見る", "みる", "보다"),
    ("食べる", "たべる", "먹다"),
    ("習う", "ならう", "배우다"),
    ("する", "する", "하다"),
    ("来る", "くる", "오다"),
    ("会う", "あう", "만나다"),
    ("聞く", "きく", "듣다"),
    ("読む", "よむ", "읽다"),
    ("ねる", "ねる", "자다"),
    ("おきる", "おきる", "일어나다"),
    ("帰る", "かえる", "돌아가다"),
    ("てつだう", "てつだう", "도와주다"),
]

# 난이도별 단어 배치: 하(쉬움) 중(보통) 상(어려움)
random.seed(42)
shallow = [w for w in WORDS if w[0] in {"する","行く","見る","食べる","買う","読む","ねる","来る","帰る"}]
medium = [w for w in WORDS if w not in shallow][:7]
hard = [w for w in WORDS if w not in shallow and w not in medium]

# Ensure we have at least 15 questions per level by sampling with repetition but every word appears at least once across levels
# We'll create a generator that mixes words with different question types

def make_questions(word_list, n):
    questions = []
    base = word_list.copy()
    # if not enough unique words, allow sampling with replacement
    while len(questions) < n:
        w = random.choice(base)
        qtype = random.choice(["meaning", "reading"])  # 두 가지 유형: 뜻 맞추기, 읽기 맞추기
        # Build options
        if qtype == "meaning":
            prompt = "다음 단어의 한국어 뜻은?""
            correct = w[2]
            # choose 3 distractors
            distractors = [x[2] for x in WORDS if x[2] != correct]
            choices = random.sample(distractors, 3) + [correct]
            random.shuffle(choices)
            questions.append({"prompt": prompt, "correct": correct, "choices": choices, "type": qtype, "word": w})
        else:
            prompt = f"다음 단어의 읽는 방법(ひらがな)은?
{w[0]}"
            correct = w[1]
            distractors = [x[1] for x in WORDS if x[1] != correct]
            choices = random.sample(distractors, 3) + [correct]
            random.shuffle(choices)
            questions.append({"prompt": prompt, "correct": correct, "choices": choices, "type": qtype, "word": w})
    return questions

# Build level question sets (15 each)
LEVELS = {
    "하 (쉬움)": make_questions(shallow, 15),
    "중 (보통)": make_questions(medium if medium else WORDS, 15),
    "상 (어려움)": make_questions(hard if hard else WORDS, 15),
}

# Helper for session state
if "name" not in st.session_state:
    st.session_state["name"] = ""
if "level" not in st.session_state:
    st.session_state["level"] = None
if "q_index" not in st.session_state:
    st.session_state["q_index"] = 0
if "wrong" not in st.session_state:
    st.session_state["wrong"] = []
if "answers" not in st.session_state:
    st.session_state["answers"] = []

# UI
st.title("🍡 일본어 동사 퀴즈 - 복습하기")
st.markdown("귀여운 일러스트: 🌸🗻🍡 (일본과 관계에 민감한 이미지 제외)\n이모티콘으로 아기자기한 디자인을 사용합니다.")

if st.session_state["name"] == "":
    name = st.text_input("이름을 입력해 주세요:", max_chars=20)
    if st.button("시작하기") and name.strip():
        st.session_state["name"] = name.strip()
        st.experimental_rerun()
    st.stop()

st.sidebar.markdown(f"**학습자:** {st.session_state['name']}")
level = st.sidebar.selectbox("난이도를 선택하세요:", [None, "하 (쉬움)", "중 (보통)", "상 (어려움)"])

if level is not None and st.session_state["level"] != level:
    # reset progress when choosing level
    st.session_state["level"] = level
    st.session_state["q_index"] = 0
    st.session_state["wrong"] = []
    st.session_state["answers"] = []

if st.session_state["level"] is None:
    st.info("사이드바에서 난이도를 선택하고 시작하세요.")
    st.stop()

questions = LEVELS[st.session_state["level"]]
qidx = st.session_state["q_index"]

st.progress(min(1.0, (qidx) / len(questions)))
st.markdown(f"### 문제 {qidx+1} / {len(questions)}")
q = questions[qidx]
st.write(q["prompt"])

# Show options as buttons
cols = st.columns(2)
selected = None
for i, choice in enumerate(q["choices"]):
    if cols[i % 2].button(choice):
        selected = choice

if selected is not None:
    correct = q["correct"]
    if selected == correct:
        st.success("よくできました！ 🎉")
        try:
            st.balloons()
        except Exception:
            pass
        st.session_state["answers"].append((q, selected, True))
    else:
        st.error("❌ 아쉽네요. 정답을 확인해보세요")
        st.session_state["answers"].append((q, selected, False))
        st.session_state["wrong"].append((q, selected))
    st.session_state["q_index"] += 1
    st.experimental_rerun()

# When finished level
if qidx >= len(questions):
    st.markdown("---")
    st.header("문제를 모두 풀었어요. よくできました！")
    # Show summary table
    rows = []
    for i, (qitem, selected, correct_flag) in enumerate(st.session_state["answers"], start=1):
        jap = qitem["word"][0]
        reading = qitem["word"][1]
        meaning = qitem["word"][2]
        rows.append({"번호": i, "단어": jap, "읽기": reading, "뜻": meaning, "선택한 답": selected, "정답 여부": "정답" if correct_flag else "오답"})
    df = pd.DataFrame(rows)
    st.dataframe(df)

    # Simple positive feedback (1-2줄)
    correct_count = sum(1 for _,_,c in st.session_state["answers"] if c)
    total = len(st.session_state["answers"])
    accuracy = int(correct_count / total * 100)
    feedback = ""
    if accuracy >= 80:
        feedback = "히라가나로 적힌 단어를 보고 한국어 뜻을 찾는 문제는 아주 잘했어요! 계속 이렇게 연습해요."
    elif accuracy >= 50:
        feedback = "괜찮아요! 자주 틀리는 단어만 다시 복습하면 실력이 빠르게 올라갈 거예요."
    else:
        feedback = "초기 단계에서 자주 틀렸네요. 읽기와 뜻을 번갈아가며 천천히 복습해봐요."
    st.info(f"학습 요약 — 정답 {correct_count} / {total} ({accuracy}%)\n피드백: {feedback}")

    # Make an image of the result table for download
    def df_to_image(df):
        # render dataframe to an image using PIL
        padding = 10
        row_h = 30
        col_w = 140
        cols = list(df.columns)
        width = col_w * len(cols) + padding * 2
        height = row_h * (len(df) + 1) + padding * 2
        img = Image.new("RGB", (width, height), color=(255,255,255))
        draw = ImageDraw.Draw(img)
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        except:
            font = ImageFont.load_default()
        # header
        y = padding
        x = padding
        for j, c in enumerate(cols):
            draw.text((x + j*col_w, y), str(c), fill=(0,0,0), font=font)
        y += row_h
        for i, row in df.iterrows():
            for j, c in enumerate(cols):
                text = str(row[c])
                draw.text((x + j*col_w, y), text, fill=(0,0,0), font=font)
            y += row_h
        return img

    img = df_to_image(df)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    st.download_button("정오답표(이미지) 다운로드", data=buf, file_name=f"{st.session_state['name']}_result.png", mime="image/png")

    # If there were wrong answers, offer review
    if st.session_state["wrong"]:
        if st.button("오답 문제를 다시 풀어볼래요? (오답 문제를 다시 확인해봅시다)"):
            # build new quiz with only wrong questions, reshuffle choices
            wrong_qs = []
            for q, sel in st.session_state["wrong"]:
                # recreate choices shuffled
                choices = q["choices"].copy()
                random.shuffle(choices)
                wrong_qs.append({"prompt": q["prompt"], "correct": q["correct"], "choices": choices, "word": q["word"], "type": q["type"]})
            # temporarily overwrite questions and restart
            LEVELS["오답리뷰"] = wrong_qs
            st.session_state["level"] = "오답리뷰"
            st.session_state["q_index"] = 0
            st.session_state["answers"] = []
            st.session_state["wrong"] = []
            st.experimental_rerun()
    else:
        st.success("모든 문제를 맞추셨어요! 정말 훌륭합니다 🎉")

    # Reset / 다시하기
    if st.button("처음으로 돌아가기"):
        for k in ["name","level","q_index","wrong","answers"]:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()
    st.stop()

# show progress hint
st.caption("정답을 선택하면 다음 문제가 자동으로 나옵니다.")

# Footer cute reminder
st.markdown("---\n즐겁게 복습하세요! 🌸 学習がんばってね！")
