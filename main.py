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
# 🧠 프롬프트 (추가 정보를 반영하도록 업그레이드)
# -------------------------------------------------------------------------
# 1. 사업계획서 전용
PROMPT_PSST = """
너는 정부지원사업 합격 전문 컨설턴트야. 
사용자의 입력 정보를 바탕으로 [PSST 표준 사업계획서]를 '상세하고 구체적으로' 작성해.
사용자가 '추가 정보'를 제공했다면, 그 내용을 각 항목에 적절히 녹여내야 해.

[필수 구조]
1. 문제 인식 (Problem): 시장의 페인포인트, 기존 한계
2. 해결 방안 (Solution): 구체적 기능, 기술적 차별성
3. 성장 전략 (Scale-up): 자금 확보, 마케팅, 시장 진입 전략
4. 팀 구성 (Team): 대표자 강점 및 역량
5. 예산 계획: 5,000만 원~1억 원 기준 예산안 (Table 필수)

[말투] '~함', '~임' 개조식 명사형 종결.
"""

# 2. SWOT 전용
PROMPT_SWOT = """
너는 전략 기획 전문가야. 아이템과 추가 정보를 종합적으로 분석해서 [SWOT 분석]을 수행해.
1. 강점(S), 약점(W), 기회(O), 위협(T)을 마크다운 표(Table)로 작성.
2. [전략 도출]: 약점(W)을 기회(O)로 바꿀 구체적 전략 3가지 제시.
"""

# 3. 면접 전용
PROMPT_INTERVIEW = """
너는 까칠한 심사위원이야. 
특히 사용자가 입력한 '추가 정보'(약점이나 특이사항)가 있다면 그 부분을 집요하게 파고드는 질문을 포함해 5개를 던져.
각 질문에 대한 합격권 방어 답변도 제시해.
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
st.caption("디테일한 정보를 입력할수록 합격 확률이 올라갑니다.")
st.markdown("---")

# 입력창 배치 (2단 구성 + 하단 추가정보)
col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: AI 기반 음식물 쓰레기 처리기")
    target = st.text_input("🎯 타겟 고객", placeholder="예: 3040 주부, 1인 가구")
with col2:
    strength = st.text_area("💪 대표자/팀 강점", placeholder="예: 관련 특허 보유, 개발 경력 5년", height=105)

# ✨ [신규 기능] 선택 입력칸 추가
st.markdown("👇 **더 정교한 결과를 원하시면 아래 내용을 적어주세요! (선택)**")
additional_info = st.text_area(
    "➕ 추가 상세 정보 (TMI 환영)", 
    placeholder="예: 현재 매출 월 500만 원 발생 중, 경쟁사 A보다 가격 20% 저렴함, 시제품 제작 완료 상태 등",
    height=100
)

# [실행 로직]
if st.button("🚀 프리미엄 컨설팅 시작 (클릭)"):
    if not item or not target:
        st.warning("기본 정보(아이템, 타겟)는 필수입니다.")
    else:
        # AI에게 보낼 통합 정보 만들기
        user_input_combined = f"""
        1. 아이템: {item}
        2. 타겟: {target}
        3. 강점: {strength}
        """
        
        # 추가 정보가 있으면 내용에 덧붙이기
        if additional_info:
            user_input_combined += f"\n4. 추가 상세 정보(중요): {additional_info}"

        # 결과를 저장할 변수들
        psst_result = ""
        swot_result = ""
        interview_result = ""
        
        with st.status("🤖 전문가가 꼼꼼하게 분석 중입니다...", expanded=True) as status:
            try:
                # 1단계
                st.write("1단계: 사업계획서 작성 중 (추가 정보 반영)...")
                response1 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_PSST},
                        {"role": "user", "content": user_input_combined}
                    ]
                )
                psst_result = response1.choices[0].message.content
                st.write("✅ 사업계획서 완료!")
                
                # 2단계
                st.write("2단계: SWOT 전략 수립 중...")
                response2 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_SWOT},
                        {"role": "user", "content": f"아이템 및 정보: {user_input_combined} -> SWOT 분석해줘"}
                    ]
                )
                swot_result = response2.choices[0].message.content
                st.write("✅ SWOT 분석 완료!")

                # 3단계
                st.write("3단계: 압박 면접 질문 생성 중...")
                response3 = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": PROMPT_INTERVIEW},
                        {"role": "user", "content": f"아이템 및 정보: {user_input_combined} -> 면접 질문 뽑아줘"}
                    ]
                )
                interview_result = response3.choices[0].message.content
                st.write("✅ 면접 대비 완료!")
                
                status.update(label="🎉 분석이 끝났습니다!", state="complete", expanded=False)

            except Exception as e:
                st.error(f"에러 발생: {e}")
                st.stop()

        # [결과 출력]
        st.success("작성 완료! 추가하신 정보가 반영되었습니다.")
        
        tab1, tab2, tab3 = st.tabs(["📄 1. 상세 사업계획서", "📊 2. SWOT 전략", "🎤 3. 면접 예상질문"])
        
        with tab1:
            st.markdown(psst_result)
        with tab2:
            st.markdown(swot_result)
        with tab3:
            st.markdown(interview_result)
            
        # [다운로드]
        full_report = f"""
[예창패 프리패스 AI 리포트 (Pro)]
*반영된 추가정보: {additional_info if additional_info else '없음'}

--- 1. 상세 사업계획서 ---
{psst_result}

--- 2. SWOT 분석 및 전략 ---
{swot_result}

--- 3. 면접 예상 질문 및 답변 ---
{interview_result}
        """
        
        st.markdown("---")
        st.download_button(
            label="💾 전체 리포트 다운로드",
            data=full_report,
            file_name="사업계획서_Full.txt",
            mime="text/plain"
        )
