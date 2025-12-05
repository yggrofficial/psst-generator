import streamlit as st
from openai import OpenAI
import time

# -------------------------------------------------------------------------
# 🔐 [설정] 비밀번호 및 API 키
# -------------------------------------------------------------------------
ACCESS_PASSWORD = "1234"  # 유료 회원용 비밀번호

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = "sk-proj-..." # 로컬 테스트용
    
client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 🧠 프롬프트 (3개로 쪼개서 전문가 모드 발동)
# -------------------------------------------------------------------------
# 1. 사업계획서 전용 프롬프트
PROMPT_PSST = """
너는 정부지원사업 합격 전문 컨설턴트야. 
사용자의 정보를 바탕으로 [PSST 표준 사업계획서]를 '아주 상세하고 구체적으로' 작성해.
내용을 요약하지 말고, 각 항목별로 꽉 채워서 작성할 것.

[필수 구조]
1. 문제 인식 (Problem): 시장의 페인포인트, 기존 해결책의 한계 (상세 서술)
2. 해결 방안 (Solution): 서비스/제품의 구체적 기능, 기술적 차별성
3. 성장 전략 (Scale-up): 자금 확보, 마케팅, 시장 진입 단계별 전략 (구체적 수치 포함)
4. 팀 구성 (Team): 대표자 강점을 기반으로 한 역량 강조
5. 예산 계획: 5,000만 원~1억 원 기준 비목별 예산안 (마크다운 표 Table 필수)

[말투] '~함', '~임' 개조식 명사형 종결.
"""

# 2. SWOT 전용 프롬프트
PROMPT_SWOT = """
너는 전략 기획 전문가야. 위 아이템을 냉정하게 분석해서 [SWOT 분석]을 수행해.
1. 강점(S), 약점(W), 기회(O), 위협(T)을 마크다운 표(Table)로 그려줘.
2. [전략 도출]: 약점(W)을 기회(O)로 바꾸거나 강점(S)으로 덮을 수 있는 구체적인 전략 3가지를 제시해.
"""

# 3. 면접 전용 프롬프트
PROMPT_INTERVIEW = """
너는 까칠한 심사위원이야. 이 사업계획서를 보고 '공격적인 질문 5개'를 던져.
그리고 각 질문에 대해 지원자가 어떻게 답변해야 합격할 수 있는지 '모범 답변 가이드'를 제시해.
질문은 예산, 실현 가능성, 경쟁사 대비 우위 등을 집요하게 물어볼 것.
"""

# -------------------------------------------------------------------------
# 💻 UI 구성
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 프리패스 Pro", page_icon="💎", layout="wide")

# [로그인 화면]
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("## 🔒 VIP 프리미엄 서비스")
    st.info("월 1,000원 멤버십 회원만 접근 가능한 전략 컨설팅 도구입니다.")
    pwd = st.text_input("비밀번호를 입력하세요", type="password")
    if st.button("로그인"):
        if pwd == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("비밀번호가 올바르지 않습니다.")
    st.stop()

# [메인 화면]
st.title("💎 정부지원사업 합격 솔루션 (Premium)")
st.caption("AI가 3단계 심층 분석을 수행합니다. (약 1분 소요)")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: AI 기반 음식물 쓰레기 처리기")
    target = st.text_input("🎯 타겟 고객", placeholder="예: 3040 주부, 1인 가구")
with col2:
    strength = st.text_area("💪 대표자/팀 강점", placeholder="예: 관련 특허 보유, 개발 경력 5년", height=105)

# [실행 로직]
if st.button("🚀 프리미엄 컨설팅 시작 (클릭)"):
    if not item or not target:
        st.warning("정보를 모두 입력해주세요.")
    else:
        # 결과를 저장할 변수들
        psst_result = ""
        swot_result = ""
        interview_result = ""
        
        # 1단계: 사업계획서 생성
        with st.status("🤖 AI가 열심히 일하는 중입니다...", expanded=True) as status:
            
            st.write("1단계: 상세 사업계획서 작성 중... (내용이 길어요!)")
            try:
                response1 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_PSST},
                        {"role": "user", "content": f"아이템: {item}, 타겟: {target}, 강점: {strength}"}
                    ]
                )
                psst_result = response1.choices[0].message.content
                st.write("✅ 사업계획서 완료!")
                
                # 2단계: SWOT 분석
                st.write("2단계: SWOT 전략 분석 중...")
                response2 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_SWOT},
                        {"role": "user", "content": f"아이템: {item} 에 대한 SWOT 분석을 해줘."}
                    ]
                )
                swot_result = response2.choices[0].message.content
                st.write("✅ SWOT 분석 완료!")

                # 3단계: 면접 질문
                st.write("3단계: 독한 면접 질문 뽑는 중...")
                response3 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_INTERVIEW},
                        {"role": "user", "content": f"아이템: {item} 에 대한 면접 질문을 뽑아줘."}
                    ]
                )
                interview_result = response3.choices[0].message.content
                st.write("✅ 면접 대비 완료!")
                
                status.update(label="🎉 모든 분석이 끝났습니다!", state="complete", expanded=False)

            except Exception as e:
                st.error(f"에러 발생: {e}")
                st.stop()

        # [결과 출력 - 탭으로 구분]
        st.success("분석 완료! 아래 탭을 눌러 확인하세요.")
        
        tab1, tab2, tab3 = st.tabs(["📄 1. 상세 사업계획서", "📊 2. SWOT 전략", "🎤 3. 면접 예상질문"])
        
        with tab1:
            st.markdown(psst_result)
        
        with tab2:
            st.markdown(swot_result)
            
        with tab3:
            st.markdown(interview_result)
            
        # [통합 다운로드]
        full_report = f"""
[예창패 프리패스 AI 리포트]

--- 1. 상세 사업계획서 ---
{psst_result}

--- 2. SWOT 분석 및 전략 ---
{swot_result}

--- 3. 면접 예상 질문 및 답변 ---
{interview_result}
        """
        
        st.markdown("---")
        st.download_button(
            label="💾 전체 리포트 다운로드 (텍스트 파일)",
            data=full_report,
            file_name="Premium_사업계획서_Full.txt",
            mime="text/plain"
        )
