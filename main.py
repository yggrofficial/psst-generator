import streamlit as st
from openai import OpenAI

# -------------------------------------------------------------------------
# 🔐 [설정] 비밀번호 및 API 키
# -------------------------------------------------------------------------
ACCESS_PASSWORD = "1234"  # 유료 회원용 비밀번호

try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    api_key = "sk-proj-..." # 로컬 테스트용 (배포 시엔 무시됨)

client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 🧠 [핵심] 독한 컨설턴트 프롬프트 (기능 대폭 추가)
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """
너는 대한민국 정부지원사업 심사위원장 출신의 '창업 컨설턴트'야.
단순한 작문이 아니라, 합격을 위한 치밀한 전략을 제시해야 해.

[작성 원칙]
1. 말투: '~함', '~임' 등 명사형 종결(개조식) 필수.
2. 수치화: '열심히' 금지. '전년 대비 30% 성장', '시장규모 10조 원' 등 추정치 포함.
3. 비판적 시각: 약점은 솔직히 인정하고 구체적인 극복 방안을 제시할 것.

[출력 형식 - 반드시 마크다운 포맷 유지]
섹션 1. PSST 사업계획서 (표와 리스트 활용)
섹션 2. 심층 분석 (SWOT 분석 표 포함)
섹션 3. 실전 면접 대비 (예상 공격 질문 5개 및 방어 논리)
"""

# -------------------------------------------------------------------------
# 💻 UI 구성 (탭 기능 적용)
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 프리패스 Pro", page_icon="💎", layout="wide")

# 1. 로그인 화면
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

# 2. 메인 화면
st.title("💎 정부지원사업 합격 솔루션 (Premium)")
st.caption("사업계획서 + SWOT 전략 + 심사위원 면접 대비까지 한 번에 해결합니다.")
st.markdown("---")

# 입력창 배치 (2단 구성)
col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: 폐플라스틱을 활용한 3D 프린터 필라멘트")
    target = st.text_input("🎯 타겟 고객", placeholder="예: ESG 경영 공공기관, 친환경 메이커스")
with col2:
    strength = st.text_area("💪 대표자/팀 강점", placeholder="예: 화학공학 박사, 관련 특허 2건, 시제품 제작 완료", height=105)

# 3. 생성 로직
if st.button("🚀 프리미엄 컨설팅 리포트 생성 (약 40초 소요)"):
    if not item or not target:
        st.warning("아이템과 타겟 정보를 모두 입력해주세요.")
    else:
        with st.spinner("심사위원 관점에서 냉철하게 분석 중입니다..."):
            try:
                # 프롬프트 조립
                user_content = f"""
                아래 창업 아이템에 대해 3가지 파트로 완벽한 리포트를 작성해.
                
                정보:
                - 아이템: {item}
                - 타겟: {target}
                - 강점: {strength}
                
                [파트 1: 사업계획서]
                - PSST(문제-해결-성장-팀) 구조
                - 소요 예산안 (표)
                
                [파트 2: 전략 분석]
                - SWOT 분석 (표 형태로 작성: 강점, 약점, 기회, 위협)
                - 약점(W)을 기회(O)로 바꿀 구체적 전략 3가지
                
                [파트 3: 면접 대비]
                - 심사위원이 공격할 만한 날카로운 질문 5가지
                - 각 질문에 대한 방어 답변 (핵심만)
                """
                
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ]
                )
                full_text = response.choices[0].message.content
                
                # 결과 보여주기 (탭으로 구분)
                st.success("분석이 완료되었습니다!")
                st.markdown("---")
                
                # 탭 생성
                tab1, tab2, tab3 = st.tabs(["📄 1. 사업계획서", "📊 2. SWOT 전략", "🎤 3. 면접 예상질문"])
                
                # AI가 준 전체 텍스트를 적절히 쪼개서 보여주면 좋겠지만, 
                # 간단하게 전체 내용을 각 탭에 안내와 함께 보여주는 방식으로 구현
                
                with tab1:
                    st.subheader("📝 표준 사업계획서 (PSST)")
                    st.info("정부 양식에 바로 붙여넣기 할 수 있는 초안입니다.")
                    st.markdown(full_text) # 전체 내용을 보여주되, 사용자가 골라 쓰도록 함
                    
                with tab2:
                    st.subheader("📊 심층 분석 (SWOT)")
                    st.info("사업의 약점을 보완하고 시장 기회를 잡기 위한 전략입니다.")
                    st.warning("팁: 사업계획서의 '실현 가능성' 파트에 SWOT 표를 넣으면 가점을 받기 좋습니다.")
                    # (여기서 내용은 위 full_text에 포함되어 있음)
                    
                with tab3:
                    st.subheader("🎤 실전 면접 시뮬레이션")
                    st.error("주의: 심사위원은 이 부분만 집중적으로 물어봅니다. 반드시 답변을 숙지하세요.")
                    # (내용 포함됨)
                
                # 다운로드 버튼
                st.markdown("---")
                st.download_button(
                    label="💾 전체 리포트 다운로드 (텍스트 파일)",
                    data=full_text,
                    file_name="프리미엄_사업계획서_리포트.txt",
                    mime="text/plain"
                )

            except Exception as e:
                st.error(f"오류 발생: {e}")
