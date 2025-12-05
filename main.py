import streamlit as st
from openai import OpenAI
import os

# -------------------------------------------------------------------------
# [중요] GitHub에는 키를 올리지 않고, Streamlit 'Secrets'에서 가져옵니다.
# -------------------------------------------------------------------------
try:
    # Streamlit 클라우드의 금고(Secrets)에서 키를 꺼내옵니다.
    api_key = st.secrets["OPENAI_API_KEY"]
except:
    st.error("🚨 API 키가 없습니다! Streamlit 설정(Secrets)에 키를 넣어주세요.")
    st.stop()

client = OpenAI(api_key=api_key)

# -------------------------------------------------------------------------
# 🧠 독한 프롬프트 (엔진)
# -------------------------------------------------------------------------
SYSTEM_PROMPT = """
너는 대한민국 정부지원사업(예비창업패키지, 초기창업패키지) 심사위원 출신의 '사업계획서 컨설턴트'야.
사용자가 아이템을 입력하면, 심사위원이 합격을 줄 수밖에 없는 [PSST 방식]의 사업계획서 초안을 작성해.

[작성 제약 사항]
1. 말투: 모든 문장은 '~함', '~임' 등의 '개조식(명사형)'으로 끝낼 것.
2. 구성: 문제 인식(Problem) - 해결 방안(Solution) - 성장 전략(Scale-up) - 팀 구성(Team) - 소요 예산안(Table)
3. 예산안: 5,000만 원~1억 원 사이의 예산 계획을 반드시 '마크다운 표(Table)'로 작성할 것.
4. 내용: 추상적 표현 금지. 구체적 수치와 전문 용어 사용.
"""

# -------------------------------------------------------------------------
# 💻 웹사이트 화면 (UI)
# -------------------------------------------------------------------------
st.set_page_config(page_title="예창패 프리패스 생성기", page_icon="🏛️")

st.title("🏛️ 정부지원사업 사업계획서 생성기 (Pro)")
st.caption("Powered by OpenAI & Streamlit Cloud")
st.markdown("---")

col1, col2 = st.columns(2)
with col1:
    item = st.text_input("💡 창업 아이템", placeholder="예: AI 라면 자판기")
with col2:
    target = st.text_input("🎯 타겟 고객", placeholder="예: 2030 커플")

strength = st.text_area("💪 대표자 강점", placeholder="예: 관련 특허 보유, 3년 경력", height=80)

if st.button("🚀 사업계획서 생성하기"):
    if not item or not target:
        st.warning("내용을 입력해주세요.")
    else:
        with st.spinner("심사위원 빙의해서 작성 중입니다..."):
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": f"아이템: {item}, 타겟: {target}, 강점: {strength}"}
                    ]
                )
                st.success("작성 완료!")
                st.markdown("---")
                st.markdown(response.choices[0].message.content)
            except Exception as e:
                st.error(f"에러: {e}")
