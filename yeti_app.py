import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, date
import random

# 페이지 설정
st.set_page_config(
    page_title="¥ETI",
    page_icon="💱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일링
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .recommendation-box {
        background-color: #e8f4fd;
        padding: 1.5rem;
        border-radius: 10px;
        border: 2px solid #1f77b4;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 10px;
        border-left: 5px solid #ffc107;
    }
</style>
""", unsafe_allow_html=True)

# 실제 데이터 로드 함수
@st.cache_data
def load_exchange_data():
    """7월 실제 환율 데이터와 8월 예측 데이터를 로드하여 통합"""
    try:
        # 7월 실제 환율 데이터 로드
        july_data = pd.read_csv('./july_yen.csv')
        july_data['ds'] = pd.to_datetime(july_data['ds'])
        july_data = july_data.rename(columns={'ds': 'date', 'y': 'rate'})
        july_data['is_prediction'] = False
        
        # 2025년 예측 데이터 로드
        forecast_data = pd.read_csv('./forecast_2025.csv')
        forecast_data['date'] = pd.to_datetime(forecast_data['date'])
        forecast_data = forecast_data.rename(columns={'predicted_fx': 'rate'})
        forecast_data['is_prediction'] = True
        
        # 데이터 통합
        combined_data = pd.concat([july_data, forecast_data], ignore_index=True)
        combined_data = combined_data.sort_values('date').reset_index(drop=True)
        
        return combined_data
        
    except FileNotFoundError as e:
        st.error(f"데이터 파일을 찾을 수 없습니다: {e}")
        st.error("july_yen.csv와 forecast_aug.csv 파일이 올바른 위치에 있는지 확인해주세요.")
        
        # 오류 시 빈 DataFrame 반환
        return pd.DataFrame(columns=['date', 'rate', 'is_prediction'])
        
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return pd.DataFrame(columns=['date', 'rate', 'is_prediction'])

# 메인 헤더
st.markdown("""
    <style>
    .main-header {
        font-size: 48px;
        font-weight: bold;
        color: black;
        text-align: center;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)
st.markdown('<div class="main-header" style="margin-top:-30px;">¥ETI</div>', unsafe_allow_html=True)
st.markdown('<div style="color: black; font-size: 20px; text-align: center; margin-top: -30px;">당신의 엔화 환전 타이밍 알리미</div>', unsafe_allow_html=True)

# 오늘 날짜 표시
today = pd.Timestamp(datetime.today().date())
st.markdown(
    f"""
    <div style="display:flex; align-items:center; gap:0px;">
        <h4 style="margin:0;">{today.strftime('%Y.%m.%d')}</h4>
        <span style="font-size:14px; color:gray;">한국은행 경제통계시스템</span>
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("---")

# 데이터 로드
exchange_data = load_exchange_data()

# 데이터가 비어있지 않은 경우에만 처리
if not exchange_data.empty:
    # 현재 환율 계산 (실제 데이터의 마지막 값)
    actual_data = exchange_data[exchange_data['is_prediction'] == False]
    nearest_actual = actual_data[actual_data['date'] >= today]

    if not nearest_actual.empty:
        current_rate = nearest_actual['rate'].iloc[0]
        yesterday_actual = actual_data[actual_data['date'] < nearest_actual.iloc[0]['date']]
        
        if not yesterday_actual.empty:
            yesterday_rate = yesterday_actual['rate'].iloc[-1]
            rate_change = current_rate - yesterday_rate

        else:
            yesterday_rate = current_rate
            rate_change = 0
    
    else:
        if not actual_data.empty:
            current_rate = actual_data.iloc[-1]['rate']
            yesterday_rate = actual_data.iloc[-2]['rate'] if len(actual_data) > 1 else current_rate
            rate_change = current_rate - yesterday_rate

        else:
            current_rate = 900  # 기본값
            yesterday_rate = 900
            rate_change = 0
else:
    st.error("환율 데이터를 로드할 수 없습니다. 파일을 확인해주세요.")
    st.stop()

# 사이드바 - 설정 및 입력
with st.sidebar:
    st.header("AI가 추천하는 환전 시점 알아보기")
    st.header("📅 여행 일정")
    
    # 여행 날짜 입력 (8월 데이터 기준으로 조정)
    col1, col2 = st.columns(2)
    with col1:
        departure_date = st.date_input(
            "출발일",
            value=date(2025, 8, 1),  # 8월 1일로 기본값 설정
            min_value=date(2025, 8, 1),
            max_value=date(2025, 12, 31)
        )
    with col2:
        # 출발일 다음 날을 기본값으로 지정
        default_return_date = departure_date + timedelta(days=1)
        if default_return_date > date(2025, 12, 31):
            default_return_date = date(2025, 12, 31)

        return_date = st.date_input(
            "도착일",
            value=default_return_date,
            min_value=departure_date,
            max_value=date(2025, 12, 31)
        )
    
    # 환전 금액 입력
    st.header("💰 환전 계획")
    exchange_amount = st.number_input(
        "환전 예정 금액 (원)",
        min_value=10000,
        max_value=10000000,
        value=1000000,
        step=10000,
        format="%d"
    )
    

    run_button = st.button("환전 추천 시점 확인하기")

    

# 메인 컨텐츠 영역
# 1. 현재 환율 상태 카드
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "오늘의 환율 (100엔)",
        f"{current_rate:.1f}원",
        f"{rate_change:+.1f}원 (어제 기준)"
    )

with col2:
    # 내일 예측값 계산
    tomorrow = pd.Timestamp.today() + timedelta(days=1)
    tomorrow_data = exchange_data[exchange_data['date'].dt.date == tomorrow.date()]
    
    if not tomorrow_data.empty:
        tomorrow_prediction = tomorrow_data['rate'].iloc[0]
        trend = "상승" if tomorrow_prediction > current_rate else "하락" if tomorrow_prediction < current_rate else "➡️ 보합"
        st.metric(
            "내일의 예상 환율",
            f"{tomorrow_prediction:.1f}원",
            trend
        )
    else:
        st.metric(
            "내일 예상",
            "데이터 없음",
            "—"
        )

with col3:
    # 여행 출발일 이전 예측 데이터 필터링
    prediction_data = exchange_data[
        (exchange_data['is_prediction'] == True) &
        (exchange_data['date'] < pd.Timestamp(departure_date))
    ]

    # 오늘 환율 데이터 (DataFrame 형태로)
    today_df = pd.DataFrame({
        'rate': [current_rate],
        'date': [pd.Timestamp(datetime.today().date())]
    })

    # 오늘 날짜가 출발일 이전이면 today_df를 prediction_data에 추가
    if today_df['date'].iloc[0] < pd.Timestamp(departure_date):
        combined_data = pd.concat([prediction_data[['rate', 'date']], today_df], ignore_index=True)
    else:
        combined_data = prediction_data[['rate', 'date']]

    if not combined_data.empty:
        week_min = combined_data['rate'].min()
        st.metric(
            "여행 전 최저 예상 환율",
            f"{week_min:.1f}원",
            f"{week_min - current_rate:+.1f}원 (오늘 기준)"
        )
    else:
        st.metric(
            "여행 전 최저 예상",
            "데이터 없음",
            "—"
        )

with col4:
    expected_yen = int(exchange_amount / current_rate * 100)
    st.metric(
        "예상 환전액",
        f"{expected_yen:,}엔",
    )

st.markdown("---")

# 2. 메인 차트와 추천사항
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("📊 환율 추이 및 예측")
    
    # 차트 생성
    fig = go.Figure()
    
    # 과거 데이터
    past_data = exchange_data[~exchange_data['is_prediction']]
    fig.add_trace(go.Scatter(
        x=past_data['date'],
        y=past_data['rate'],
        mode='lines',
        name='실제 환율',
        line=dict(color='#1f77b4', width=2)
    ))
    
    # 예측 데이터
    future_data = exchange_data[exchange_data['is_prediction']]
    fig.add_trace(go.Scatter(
        x=future_data['date'],
        y=future_data['rate'],
        mode='lines',
        name='예측 환율',
        line=dict(color='#ff7f0e', width=2, dash='dash')
    ))
    
    # 여행 기간 하이라이트
    fig.add_vrect(
        x0=departure_date, x1=return_date,
        fillcolor="rgba(255, 0, 0, 0.1)",
        layer="below", line_width=0,
        annotation_text="여행 기간", annotation_position="top left"
    )
    
    fig.update_layout(
        title="엔화 환율 추이 (100엔 기준)",
        title_font_size=24,
        xaxis_title="날짜",
        yaxis_title="환율 (원)",
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💡 환전 시점 추천")

    if run_button:
        today = pd.Timestamp(datetime.today().date())

        travel_period = exchange_data[
            (exchange_data['date'] >= today) & 
            (exchange_data['date'] < pd.Timestamp(departure_date))
        ]

        if not travel_period.empty:
            top3 = travel_period.nsmallest(3, 'rate')
            st.session_state['top3'] = top3
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("#### 여행 전 최적 환전 일자")


            for idx, (_, row) in enumerate(top3.iterrows()):
                format_date = row['date'].strftime('%Y.%m.%d')
                rate = row['rate']

                with st.container():
                    st.markdown(f"##### **{idx + 1}. {format_date}**")
                    st.markdown(f"AI 예상 환율: **{rate:.1f}원**")
                    st.markdown("<hr style='margin-top: 4px; margin-bottom: 4px;'>", unsafe_allow_html=True)

        else:
            st.warning("해당 기간에 환율 정보가 없어요!")
            st.session_state['top3'] = None
    else:
        # run_button 안 누르면 세션 상태 초기화(없으면 None으로)
        if 'top3' not in st.session_state:
            st.session_state['top3'] = None


# 3. 상세 분석 및 도구
tab1, tab2, tab3 = st.tabs(["🧠 스마트 환전 플래너", "📰 월별 리포트", "🧮 환전 계산기"])

with tab1:
    st.subheader("🧠 스마트 환전 플래너")
    st.write("나의 성향에 맞는 환전 전략을 알아보세요.")
    st.write("- 여행지를 선택한 이유 TOP 3를 선택해주세요")

    reasons = [
        (1, '🗺️ 유명한 여행지'), (2, '🏯 볼거리 제공'), (3, '💸 저렴한 경비'), (4, '🚗 이동 거리'),
        (5, '🕒 여행 기간'), (6, '🏨 숙박시설'), (7, '🛍️ 쇼핑'), (8, '🍜 음식'),
        (9, '🚉 교통편'), (10, '🎯 체험 프로그램'), (11, '🗣️ 주변인 추천'),
        (12, '♿ 관광지 편의시설'), (13, '📚 교육성'), (14, '🧑‍🤝‍🧑 여행 동반자'), (15, '❓ 기타')
    ]

    # 세션 상태 초기화
    if "selected_reasons" not in st.session_state:
        st.session_state.selected_reasons = []

    cols = st.columns(5)
    for i, (code, text) in enumerate(reasons):
        col = cols[i % 5]
        label = text  # 그냥 텍스트만

        if col.button(label, key=text):
            if code in st.session_state.selected_reasons:
                st.session_state.selected_reasons.remove(code)
            else:
                if len(st.session_state.selected_reasons) < 3:
                    st.session_state.selected_reasons.append(code)

    selected = st.session_state.selected_reasons

    st.write("선택항목:")

    selected_texts = [text for c, text in reasons if c in selected]
    numbered_list = "\n".join([f"{i+1}. {text}" for i, text in enumerate(selected_texts)])
    st.markdown(numbered_list)
    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        purchase_time = st.selectbox(
            "여행 상품 구매 시기를 알려주세요",
            options=[
                (1, "1년 이내"), (2, "6개월 이내"), (3, "3개월 이내"),
                (4, "2개월 이내"), (5, "1개월 이내"), (6, "2주 이내"),
                (7, "1주 이내"), (8, "3일 이내"), (9, "당일")
            ],
            format_func=lambda x: x[1]
        )[0]

    with col2:
        estimated_cost = st.number_input("여행 총 경비는 얼마나 생각하고 있나요? (원)", min_value=0, step=10000)

    with col3:
        income_map = {
            1: '소득없음', 2: '월평균 100만원 미만', 3: '월평균 100~200만원 미만',
            4: '월평균 200~300만원 미만', 5: '월평균 300~400만원 미만', 6: '월평균 400~500만원 미만',
            7: '월평균 500~600만원 미만', 8: '월평균 600~700만원 미만', 9: '월평균 700~800만원 미만',
            10: '월평균 800~900만원 미만', 11: '월평균 900~1,000만원 미만', 12: '월평균 1,000만원 이상'
        }
        monthly_income = st.selectbox(
            "월 평균 소득을 알려주세요.",
            options=list(income_map.items()),
            format_func=lambda x: x[1]
        )[0]

    if st.button("분석 시작"):
        score_time = 0
        if purchase_time in [5, 6]:
            score_time = 1
        elif purchase_time in [1, 2]:
            score_time = -1

        score_reason = 0
        if selected[0] == 3:
            score_reason = 3
        elif selected[1] == 3:
            score_reason = 2
        elif selected[2] == 3:
            score_reason = 1

        score_cost = 0
        if estimated_cost < 700000:
            score_cost = 1
        elif estimated_cost >= 1500000:
            score_cost = -1

        score_income = 0
        if monthly_income in [1, 2, 3]:
            score_income = 1
        elif monthly_income in [9, 10, 11, 12]:
            score_income = -1

        sensitivity_score = score_time + score_reason + score_income

        result_group = '전략적 환전 추천 유형' if sensitivity_score >= 0 else '간편 환전 추천 유형'

        st.markdown("---")
        st.markdown(f"#### 🪄나의 여행 스타일에 최적화된 환전 플랜")
        st.write(f"**{result_group}**에 해당하시네요!")


        top3 = st.session_state.get('top3', None)
        dates = list(top3['date'])

        if result_group == '전략적 환전 추천 유형':
            st.markdown("입력하신 여행 계획과 예산 정보를 분석한 결과, 환율 변동에 따른 영향을 균형 있게 관리할 수 있는 **분할 환전** 방식을 추천드립니다.")
            st.markdown("아래는 추천드리는 환전 시점입니다:")
            st.markdown(f"- 1차 환전일: **{dates[0].strftime('%Y.%m.%d')}**")
            st.markdown(f"- 2차 환전일: **{dates[1].strftime('%Y.%m.%d')}**")
            st.markdown(f"- 3차 환전일: **{dates[2].strftime('%Y.%m.%d')}**")

        else:
            # 일괄 환전

            st.markdown("입력하신 여행 계획과 예산 정보를 분석한 결과, 번거로움 없이 원하는 날짜에 한 번에 환전하는 **일괄 환전** 방식을 추천드립니다.")
            st.markdown("아래는 추천드리는 환전 시점입니다:")
            st.markdown(f"- 추천 환전일: **{dates[0].strftime('%Y.%m.%d')}**")


with tab3:
    st.subheader("🧮 환전 계산기")
    st.write("환전 금액과 환율을 입력하여 예상 환전액을 계산해보세요.")

    col1, col2 = st.columns(2)

    with col1:
        calc_amount = st.number_input(
            "계산할 금액 (원)",
            min_value=10000,
            value=500000,
            step=10000
        )

        mode = st.radio("환율 설정 방식", ("자동 예측", "직접 입력"), horizontal=True)

        if mode == "자동 예측":
            calc_date = st.date_input(
                "환전 예정일",
                value=date(2025, 8, 1),
                min_value=date(2025, 8, 1),
                max_value=date(2025, 8, 31)
            )
            selected_rate = exchange_data[
                exchange_data['date'] == pd.Timestamp(calc_date)
            ]['rate'].iloc[0] if not exchange_data[
                exchange_data['date'] == pd.Timestamp(calc_date)
            ].empty else current_rate

        else:
            selected_rate = st.number_input(
                "직접 입력한 환율 (1엔당 원)",
                min_value=0.01,
                step=0.01,
                value=current_rate
            )
            calc_date = None  # 입력 안 받음

    with col2:
        calc_yen = int(calc_amount / selected_rate * 100)
        current_yen = int(calc_amount / current_rate * 100)
        difference = calc_yen - current_yen

        card_html = f"""
        <div style="
            background-color: #f0f4f8; 
            border: 2px solid #1f77b4; 
            border-radius: 12px; 
            padding: 20px; 
            text-align: center; 
            font-size: 24px; 
            font-weight: bold;
            width: 100%;
            max-width: 300px;
            margin: 0 auto;
            ">
            예상 환전액<br>
            <span style="color:#1f77b4; font-size: 32px;">{calc_yen:,}엔</span>
        </div>
        """
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(card_html, unsafe_allow_html=True)


with tab2:
    st.subheader("📰 월별 리포트")
    st.write("엔화 시장 흐름을 파악할 수 있는 최근 3개월의 AI 뉴스 요약을 확인해보세요.")

    news_df = pd.read_csv('./monthly_news_202007202507.csv')

    # 날짜를 datetime으로 변환
    news_df['date'] = pd.to_datetime(news_df['date'])

    # 최신 3개 추출
    latest_news = news_df.sort_values('date', ascending=False).head(3)

    for i, row in enumerate(latest_news.itertuples(), 1):
        year_month = row.date.strftime('%Y.%m')
        summary = row.summary
        st.write(f"{i}. **{year_month}** : {summary}")
        st.markdown("---")
    

# 푸터
st.markdown("""
<div style='text-align: center; color: #666; padding: 1rem;'>
<small>본 서비스는 예측 정보만을 제공하며, 실제 환전 시 금융기관의 환율을 확인하시기 바랍니다.</small>
</div>
""", unsafe_allow_html=True)
