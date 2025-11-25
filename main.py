import streamlit as st
import random
import pandas as pd
import io
import base64
from matplotlib import pyplot as plt
from matplotlib.table import Table

st.set_page_config(page_title="일본어 동사 퀴즈", layout="centered")

# ----- 스타일 (파스텔톤, 분홍) -----
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(180deg, #fff0f6, #ffeef8); }
    .quiz-card { border: 2px solid #ffb3d9; border-radius: 12px; padding: 16px; background: rgba(255,255,255,0.6); }
    .center { text-align: center; }
    .small-muted { color: #666; font-size:12px }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----- 동사 데이터 (원본 사용자 데이터 반영) -----
RAW_DATA = [
    {"japanese":"買う", "reading":"かう", "korean":"사다", "has_kanji":True},
    {"japanese":"行く", "reading":"いく", "korean":"가다", "has_kanji":True},
    {"japanese":"話す", "reading":"はなす", "korean":"이야기하다", "has_kanji":True},
    {"japanese":"あそぶ", "reading":"あそぶ", "korean":"놀다", "has_kanji":False},
    {"japanese":"飲む", "reading":"のむ", "korean":"마시다", "has_kanji":True},
    {"japanese":"すわる", "reading":"すわる", "korean":"앉다", "has_kanji":False},
    {"japanese":"つくる", "reading":"つくる", "korean":"만들다", "has_kanji":False},
    {"japanese":"のぼる", "reading":"のぼる", "korean":"오르다", "has_kanji":False},
    {"japanese":"見る", "reading":"みる", "korean":"보다", "has_kanji":True},
    {"japanese":"食べる", "reading":"たべる", "korean":"먹다", "has_kanji":True},
    {"japanese":"習う", "reading":"ならう", "korean":"배우다", "has_kanji":True},
    {"japanese":"する", "reading":"する", "korean":"하다", "has_kanji":False},
    {"japanese":"来る", "reading":"くる", "korean":"오다", "has_kanji":True},
    {"japanese":"会う", "reading":"あう", "korean":"만나다", "has_kanji":True},
    {"japanese":"聞く", "reading":"きく", "korean":"듣다", "has_kanji":True},
    {"japanese":"読む", "reading":"よむ", "korean":"읽다", "has_kanji":True},
    {"japanese":"ねる", "reading":"ねる", "korean":"자다", "has_kanji":False},
    {"japanese":"おきる", "reading":"おきる", "korean":"일어나다", "has_kanji":False},
    {"japanese":"帰る", "reading":"かえる", "korean":"돌아가(오)다", "has_kanji":True},
    {"japanese":"てつだう", "reading":"てつだう", "korean":"도와주다", "has_kanji":False},
]

# helpers
def sample_questions(data, difficulty, n):
    # difficulty affects ratio of reading vs meaning and inclusion of harder items
    kanji_items = [d for d in data if d['has_kanji']]
    all_items = data[:]
    questions = []

    for _ in range(n):
        qtype = random.choices(["meaning","reading"], weights=[0.6,0.4] if difficulty=="하" else ([0.5,0.5] if difficulty=="중" else [0.3,0.7]))[0]
        if qtype=="reading":
            # must pick from kanji items; if none left, fallback
            if not kanji_items:
                item = random.choice(all_items)
                qtype = "meaning"
            else:
                item = random.choice(kanji_items)
        else:
            item = random.choice(all_items)
        questions.append({"type":qtype, "item":item})
    return questions


def make_choices(question, data):
    correct = question['item']
    if question['type']=="meaning":
        correct_text = correct['korean']
        pool = list({d['korean'] for d in data if d['korean']!=correct_text})
    else:
        correct_text = correct['reading']
        pool = list({d['reading'] for d in data if d['reading']!=correct_text})
    distractors = random.sample(pool, k=min(3, len(pool)))
    choices = distractors + [correct_text]
    random.shuffle(choices)
    return choices, correct_text

# UI
st.title("🦊 일본어 동사 퀴즈")
st.write("귀여운 파스텔톤 디자인의 퀴즈로 동사를 연습해봐요!")

with st.container():
    with st.form(key='start_form'):
        name = st.text_input("이름을 입력하세요", value="학생")
        difficulty = st.radio("난이도 선택", ("하","중","상"), index=1, horizontal=True)
        submitted = st.form_submit_button("시작하기 🎯")

if not submitted:
    st.info("이름과 난이도를 선택한 뒤 '시작하기' 버튼을 눌러주세요.")
    st.stop()

# determine number of questions per difficulty
n_q = 10 if difficulty=="하" else (12 if difficulty=="중" else 15)
questions = sample_questions(RAW_DATA, difficulty, n_q)

# quiz state containers
if 'q_index' not in st.session_state:
    st.session_state.q_index = 0
    st.session_state.correct = 0
    st.session_state.results = []
    st.session_state.wrong_list = []

q_idx = st.session_state.q_index
if q_idx >= len(questions):
    # finished
    st.success("문제를 모두 풀었어요. よくできました！ 🎉")
    # show summary
    df = pd.DataFrame(st.session_state.results)
    accuracy = (st.session_state.correct / len(questions)) * 100
    st.markdown(f"### 학습 결과 및 피드백 - {name}  (단계: {difficulty})")
    st.markdown(f"**정답률:** {st.session_state.correct}/{len(questions)} ({accuracy:.1f}%)")
    st.dataframe(df[['index','type','prompt','your_answer','correct_answer','ok']])

    # generate motivational feedback
    # simple heuristic
    reading_correct = df.loc[df['type']=='reading','ok'].mean() if not df[df['type']=='reading'].empty else 1.0
    meaning_correct = df.loc[df['type']=='meaning','ok'].mean() if not df[df['type']=='meaning'].empty else 1.0
    feedback = ""
    if meaning_correct>0.8:
        feedback += "히라가나로 적힌 단어의 뜻 찾기는 아주 잘했어요! "
    elif meaning_correct>0.5:
        feedback += "뜻 찾기는 잘 하셨어요 — 조금 더 연습해요. "
    else:
        feedback += "뜻 찾기에서 더 연습하면 도움이 될 거예요. "
    if reading_correct>0.8:
        feedback += "한자 읽기도 잘하셨어요 — 계속 유지하세요!"
    elif reading_correct>0.5:
        feedback += "한자 읽기는 괜찮지만 더 연습하면 좋아요."
    else:
        feedback += "한자 읽기는 어려웠네요 — 한자 공부를 조금 병행해보면 실력이 빠르게 늘 거예요!"
    st.info(feedback)

    # create downloadable PNG of results
    def create_result_image(name, difficulty, df, accuracy):
        fig, ax = plt.subplots(figsize=(6,6))
        ax.axis('off')
        header = f"{name}_{difficulty}  학습결과"
        ax.text(0, 1.0, header, fontsize=16, fontweight='bold')
        ax.text(0, 0.94, f"정답률: {st.session_state.correct}/{len(questions)} ({accuracy:.1f}%)")

        # small table of top wrong items
        display_df = df[['index','prompt','your_answer','correct_answer','ok']].head(8)
        table = Table(ax, bbox=[0,0,1,0.8])
        ax.add_table(table)
        # fallback: just show text rows
        y = 0.8
        for _, row in display_df.iterrows():
            y -= 0.09
            ax.text(0, y, f"{int(row['index'])}. {row['prompt']} -> {row['your_answer']} ({'○' if row['ok'] else '✕'}), 정답: {row['correct_answer']}", fontsize=9)
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)
        return buf

    buf = create_result_image(name, difficulty, df, accuracy)
    st.download_button(label="학습 결과 이미지로 저장 (PNG)", data=buf, file_name=f"{name}_{difficulty}.png", mime="image/png")

    # if wrongs exist, offer re-quiz
    if st.session_state.wrong_list:
        st.markdown("---")
        st.write("오답 문제를 다시 확인해봅시다")
        if st.button("오답 재출제 시작"): 
            # prepare new questions from wrong_list
            questions = [ { 'type':w['type'], 'item':w['item'] } for w in st.session_state.wrong_list ]
            st.session_state.questions_override = questions
            st.session_state.q_index = 0
            st.session_state.correct = 0
            st.session_state.results = []
            st.session_state.wrong_list = []
            st.experimental_rerun()
    st.stop()

# present current question
question = questions[q_idx]
choices, correct_text = make_choices(question, RAW_DATA)

with st.container():
    st.markdown(f"<div class='quiz-card'>", unsafe_allow_html=True)
    if question['type']=='meaning':
        prompt = f"다음 일본어 동사의 한국어 뜻을 고르세요: **{question['item']['japanese']}**"
    else:
        # show kanji only for reading question
        prompt = f"다음 한자의 읽는 방법을 고르세요: **{question['item']['japanese']}**"
    st.markdown(f"### {prompt}")
    choice = st.radio("선택지", choices, key=f"choice_{q_idx}")
    submitted_answer = st.button("답안 제출")
    st.markdown("</div>", unsafe_allow_html=True)

if submitted_answer:
    is_ok = (choice == correct_text)
    st.session_state.results.append({
        'index': q_idx+1,
        'type': question['type'],
        'prompt': question['item']['japanese'],
        'your_answer': choice,
        'correct_answer': correct_text,
        'ok': is_ok,
        'item': question['item']
    })
    if is_ok:
        st.balloons()
        st.success("정답이에요! 잘했어요 🎉")
        st.session_state.correct += 1
    else:
        st.error("❌ 오답입니다.")
        st.info(f"정답: {correct_text} — {question['item']['korean']}")
        # add to wrong list for re-test
        st.session_state.wrong_list.append({'type':question['type'], 'item':question['item']})
    st.session_state.q_index += 1
    st.experimental_rerun()
else:
    st.write("선택지를 고르고 '답안 제출' 버튼을 눌러주세요.")

# EOF
