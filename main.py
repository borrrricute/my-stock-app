import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ----------------------------------------------------
# 기본 페이지 설정
# ----------------------------------------------------
st.set_page_config(
    page_title="주가 조회 대시보드",
    page_icon="📈",
    layout="centered",
)

# 따뜻한 톤을 위한 간단한 CSS (배경/카드 색상 조정)
st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF9EC;
    }
    div[data-testid="stMetric"] {
        background-color: #FFF3D6;
        border: 1px solid #F0DFA8;
        border-radius: 16px;
        padding: 16px 12px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------
# 제목과 설명
# ----------------------------------------------------
st.title("📈 주가 조회 대시보드")
st.write(
    "종목 코드를 입력하면 최근 1년간의 주가 흐름을 그래프로 보여드려요. "
    "한국 주식은 종목코드 뒤에 `.KS`(코스피) 또는 `.KQ`(코스닥)를 붙여주세요. "
    "예) 삼성전자 `005930.KS`, 애플 `AAPL`"
)

# ----------------------------------------------------
# 종목 코드 입력창
# ----------------------------------------------------
ticker_input = st.text_input(
    "종목 코드를 입력하세요",
    value="AAPL",
    placeholder="예: 005930.KS 또는 AAPL",
)

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (티커는 보통 대문자 사용)
ticker = ticker_input.strip().upper()

if ticker:
    # ------------------------------------------------
    # yfinance로 최근 1년 데이터 불러오기
    # ------------------------------------------------
    with st.spinner(f"{ticker} 데이터를 불러오는 중이에요..."):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)

        try:
            data = yf.download(
                ticker,
                start=start_date,
                end=end_date,
                progress=False,
            )
        except Exception as e:
            data = None
            st.error(f"데이터를 불러오는 중 오류가 발생했어요: {e}")

    # 데이터가 비어있으면(잘못된 종목코드 등) 안내 메시지 표시
    if data is None or data.empty:
        st.warning("해당 종목의 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해 주세요.")
    else:
        # yfinance가 멀티인덱스 컬럼을 반환하는 경우가 있어 정리해줌
        if isinstance(data.columns, type(data.columns)) and hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
            data.columns = data.columns.get_level_values(0)

        # ----------------------------------------------
        # 현재가 / 1년 등락률 계산
        # ----------------------------------------------
        first_price = float(data["Close"].iloc[0])   # 1년 전 종가
        last_price = float(data["Close"].iloc[-1])    # 가장 최근 종가
        change_pct = (last_price - first_price) / first_price * 100

        # 통화 단위 결정 (한국 종목이면 원, 그 외에는 달러로 표시)
        currency_label = "원" if ticker.endswith((".KS", ".KQ")) else "달러"

        # ----------------------------------------------
        # 지표 카드 2개를 나란히 표시
        # ----------------------------------------------
        col1, col2 = st.columns(2)
        with col1:
            st.metric(
                label="현재가",
                value=f"{last_price:,.2f} {currency_label}",
            )
        with col2:
            st.metric(
                label="최근 1년 등락률",
                value=f"{change_pct:+.2f}%",
                delta=f"{change_pct:+.2f}%",
            )

        # ----------------------------------------------
        # Plotly 꺾은선 그래프
        # ----------------------------------------------
        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name="종가",
                line=dict(color="#FF9F1C", width=2),
            )
        )

        fig.update_layout(
            title=f"{ticker} 최근 1년 주가",
            xaxis_title="날짜",
            yaxis_title=f"종가 ({currency_label})",
            plot_bgcolor="#FFFFFF",
            paper_bgcolor="#FFF9EC",
            font=dict(color="#4A3B22"),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)

        # 참고용 원본 데이터 표(접어두기)
        with st.expander("원본 데이터 보기"):
            st.dataframe(data.sort_index(ascending=False))
else:
    st.info("종목 코드를 입력하면 주가 정보가 표시돼요.")
