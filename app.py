import streamlit as st
import random
import pandas as pd
import time
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc

# --- 1. 페이지 설정 및 CSS 스타일링 ---
st.set_page_config(
    page_title="일본어 단어 복습 퀴즈 🌸",
    page_icon="🌸",
    layout="centered"
)

# 폰트 설정 (한글 깨짐 방지 - Streamlit Cloud 환경 고려)
# 로컬이나 특정 환경에서는 폰트 설치가 필요할 수 있습니다.
# 여기서는 기본적으로 제공되는 폰트를 사용하거나 시스템 폰트를 fallback으로 둡니다.
plt.rcParams['font.family'] = 'sans-serif' 
plt.rcParams['axes.unicode_minus'] = False

# 커스텀 CSS (귀여운 디자인 적용)
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #FFF9F9;
        font-family: 'Inter', sans-serif;
    }
    
    /* 제목 스타일 */
    h1 {
        color: #EC4899 !important; /* Pink-500 */
        font-weight: 800 !important;
        text-align: center;
    }
    h2, h3 {
        color: #DB2777 !important; /* Pink-600 */
        text-align: center;
    }
    
    /* 버튼 스타일 */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        border: 2px solid #FBCFE8;
        background-color: white;
        color: #374151;
        font-weight: 600;
        padding: 0.75rem 1rem;
        transition: all 0.2s;
    }
    .stButton > button:hover {
        background-color: #FDF2F8;
        border-color: #EC4899;
        transform: scale(1.02);
    }
    
    /* 정답/오답 메시지 박스 */
    .success-box {
        padding: 20px;
        background-color: #D1FAE5;
        border-radius: 10px;
        color: #065F46;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .error-box {
        padding: 20px;
        background-color: #FEE2E2;
        border-radius: 10px;
        color: #991B1B;
        text-align: center;
        font-weight: bold;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. 데이터 준비 ---
VOCABULARY = [
    { 'kanji': '買う', 'hiragana': 'かう', 'meaning': '사다' },
    { 'kanji': '行く', 'hiragana': 'いく', 'meaning': '가다' },
    { 'kanji': '話す', 'hiragana': 'はなす', 'meaning': '이야기하다' },
    { 'kanji': '遊ぶ', 'hiragana': 'あそぶ', 'meaning': '놀다' },
    { 'kanji': '飲む', 'hiragana': 'のむ', 'meaning': '마시다' },
    { 'kanji': '座る', 'hiragana': 'すわる', 'meaning': '앉다' },
    { 'kanji': '作る', 'hiragana': 'つくる', 'meaning': '만들다' },
    { 'kanji': '登る', 'hiragana': 'のぼる', 'meaning': '오르다' },
    { 'kanji': '見る', 'hiragana': 'みる', 'meaning': '보다' },
    { 'kanji': '食べる', 'hiragana': 'たべる', 'meaning': '먹다' },
    { 'kanji': '習う', 'hiragana': 'ならう', 'meaning': '배우다' },
    { 'kanji': '会う', 'hiragana': 'あう', 'meaning': '만나다' },
    { 'kanji': '聞く', 'hiragana': 'きく', 'meaning': '듣다' },
    { 'kanji': '読む', 'hiragana': 'よむ', 'meaning': '읽다' },
    { 'kanji': '寝る', 'hiragana': 'ねる', 'meaning': '자다' },
    { 'kanji': '起きる', 'hiragana': 'おきる', 'meaning': '일어나다' },
    { 'kanji': '帰る', 'hiragana': 'かえる', 'meaning': '돌아가(오)다' }
]

# --- 3. 상태(Session State) 초기화 ---
if 'page' not in st.session_state:
    st.session_state.page = 'start'
if 'user_name' not in st.session_state:
    st.session_state.user_name = ''
if 'current_level' not in st.session_state:
    st.session_state.current_level = None
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = []
if 'current_q_index' not in st.session_state:
    st.session_state.current_q_index = 0
if 'mistakes' not in st.session_state:
    st.session_state.mistakes = []
if 'all_results' not in st.session_state:
    st.session_state.all_results = []
if 'is_requiz' not in st.session_state:
    st.session_state.is_requiz = False
if 'completed_levels' not in st.session_state:
    st.session_state.completed_levels = {'easy': False, 'medium': False, 'hard': False}
if 'feedback_msg' not in st.session_state:
    st.session_state.feedback_msg = None # 정답/오답 피드백 저장

# --- 4. 헬퍼 함수들 ---

def generate_questions(level):
    questions = []
    shuffled_vocab = random.sample(VOCABULARY, len(VOCABULARY))
    
    for word in shuffled_vocab:
        q_type = ''
        if level == 'easy':
            q_type = random.choice(['hiragana-to-meaning', 'meaning-to-hiragana'])
        elif level == 'medium':
            q_type = random.choice(['kanji-to-hiragana', 'hiragana-to-kanji'])
        else: # hard
            q_type = random.choice(['kanji-to-meaning', 'meaning-to-kanji'])
            
        question, answer, opt_prop = '', '', ''
        
        if q_type == 'hiragana-to-meaning':
            question, answer, opt_prop = word['hiragana'], word['meaning'], 'meaning'
        elif q_type == 'meaning-to-hiragana':
            question, answer, opt_prop = word['meaning'], word['hiragana'], 'hiragana'
        elif q_type == 'kanji-to-hiragana':
            question, answer, opt_prop = word['kanji'], word['hiragana'], 'hiragana'
        elif q_type == 'hiragana-to-kanji':
            question, answer, opt_prop = word['hiragana'], word['kanji'], 'kanji'
        elif q_type == 'kanji-to-meaning':
            question, answer, opt_prop = word['kanji'], word['meaning'], 'meaning'
        elif q_type == 'meaning-to-kanji':
            question, answer, opt_prop = word['meaning'], word['kanji'], 'kanji'
            
        # 오답 선지 생성
        wrong_options = [w[opt_prop] for w in VOCABULARY if w[opt_prop] != answer]
        options = random.sample(wrong_options, 3)
        options.append(answer)
        random.shuffle(options)
        
        questions.append({
            'original_word': word,
            'type': q_type,
            'question': question,
            'answer': answer,
            'options': options
        })
    return questions

def check_answer(selected_option):
    current_q = st.session_state.quiz_data[st.session_state.current_q_index]
    is_correct = (selected_option == current_q['answer'])
    
    # 결과 저장 (재시험 아닐 때만)
    if not st.session_state.is_requiz:
        st.session_state.all_results.append({
            'Level': st.session_state.current_level,
            '문제': current_q['question'],
            '정답': current_q['answer'],
            '제출': selected_option,
            '결과': 'O' if is_correct else 'X',
            'type': current_q['type']
        })
        if not is_correct:
            st.session_state.mistakes.append(current_q)

    # 피드백 설정
    if is_correct:
        st.session_state.feedback_msg = 'correct'
    else:
        st.session_state.feedback_msg = 'incorrect'
        
    # 다음 문제로 넘어가기 위한 인덱스 증가 (화면 갱신 후 처리됨)
    st.session_state.current_q_index += 1

def reset_game():
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()

# --- 5. 화면 렌더링 ---

# A. 시작 화면
if st.session_state.page == 'start':
    st.title("🌸 일본어 동사 퀴즈 🌸")
    st.write(" ")
    st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExajFqdnJ6YzZ6bm16bm16bm16bm16bm16bm16bm16biZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9cw/LpDmM2wStDUs0/giphy.gif", width=100)
    st.markdown("<h3 style='text-align: center;'>당신의 이름을 입력해주세요!</h3>", unsafe_allow_html=True)
    
    name = st.text_input("이름", placeholder="예) 김성보", label_visibility="collapsed")
    
    if st.button("퀴즈 시작하기 🍙"):
        if name.strip():
            st.session_state.user_name = name
            st.session_state.page = 'level_select'
            st.rerun()
        else:
            st.warning("이름을 입력해야 시작할 수 있어요!")

# B. 레벨 선택 화면
elif st.session_state.page == 'level_select':
    st.title(f"{st.session_state.user_name}님, 환영합니다! 🐱")
    st.markdown("### 도전할 레벨을 선택하세요!")
    st.info("모든 단계 문제를 풀고 최종 결과지를 리로스쿨에 업로드해주세요!")
    
    col1, col2, col3 = st.columns(3)
    
    levels = [
        ('easy', '하 (下)', '히라가나 ↔ 뜻', '🟢'),
        ('medium', '중 (中)', '한자 ↔ 히라가나', '🔵'),
        ('hard', '상 (上)', '한자 ↔ 뜻', '🔴')
    ]
    
    for lvl_code, lvl_name, lvl_desc, color in levels:
        is_done = st.session_state.completed_levels[lvl_code]
        btn_label = f"{lvl_name}\n{lvl_desc}"
        if is_done:
            btn_label += " (완료 ✅)"
            
        if st.button(btn_label, key=lvl_code, disabled=is_done):
            st.session_state.current_level = lvl_code
            st.session_state.quiz_data = generate_questions(lvl_code)
            st.session_state.current_q_index = 0
            st.session_state.mistakes = []
            st.session_state.is_requiz = False
            st.session_state.feedback_msg = None
            st.session_state.page = 'quiz'
            st.rerun()

    # 모든 레벨 완료 시 결과 버튼
    if all(st.session_state.completed_levels.values()):
        st.write("---")
        if st.button("최종 결과 보기 📜", type="primary"):
            st.session_state.page = 'final_result'
            st.rerun()

# C. 퀴즈 화면
elif st.session_state.page == 'quiz':
    
    # 퀴즈 종료 조건 확인
    if st.session_state.current_q_index >= len(st.session_state.quiz_data):
        # 1. 정규 퀴즈 끝났는데 틀린게 있는 경우 -> 다시 풀기 모드 진입
        if not st.session_state.is_requiz and len(st.session_state.mistakes) > 0:
            st.session_state.is_requiz = True
            st.session_state.quiz_data = st.session_state.mistakes # 오답만 다시
            
            # 오답 선지 섞기
            for q in st.session_state.quiz_data:
                random.shuffle(q['options'])
                
            st.session_state.mistakes = [] # 오답 초기화 (재시험에서 또 틀리면 그냥 넘어감)
            st.session_state.current_q_index = 0
            st.session_state.feedback_msg = None
            st.rerun()
            
        # 2. 진짜 끝난 경우 (재시험 완료 or 오답 없음)
        else:
            st.session_state.completed_levels[st.session_state.current_level] = True
            st.session_state.page = 'level_complete'
            st.rerun()
            
    # 피드백 표시 (토스트 메시지)
    if st.session_state.feedback_msg == 'correct':
        st.toast("정답입니다! 🎉", icon="⭕")
        time.sleep(0.5) # 잠시 대기
        st.session_state.feedback_msg = None
        st.rerun() # 다음 문제 로드를 위해 리런
    elif st.session_state.feedback_msg == 'incorrect':
        st.toast("오답입니다! 다시 외워봐요! ❌", icon="❌")
        # 오답일 때 X 표시를 크게 보여주기 위한 임시 컨테이너
        with st.container():
            st.markdown("<div style='position:fixed; top:40%; left:0; width:100%; text-align:center; z-index:9999; font-size:100px;'>❌</div>", unsafe_allow_html=True)
            time.sleep(1.0)
        st.session_state.feedback_msg = None
        st.rerun()

    # 현재 문제 로드
    q_data = st.session_state.quiz_data[st.session_state.current_q_index]
    
    # 상단 정보
    lvl_map = {'easy': '하', 'medium': '중', 'hard': '상'}
    lvl_text = lvl_map.get(st.session_state.current_level, '')
    if st.session_state.is_requiz:
        st.warning(f"🔄 오답 다시 풀기 모드! ({st.session_state.current_q_index + 1}/{len(st.session_state.quiz_data)})")
    else:
        st.info(f"레벨: {lvl_text} | 문제: {st.session_state.current_q_index + 1}/{len(st.session_state.quiz_data)}")

    # 문제 표시
    st.markdown(f"<div style='background-color:#F3F4F6; padding:40px; border-radius:15px; text-align:center; margin-bottom:20px;'><h1 style='color:#1F2937 !important; margin:0;'>{q_data['question']}</h1></div>", unsafe_allow_html=True)
    
    # 선지 표시 (2x2 그리드)
    col1, col2 = st.columns(2)
    options = q_data['options']
    
    for i, opt in enumerate(options):
        # 버튼 클릭 시 check_answer 콜백 호출
        if i % 2 == 0:
            with col1:
                if st.button(opt, key=f"opt_{i}_{st.session_state.current_q_index}"):
                    check_answer(opt)
        else:
            with col2:
                if st.button(opt, key=f"opt_{i}_{st.session_state.current_q_index}"):
                    check_answer(opt)

# D. 레벨 완료 화면
elif st.session_state.page == 'level_complete':
    st.balloons()
    st.markdown("<div style='text-align: center; padding: 50px;'>", unsafe_allow_html=True)
    st.markdown("## 문제를 모두 풀었어요!")
    st.markdown("# よくできました！ 🎉")
    st.markdown("</div>", unsafe_allow_html=True)
    
    if st.button("다른 레벨 도전하기 🏠"):
        st.session_state.page = 'level_select'
        st.rerun()

# E. 최종 결과 화면
elif st.session_state.page == 'final_result':
    st.title(f"{st.session_state.user_name}님의 최종 결과 📜")
    
    # 데이터프레임 생성
    df = pd.DataFrame(st.session_state.all_results)
    
    # 통계 계산
    if not df.empty:
        total = len(df)
        correct = len(df[df['결과'] == 'O'])
        accuracy = (correct / total * 100)
        
        # 피드백 생성
        feedback = f"{st.session_state.user_name}님, 총 {total}문제 중 {correct}문제를 맞혀 {accuracy:.1f}%의 정답률을 기록했어요! "
        if accuracy == 100:
            feedback += "완벽해요! 일본어 마스터시네요! 🐱👍"
        elif accuracy >= 80:
            feedback += "아주 잘했어요! 조금만 더 하면 완벽해질 거예요! 🌸"
        else:
            feedback += "수고했어요! 틀린 단어를 위주로 다시 복습해볼까요? 💪"
            
        st.success(feedback)
        
        # 유형별 분석 (간단히)
        st.markdown("### 📊 상세 결과표")
        
        # 보기 좋게 표시하기 위해 인덱스 숨김 처리 및 스타일링은 Streamlit에서 제한적이지만 dataframe으로 보여줌
        st.dataframe(df, use_container_width=True)
        
        # 결과 이미지(표) 생성 및 다운로드 버튼
        # Streamlit은 브라우저 캡처가 어려우므로 matplotlib으로 표를 그려서 이미지로 저장 제공
        
        def create_result_image(dataframe, name):
            fig, ax = plt.subplots(figsize=(10, len(dataframe) * 0.5 + 2))
            ax.axis('off')
            ax.axis('tight')
            
            # 테이블 데이터 준비
            table_data = [dataframe.columns.to_list()] + dataframe.values.tolist()
            
            # 테이블 그리기
            table = ax.table(cellText=table_data, loc='center', cellLoc='center', colWidths=[0.1, 0.3, 0.2, 0.2, 0.1, 0.1])
            table.auto_set_font_size(False)
            table.set_fontsize(12)
            table.scale(1.2, 1.5)
            
            # 헤더 색상
            for k, cell in table._cells.items():
                if k[0] == 0:
                    cell.set_text_props(weight='bold', color='white')
                    cell.set_facecolor('#EC4899')
            
            plt.title(f"{name}님의 퀴즈 결과", pad=20, fontsize=15, weight='bold', color='#DB2777')
            plt.tight_layout()
            
            # 이미지 파일로 변환
            from io import BytesIO
            buf = BytesIO()
            plt.savefig(buf, format='png', dpi=150, bbox_inches='tight')
            buf.seek(0)
            return buf

        img_buffer = create_result_image(df[['Level', '문제', '정답', '제출', '결과']], st.session_state.user_name)
        
        st.download_button(
            label="결과 이미지 다운로드 💾",
            data=img_buffer,
            file_name=f"{st.session_state.user_name}_일본어퀴즈결과.png",
            mime="image/png"
        )
        
    else:
        st.warning("아직 푼 문제가 없어요!")

    st.markdown("---")
    if st.button("처음으로 돌아가기 🏠"):
        reset_game()
