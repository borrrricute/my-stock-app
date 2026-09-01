import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ----------------------------------------------------
# 기본 페이지 설정
# ----------------------------------------------------
st.set_page_config(
    page_title="주가 비교 대시보드",
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
st.title("📈 주가 비교 대시보드")
st.write(
    "종목 코드를 최대 2개까지 입력하면 같은 기간의 주가 흐름을 한 그래프에서 비교할 수 있어요. "
    "한국 주식은 종목코드 뒤에 `.KS`(코스피) 또는 `.KQ`(코스닥)를 붙여주세요. "
    "예) 삼성전자 `005930.KS`, 애플 `AAPL`"
)

# ----------------------------------------------------
# 종목 코드 입력창 2개 (나란히 배치)
# ----------------------------------------------------
input_col1, input_col2 = st.columns(2)
with input_col1:
    ticker_input_1 = st.text_input(
        "종목 1",
        value="AAPL",
        placeholder="예: AAPL",
    )
with input_col2:
    ticker_input_2 = st.text_input(
        "종목 2 (선택)",
        value="",
        placeholder="예: 005930.KS",
    )

# ----------------------------------------------------
# 조회 기간 선택 버튼 (1개월 / 6개월 / 1년 / 5년)
# ----------------------------------------------------
period_options = {
    "1개월": 30,
    "6개월": 182,
    "1년": 365,
    "5년": 365 * 5,
}
selected_period = st.radio(
    "조회 기간",
    options=list(period_options.keys()),
    index=2,  # 기본값: 1년
    horizontal=True,
)
period_days = period_options[selected_period]

# 입력값 앞뒤 공백 제거 + 대문자로 변환 (티커는 보통 대문자 사용)
tickers = []
for raw in [ticker_input_1, ticker_input_2]:
    cleaned = raw.strip().upper()
    if cleaned:
        tickers.append(cleaned)

# 중복 입력 제거 (같은 종목을 두 번 입력한 경우)
tickers = list(dict.fromkeys(tickers))


def load_stock_data(ticker: str, days: int):
    """yfinance로 지정한 기간만큼 주가 데이터를 불러오는 함수"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    data = yf.download(
        ticker,
        start=start_date,
        end=end_date,
        progress=False,
    )

    # yfinance가 멀티인덱스 컬럼을 반환하는 경우가 있어 정리해줌
    if hasattr(data.columns, "nlevels") and data.columns.nlevels > 1:
        data.columns = data.columns.get_level_values(0)

    return data


if not tickers:
    st.info("종목 코드를 입력하면 주가 정보가 표시돼요.")
else:
    # 그래프에 쓸 색상 (종목별로 다르게)
    line_colors = ["#FF9F1C", "#4A6FA5"]

    fig = go.Figure()
    stock_results = []  # 나중에 카드 표시에 쓸 데이터 모음

    with st.spinner("데이터를 불러오는 중이에요..."):
        for ticker in tickers:
            try:
                data = load_stock_data(ticker, period_days)
            except Exception as e:
                data = None
                st.error(f"{ticker} 데이터를 불러오는 중 오류가 발생했어요: {e}")
                continue

            if data is None or data.empty:
                st.warning(f"'{ticker}' 데이터를 찾을 수 없어요. 종목 코드를 다시 확인해 주세요.")
                continue

            stock_results.append((ticker, data))

    if not stock_results:
        st.stop()

    # ----------------------------------------------
    # 종목별 현재가 / 등락률 카드
    # ----------------------------------------------
    metric_cols = st.columns(len(stock_results) * 2)
    col_idx = 0

    for ticker, data in stock_results:
        first_price = float(data["Close"].iloc[0])
        last_price = float(data["Close"].iloc[-1])
        change_pct = (last_price - first_price) / first_price * 100

        currency_label = "원" if ticker.endswith((".KS", ".KQ")) else "달러"

        with metric_cols[col_idx]:
            st.metric(
                label=f"{ticker} 현재가",
                value=f"{last_price:,.2f} {currency_label}",
            )
        with metric_cols[col_idx + 1]:
            st.metric(
                label=f"{ticker} {selected_period} 등락률",
                value=f"{change_pct:+.2f}%",
                delta=f"{change_pct:+.2f}%",
            )
        col_idx += 2

    # ----------------------------------------------
    # Plotly 꺾은선 그래프 (종목을 한 그래프에 겹쳐서 표시)
    # ----------------------------------------------
    for i, (ticker, data) in enumerate(stock_results):
        fig.add_trace(
            go.Scatter(
                x=data.index,
                y=data["Close"],
                mode="lines",
                name=ticker,
                line=dict(color=line_colors[i % len(line_colors)], width=2),
            )
        )

    fig.update_layout(
        title=f"주가 비교 ({selected_period})",
        xaxis_title="날짜",
        yaxis_title="종가",
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFF9EC",
        font=dict(color="#4A3B22"),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )

    st.plotly_chart(fig, use_container_width=True)

    # ----------------------------------------------
    # 종목별 최고가 / 최저가 / 평균가 카드
    # ----------------------------------------------
    st.subheader("📊 기간 내 가격 통계")

    for ticker, data in stock_results:
        currency_label = "원" if ticker.endswith((".KS", ".KQ")) else "달러"

        highest = float(data["Close"].max())
        lowest = float(data["Close"].min())
        average = float(data["Close"].mean())

        st.markdown(f"**{ticker}**")
        stat_col1, stat_col2, stat_col3 = st.columns(3)
        with stat_col1:
            st.metric(label="최고가", value=f"{highest:,.2f} {currency_label}")
        with stat_col2:
            st.metric(label="최저가", value=f"{lowest:,.2f} {currency_label}")
        with stat_col3:
            st.metric(label="평균가", value=f"{average:,.2f} {currency_label}")

    # 참고용 원본 데이터 표(접어두기)
    with st.expander("원본 데이터 보기"):
        for ticker, data in stock_results:
            st.write(f"**{ticker}**")
            st.dataframe(data.sort_index(ascending=False))
