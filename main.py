import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import time
from datetime import datetime

# -------------------------------------------------------------------------
# 🔐 [설정] 비밀번호 및 API 키
# -------------------------------------------------------------------------
ACCESS_PASSWORD = "1234" # 유료 회원용 비밀번호

# GitHub 배포 환경(Secrets)과 로컬 테스트 환경(직접 입력) 모두 호환되게 설정
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = "sk-proj-..." # Replit에서 테스트할 때는 여기에 본인 키를 잠시 넣으세요 (배포 전엔 지우기!)
    
client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 💾 [핵심] 데이터베이스(DB) 시스템 구축 (SQLite)
# -------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('startup_data.db')
    c = conn.cursor()
    # 테이블이 없으면 생성 (아이템, 타겟, 강점, 점수, 평가, 날짜)
    c.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT,
            target TEXT,
            strength TEXT,
            score INTEGER,
            review TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(item, target, strength, score, review):
    conn = sqlite3.connect('startup_data.db')
    c = conn.cursor()
    c.execute('INSERT INTO history (item, target, strength, score, review, created_at) VALUES (?, ?, ?, ?, ?, ?)',
              (item, target, strength, score, review, datetime.now()))
    conn.commit()
    conn.close()

def get_db_stats():
    conn = sqlite3.connect('startup_data.db')
    # 데이터프레임으로 읽어오기 (통계 내기 쉬움)
    try:
        df = pd.read_sql_query("SELECT * FROM history", conn)
        conn.close()
        if df.empty:
            return 0, 0
        return len(df), round(df['score'].mean(), 1)
    except:
        conn.close()
        return 0, 0

# 앱 시작할 때 DB 확인
init_db()

# -------------------------------------------------------------------------
# 🧠 [평가 엔진] 합격 확률 분석 프롬프트
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """
너는 대한민국 정부지원사업 심사위원장이야. 
사용자의 아이템을 냉정하게 평가해서 '합격 확률(점수)'과 '독한 피드백'을 줘.

[출력 형식]
반드시 아래 형식을 지켜서 답변해. 다른 말 하지 말고.

SCORE: [0~100 사이 숫자만]
REVIEW: [평가 내용]
1. 시장성 (점수/25): ...
2. 기술성 (점수/25): ...
3. 사업성 (점수/25): ...
4. 팀역량 (점수/25): ...

[총평]: 합격을 위해 보완해야 할 점 3가지 (개조식)
"""

# -------------------------------------------------------------------------
# 💻 UI 구성
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 합격 확률 예측기", page_icon="📊", layout="wide")

# [로그인 화면]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔒 데이터 기반 합격 예측 솔루션")
    st.info("월 1,000원 멤버십 회원 전용입니다.")
    pwd = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if pwd == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호 오류")
    st.stop()

# [메인 화면]
st.title("📊 정부지원사업 합격 확률 진단 AI")

# --- 데이터 과시 (친구 피드백 반영: DB가 있다는 걸 보여줌) ---
total_cnt, avg_score = get_db_stats()

st.metric(label="누적 분석 데이터", value=f"{total_cnt}건", delta="실시간 업데이트 중")
if total_cnt > 0:
    st.caption(f"현재 지원자들의 평균 점수는 **{avg_score}점**입니다.")
else:
    st.caption("아직 데이터가 없습니다. 첫 번째 분석가가 되어보세요!")

st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: AI 기반 폐플라스틱 처리기")
    target = st.text_input("🎯 타겟 고객", placeholder="예: ESG 경영 공공기관")
with col2:
    strength = st.text_area("💪 대표자/팀 강점", placeholder="예: 관련 특허 1건, 개발 경력 5년", height=105)

st.markdown("👇 **더 정교한 예측을 위한 추가 정보 (선택)**")
additional = st.text_area("➕ 현재 진행 상황 (매출, MOU, 시제품 유무 등)", height=80)

if st.button("🚀 내 합격 확률 무료 진단하기"):
    if not item or not target:
        st.warning("아이템과 타겟은 필수입니다.")
    else:
        user_input = f"아이템:{item}, 타겟:{target}, 강점:{strength}, 추가정보:{additional}"
        
        with st.spinner("빅데이터 기준으로 냉철하게 분석 중입니다..."):
            try:
                # 1. AI 평가 요청
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_input}
                    ]
                )
                full_text = response.choices[0].message.content
                
                # 2. 결과 파싱 (점수와 내용 분리)
                score = 0
                review_content = full_text
                
                if "SCORE:" in full_text:
                    parts = full_text.split("REVIEW:")
                    score_part = parts[0].replace("SCORE:", "").strip()
                    # 숫자가 아닌 문자가 섞여있을 경우 대비
                    import re
                    numbers = re.findall(r'\d+', score_part)
                    if numbers:
                        score = int(numbers[0])
                    
                    review_content = parts[1].strip() if len(parts) > 1 else full_text
                
                # 3. DB에 저장 (이게 자산화!)
                save_to_db(item, target, strength, score, review_content)
                
                # 4. 결과 보여주기
                st.success("분석 완료! 데이터베이스에 저장되었습니다.")
                
                # 점수 시각화
                st.markdown(f"### 📈 당신의 합격 확률: **{score}%**")
                my_bar = st.progress(0)
                for percent_complete in range(score):
                    time.sleep(0.01)
                    my_bar.progress(percent_complete + 1)
                
                # 피드백 내용
                st.markdown("---")
                st.subheader("📝 심사위원 직설 피드백")
                st.markdown(review_content)
                
                # 비교 분석 (내 점수 vs 평균 점수)
                if total_cnt > 0:
                    if score > avg_score:
                        st.info(f"🎉 축하합니다! 평균({avg_score}점)보다 **{round(score - avg_score, 1)}점** 높습니다.")
                    else:
                        st.warning(f"⚠️ 평균({avg_score}점)보다 낮습니다. 위 피드백을 반영해 보완하세요.")

            except Exception as e:
                st.error(f"분석 중 오류 발생: {e}")
