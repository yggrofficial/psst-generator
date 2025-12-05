import streamlit as st
from openai import OpenAI
import os

# -------------------------------------------------------------------------
# 🔐 [기능 1] 비밀번호 설정 (여기를 원하는 비번으로 바꾸세요!)
# -------------------------------------------------------------------------
# 입금한 사람에게만 이 비밀번호("1000won")를 알려주면 됩니다.
ACCESS_PASSWORD = "1234" 

# -------------------------------------------------------------------------
# 🔑 API 키 설정 (Streamlit Secrets에서 가져옴)
# -------------------------------------------------------------------------
try:
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    # 로컬 테스트용 (혹시 Secrets가 안 될 경우를 대비해)
    api_key = "sk-proj-..." # 여기에 본인 키를 잠깐 넣어서 테스트해도 됨
    
client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 🧠 AI 시스템 프롬프트 (전문가 모드)
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """
너는 대한민국 정부지원사업(예비창업패키지, 초기창업패키지) 심사위원 출신의 '사업계획서 컨설턴트'야.
사용자가 아이템을 입력하면, 심사위원이 합격을 줄 수밖에 없는 [PSST 방식]의 사업계획서 초안을 작성해.

[작성 규칙]
1. 말투: 모든 문장은 '~함', '~임' 등의 개조식(명사형)으로 끝낼 것.
2. 구조: 
   - 1. 문제 인식 (Problem)
   - 2. 해결 방안 (Solution)
   - 3. 성장 전략 (Scale-up)
   - 4. 팀 구성 (Team)
   - 5. 소요 예산안 (Table)
3. 예산안: 5,000만 원~1억 원 사이의 예산을 마크다운 표(Table)로 작성할 것.
4. 내용: 추상적 표현 금지. 구체적 수치, 전문 용어, 통계적 추정 사용.
"""

# -------------------------------------------------------------------------
# 💻 화면 구성 (UI)
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 프리패스 생성기 Pro", page_icon="🏛️")

# --- 비밀번호 잠금 화면 ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 유료 회원 전용 서비스")
    st.markdown("이 서비스는 **월 1,000원 멤버십** 회원만 이용 가능합니다.")
    
    password_input = st.text_input("비밀번호를 입력하세요", type="password")
    
    if st.button("로그인"):
        if password_input == ACCESS_PASSWORD:
            st.session_state.authenticated = True
            st.rerun() # 화면 새로고침
        else:
            st.error("비밀번호가 틀렸습니다. 관리자에게 문의하세요.")
    st.stop() # 비밀번호 틀리면 아래 코드 실행 안 함

# --- 메인 서비스 화면 (로그인 성공 시 보임) ---
st.title("🏛️ 예창패/초창패 프리패스 생성기 (VIP)")
st.caption("Pro 버전: 예산안 자동 수립 및 HWP용 텍스트 다운로드 지원")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: AI 라면 자판기")
with col2:
    target = st.text_input("🎯 타겟 고객", placeholder="예: 2030 1인 가구")

strength = st.text_area("💪 대표자 강점", placeholder="예: 관련 특허 보유, 3년 경력, 수상 내역", height=80)

if st.button("🚀 사업계획서 생성하기"):
    if not item or not target:
        st.warning("아이템과 타겟 고객을 입력해주세요.")
    else:
        with st.spinner("심사위원 빙의해서 독하게 작성 중입니다... (약 30초)"):
            try:
                # AI 호출
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"아이템: {item}, 타겟: {target}, 강점: {strength}"}
                    ]
                )
                result_text = response.choices[0].message.content
                
                # 결과 보여주기
                st.success("작성 완료! 아래 내용을 복사하거나 다운로드하세요.")
                st.markdown("---")
                st.markdown(result_text)
                
                # 📥 [기능 2] 다운로드 버튼 추가
                st.markdown("---")
                st.download_button(
                    label="💾 텍스트 파일로 다운로드 (HWP 붙여넣기용)",
                    data=result_text,
                    file_name="사업계획서_초안.txt",
                    mime="text/plain"
                )
                
                # PDF 안내
                st.info("💡 PDF 저장을 원하시면 브라우저에서 [Ctrl + P]를 누르고 'PDF로 저장'을 선택하세요.")

            except Exception as e:
                st.error(f"에러가 발생했습니다: {e}")
