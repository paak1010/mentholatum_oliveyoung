import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. 페이지 기본 설정 (탭 아이콘 변경)
# ==========================================
# page_icon에 깃허브에 올라간 이미지의 'Raw' 링크를 넣거나, 
# 동일한 폴더에 있는 로컬 파일명(예: "logo.png")을 입력하세요.
github_logo_url = "https://raw.githubusercontent.com/사용자이름/저장소이름/main/logo.png" 

st.set_page_config(
    page_title="올리브영 수주업로드 자동 입력 시스템", 
    page_icon=github_logo_url, # 🌿 대신 깃허브 로고 경로 적용
    layout="wide"
)

# ==========================================
# 2. 커스텀 CSS 디자인 적용 (사이드바 흰색 & 기본 메뉴 숨기기)
# ==========================================
custom_css = """
<style>
/* 1. 우측 상단 기본 햄버거 메뉴 및 Deploy 헤더 숨기기 */
[data-testid="stHeader"] {
    visibility: hidden;
}

/* 2. 하단 Streamlit 워터마크 숨기기 (선택사항) */
footer {
    visibility: hidden;
}

/* 3. 사이드바 배경색을 완전히 흰색(#FFFFFF)으로 변경 */
[data-testid="stSidebar"] {
    background-color: #FFFFFF !important;
}
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# ==========================================
# 🎨 사이드바 디자인 (이하 기존 코드 동일)
# ==========================================
with st.sidebar:
    st.image("https://static.wikia.nocookie.net/mycompanies/images/d/de/Fe328a0f-a347-42a0-bd70-254853f35374.jpg/revision/latest?cb=20191117172510", use_container_width=True)
    st.markdown("---")
# ... (이하 생략) ...
