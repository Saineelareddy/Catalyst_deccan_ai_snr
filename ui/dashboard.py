import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime

def render_results_dashboard(assessment_data: dict, plan) -> None:
    """
    Renders a cinematic, data-driven Mastery Intelligence Dashboard.
    Uses Plotly for high-fidelity charts and custom CSS for glassmorphism.
    """
    
    # 1. Inject Neural CSS
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap');
    
    .stApp {
        font-family: 'Outfit', sans-serif;
    }
    
    .neural-header {
        margin-bottom: 3rem;
        padding-top: 1rem;
    }
    
    .h1-neural {
        font-size: 3.5rem;
        font-weight: 800;
        background: linear-gradient(135deg, #f8fafc 30%, #94a3b8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        line-height: 1.1;
        margin-bottom: 0.5rem;
    }
    
    .blueprint-subtitle {
        color: #7c3aed;
        text-transform: uppercase;
        letter-spacing: 0.2rem;
        font-weight: 600;
        font-size: 0.9rem;
    }
    
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 1.5rem;
        padding: 2rem;
        margin-bottom: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        border-color: rgba(124, 58, 237, 0.3);
        background: rgba(30, 41, 59, 0.5);
    }
    
    .metric-val {
        font-size: 2.5rem;
        font-weight: 800;
        color: #f8fafc;
        line-height: 1;
    }
    
    .metric-lbl {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.1rem;
        color: #94a3b8;
        margin-top: 0.5rem;
    }
    
    .insight-box {
        border-left: 4px solid #7c3aed;
        background: rgba(124, 58, 237, 0.05);
        padding: 1.5rem;
        border-radius: 0 1rem 1rem 0;
        margin: 1rem 0;
    }
    
    .insight-title {
        color: #a78bfa;
        font-weight: 700;
        font-size: 0.8rem;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }
    
    /* Plotly Background Sync */
    .js-plotly-plot .plotly .bg {
        fill: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 2. Header Section
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown(f'<div class="blueprint-subtitle">NeuralHire // Mastery Intelligence Blueprint</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="h1-neural">{plan.candidate_name}</div>', unsafe_allow_html=True)
        st.markdown(f'<div style="color:#94a3b8; font-size:1.1rem;">Targeting <b>{plan.target_role}</b> readiness</div>', unsafe_allow_html=True)
    
    with col_h2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("📥 EXPORT INTELLIGENCE PDF", use_container_width=True, key="btn_export_pdf"):
             st.toast("Generating Neural Blueprint PDF...", icon="🧠")
    
    # 3. Intelligence Metrics Row
    st.markdown("<br>", unsafe_allow_html=True)
    m1, m2, m3, m4 = st.columns(4)
    
    readiness = round(sum(s.current_level for s in plan.skills) / sum(s.target_level for s in plan.skills) * 100) if plan.skills else 0
    gaps = sum(1 for s in plan.skills if s.category == "GAP")
    weeks = plan.total_weeks
    
    with m1:
        st.markdown(f'<div class="glass-card"><div class="metric-val">{readiness}%</div><div class="metric-lbl">Readiness Score</div></div>', unsafe_allow_html=True)
    with m2:
        st.markdown(f'<div class="glass-card"><div class="metric-val" style="color:#ef4444">{gaps}</div><div class="metric-lbl">Critical Gaps</div></div>', unsafe_allow_html=True)
    with m3:
        st.markdown(f'<div class="glass-card"><div class="metric-val" style="color:#7c3aed">{weeks}</div><div class="metric-lbl">Weeks to Mastery</div></div>', unsafe_allow_html=True)
    with m4:
        st.markdown(f'<div class="glass-card"><div class="metric-val" style="color:#22c55e">DNA</div><div class="metric-lbl">Neural Signature</div></div>', unsafe_allow_html=True)

    # 4. Competency Map (Radar) & Intelligence Synthesis
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.markdown('<div class="insight-title">◈ Competency Radar</div>', unsafe_allow_html=True)
        
        categories = [s.skill_name for s in plan.skills]
        actual = [s.current_level for s in plan.skills]
        target = [s.target_level for s in plan.skills]
        
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=actual, theta=categories, fill='toself', name='Current',
            line_color='#7c3aed', fillcolor='rgba(124, 58, 237, 0.3)'
        ))
        fig.add_trace(go.Scatterpolar(
            r=target, theta=categories, mode='lines', name='Target',
            line_color='rgba(248, 250, 252, 0.3)', line_dash='dash'
        ))
        
        fig.update_layout(
            polar=dict(
                bgcolor='rgba(0,0,0,0)',
                radialaxis=dict(visible=True, range=[0, 10], color='#64748b', gridcolor='rgba(255,255,255,0.05)'),
                angularaxis=dict(color='#94a3b8', gridcolor='rgba(255,255,255,0.05)')
            ),
            showlegend=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=30, b=30, l=30, r=30),
            height=400
        )
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    with c2:
        st.markdown('<div class="insight-title">◈ Intelligence Synthesis</div>', unsafe_allow_html=True)
        for s in plan.skills[:3]: # Show top 3 insights
            if s.category != "STRONG":
                st.markdown(f"""
                <div class="insight-box">
                    <div style="font-weight:600; color:#f8fafc; margin-bottom:5px;">{s.skill_name} Leverage</div>
                    <div style="color:#94a3b8; font-size:0.9rem;">{s.candidate_feedback}</div>
                </div>
                """, unsafe_allow_html=True)

    # 5. Mastery Timeline (Gantt)
    st.markdown('<div class="insight-title" style="margin-top:2rem;">◈ Mastery Timeline</div>', unsafe_allow_html=True)
    
    gantt_data = []
    current_start = 0
    for s in plan.skills:
        if s.total_weeks > 0:
            gantt_data.append({
                "Skill": s.skill_name,
                "Start": current_start,
                "End": current_start + s.total_weeks,
                "Duration": s.total_weeks,
                "Color": s.color
            })
            current_start += s.total_weeks
            
    if gantt_data:
        df = pd.DataFrame(gantt_data)
        fig_gantt = px.bar(
            df, x="Duration", y="Skill", base="Start",
            color="Color", color_discrete_map={"red": "#ef4444", "amber": "#f59e0b", "green": "#22c55e"},
            orientation='h'
        )
        fig_gantt.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(showgrid=False, zeroline=False, title="Weeks", color='#94a3b8'),
            yaxis=dict(showgrid=False, title="", color='#f8fafc'),
            showlegend=False,
            height=300,
            margin=dict(t=0, b=0, l=0, r=0)
        )
        st.plotly_chart(fig_gantt, use_container_width=True, config={'displayModeBar': False})

    # 6. Skill Breakdown Table
    st.markdown('<div class="insight-title" style="margin-top:2rem;">◈ Detailed Skill DNA</div>', unsafe_allow_html=True)
    
    # Table Header
    cols = st.columns([3, 1, 1, 2])
    cols[0].markdown("**Skill**")
    cols[1].markdown("**Level**")
    cols[2].markdown("**Gap**")
    cols[3].markdown("**Neural Status**")
    
    for s in plan.skills:
        scol = st.columns([3, 1, 1, 2])
        scol[0].markdown(f"**{s.skill_name}**")
        scol[1].markdown(f"{s.current_level}/10")
        gap = s.target_level - s.current_level
        scol[2].markdown(f"**{'+' if gap > 0 else ''}{gap}**", unsafe_allow_html=True)
        
        status_color = "#ef4444" if s.category == "GAP" else ("#f59e0b" if s.category == "DEVELOPING" else "#22c55e")
        scol[3].markdown(f'<span style="color:{status_color}; font-weight:700; font-size:0.8rem;">● {s.category}</span>', unsafe_allow_html=True)
        st.markdown('<div style="height:1px; background:rgba(255,255,255,0.05); margin:5px 0;"></div>', unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)
