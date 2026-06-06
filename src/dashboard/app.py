import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import snowflake.connector
import os
from dotenv import load_dotenv
from openai import OpenAI
import time

load_dotenv('../../config/.env')

st.set_page_config(
    page_title="Fraud Detection Command Center",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', sans-serif; }

    .stApp {
        background: #0d0d1a;
    }

    section[data-testid="stSidebar"] {
        background: #12122a !important;
        border-right: 1px solid #2d2d5e;
    }

    .main-header {
        background: linear-gradient(135deg, #1a1a3e 0%, #2d1b69 50%, #1a1a3e 100%);
        border: 1px solid #4a3f8a;
        border-radius: 16px;
        padding: 28px 36px;
        margin-bottom: 24px;
        position: relative;
        overflow: hidden;
    }

    .main-header::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: radial-gradient(circle, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
        animation: pulse 4s ease-in-out infinite;
    }

    .header-title {
        font-size: 28px;
        font-weight: 700;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.5px;
    }

    .header-subtitle {
        font-size: 13px;
        color: #8b7fc7;
        margin-top: 6px;
        letter-spacing: 0.5px;
    }

    .live-badge {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(34, 197, 94, 0.15);
        border: 1px solid rgba(34, 197, 94, 0.3);
        border-radius: 20px;
        padding: 4px 12px;
        font-size: 11px;
        font-weight: 600;
        color: #22c55e;
        letter-spacing: 1px;
        text-transform: uppercase;
    }

    .live-dot {
        width: 6px;
        height: 6px;
        background: #22c55e;
        border-radius: 50%;
        box-shadow: 0 0 8px #22c55e;
        animation: blink 1s infinite;
    }

    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.3; }
    }

    .kpi-card {
        background: linear-gradient(145deg, #1a1a3e, #1e1e4a);
        border: 1px solid #2d2d5e;
        border-radius: 14px;
        padding: 22px 24px;
        position: relative;
        overflow: hidden;
        transition: all 0.3s ease;
    }

    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 3px;
        border-radius: 14px 14px 0 0;
    }

    .kpi-blue::after { background: linear-gradient(90deg, #3b82f6, #60a5fa); }
    .kpi-red::after { background: linear-gradient(90deg, #ef4444, #f87171); }
    .kpi-purple::after { background: linear-gradient(90deg, #8b5cf6, #a78bfa); }
    .kpi-green::after { background: linear-gradient(90deg, #22c55e, #4ade80); }

    .kpi-label {
        font-size: 11px;
        font-weight: 600;
        color: #6b6b9a;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 10px;
    }

    .kpi-value {
        font-size: 32px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -1px;
        line-height: 1;
    }

    .kpi-delta {
        font-size: 12px;
        color: #6b6b9a;
        margin-top: 8px;
    }

    .kpi-icon {
        position: absolute;
        top: 20px;
        right: 20px;
        font-size: 28px;
        opacity: 0.15;
    }

    .section-header {
        font-size: 14px;
        font-weight: 600;
        color: #a89fd4;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
    }

    .section-header::after {
        content: '';
        flex: 1;
        height: 1px;
        background: linear-gradient(90deg, #2d2d5e, transparent);
    }

    .chart-container {
        background: linear-gradient(145deg, #1a1a3e, #1e1e4a);
        border: 1px solid #2d2d5e;
        border-radius: 14px;
        padding: 20px;
    }

    .alert-card {
        background: linear-gradient(135deg, #2d1a1a, #1f1525);
        border: 1px solid #5c2d2d;
        border-left: 4px solid #ef4444;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 10px;
        position: relative;
    }

    .alert-customer {
        font-size: 13px;
        font-weight: 600;
        color: #f8a5a5;
    }

    .alert-amount {
        font-size: 20px;
        font-weight: 700;
        color: #ffffff;
    }

    .alert-meta {
        font-size: 11px;
        color: #7a5a5a;
        margin-top: 4px;
    }

    .alert-score {
        position: absolute;
        top: 16px;
        right: 20px;
        background: rgba(239, 68, 68, 0.15);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 20px;
        padding: 3px 10px;
        font-size: 11px;
        font-weight: 600;
        color: #ef4444;
    }

    .alert-explanation {
        font-size: 12px;
        color: #c9a0a0;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid rgba(255,255,255,0.05);
        font-style: italic;
    }

    .ai-container {
        background: linear-gradient(145deg, #1a1a3e, #1e1552);
        border: 1px solid #3d2d7a;
        border-radius: 14px;
        padding: 24px;
    }

    .ai-response {
        background: linear-gradient(135deg, #1e2d1e, #1a2d3e);
        border: 1px solid #2d5c2d;
        border-left: 4px solid #22c55e;
        border-radius: 10px;
        padding: 16px 20px;
        font-size: 14px;
        color: #a0f0b0;
        line-height: 1.6;
    }

    .status-bar {
        background: #12122a;
        border: 1px solid #2d2d5e;
        border-radius: 10px;
        padding: 10px 20px;
        display: flex;
        gap: 24px;
        margin-bottom: 20px;
        font-size: 12px;
        color: #6b6b9a;
    }

    div[data-testid="stMetric"] {
        background: transparent !important;
    }

    .stButton button {
        background: linear-gradient(135deg, #6d28d9, #8b5cf6) !important;
        border: none !important;
        border-radius: 8px !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px !important;
        padding: 8px 20px !important;
        transition: all 0.3s ease !important;
    }

    .stButton button:hover {
        background: linear-gradient(135deg, #7c3aed, #9d70ff) !important;
        box-shadow: 0 4px 20px rgba(139, 92, 246, 0.4) !important;
        transform: translateY(-1px) !important;
    }

    .stTextArea textarea {
        background: #0d0d1a !important;
        border: 1px solid #2d2d5e !important;
        border-radius: 8px !important;
        color: #c4b9f0 !important;
        font-size: 13px !important;
    }

    .stSelectbox select, div[data-testid="stSelectbox"] {
        background: #1a1a3e !important;
    }

    hr { border-color: #2d2d5e !important; }

    .stSpinner { color: #8b5cf6 !important; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE')
    )

@st.cache_resource
def get_openai_client():
    return OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def run_query(query):
    try:
        conn = get_snowflake_connection()
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        data = cursor.fetchall()
        return pd.DataFrame(data, columns=columns)
    except Exception as e:
        return pd.DataFrame()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style='padding: 16px 0 8px 0;'>
        <div style='font-size:20px; font-weight:700; color:#c4b9f0;'>🛡️ FraudShield</div>
        <div style='font-size:11px; color:#6b6b9a; margin-top:4px;'>Command Center v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    st.markdown("<div style='font-size:11px; font-weight:600; color:#6b6b9a; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>⚙️ Settings</div>", unsafe_allow_html=True)

    auto_refresh = st.toggle("Live Mode", value=True)
    refresh_rate = st.slider("Refresh (seconds)", 5, 60, 15)

    st.divider()

    st.markdown("<div style='font-size:11px; font-weight:600; color:#6b6b9a; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>📅 Time Window</div>", unsafe_allow_html=True)

    time_window = st.selectbox("", [
        "Last 15 minutes",
        "Last 1 hour",
        "Last 6 hours",
        "All time"
    ], label_visibility="collapsed")

    st.divider()

    st.markdown("<div style='font-size:11px; font-weight:600; color:#6b6b9a; text-transform:uppercase; letter-spacing:1px; margin-bottom:12px;'>🤖 AI Assistant</div>", unsafe_allow_html=True)

    user_question = st.text_area(
        "",
        placeholder="Which merchant has the most fraud?\nWhat's the avg flagged amount?\nWhich location is highest risk?",
        height=120,
        label_visibility="collapsed"
    )
    ask_button = st.button("✨ Ask AI", use_container_width=True)

    st.divider()

    st.markdown("""
    <div style='font-size:11px; color:#4a4a7a; line-height:1.8;'>
        <div>⚡ Kafka Streaming</div>
        <div>🧠 Isolation Forest ML</div>
        <div>🤖 GPT-4o Mini</div>
        <div>❄️ Snowflake DWH</div>
        <div>📊 Real-time Analytics</div>
    </div>
    """, unsafe_allow_html=True)

# Time filter map
time_filters = {
    "Last 15 minutes": "DATEADD(minute, -15, CURRENT_TIMESTAMP())",
    "Last 1 hour": "DATEADD(hour, -1, CURRENT_TIMESTAMP())",
    "Last 6 hours": "DATEADD(hour, -6, CURRENT_TIMESTAMP())",
    "All time": "DATEADD(year, -10, CURRENT_TIMESTAMP())"
}
time_filter = time_filters[time_window]

# Main Header
st.markdown("""
<div class='main-header'>
    <div style='display:flex; justify-content:space-between; align-items:flex-start;'>
        <div>
            <div class='header-title'>🛡️ Real-Time Fraud Detection Command Center</div>
            <div class='header-subtitle'>Powered by Apache Kafka • Isolation Forest ML • GPT-4 • Snowflake • Python</div>
        </div>
        <div class='live-badge'>
            <div class='live-dot'></div>
            LIVE
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# KPI Cards
total_df = run_query(f"""
    SELECT COUNT(*) as total,
           SUM(CASE WHEN IS_ANOMALY = TRUE THEN 1 ELSE 0 END) as anomalies,
           AVG(AMOUNT) as avg_amount,
           SUM(AMOUNT) as total_amount
    FROM FRAUD_DETECTION.TRANSACTIONS.ALL_TRANSACTIONS
    WHERE INSERTED_AT >= {time_filter}
""")

total = int(total_df['TOTAL'].iloc[0] or 0) if not total_df.empty else 0
anomalies = int(total_df['ANOMALIES'].iloc[0] or 0) if not total_df.empty else 0
avg_amount = float(total_df['AVG_AMOUNT'].iloc[0] or 0) if not total_df.empty else 0
total_amount = float(total_df['TOTAL_AMOUNT'].iloc[0] or 0) if not total_df.empty else 0
anomaly_rate = (anomalies / total * 100) if total > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class='kpi-card kpi-blue'>
        <div class='kpi-icon'>⚡</div>
        <div class='kpi-label'>Total Transactions</div>
        <div class='kpi-value'>{total:,}</div>
        <div class='kpi-delta'>Streaming live from Kafka</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class='kpi-card kpi-red'>
        <div class='kpi-icon'>🚨</div>
        <div class='kpi-label'>Anomalies Detected</div>
        <div class='kpi-value'>{anomalies:,}</div>
        <div class='kpi-delta'>{anomaly_rate:.1f}% anomaly rate</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class='kpi-card kpi-purple'>
        <div class='kpi-icon'>💳</div>
        <div class='kpi-label'>Avg Transaction</div>
        <div class='kpi-value'>${avg_amount:,.0f}</div>
        <div class='kpi-delta'>Across all merchants</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class='kpi-card kpi-green'>
        <div class='kpi-icon'>💰</div>
        <div class='kpi-label'>Total Volume</div>
        <div class='kpi-value'>${total_amount:,.0f}</div>
        <div class='kpi-delta'>Monitored in real time</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Charts Row
col_left, col_right = st.columns([2, 1])

with col_left:
    st.markdown("<div class='section-header'>📈 Transaction Volume & Anomalies</div>", unsafe_allow_html=True)
    volume_df = run_query(f"""
        SELECT
            DATE_TRUNC('minute', INSERTED_AT) as minute,
            COUNT(*) as total,
            SUM(CASE WHEN IS_ANOMALY = TRUE THEN 1 ELSE 0 END) as anomalies
        FROM FRAUD_DETECTION.TRANSACTIONS.ALL_TRANSACTIONS
        WHERE INSERTED_AT >= {time_filter}
        GROUP BY 1 ORDER BY 1
    """)

    if not volume_df.empty:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=volume_df['MINUTE'], y=volume_df['TOTAL'],
            name='All Transactions', fill='tozeroy',
            line=dict(color='#7c3aed', width=2.5),
            fillcolor='rgba(124, 58, 237, 0.08)'
        ))
        fig.add_trace(go.Scatter(
            x=volume_df['MINUTE'], y=volume_df['ANOMALIES'],
            name='Anomalies', fill='tozeroy',
            line=dict(color='#ef4444', width=2.5),
            fillcolor='rgba(239, 68, 68, 0.15)'
        ))
        fig.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8b7fc7', size=11)
            ),
            xaxis=dict(gridcolor='#1e1e4a', color='#6b6b9a'),
            yaxis=dict(gridcolor='#1e1e4a', color='#6b6b9a'),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Waiting for data...")

with col_right:
    st.markdown("<div class='section-header'>🎯 Anomaly Rate</div>", unsafe_allow_html=True)
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=anomaly_rate,
        number={
            'suffix': '%',
            'font': {'size': 36, 'color': '#ffffff', 'family': 'Inter'}
        },
        gauge={
            'axis': {
                'range': [0, 20],
                'tickcolor': '#6b6b9a',
                'tickfont': {'color': '#6b6b9a', 'size': 10}
            },
            'bar': {'color': '#8b5cf6', 'thickness': 0.7},
            'bgcolor': 'rgba(0,0,0,0)',
            'borderwidth': 0,
            'steps': [
                {'range': [0, 5], 'color': 'rgba(34, 197, 94, 0.1)'},
                {'range': [5, 10], 'color': 'rgba(234, 179, 8, 0.1)'},
                {'range': [10, 20], 'color': 'rgba(239, 68, 68, 0.1)'}
            ],
            'threshold': {
                'line': {'color': '#ef4444', 'width': 3},
                'thickness': 0.8,
                'value': 5
            }
        }
    ))
    fig_gauge.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family='Inter', color='#8b7fc7'),
        height=280,
        margin=dict(l=20, r=20, t=20, b=10)
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Second Charts Row
col_b1, col_b2 = st.columns(2)

with col_b1:
    st.markdown("<div class='section-header'>🏪 Fraud by Merchant Category</div>", unsafe_allow_html=True)
    category_df = run_query(f"""
        SELECT MERCHANT_CATEGORY, COUNT(*) as count
        FROM FRAUD_DETECTION.TRANSACTIONS.ALL_TRANSACTIONS
        WHERE IS_ANOMALY = TRUE AND INSERTED_AT >= {time_filter}
        GROUP BY MERCHANT_CATEGORY ORDER BY count DESC
    """)

    if not category_df.empty:
        fig_bar = go.Figure(go.Bar(
            x=category_df['COUNT'],
            y=category_df['MERCHANT_CATEGORY'],
            orientation='h',
            marker=dict(
                color=category_df['COUNT'],
                colorscale=[[0, '#3d1a6e'], [0.5, '#7c3aed'], [1, '#a78bfa']],
                showscale=False
            )
        ))
        fig_bar.update_layout(
            template='plotly_dark',
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            xaxis=dict(gridcolor='#1e1e4a', color='#6b6b9a'),
            yaxis=dict(gridcolor='rgba(0,0,0,0)', color='#c4b9f0'),
            font=dict(family='Inter')
        )
        st.plotly_chart(fig_bar, use_container_width=True)

with col_b2:
    st.markdown("<div class='section-header'>🌍 Fraud by Location</div>", unsafe_allow_html=True)
    location_df = run_query(f"""
        SELECT LOCATION, COUNT(*) as count
        FROM FRAUD_DETECTION.TRANSACTIONS.ALL_TRANSACTIONS
        WHERE IS_ANOMALY = TRUE AND INSERTED_AT >= {time_filter}
        GROUP BY LOCATION ORDER BY count DESC LIMIT 8
    """)

    if not location_df.empty:
        fig_pie = go.Figure(go.Pie(
            labels=location_df['LOCATION'],
            values=location_df['COUNT'],
            hole=0.6,
            marker=dict(
                colors=['#6d28d9','#7c3aed','#8b5cf6','#9d70ff',
                       '#a78bfa','#b69dff','#c4b5fd','#ddd6fe']
            ),
            textfont=dict(color='#c4b9f0', size=11),
            hovertemplate='<b>%{label}</b><br>Anomalies: %{value}<extra></extra>'
        ))
        fig_pie.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Inter', color='#8b7fc7'),
            height=260,
            margin=dict(l=0, r=0, t=10, b=0),
            legend=dict(
                bgcolor='rgba(0,0,0,0)',
                font=dict(color='#8b7fc7', size=10)
            ),
            annotations=[dict(
                text=f'<b>{location_df["COUNT"].sum()}</b><br>flagged',
                x=0.5, y=0.5, font_size=14,
                font_color='#c4b9f0', showarrow=False
            )]
        )
        st.plotly_chart(fig_pie, use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# Live Alerts Feed
st.markdown("<div class='section-header'>🚨 Live Anomaly Alert Feed</div>", unsafe_allow_html=True)

flagged_df = run_query(f"""
    SELECT CUSTOMER_ID, AMOUNT, MERCHANT, MERCHANT_CATEGORY,
           LOCATION, ANOMALY_SCORE, AI_EXPLANATION, TIMESTAMP
    FROM FRAUD_DETECTION.TRANSACTIONS.FLAGGED_TRANSACTIONS
    WHERE INSERTED_AT >= {time_filter}
    ORDER BY INSERTED_AT DESC LIMIT 8
""")

if not flagged_df.empty:
    for _, row in flagged_df.iterrows():
        explanation = row['AI_EXPLANATION'] if row['AI_EXPLANATION'] else "Anomaly detected — manual review required."
        st.markdown(f"""
        <div class='alert-card'>
            <div class='alert-score'>Score: {row['ANOMALY_SCORE']:.4f}</div>
            <div class='alert-customer'>{row['CUSTOMER_ID']}</div>
            <div class='alert-amount'>${row['AMOUNT']:,.2f}</div>
            <div class='alert-meta'>
                🏪 {row['MERCHANT']} &nbsp;•&nbsp; 
                🏷️ {row['MERCHANT_CATEGORY']} &nbsp;•&nbsp; 
                📍 {row['LOCATION']} &nbsp;•&nbsp;
                🕐 {str(row['TIMESTAMP'])[:16]}
            </div>
            <div class='alert-explanation'>🤖 {explanation}</div>
        </div>
        """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style='background:#1a1a3e; border:1px solid #2d2d5e; border-radius:10px; 
                padding:24px; text-align:center; color:#6b6b9a; font-size:13px;'>
        No anomalies detected in this time window yet
    </div>
    """, unsafe_allow_html=True)

# AI Assistant Response
if ask_button and user_question:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<div class='section-header'>🤖 AI Assistant</div>", unsafe_allow_html=True)

    with st.spinner("Analyzing your fraud data..."):
        schema_info = """
        Tables in FRAUD_DETECTION.TRANSACTIONS:
        - ALL_TRANSACTIONS: TRANSACTION_ID, TIMESTAMP, AMOUNT, MERCHANT, MERCHANT_CATEGORY, LOCATION, CUSTOMER_ID, ANOMALY_SCORE, IS_ANOMALY, INSERTED_AT
        - FLAGGED_TRANSACTIONS: Same columns plus AI_EXPLANATION
        """
        client = get_openai_client()

        sql_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": f"""Generate a Snowflake SQL query for this question.
Schema: {schema_info}
Question: {user_question}
Return ONLY the SQL. No markdown. No explanation."""}],
            max_tokens=200
        )

        sql_query = sql_response.choices[0].message.content.strip()

        try:
            result_df = run_query(sql_query)
            insight_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": f"""Question: {user_question}
Data: {result_df.to_string()}
Give a 2-3 sentence business insight. Be specific with numbers."""}],
                max_tokens=200
            )
            insight = insight_response.choices[0].message.content.strip()
            st.markdown(f"""
            <div class='ai-response'>
                🤖 {insight}
            </div>
            """, unsafe_allow_html=True)
            if not result_df.empty:
                st.dataframe(
                    result_df,
                    use_container_width=True,
                    hide_index=True
                )
        except Exception as e:
            st.error(f"Query failed: {e}")

# Auto refresh
if auto_refresh:
    time.sleep(refresh_rate)
    st.rerun()