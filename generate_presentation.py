import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import os

def main():
    print("Generating interactive aviation safety presentation slide deck...")
    
    # Load data
    df = pd.read_csv("data/aviation_accidents_master.csv", low_memory=False)

    # Configure default Plotly templates for presentation (dark theme matches our slides)
    import plotly.io as pio
    pio.templates.default = "plotly_dark"

    # --- Generate Figures to embed ---
    
    # Fig 1: Annual frequency
    df_q1 = df[df['investigation_type'].isin(['Accident', 'Incident'])].groupby(['year', 'investigation_type'])['event_id'].count().reset_index()
    df_q1 = df_q1.rename(columns={'event_id': 'count'})
    fig1 = go.Figure()
    for t, col, w in [('Accident', '#ef4444', 3), ('Incident', '#38bdf8', 2)]:
        df_t = df_q1[df_q1['investigation_type'] == t]
        fig1.add_trace(go.Scatter(x=df_t['year'], y=df_t['count'], mode='lines+markers', name=t, line=dict(color=col, width=w), marker=dict(size=4)))
    fig1.update_layout(title="Global Aviation Accidents & Incidents (1982-2024)", xaxis_title="Year", yaxis_title="Reported Occurrences", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=60, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig1.update_xaxes(showgrid=False)
    fig1.update_yaxes(showgrid=True, gridcolor='#334155')
    html_fig1 = fig1.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})

    # Fig 2: Flight Phase
    df_q2 = df[df['broad_phase_of_flight'] != 'Unknown'].copy()
    df_q2_grouped = df_q2.groupby('broad_phase_of_flight').agg(
        occurrences=('event_id', 'count'),
        avg_fatality_rate=('fatality_rate', 'mean')
    ).reset_index().sort_values(by='occurrences', ascending=True)
    
    fig2 = make_subplots(rows=1, cols=2, shared_yaxes=True, subplot_titles=("Occurrences count", "Avg Fatality Rate"))
    fig2.add_trace(go.Bar(y=df_q2_grouped['broad_phase_of_flight'], x=df_q2_grouped['occurrences'], orientation='h', marker_color='#94a3b8', name='Occurrences'), row=1, col=1)
    
    colors_fatality = ['#888888'] * len(df_q2_grouped)
    try:
        cruise_pos = df_q2_grouped['broad_phase_of_flight'].tolist().index('Cruise')
        maneuver_pos = df_q2_grouped['broad_phase_of_flight'].tolist().index('Maneuvering')
        colors_fatality[cruise_pos] = '#38bdf8'
        colors_fatality[maneuver_pos] = '#ef4444'
    except Exception:
        pass
        
    fig2.add_trace(go.Bar(y=df_q2_grouped['broad_phase_of_flight'], x=df_q2_grouped['avg_fatality_rate'], orientation='h', marker_color=colors_fatality, name='Fatality Rate'), row=1, col=2)
    fig2.update_layout(title="Flight Phase Danger Profiles", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=40), showlegend=False)
    fig2.update_xaxes(showgrid=True, gridcolor='#334155')
    fig2.update_yaxes(showgrid=False)
    html_fig2 = fig2.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 3: Weather vs. Damage
    df_q3 = df[df['weather_condition'].isin(['VMC', 'IMC']) & df['aircraft_damage'].isin(['Destroyed', 'Substantial', 'Minor', 'Unknown'])].copy()
    df_q3_grouped = df_q3.groupby(['weather_condition', 'aircraft_damage'])['event_id'].count().reset_index()
    totals = df_q3.groupby('weather_condition')['event_id'].count().to_dict()
    df_q3_grouped['pct'] = df_q3_grouped.apply(lambda r: (r['event_id'] / totals[r['weather_condition']]) * 100, axis=1)
    
    fig3 = px.bar(df_q3_grouped, x='weather_condition', y='pct', color='aircraft_damage', color_discrete_map={'Destroyed': '#ef4444', 'Substantial': '#f97316', 'Minor': '#38bdf8', 'Unknown': '#94a3b8'})
    fig3.update_layout(title="Aircraft Damage Severity by Weather Condition", xaxis_title="Weather Condition", yaxis_title="Percentage (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=60), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    fig3.update_xaxes(showgrid=False)
    fig3.update_yaxes(showgrid=True, gridcolor='#334155')
    html_fig3 = fig3.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 4: Bubble chart
    valid_engines = ['Reciprocating', 'Turbo Fan', 'Turbo Jet', 'Turbo Prop', 'Turbo Shaft']
    df_q4 = df[df['engine_type'].isin(valid_engines)].copy()
    df_q4_grouped = df_q4.groupby('engine_type').agg(
        occurrences=('event_id', 'count'),
        avg_engines=('number_of_engines', 'mean'),
        avg_fatality_rate=('fatality_rate', 'mean')
    ).reset_index()
    fig4 = px.scatter(df_q4_grouped, x='avg_engines', y='avg_fatality_rate', size='occurrences', color='engine_type', text='engine_type', color_discrete_sequence=px.colors.qualitative.Safe, size_max=40)
    fig4.update_layout(title="Engine Type Safety & Redundancy Profile", xaxis_title="Average Number of Engines", yaxis_title="Average Fatality Rate", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=60), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    fig4.update_traces(textposition='top center')
    fig4.update_xaxes(showgrid=True, gridcolor='#334155')
    fig4.update_yaxes(showgrid=True, gridcolor='#334155')
    html_fig4 = fig4.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 5: Top Manufacturers
    df_q5_raw = df[(df['year'] >= 2000) & (df['make_cleaned'] != 'Unknown') & df['aircraft_damage'].isin(['Destroyed', 'Substantial', 'Minor', 'Unknown'])].copy()
    top_makes = df_q5_raw.groupby('make_cleaned')['event_id'].count().nlargest(10).index.tolist()
    df_q5_filtered = df_q5_raw[df_q5_raw['make_cleaned'].isin(top_makes)].copy()
    df_q5_grouped = df_q5_filtered.groupby(['make_cleaned', 'aircraft_damage'])['event_id'].count().reset_index()
    fig5 = px.bar(df_q5_grouped, x='make_cleaned', y='event_id', color='aircraft_damage', color_discrete_map={'Destroyed': '#ef4444', 'Substantial': '#f97316', 'Minor': '#38bdf8', 'Unknown': '#94a3b8'})
    fig5.update_layout(title="Incident Volume & Damage by Top 10 Manufacturers (since 2000)", xaxis_title="Manufacturer", yaxis_title="Incident Count", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=60), xaxis={'categoryorder':'total descending'}, legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    html_fig5 = fig5.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 6: US Choropleth
    us_states = df[(df['country'] == 'United States') & (df['state_or_region'].str.len() == 2)].copy()
    df_q6 = us_states.groupby('state_or_region')['event_id'].count().reset_index()
    fig6 = px.choropleth(df_q6, locations="state_or_region", color="event_id", locationmode="USA-states", scope="usa", color_continuous_scale="Oranges")
    fig6.update_layout(title="Reported Incidents by U.S. State (1982-2024)", paper_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=50, b=0))
    html_fig6 = fig6.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 7: Decade area chart
    df_q9 = df[df['aircraft_damage'].isin(['Destroyed', 'Substantial', 'Minor', 'Unknown'])].copy()
    df_q9['decade'] = (df_q9['year'] // 10) * 10
    df_q9_grouped = df_q9.groupby(['decade', 'aircraft_damage'])['event_id'].count().reset_index()
    df_q9_pivot = df_q9_grouped.pivot(index='decade', columns='aircraft_damage', values='event_id').fillna(0)
    df_q9_pct = df_q9_pivot.div(df_q9_pivot.sum(axis=1), axis=0) * 100
    df_q9_pct = df_q9_pct.reset_index()
    fig7 = go.Figure()
    fig7.add_trace(go.Scatter(x=df_q9_pct['decade'], y=df_q9_pct['Unknown'], name='Unknown', stackgroup='one', line=dict(color='#94a3b8')))
    fig7.add_trace(go.Scatter(x=df_q9_pct['decade'], y=df_q9_pct['Minor'], name='Minor', stackgroup='one', line=dict(color='#38bdf8')))
    fig7.add_trace(go.Scatter(x=df_q9_pct['decade'], y=df_q9_pct['Substantial'], name='Substantial', stackgroup='one', line=dict(color='#f97316')))
    fig7.add_trace(go.Scatter(x=df_q9_pct['decade'], y=df_q9_pct['Destroyed'], name='Destroyed', stackgroup='one', line=dict(color='#ef4444')))
    fig7.update_layout(title="Share of Aircraft Damage Severity by Decade (%)", xaxis_title="Decade", yaxis_title="Percentage (%)", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=50, b=60), legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5))
    fig7.update_xaxes(type='category', showgrid=False)
    fig7.update_yaxes(showgrid=True, gridcolor='#334155', range=[0, 100])
    html_fig7 = fig7.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Fig 8: Single vs Multi Engine
    df_q10 = df[df['number_of_engines'] > 0].copy()
    df_q10['engine_class'] = df_q10['number_of_engines'].apply(lambda x: 'Single-Engine' if x == 1 else 'Multi-Engine')
    df_q10_grouped = df_q10.groupby(['year', 'engine_class'])['fatality_rate'].mean().reset_index()
    fig8 = px.line(df_q10_grouped, x='year', y='fatality_rate', color='engine_class', color_discrete_map={'Single-Engine': '#ef4444', 'Multi-Engine': '#38bdf8'}, labels={'year': 'Year', 'fatality_rate': 'Average Fatality Rate', 'engine_class': 'Engine Class'})
    fig8.update_layout(title="Fatality Rate: Single-Engine vs. Multi-Engine Redundancy", paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=40, r=40, t=60, b=40), legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig8.update_xaxes(showgrid=False)
    fig8.update_yaxes(showgrid=True, gridcolor='#334155')
    html_fig8 = fig8.to_html(full_html=False, include_plotlyjs='none', config={'responsive': True})

    # Assemble HTML Slides
    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Aviation Accidents & Flight Safety Storyboard</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
        
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Outfit', sans-serif;
            overflow-x: hidden;
        }}
        
        .slide-container {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100vw;
        }}
        
        .slide {{
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            border-bottom: 2px solid #334155;
            width: 100%;
            height: 100vh;
            padding: 40px 60px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
        }}
        
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            padding-bottom: 15px;
        }}
        
        .title {{
            font-size: 32px;
            font-weight: 800;
            background: linear-gradient(to right, #38bdf8, #f97316);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }}
        
        .subtitle {{
            font-size: 16px;
            color: #94a3b8;
            margin-top: 5px;
        }}
        
        .content {{
            display: flex;
            flex: 1;
            margin-top: 20px;
            gap: 40px;
            align-items: center;
        }}
        
        .chart-box {{
            flex: 3.5;
            height: 100%;
            border-radius: 12px;
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(255,255,255,0.05);
            padding: 10px;
            min-height: 400px;
            min-width: 0;
            overflow: hidden;
        }}
        
        .text-box {{
            flex: 1.5;
            display: flex;
            flex-direction: column;
            gap: 15px;
            min-width: 0;
        }}

        .main-svg {{
            width: 100% !important;
            max-width: 100% !important;
        }}
        
        .bullet-point {{
            background: rgba(255, 255, 255, 0.03);
            border-left: 4px solid #f97316;
            padding: 15px;
            border-radius: 4px;
            font-size: 16px;
            line-height: 1.5;
        }}
        
        .bullet-blue {{
            border-left-color: #38bdf8;
        }}
        
        .footer {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: #64748b;
            font-size: 14px;
            margin-top: 15px;
        }}
        
        .slide-title-only {{
            justify-content: center;
            align-items: center;
            text-align: center;
        }}
        
        .big-title {{
            font-size: 54px;
            font-weight: 800;
            margin-bottom: 20px;
        }}
        
        .author-box {{
            font-size: 20px;
            color: #94a3b8;
            margin-top: 30px;
        }}
        
        @media print {{
            @page {{
                size: landscape;
                margin: 0;
            }}
            .slide {{
                height: 100vh;
                page-break-after: always;
                border: none;
            }}
            body {{
                background-color: #0f172a;
            }}
        }}
    </style>
</head>
<body>
    <div class="slide-container">
        
        <!-- SLIDE 1: TITLE SLIDE -->
        <div class="slide slide-title-only">
            <h1 class="big-title" style="background: linear-gradient(to right, #38bdf8, #f97316); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Aviation Accidents &<br>Flight Safety Intelligence</h1>
            <p style="font-size:22px; max-width:800px; margin: 0 auto; line-height:1.6; opacity:0.8;">An explanatory data story detailing U.S. and global flight safety metrics, structural durability, weather impact, and mechanical engineering redundancy (1982-2026)</p>
            <div class="author-box">
                Mohammed Abrar &bull; Matriculation No.: 97193111 &bull; Data Science, M.Sc. 120b
            </div>
        </div>
        

        <!-- SLIDE 3: PROJECT OVERVIEW -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Project Overview & Data Sourcing</h2>
                    <div class="subtitle">Investigating civil flight safety using national databases</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 2 of 12</div>
            </div>
            <div class="content">
                <div class="text-box" style="flex:1;">
                    <div class="bullet-point">
                        <strong>The Goal:</strong> To determine flight safety risks across various aircraft dimensions, assessing weather hazards, engine types, and structural integrity parameters.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Authoritative Dataset:</strong> Sourced directly from the <strong>U.S. National Transportation Safety Board (NTSB)</strong> logs (1982-2026), containing over 87,000 observations.
                    </div>
                </div>
                <div class="text-box" style="flex:1;">
                    <div class="bullet-point">
                        <strong>Engineering Attributes:</strong> Engine types, passenger counts, coordinates, weather rules (VMC/IMC), flight phases, and structural damage classes.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Tidy Reshaping:</strong> Deluxe cleaning pipeline resolved coordinate DMS strings and grouped spelling variations for manufacturers (e.g. Cessna, Boeing).
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Visualization Summer 2026</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 3: ACCIDENTS TREND -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Accidents Continue to Decline</h2>
                    <div class="subtitle">Annual occurrence trends since 1982 (Q1 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 3 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig1}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>Engineering Triumphs:</strong> Global accidents have dropped consistently, highlighting successes in avionics, flight-envelope protections, and pilot training systems.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Incident Volatility:</strong> Minor "Incidents" show a flatter trend, likely due to more stringent logging guidelines over time.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 4: FLIGHT PHASE -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Flight Phase Risk Profiles</h2>
                    <div class="subtitle">When do incidents happen, and when are they fatal? (Q2 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 4 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig2}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>High-Activity Exposure:</strong> Landing and Takeoff constitute the absolute majority of incidents because they involve close proximity to the ground and high pilot workload.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Cruise Lethality:</strong> Cruise and Maneuvering are statistically the most lethal phases; an emergency in these envelopes often involves higher speeds and altitudes, resulting in greater impact velocities.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 5: WEATHER IMPACT -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Instrument Weather Multiplies Damage</h2>
                    <div class="subtitle">Weather conditions vs. aircraft hull loss (Q3 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 5 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig3}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>IMC Hazards:</strong> Low-visibility Instrument Meteorological Conditions (IMC) lead to completely "Destroyed" aircraft in nearly 50% of incident records.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>VMC Safety:</strong> Under Visual Conditions (VMC), pilots maintain a visual reference with the horizon, resulting in a much higher rate of minor or substantial (non-fatal) damage profiles.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 6: ENGINE TYPE RELIABILITY -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Engine Configurations & Fatality</h2>
                    <div class="subtitle">Engine architectures and passenger safety (Q4 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 6 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig4}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>Reciprocating Props:</strong> Carry the highest average fatality rates, as they are typically fitted to single-engine recreational light aircraft without backup systems.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Commercial Jets:</strong> Turbofan/Turbojet engines have the lowest average fatality rates due to multi-engine redundancies and rigorous commercial airline maintenance logs.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 7: MANUFACTURERS -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Incident Volumes by Manufacturer</h2>
                    <div class="subtitle">Top 10 brands and their aircraft damage records (Q5 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 7 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig5}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>General Aviation Exposure:</strong> Cessna and Piper dominate absolute volume due to their vast fleet presence in flight training schools and recreational operations.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Commercial Builders:</strong> Boeing shows a lower incident footprint in terms of major hull damage, reflecting commercial airline fleet oversight.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 8: U.S. MAP -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">United States Incident Hotspots</h2>
                    <div class="subtitle">State-level incident distribution map (Q6 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 8 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig6}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>The High-Traffic States:</strong> California, Texas, and Florida host the most incidents. This correlates directly with high general aviation traffic and private pilot certifications.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Training Hubs:</strong> These states feature favorable weather year-round, making them hubs for private pilot academies.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 9: DECADES STRUCTURAL IMPROVEMENT -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Structural Integrity Progress</h2>
                    <div class="subtitle">Hull loss rates by decade (Q9 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 9 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig7}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>Halving Hull Loss:</strong> The percentage of crashes resulting in a "Destroyed" aircraft has shrunk consistently from the 1980s to the 2020s.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Resilient Cabins:</strong> Improvements in composite materials, cabin structural cages, and landing gear energy absorption have dramatically increased crash survival rates.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 10: ENGINE REDUNDANCY SAFETY -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">The Power of Engine Redundancy</h2>
                    <div class="subtitle">Single-Engine vs. Multi-Engine fatality trends (Q10 Analysis)</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 10 of 12</div>
            </div>
            <div class="content">
                <div class="chart-box">
                    {html_fig8}
                </div>
                <div class="text-box">
                    <div class="bullet-point">
                        <strong>Redundancy Decouples Failure:</strong> Multi-engine planes have a fatality rate that is consistently lower than single-engine planes.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>The backup engine:</strong> If one engine fails on a twin-engine jet, the aircraft can safely fly to an emergency airport using the remaining engine.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Source: NTSB Database</span>
                <span>Final Individual Project</span>
            </div>
        </div>

        <!-- SLIDE 11: CONCLUSIONS -->
        <div class="slide slide-title-only">
            <h2 class="title" style="font-size:42px;">Conclusions & Takeaways</h2>
            <div style="max-width:900px; margin: 40px auto; text-align: left; display:flex; flex-direction:column; gap:20px;">
                <div class="bullet-point">
                    <strong>1. Engineering saves lives:</strong> Decades of updates to aircraft hulls, fire retardant cabin interiors, and engine failure redundancy have made flying progressively safer.
                </div>
                <div class="bullet-point bullet-blue">
                    <strong>2. General Aviation needs focus:</strong> Cessna/Piper single-engine prop aircraft represent the largest share of accidents and fatality rates, indicating a need for better pilot warnings and automation in light aircraft.
                </div>
                <div class="bullet-point">
                    <strong>3. Weather risk remains constant:</strong> Instrument weather (IMC) continues to multiply aircraft damage, proving that low visibility is the biggest threat to manual flight operations.
                </div>
            </div>
            <div class="footer" style="width:100%; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; margin-top:0;">
                <span>Mohammed Abrar &bull; Matriculation No.: 97193111 &bull; Data Science, M.Sc. 120b</span>
                <span>Thank You</span>
            </div>
        </div>

        <!-- SLIDE 12: QUICK START & NAVIGATION GUIDE -->
        <div class="slide">
            <div class="header">
                <div>
                    <h2 class="title">Quick Start & Navigation Guide</h2>
                    <div class="subtitle">Instructions for professors, reviewers, and developers</div>
                </div>
                <div style="font-size:14px; color:#64748b;">Slide 12 of 12</div>
            </div>
            <div class="content" style="display:grid; grid-template-columns: 1fr 1fr; gap:30px; align-items: stretch; margin-top:20px;">
                <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.05); padding: 25px; border-radius: 12px; display:flex; flex-direction:column; gap:15px; min-width: 0;">
                    <h3 style="margin:0 0 10px 0; color:#38bdf8; font-size:20px; font-weight:600; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">🖥️ How to Run the Project</h3>
                    <div class="bullet-point">
                        <strong>Streamlit Dashboard:</strong> Run <code>.venv/bin/python3 -m streamlit run app.py</code> to launch the interactive app.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Jupyter Notebook:</strong> Open <code>analysis.ipynb</code> inside Anaconda or Jupyter to see the full code and data query outputs.
                    </div>
                    <div class="bullet-point">
                        <strong>Re-run Pipeline:</strong> Execute <code>python download_and_clean.py</code> to download and rebuild the datasets.
                    </div>
                </div>
                <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255,255,255,0.05); padding: 25px; border-radius: 12px; display:flex; flex-direction:column; gap:15px; min-width: 0;">
                    <h3 style="margin:0 0 10px 0; color:#f97316; font-size:20px; font-weight:600; border-bottom:1px solid rgba(255,255,255,0.1); padding-bottom:8px;">📊 Presentation Navigation</h3>
                    <div class="bullet-point bullet-blue">
                        <strong>Widescreen Scrolling:</strong> Scroll vertically to browse through the 12 slides. Each slide is sized to fit exactly 100vh.
                    </div>
                    <div class="bullet-point">
                        <strong>Interactive Charts:</strong> All charts in this deck are live Plotly graphs. Hover to see exact counts, drag to zoom, and double-click to reset.
                    </div>
                    <div class="bullet-point bullet-blue">
                        <strong>Print to PDF:</strong> Press <code>Cmd/Ctrl + P</code>, select <strong>Landscape</strong>, set <strong>Margins: None</strong>, enable <strong>Background graphics</strong> to generate a clean PDF deck.
                    </div>
                </div>
            </div>
            <div class="footer">
                <span>Data Science, M.Sc. 120b</span>
                <span>Final Individual Project</span>
            </div>
        </div>

    </div>
</body>
</html>
"""
    
    # Save presentation HTML
    output_path = "presentation.html"
    with open(output_path, "w") as f:
        f.write(html_content)
        
    print(f"Interactive presentation slide deck successfully saved to {output_path}!")

if __name__ == "__main__":
    main()
