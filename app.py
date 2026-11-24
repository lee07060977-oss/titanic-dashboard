# ===== 설정 =====
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Titanic 대시보드", layout="wide")

# ===== 함수 =====
TEAL, GRAY = "#1B6F8F", "#A7B1B9"                     # 색 의미 고정: 생존=틸, 사망=회색

def filter_data(df, sexes, classes, age_range, ports):
    f = df[df["sex"].isin(sexes)                        # 성별 조건
           & df["pclass"].isin(classes)                 # 객실 등급 조건
           & df["embarked"].isin(ports)]                # 승선 항구 조건
    if age_range != (0, 80):                            # 전체 범위가 아닐 때만 나이 조건
        f = f[f["age"].between(*age_range)]
    return f

def kpi(df):
    if len(df) == 0:                                    # 빈 데이터면 (0, 0, 0)
        return 0, 0, 0
    n = len(df)                                         # 승객 수
    rate = round(float(df["survived"].mean()) * 100, 1) # 생존율(%)
    age = round(float(df["age"].mean()), 1)             # 평균 나이
    return n, rate, age


def class_rate_bar(df):
    r = (df.groupby("pclass")["survived"]               # 등급별로 묶기
           .mean().mul(100).round(1)                    # 생존율(%) 계산
           .reset_index())                              # 일반 표로 되돌리기
    fig = px.bar(r, x="pclass", y="survived", text="survived",
                 title="객실 등급별 생존율(%)",
                 color_discrete_sequence=[TEAL])        # 막대 색: 틸
    fig.update_xaxes(type="category")                   # 1·2·3을 범주로 표시
    return fig


def age_hist(df):
    fig = px.histogram(df, x="age", color="survived",   # 생존 여부별 색 구분
                       barmode="overlay", opacity=0.6,  # 겹쳐 그리기 + 투명도
                       color_discrete_map={0: GRAY, 1: TEAL},   # 사망=회색, 생존=틸
                       title="생존 여부별 나이 분포")
    return fig


LABELS = {"sex": "성별", "class": "객실 등급", "embarked": "승선 항구"}   # 기준 이름(한글)

def group_rate_bar(df, col):                            # 기준(col)별 생존율 막대
    r = (df.groupby(col)["survived"]
           .mean().mul(100).round(1)
           .reset_index())
    fig = px.bar(r, x=col, y="survived", text="survived",
                 labels={col: LABELS[col], "survived": "생존율(%)"},
                 title=f"{LABELS[col]}별 생존율(%)",
                 color_discrete_sequence=[TEAL])
    return fig


NUM_COLS = ["survived", "pclass", "age", "sibsp", "parch", "fare"]   # [추가] 수치형 열

def corr_heatmap(df):                                   # [추가] 상관 히트맵
    corr = df[NUM_COLS].corr().round(2)
    fig = px.imshow(corr, text_auto=True, zmin=-1, zmax=1,
                    color_continuous_scale="RdBu_r",
                    title="수치형 열 상관계수")
    return fig


def iqr_outliers(df, col):                              # [추가] IQR 이상치 개수
    s = df[col].dropna()
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n_out = int(((s < lower) | (s > upper)).sum())
    return n_out, lower, upper

# ===== 데이터 읽기 =====
@st.cache_data                                          # 처음 한 번만 읽고 기억
def load_data():
    return pd.read_csv("titanic.csv")

df = load_data()

# ===== 제목 =====
st.title("타이타닉, 누가 살아남았나?")

# ===== 사이드바 =====
sexes = st.sidebar.multiselect("성별", ["male", "female"], ["male", "female"])
classes = st.sidebar.multiselect("객실 등급", [1, 2, 3], [1, 2, 3])
ages = st.sidebar.slider("나이", 0, 80, (0, 80))
ports = st.sidebar.multiselect("승선 항구", ["S", "C", "Q"], ["S", "C", "Q"])

if not sexes or not classes or not ports:               # 항구도 검사
    st.warning("성별 · 등급 · 항구를 하나 이상 선택하세요.")
    st.stop()

# ===== 본문 =====
f = filter_data(df, sexes, classes, ages, ports)        # ports 전달

if len(f) == 0:
    st.warning("조건에 맞는 승객이 없습니다.")
    st.stop()

# ===== KPI =====
n, rate, age = kpi(f)
_, base_rate, _ = kpi(df)                               # 전체 생존율(38.4%)
c1, c2, c3 = st.columns(3)
c1.metric("승객 수", f"{n}명")
c2.metric("생존율", f"{rate}%", f"{rate - base_rate:+.1f}%p")   # 전체 대비 차이
c3.metric("평균 나이", f"{age}세")

# ===== 탭 =====
tab1, tab2, tab3 = st.tabs(["개요", "관계", "이상치"])           # [추가]

with tab1:                                                      # [추가] 개요: 기존 차트
    left, right = st.columns(2)
    left.plotly_chart(class_rate_bar(f))
    right.plotly_chart(age_hist(f))
    col = st.selectbox("비교 기준", ["sex", "class", "embarked"],
                       format_func=lambda c: LABELS[c])
    st.plotly_chart(group_rate_bar(f, col))

with tab2:                                                      # [추가] 관계: 상관 히트맵
    st.plotly_chart(corr_heatmap(f))

with tab3:                                                      # [추가] 이상치: IQR + 박스플롯
    out_col = st.selectbox("열 선택", ["age", "fare", "sibsp", "parch"])
    n_out, lower, upper = iqr_outliers(f, out_col)
    st.metric("IQR 이상치 수", f"{n_out}개")
    st.caption(f"정상 범위: {lower:.1f} ~ {upper:.1f}")
    st.plotly_chart(px.box(f, y=out_col, points="outliers",
                           title=f"{out_col} 박스플롯"))

# ===== 데이터 표 =====
with st.expander("데이터 보기"):
    st.dataframe(f)
