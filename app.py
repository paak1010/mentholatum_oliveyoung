import streamlit as st
import pandas as pd
import io

# ==========================================
# 1. 페이지 기본 설정 (깃허브 로고 적용)
# ==========================================
st.set_page_config(
    page_title="올리브영 수주업로드 자동 입력 시스템", 
    page_icon="https://raw.githubusercontent.com/paak1010/mentholatum_oliveyoung/main/logo.png",
    layout="wide"
)

custom_css = """
<style>
[data-testid="stHeader"] { visibility: hidden; }
footer { visibility: hidden; }
[data-testid="stSidebar"] { background-color: #FFFFFF !important; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

with st.sidebar:
    st.image("https://static.wikia.nocookie.net/mycompanies/images/d/de/Fe328a0f-a347-42a0-bd70-254853f35374.jpg/revision/latest?cb=20191117172510", use_container_width=True)
    st.markdown("---")
    st.header("⚙️ 작업 설정")
    uploaded_file = st.file_uploader("올리브영 발주 엑셀 업로드", type=['xlsx'])
    st.markdown("---")
    apply_shelf_life = st.checkbox("✔️ 잔여 유효일자 548일 이하 제외 적용", value=True)
    st.caption("💡 자동 부분 할당 및 재고 차감 적용")
    st.caption("Developed by Jay")

st.title("올리브영 수주업로드 자동 입력 시스템")
st.markdown("Mentholatum : Moving The Heart")

def to_safe_float(series):
    cleaned = series.astype(str).str.replace(r'[^0-9.]', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce').fillna(0)

if uploaded_file:
    try:
        df_order_raw = pd.read_excel(uploaded_file, sheet_name='서식(수주업로드)', header=1)
        df_inv_raw = pd.read_excel(uploaded_file, sheet_name='재고', header=2)
        
        df_order = df_order_raw.copy()
        df_inv = df_inv_raw.copy()

        rename_dict = {}
        for col in df_inv.columns:
            col_str = str(col).replace(" ", "").upper()
            if '상품' in col_str and '상품명' not in col_str:
                rename_dict[col] = '상품'
            elif 'LOT' in col_str:
                rename_dict[col] = '화주LOT'
            elif '유효일자' in col_str or '유통기한' in col_str:
                rename_dict[col] = '유효일자'
            elif '환산' in col_str:
                rename_dict[col] = '환산'
        
        df_inv.rename(columns=rename_dict, inplace=True)

        if '잔여일수' in df_order.columns:
            start_idx = list(df_order.columns).index('잔여일수')
            cols_to_drop = df_order.columns[start_idx:]
            df_order = df_order.drop(columns=cols_to_drop)

        new_cols = ['LOT', '유효일자', '할당상태', '부족시_최대가능수량', '부족시_LOT', '부족시_유효일자']
        for col in new_cols:
            df_order[col] = ""
            df_order[col] = df_order[col].astype(object)

        # 무적의 글자 정제 (특수문자, 띄어쓰기 완전 제거)
        df_order['MECODE'] = df_order['MECODE'].astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.upper()
        df_inv['상품'] = df_inv['상품'].astype(str).str.replace(r'[^a-zA-Z0-9]', '', regex=True).str.upper()
        
        df_order['수량'] = to_safe_float(df_order['수량']).astype(float)
        df_inv['환산'] = to_safe_float(df_inv['환산']).astype(float)
        
        df_inv['유효일자_DT'] = pd.to_datetime(df_inv['유효일자'], errors='coerce')
        df_inv['유효일자_보존'] = df_inv['유효일자_DT'].fillna(pd.Timestamp('2099-12-31'))
        df_inv['유효일자_STR'] = df_inv['유효일자_DT'].dt.strftime('%Y-%m-%d').fillna('')

        box_col_candidates = [col for col in df_inv.columns if 'BOX' in str(col).upper() or '입수량' in str(col)]
        box_col_name = box_col_candidates[0] if box_col_candidates else None
        product_box_unit = {}
        if box_col_name:
            for mecode, group in df_inv.groupby('상품'):
                box_vals = to_safe_float(group[box_col_name])
                box_vals = box_vals[box_vals > 0]
                if not box_vals.empty:
                    product_box_unit[mecode] = int(box_vals.min())

        if apply_shelf_life:
            today = pd.Timestamp.today().normalize()
            cutoff_date = today + pd.Timedelta(days=548)
            idx_short_shelf_life = (df_inv['유효일자_보존'] <= cutoff_date)
            df_inv_valid = df_inv[~idx_short_shelf_life].copy()
        else:
            df_inv_valid = df_inv.copy()

        # ==========================================
        # 🕵️ 실시간 디버깅 안내판 (화면에 띄워줌)
        # ==========================================
        st.warning("**[시스템 체크] 데이터 인식 현황**")
        oc2_order_qty = df_order[df_order['MECODE'] == 'ME90621OC2']['수량'].sum()
        oc2_inv_raw_qty = df_inv[df_inv['상품'] == 'ME90621OC2']['환산'].sum()
        oc2_inv_valid_qty = df_inv_valid[df_inv_valid['상품'] == 'ME90621OC2']['환산'].sum()
        
        col1, col2, col3 = st.columns(3)
        col1.metric("발주서 요구 수량", f"{oc2_order_qty}개")
        col2.metric("엑셀 원본 총 재고", f"{oc2_inv_raw_qty}개")
        col3.metric("필터링 통과된 실재고", f"{oc2_inv_valid_qty}개")
        
        if oc2_inv_valid_qty == 0 and oc2_inv_raw_qty > 0:
            st.error("🚨 원본에는 재고가 있는데 유효기간 필터링 등에서 걸려 0개로 지워졌습니다. 좌측 체크박스를 끄고 다시 돌려주세요!")
        elif oc2_inv_raw_qty == 0:
            st.error("🚨 컴퓨터가 재고 엑셀에서 OC2 상품 자체를 읽어오지 못했습니다. 파일 문제일 확률이 높습니다.")
        else:
            st.success("✅ 정상적으로 재고를 파악했습니다. 할당이 성공할 것입니다!")
        st.markdown("---")

        df_inv_valid['화주LOT'] = df_inv_valid['화주LOT'].astype(str)
        if not df_inv_valid.empty:
            inv_grouped = df_inv_valid.groupby(['상품', '유효일자_보존']).agg({
                '환산': 'sum', 
                '화주LOT': 'first', 
                '유효일자_STR': 'first'
            }).reset_index()
        else:
            inv_grouped = pd.DataFrame(columns=['상품', '유효일자_보존', '환산', '화주LOT', '유효일자_STR'])

        with st.spinner('재고 매칭 중...'):
            for i, row in df_order.iterrows():
                mecode = str(row['MECODE'])
                order_qty = float(row['수량'])
                
                if mecode in ['NAN', '', 'NONE'] or order_qty <= 0:
                    df_order.at[i, '할당상태'] = "제외"
                    continue
                    
                available_inv = inv_grouped[(inv_grouped['상품'] == mecode) & (inv_grouped['환산'] > 0)]
                
                if available_inv.empty:
                    df_order.at[i, 'LOT'], df_order.at[i, '유효일자'], df_order.at[i, '할당상태'] = '재고없음', '재고없음', '재고없음'
                    continue

                full_match_inv = available_inv[available_inv['환산'] >= order_qty]
                best_match = full_match_inv.sort_values(by='유효일자_보존').iloc[0] if not full_match_inv.empty else available_inv.sort_values(by='유효일자_보존').iloc[0]

                best_idx = best_match.name
                max_qty = float(best_match['환산'])
                lot_str = str(best_match['화주LOT'])
                date_str = str(best_match['유효일자_STR']) 
                
                box_unit = product_box_unit.get(mecode, 1)
                potential_qty = min(order_qty, max_qty)
                allocated_boxes = int(potential_qty // box_unit)
                allocated_qty = float(allocated_boxes * box_unit)

                if allocated_qty > 0:
                    df_order.at[i, '수량'] = allocated_qty
                    df_order.at[i, 'LOT'] = lot_str
                    df_order.at[i, '유효일자'] = date_str
                    df_order.at[i, '할당상태'] = "정상할당" if allocated_qty == order_qty else f"부분할당({allocated_boxes}BOX)"
                    inv_grouped.at[best_idx, '환산'] -= allocated_qty
                else:
                    df_order.at[i, '할당상태'] = '박스단위부족'
                    df_order.at[i, '부족시_최대가능수량'] = max_qty
                    df_order.at[i, '부족시_LOT'] = lot_str
                    df_order.at[i, '부족시_유효일자'] = date_str

        st.subheader("📊 작업 결과 미리보기 (상위 100건)")
        view_cols = ['MECODE', '상품명', '수량', 'LOT', '유효일자', '할당상태']
        existing_view_cols = [c for c in view_cols if c in df_order.columns]
        
        df_display = df_order[existing_view_cols].head(100).copy()
        df_safe_display = pd.DataFrame(df_display.to_numpy().astype(str), columns=df_display.columns)
        
        st.dataframe(df_safe_display, use_container_width=True, hide_index=True)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            df_order.to_excel(writer, index=False, sheet_name='서식(수주업로드)')
            workbook = writer.book
            worksheet = writer.sheets['서식(수주업로드)']
            text_format = workbook.add_format({'num_format': '@'}) 
            
            for target_col in ['유효일자', '부족시_유효일자']:
                if target_col in df_order.columns:
                    idx = df_order.columns.get_loc(target_col)
                    worksheet.set_column(idx, idx, 15, text_format)

        st.download_button(
            label="💾 최종 완성본 엑셀 다운로드", 
            data=buffer.getvalue(), 
            file_name="올리브영_자동할당완료.xlsx", 
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            type="primary"
        )

    except Exception as e:
        st.error(f"오류 발생: {e}")
