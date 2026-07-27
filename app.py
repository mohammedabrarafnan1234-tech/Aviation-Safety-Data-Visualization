# pyrefly: ignore [missing-import]
import streamlit as st
import pandas as pd
# pyrefly: ignore [missing-import]
import numpy as np
# pyrefly: ignore [missing-import]
import plotly.express as px
# pyrefly: ignore [missing-import]
import plotly.graph_objects as go
# pyrefly: ignore [missing-import]
from plotly.subplots import make_subplots
import ssl

# Bypass SSL certificate verification for macOS
ssl._create_default_https_context = ssl._create_unverified_context

# ----------------------------------------------------
# 1. Page Configuration & Theme Setup
# ----------------------------------------------------
st.set_page_config(
    page_title="Aviation Accidents & Flight Safety Dashboard",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject custom premium CSS for aesthetics (Outfit font, gradient cards, subtle transitions)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
html, body, [class*="css"] {
    font-family: 'Outfit', sans-serif;
}
.main-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    padding: 30px;
    border-radius: 16px;
    color: white;
    margin-bottom: 25px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.05);
}
.card {
    background-color: #ffffff;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.02);
    border: 1px solid #f1f5f9;
    margin-bottom: 20px;
}
.metric-card {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.05);
    color: white;
    text-align: center;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
}
.metric-title {
    font-size: 13px;
    color: #94a3b8;
    text-transform: uppercase;
    font-weight: 600;
    letter-spacing: 0.05em;
}
.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #38bdf8; /* light blue */
    margin-top: 5px;
}
.metric-value-damage {
    font-size: 28px;
    font-weight: 800;
    color: #f97316; /* orange */
    margin-top: 5px;
}
.metric-value-deaths {
    font-size: 28px;
    font-weight: 800;
    color: #ef4444; /* red */
    margin-top: 5px;
}
.metric-subtitle {
    font-size: 11px;
    color: #64748b;
    margin-top: 5px;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Data Loading & Caching
# ----------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv("data/aviation_accidents_master.csv", low_memory=False)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Error loading data: {e}. Please ensure data is preprocessed.")
    st.stop()

# ----------------------------------------------------
# 3. Sidebar Filtering (Global Settings)
# ----------------------------------------------------
st.sidebar.markdown("## ⚙️ Filter Settings")

# Year Range Slider
min_year = int(df['year'].min())
max_year = int(df['year'].max())
year_range = st.sidebar.slider(
    "Select Year Range",
    min_value=min_year,
    max_value=max_year,
    value=(2000, max_year),
    step=1
)

# Weather Condition Multiselect
weather_options = sorted(df['weather_condition'].unique())
selected_weather = st.sidebar.multiselect(
    "Weather Condition",
    options=weather_options,
    default=weather_options
)

# Aircraft Category Multiselect
aircraft_options = sorted([c for c in df['aircraft_category'].unique() if str(c) != 'Unknown'])
selected_categories = st.sidebar.multiselect(
    "Aircraft Category",
    options=aircraft_options,
    default=['Airplane', 'Helicopter']
)

# Engine Count Slider
engine_max = int(df['number_of_engines'].max())
selected_engines = st.sidebar.slider(
    "Minimum Number of Engines",
    min_value=1,
    max_value=engine_max,
    value=1
)

# Apply filters
df_filtered = df[
    (df['year'] >= year_range[0]) & 
    (df['year'] <= year_range[1]) & 
    (df['number_of_engines'] >= selected_engines)
]

if selected_weather:
    df_filtered = df_filtered[df_filtered['weather_condition'].isin(selected_weather)]
if selected_categories:
    df_filtered = df_filtered[df_filtered['aircraft_category'].isin(selected_categories)]

# ----------------------------------------------------
# 4. Main Header
# ----------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-weight:800; font-size:32px;">✈️ NTSB Aviation Accidents & Safety Intelligence</h1>
    <p style="margin:5px 0 0 0; font-size:16px; opacity:0.85;">An interactive dashboard analyzing historical flight crash frequencies, fatalities, weather correlations, and engineering reliability</p>
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 5. Dashboard Metrics (KPIs)
# ----------------------------------------------------
total_incidents = len(df_filtered)
total_fatalities = df_filtered['total_fatal_injuries'].sum()
total_uninjured = df_filtered['total_uninjured'].sum()
total_on_board = df_filtered['total_on_board'].sum()

survival_rate = (total_uninjured / total_on_board * 100) if total_on_board > 0 else 100.0
destroyed_count = len(df_filtered[df_filtered['aircraft_damage'] == 'Destroyed'])
destroyed_rate = (destroyed_count / total_incidents * 100) if total_incidents > 0 else 0.0

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Reported Incidents</div>
        <div class="metric-value">{total_incidents:,}</div>
        <div class="metric-subtitle">Filtered event occurrences</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Total Fatalities</div>
        <div class="metric-value-deaths">{int(total_fatalities):,}</div>
        <div class="metric-subtitle">Reported crash deaths</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Survival Rate</div>
        <div class="metric-value" style="color: #10b981;">{survival_rate:,.1f}%</div>
        <div class="metric-subtitle">Uninjured / total passengers on board</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">Hull Loss Rate (Destroyed)</div>
        <div class="metric-value-damage">{destroyed_rate:,.1f}%</div>
        <div class="metric-subtitle">Aircraft completely destroyed</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ----------------------------------------------------
# 6. Tabbed Navigation Layout
# ----------------------------------------------------
tab1, tab2, tab3 = st.tabs([
    "📈 Safety Trends Over Time", 
    "🗺️ Geographic Hotspots Map", 
    "🛠️ Engineering & Weather Factors"
])

# ----------------------------------------------------
# TAB 1: Safety Trends Over Time
# ----------------------------------------------------
with tab1:
    col1_1, col1_2 = st.columns(2)
    
    with col1_1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Annual Occurrences by Investigation Type")
        
        df_q1 = df_filtered[df_filtered['investigation_type'].isin(['Accident', 'Incident'])].groupby(['year', 'investigation_type'])['event_id'].count().reset_index()
        df_q1 = df_q1.rename(columns={'event_id': 'count'})
        
        fig1 = px.line(
            df_q1, x='year', y='count', color='investigation_type',
            color_discrete_map={'Accident': '#ef4444', 'Incident': '#38bdf8'},
            labels={'year': 'Year', 'count': 'Event Count', 'investigation_type': 'Type'}
        )
        fig1.update_layout(
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig1.update_xaxes(showgrid=False)
        fig1.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
        st.plotly_chart(fig1, width="stretch")
        st.markdown("<p style='font-size:12px; color:#64748b;'>Insight: General accidents have been declining globally, reflecting the steady integration of modern autopilot systems, ground collision warnings, and mechanical redundancy.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col1_2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Single-Engine vs. Multi-Engine Fatality Rate")
        
        df_q10 = df_filtered[df_filtered['number_of_engines'] > 0].copy()
        df_q10['engine_class'] = df_q10['number_of_engines'].apply(lambda x: 'Single-Engine' if x == 1 else 'Multi-Engine')
        df_q10_grouped = df_q10.groupby(['year', 'engine_class'])['fatality_rate'].mean().reset_index()
        
        fig10 = px.line(
            df_q10_grouped, x='year', y='fatality_rate', color='engine_class',
            color_discrete_map={'Single-Engine': '#ef4444', 'Multi-Engine': '#2b5c8f'},
            labels={'year': 'Year', 'fatality_rate': 'Average Fatality Rate', 'engine_class': 'Engine Class'}
        )
        fig10.update_layout(
            template="plotly_white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        fig10.update_xaxes(showgrid=False)
        fig10.update_yaxes(showgrid=True, gridcolor='#f1f5f9')
        st.plotly_chart(fig10, width="stretch")
        st.markdown("<p style='font-size:12px; color:#64748b;'>Insight: Multi-engine aircraft offer double the thrust security. If one engine fails, pilots can usually maintain control, explaining the significantly lower fatality rate compared to single-engine planes.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 2: Geographic Hotspots Map
# ----------------------------------------------------
with tab2:
    col2_1, col2_2 = st.columns([3, 2])
    
    with col2_1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Global Incident Coordinate Scatter Map")
        
        # Sample coordinates for performance
        df_coords = df_filtered[df_filtered['latitude'].notna() & df_filtered['longitude'].notna() & (df_filtered['latitude'] != 0)].copy()
        sample_size = min(len(df_coords), 3000)
        df_sample = df_coords.sample(n=sample_size, random_state=42) if sample_size > 0 else df_coords
        
        if len(df_sample) > 0:
            fig7 = px.scatter_geo(
                df_sample,
                lat="latitude",
                lon="longitude",
                color="weather_condition",
                hover_name="location",
                color_discrete_map={'VMC': '#38bdf8', 'IMC': '#ef4444', 'Unknown': '#94a3b8'}
            )
            fig7.update_layout(
                template="plotly_white",
                margin=dict(l=0, r=0, t=10, b=0),
                coloraxis_showscale=False,
                geo=dict(showland=True, landcolor="#f8fafc", oceancolor="#ffffff", showocean=True, showcountries=True)
            )
            st.plotly_chart(fig7, width="stretch")
        else:
            st.warning("No incidents with valid coordinates found in the selected range.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col2_2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Incident Volume by U.S. State")
        
        us_states = df_filtered[(df_filtered['country'] == 'United States') & (df_filtered['state_or_region'].str.len() == 2)].copy()
        df_states_grouped = us_states.groupby('state_or_region')['event_id'].count().reset_index()
        
        if len(df_states_grouped) > 0:
            fig6 = px.choropleth(
                df_states_grouped,
                locations="state_or_region",
                color="event_id",
                locationmode="USA-states",
                scope="usa",
                color_continuous_scale="Oranges"
            )
            fig6.update_layout(
                template="plotly_white",
                margin=dict(l=0, r=0, t=10, b=0)
            )
            st.plotly_chart(fig6, width="stretch")
        else:
            st.warning("No U.S. incidents found in the selected filter settings.")
        st.markdown("<p style='font-size:12px; color:#64748b;'>Insight: California, Texas, and Florida stand out as flight safety hotspots due to high densities of flight training schools, general aviation fields, and high traffic routes.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# ----------------------------------------------------
# TAB 3: Engineering & Weather Factors
# ----------------------------------------------------
with tab3:
    col3_1, col3_2 = st.columns(2)
    
    with col3_1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Engine Type Safety & Redundancy Profile")
        
        valid_engines = ['Reciprocating', 'Turbo Fan', 'Turbo Jet', 'Turbo Prop', 'Turbo Shaft']
        df_q4 = df_filtered[df_filtered['engine_type'].isin(valid_engines)].copy()
        df_q4_grouped = df_q4.groupby('engine_type').agg(
            occurrences=('event_id', 'count'),
            avg_engines=('number_of_engines', 'mean'),
            avg_fatality_rate=('fatality_rate', 'mean')
        ).reset_index()
        
        if len(df_q4_grouped) > 0:
            fig4 = px.scatter(
                df_q4_grouped, x='avg_engines', y='avg_fatality_rate', size='occurrences',
                color='engine_type', text='engine_type',
                color_discrete_sequence=px.colors.qualitative.Safe,
                size_max=40
            )
            fig4.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=10, b=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            fig4.update_traces(textposition='top center')
            st.plotly_chart(fig4, width="stretch")
        else:
            st.warning("No valid engine types found for current filters.")
        st.markdown("<p style='font-size:12px; color:#64748b;'>Insight: Reciprocating engines (small private props) statistically carry the highest fatality rate, reflecting their single-engine architecture and recreational flying risks.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col3_2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Flight Phase Occurrences and Fatality Rate")
        
        df_q2 = df_filtered[df_filtered['broad_phase_of_flight'] != 'Unknown'].copy()
        df_q2_grouped = df_q2.groupby('broad_phase_of_flight').agg(
            occurrences=('event_id', 'count'),
            avg_fatality_rate=('fatality_rate', 'mean')
        ).reset_index().sort_values(by='occurrences', ascending=True)
        
        if len(df_q2_grouped) > 0:
            fig2 = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("Occurrences count", "Avg Fatality Rate"))
            fig2.add_trace(
                go.Bar(y=df_q2_grouped['broad_phase_of_flight'], x=df_q2_grouped['occurrences'], orientation='h', marker_color='#94a3b8', name='Count'),
                row=1, col=1
            )
            fig2.add_trace(
                go.Bar(y=df_q2_grouped['broad_phase_of_flight'], x=df_q2_grouped['avg_fatality_rate'], orientation='h', marker_color='#ef4444', name='Fatality Rate'),
                row=1, col=2
            )
            fig2.update_layout(
                template="plotly_white",
                margin=dict(l=10, r=10, t=40, b=10),
                showlegend=False
            )
            fig2.update_xaxes(showgrid=True, gridcolor='#f1f5f9')
            st.plotly_chart(fig2, width="stretch")
        else:
            st.warning("No flight phase data available for current filters.")
        st.markdown("<p style='font-size:12px; color:#64748b;'>Insight: Landing and Takeoff are highly active phases where errors happen frequently, but Cruise and Maneuvering are the most fatal if a failure occurs.</p>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
