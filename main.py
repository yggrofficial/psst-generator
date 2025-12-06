import streamlit as st
from openai import OpenAI
import sqlite3
import pandas as pd
import time
from datetime import datetime
import re
import os

# -------------------------------------------------------------------------
# 🚨 [필수] 페이지 설정 (무조건 맨 위)
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 모의 심사위원", page_icon="⚖️", layout="wide")

# -------------------------------------------------------------------------
# 🔐 [설정] 비밀번호 및 API 키 관리
# -------------------------------------------------------------------------
ACCESS_PASSWORD = "1234"  # 유료 회원용 비밀번호

try:
    # 1. Streamlit Cloud 배포 환경 (Secrets)
    if "OPENAI_API_KEY" in st.secrets:
        api_key = st.secrets["OPENAI_API_KEY"]
    else:
        # secrets.toml 파일이 없으면 에러 발생 -> except로 이동
        raise ValueError("Secrets not found")
except:
    # 2. Replit 테스트 환경 (본인 키 입력 필요)
    # ⚠️ 테스트할 때만 본인 키를 넣고, GitHub 배포 전에는 지우는 게 안전함
    api_key = "비워둠" 

client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 💾 [핵심] 데이터베이스(DB) - 평가 이력 저장
# -------------------------------------------------------------------------
def init_db():
    conn = sqlite3.connect('startup_data.db')
    c = conn.cursor()
    # 테이블: 아이템명, 본문, 점수, 독창성점수, 리뷰, 날짜
    c.execute('''
        CREATE TABLE IF NOT EXISTS evaluation_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_name TEXT,
            full_text TEXT,
            score INTEGER,
            originality INTEGER,
            review TEXT,
            created_at TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_to_db(item_name, full_text, score, originality, review):
    conn = sqlite3.connect('startup_data.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO evaluation_history (item_name, full_text, score, originality, review, created_at) VALUES (?, ?, ?, ?, ?, ?)',
                  (item_name, full_text, score, originality, review, datetime.now()))
    except:
        pass
    conn.commit()
    conn.close()

def get_db_stats():
    conn = sqlite3.connect('startup_data.db')
    try:
        df = pd.read_sql_query("SELECT * FROM evaluation_history", conn)
        conn.close()
        if df.empty:
            return 0, 0
        return len(df), round(df['score'].mean(), 1)
    except:
        conn.close()
        return 0, 0

init_db()

# -------------------------------------------------------------------------
# 🧠 [심사 엔진] PSST + 독창성(표절) 검사 프롬프트
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """
너는 대한민국 정부지원사업(예비창업패키지)의 최종 심사위원장이야.
사용자가 제출한 사업계획서를 읽고 [합격 점수]와 [독창성(표절 위험도)]를 냉정하게 평가해.

[평가 기준 1: PSST (합격 점수)]
1. Problem (문제인식)
2. Solution (해결방안)
3. Scale-up (성장전략)
4. Team (팀 구성)

[평가 기준 2: 독창성 (Originality)]
- 문장이 너무 일반적이거나(Cliché), 챗GPT가 쓴 티가 많이 나면 독창성 점수를 낮게 줄 것 (50점 미만).
- 구체적인 수치, 고유 명사, 경험담이 있으면 독창성 점수를 높게 줄 것.

[출력 형식]
반드시 아래 형식을 지켜라. 다른 사족 달지 마라.
SCORE: [0~100 숫자]
ORIGINALITY: [0~100 숫자]
REVIEW:
## 📊 심사 요약
- **종합 점수**: 00점
- **독창성 지수**: 00% (높을수록 좋음)

## 🛑 독창성/표절 유사도 검토
- [AI가 판단한 독창성 평가 멘트]

## 💡 항목별 상세 피드백
- **문제인식**: [평가]
- **해결방안**: [평가]
- **성장전략**: [평가]
- **팀 구 성**: [평가]

## 🎯 총평 및 보완점
- ...
"""

# -------------------------------------------------------------------------
# 💻 UI 구성
# -------------------------------------------------------------------------
# [로그인 화면]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## ⚖️ AI 모의 심사 & 표절 탐지기")
    st.info("작성하신 사업계획서의 합격 확률과 독창성을 진단해 드립니다. (유료 회원 전용)")
    pwd = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if pwd == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호 오류")
    st.stop()

# [메인 화면]
st.title("⚖️ 정부지원사업 AI 모의 심사장")
st.caption("ChatGPT로 쓴 사업계획서, 표절 의심 받을까? AI 심사위원이 미리 채점해 드립니다.")

# 통계 표시
total_cnt, avg_score = get_db_stats()
col_a, col_b = st.columns(2)
col_a.metric("누적 심사 건수", f"{total_cnt}건")
if total_cnt > 0:
    col_b.metric("평균 합격 점수", f"{avg_score}점")

st.markdown("---")

# 입력 폼
item_name = st.text_input("💡 창업 아이템명 (식별용)", placeholder="예: 시각장애인용 AI 안내견 앱")
st.markdown("👇 **작성하신 사업계획서 내용을 아래에 붙여넣어 주세요.** (HWP/PDF 내용 복사)")
full_plan = st.text_area("사업계획서 본문", height=300, placeholder="1. 문제 인식\n현재 시장은...\n\n2. 해결 방안\n우리는 이를 AI 기술로...\n(내용을 길게 넣을수록 정확한 심사가 가능합니다)")

# [실행 로직]
if st.button("🚀 모의 심사 및 표절 검사 시작"):
    if not item_name or len(full_plan) < 50:
        st.warning("아이템명과 사업계획서 내용을 충분히 입력해주세요 (최소 50자 이상).")
    else:
        with st.spinner("심사위원들이 귀하의 사업계획서를 검토 중입니다..."):
            try:
                # 1. AI 평가 요청
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"아이템명: {item_name}\n\n[사업계획서 내용]\n{full_plan}"}
                    ]
                )
                full_text = response.choices[0].message.content

                # 2. 결과 파싱 (점수와 독창성 분리)
                score = 0
                originality = 0
                review_content = full_text

                # SCORE 파싱
                if "SCORE:" in full_text:
                    parts = full_text.split("ORIGINALITY:")
                    score_part = parts[0].replace("SCORE:", "").strip()
                    numbers = re.findall(r'\d+', score_part)
                    if numbers:
                        score = int(numbers[0])

                    # ORIGINALITY 파싱
                    if len(parts) > 1:
                        orig_parts = parts[1].split("REVIEW:")
                        orig_num_part = orig_parts[0].strip()
                        orig_numbers = re.findall(r'\d+', orig_num_part)
                        if orig_numbers:
                            originality = int(orig_numbers[0])

                        review_content = orig_parts[1].strip() if len(orig_parts) > 1 else full_text

                # 3. DB 저장
                save_to_db(item_name, full_plan, score, originality, review_content)

                # 4. 결과 화면 출력
                st.success("심사가 완료되었습니다.")

                st.markdown("### 🏆 심사 결과 리포트")

                # 메트릭 시각화
                m_col1, m_col2 = st.columns(2)
                m_col1.metric("종합 합격 점수", f"{score}점")
                m_col2.metric("독창성(표절 안전도)", f"{originality}%", 
                              delta="안전" if originality >= 70 else "위험",
                              delta_color="normal" if originality >= 70 else "inverse")

                # 독창성 경고 메시지
                if originality < 50:
                    st.error("🚨 **[표절/양산형 경고]** 내용이 너무 일반적입니다. 구체적인 경험이나 데이터를 추가하여 보완하세요.")
                elif originality < 70:
                    st.warning("⚠️ **[주의]** 독창성이 다소 부족합니다. 차별점을 더 강조하세요.")
                else:
                    st.success("✅ **[독창성 통과]** 고유한 내용이 잘 포함되어 있습니다.")

                st.markdown("---")
                st.markdown(review_content)

            except Exception as e:
                st.error(f"심사 중 오류 발생: {e}")
