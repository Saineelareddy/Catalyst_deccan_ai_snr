import streamlit as st
import os
import time
from dotenv import load_dotenv

# Ensure we load env before imports
load_dotenv()

from utils.document_parser import extract_text_from_file
from agents.parser_agent import ParserAgent
from agents.skill_extractor import SkillExtractorAgent
from agents.assessment_agent import AssessmentAgent
from agents.scoring_agent import ScoringAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.learning_plan_agent import LearningPlanAgent
from ui.dashboard import render_results_dashboard
from ui.processing import render_processing_screen
from datetime import datetime

# Load custom CSS
def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

local_css("ui/style.css")

# Initialize agents
def get_agents():
    return {
        "parser": ParserAgent(),
        "extractor": SkillExtractorAgent(),
        "assessor": AssessmentAgent(),
        "scorer": ScoringAgent(),
        "analyzer": GapAnalysisAgent(),
        "planner": LearningPlanAgent()
    }

agents = get_agents()

st.set_page_config(page_title="AI Skill Assessment", layout="wide")
st.title("AI-Powered Skill Assessment & Learning Plan")

# State Management
if "setup_complete" not in st.session_state:
    st.session_state.setup_complete = False
if "jd_skills" not in st.session_state:
    st.session_state.jd_skills = []
if "parsed_resume" not in st.session_state:
    st.session_state.parsed_resume = None
if "current_skill_index" not in st.session_state:
    st.session_state.current_skill_index = 0
if "chat_history" not in st.session_state:
    st.session_state.chat_history = {}
if "actual_scores" not in st.session_state:
    st.session_state.actual_scores = []
if "assessment_complete" not in st.session_state:
    st.session_state.assessment_complete = False
if "processing_phase" not in st.session_state:
    st.session_state.processing_phase = None
if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "learning_plan" not in st.session_state:
    st.session_state.learning_plan = None

# Stepper Renderer
def render_stepper():
    steps = ["Setup", "Assessment", "Results & Roadmap"]
    current = min(st.session_state.current_step, len(steps) - 1)
    progress_width = (current / (len(steps) - 1)) * 100
    
    # Inline critical styles to ensure it renders as a bar immediately
    stepper_html = f"""
    <style>
        .stepper-container {{ display: flex; justify-content: space-between; align-items: center; position: relative; max-width: 800px; margin: 10px auto; font-family: sans-serif; }}
        .stepper-line {{ position: absolute; top: 40%; left: 0; right: 0; height: 4px; background: #334155; z-index: 1; transform: translateY(-50%); }}
        .stepper-line-progress {{ position: absolute; top: 40%; left: 0; height: 4px; background: #7c3aed; z-index: 2; transform: translateY(-50%); transition: width 0.5s ease; }}
        .step {{ width: 35px; height: 35px; border-radius: 50%; background: #1e293b; border: 3px solid #334155; display: flex; justify-content: center; align-items: center; z-index: 3; font-weight: bold; color: #94a3b8; position: relative; transition: all 0.3s; }}
        .step.active {{ background: #7c3aed; border-color: #a78bfa; color: white; box-shadow: 0 0 15px #7c3aed; transform: scale(1.1); }}
        .step.completed {{ background: #7c3aed; border-color: #7c3aed; color: white; }}
        .step-label {{ position: absolute; top: 45px; white-space: nowrap; font-size: 0.8rem; color: #94a3b8; text-align: center; width: 100px; left: 50%; transform: translateX(-50%); }}
        .step.active .step-label {{ color: #f8fafc; font-weight: bold; }}
    </style>
    <div class="stepper-container">
        <div class="stepper-line"></div>
        <div class="stepper-line-progress" style="width: {progress_width}%;"></div>
    """
    for i, label in enumerate(steps):
        status = "active" if i == current else ("completed" if i < current else "")
        stepper_html += f'<div class="step {status}">{i+1}<div class="step-label">{label}</div></div>'
    
    stepper_html += "</div>"
    st.components.v1.html(stepper_html, height=100)

render_stepper()

# --- PROCESSING OVERLAY HANDLER ---
if st.session_state.processing_phase:
    phase = st.session_state.processing_phase
    render_processing_screen(phase, estimated_seconds=15)
    
    # Perform the actual work while the gears spin
    if phase == "setup_to_assessment":
        # 1. Parse Resume & Skills
        st.session_state.parsed_resume = agents["parser"].parse_resume(st.session_state.temp_resume_text)
        st.session_state.jd_skills = agents["extractor"].extract_skills(st.session_state.temp_jd_text).skills
        
        # 2. Init Chat
        st.session_state.chat_history = {}
        for skill in st.session_state.jd_skills:
            st.session_state.chat_history[skill.skill_name] = []
        
        st.session_state.setup_complete = True
        st.session_state.current_skill_index = 0
        st.session_state.actual_scores = []
        st.session_state.assessment_complete = False
        
        time.sleep(1) # Small buffer
        st.session_state.processing_phase = None
        st.session_state.current_step = 1
        st.rerun()
        
    elif phase == "assessment_to_plan":
        # Final Scoring & Planning
        gaps = agents["analyzer"].analyze_gaps(st.session_state.jd_skills, st.session_state.actual_scores)
        name = getattr(st.session_state.parsed_resume, "name", "Candidate") or "Candidate"
        
        # Parallel Racing in background
        import asyncio
        st.session_state.learning_plan = asyncio.run(agents["planner"].agenerate_plan(gaps, candidate_name=name))
        
        time.sleep(1) # Small buffer
        st.session_state.processing_phase = None
        st.session_state.current_step = 2
        st.rerun()

# Content Routing based on Step
if st.session_state.current_step == 0:
    # --- STEP 1: SETUP ---
    st.header("Document Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Job Description")
        jd_source = st.radio("Select JD Source", ["Upload File", "Paste Text"], key="jd_source")
        if jd_source == "Upload File":
            jd_file = st.file_uploader("Upload Job Description (PDF or TXT)", type=["pdf", "txt"], key="jd")
            jd_input = None
        else:
            jd_input = st.text_area("Paste Job Description Text here", height=200, key="jd_text_area")
            jd_file = None

    with col2:
        st.subheader("Resume")
        resume_source = st.radio("Select Resume Source", ["Upload File", "Paste Text"], key="resume_source")
        if resume_source == "Upload File":
            resume_file = st.file_uploader("Upload Resume (PDF or TXT)", type=["pdf", "txt"], key="resume")
            resume_input = None
        else:
            resume_input = st.text_area("Paste Resume Text here", height=200, key="resume_text_area")
            resume_file = None
    
    if st.button("Analyze Documents"):
        jd_text = ""
        resume_text = ""
        
        with st.spinner("Processing documents..."):
            # Process JD
            if jd_source == "Upload File" and jd_file:
                jd_text = extract_text_from_file(jd_file.read(), jd_file.name).strip()
            elif jd_source == "Paste Text" and jd_input:
                jd_text = jd_input.strip()
                
            # Process Resume
            if resume_source == "Upload File" and resume_file:
                resume_text = extract_text_from_file(resume_file.read(), resume_file.name).strip()
            elif resume_source == "Paste Text" and resume_input:
                resume_text = resume_input.strip()

        if not jd_text:
            st.error("Please provide a Job Description (file or text).")
        elif not resume_text:
            st.error("Please provide a Resume (file or text).")
        else:
            # Store text for the processing phase
            st.session_state.temp_jd_text = jd_text
            st.session_state.temp_resume_text = resume_text
            st.session_state.processing_phase = "setup_to_assessment"
            st.rerun()

elif st.session_state.current_step == 1:
    # --- STEP 2: ASSESSMENT ---
    if not st.session_state.setup_complete:
        st.session_state.current_step = 0
        st.rerun()
        
    if st.session_state.assessment_complete:
        if st.session_state.learning_plan is None:
            st.session_state.processing_phase = "assessment_to_plan"
            st.rerun()
        st.session_state.current_step = 2  # Go to Results & Roadmap
        st.rerun()
    else:
        current_skill = st.session_state.jd_skills[st.session_state.current_skill_index]
        st.subheader(f"Assessing Skill: {current_skill.skill_name}")
        st.progress((st.session_state.current_skill_index) / len(st.session_state.jd_skills))
        
        history = st.session_state.chat_history[current_skill.skill_name]
        
        # Display history
        for msg in history:
            with st.chat_message("assistant" if msg["role"] == "interviewer" else "user"):
                st.write(msg["content"])
                
        # Generate question if AI's turn
        if len(history) == 0 or history[-1]["role"] == "candidate":
            with st.chat_message("assistant"):
                import asyncio
                
                def get_stream():
                    # Helper to run async gen in sync streamlit
                    gen = agents["assessor"].astream_question(
                        current_skill.skill_name, 
                        current_skill.required_proficiency, 
                        str(st.session_state.parsed_resume.experience), 
                        history
                    )
                    loop = asyncio.new_event_loop()
                    try:
                        while True:
                            try:
                                yield loop.run_until_complete(gen.__anext__())
                            except StopAsyncIteration:
                                break
                    finally:
                        loop.close()

                full_q = st.write_stream(get_stream())
                history.append({"role": "interviewer", "content": full_q})
                st.rerun()
                
        # If it's the candidate's turn to answer
        if len(history) > 0 and history[-1]["role"] == "interviewer":
            user_input = st.chat_input("Type your answer...")
            if user_input:
                history.append({"role": "candidate", "content": user_input})
                st.rerun()
                
        # Navigation and Evaluate
        st.markdown("---")
        c_back, c_next = st.columns([1, 4])
        
        if c_back.button("← Back to Setup"):
            st.session_state.current_step = 0
            st.rerun()

        if len(history) >= 2: # At least one Q&A pair
            if c_next.button("Finish this Skill & Evaluate"):
                with st.spinner("Scoring..."):
                    score = agents["scorer"].evaluate_skill(current_skill.skill_name, history)
                    st.session_state.actual_scores.append(score)
                    
                    if st.session_state.current_skill_index < len(st.session_state.jd_skills) - 1:
                        st.session_state.current_skill_index += 1
                        st.rerun()
                    else:
                        st.session_state.assessment_complete = True
                        st.session_state.processing_phase = "assessment_to_plan"
                        st.rerun()

elif st.session_state.current_step == 2:
    # --- STEP 3: RESULTS & ROADMAP (COMBINED) ---
    if not st.session_state.assessment_complete or st.session_state.learning_plan is None:
        st.session_state.current_step = 1
        st.rerun()

    # 1. Plan already generated in processing phase
    plan = st.session_state.learning_plan

    # 2. Results Dashboard
    render_results_dashboard({}, plan) # Using {} for backward compat if needed, but 'plan' is the main source now

    # 3. Unified UI Layout
    st.markdown(f"### 🚀 Performance & Roadmap: {plan.candidate_name}")
    
    tab_dashboard, tab_roadmap = st.tabs(["📊 Detailed Analysis", "🗺️ Learning Roadmap"])

    with tab_dashboard:
        render_results_dashboard({}, plan)

    with tab_roadmap:
        st.markdown("<br>", unsafe_allow_html=True)
        inner_tabs = st.tabs([f"◈ {s.skill_name}" for s in plan.skills])
        
        for skill_idx, (itab, skill) in enumerate(zip(inner_tabs, plan.skills)):
            with itab:
                # 1. Feedback Box
                st.markdown(f"""
                <div class="insight-box">
                    <div class="insight-title">Neural Feedback</div>
                    <div style="color:#f8fafc; font-size:1.1rem; line-height:1.5;">{skill.candidate_feedback}</div>
                </div>
                """, unsafe_allow_html=True)
                
                if not skill.topics:
                    st.success(f"✅ Mastery Achieved: You have met all requirements for {skill.skill_name}.")
                    continue

                # 2. Weekly Timeline
                st.markdown(f"#### ◈ {skill.total_weeks}-Week Intelligence Blueprint")
                
                for week in skill.topics:
                    with st.expander(f"● {week.week_label}: {week.title}", expanded=True):
                        st.info(f"🎯 **Objective:** {week.objective}")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**What to Study**")
                            for topic in week.what_to_study:
                                st.markdown(f"- {topic}")
                            
                            st.markdown("**Core Documentation**")
                            for d in week.documentation:
                                st.markdown(f"- [{d.title}]({d.url})")
                        
                        with col2:
                            st.markdown("**Video Deep-Dives**")
                            v = week.youtube
                            st.markdown(f"🟢 [Easy] **{v.easy.channel}**: [{v.easy.title}]({v.easy.url})")
                            st.caption(f"_{v.easy.why}_")
                            
                            st.markdown(f"🟡 [Medium] **{v.medium.channel}**: [{v.medium.title}]({v.medium.url})")
                            st.caption(f"_{v.medium.why}_")
                            
                            st.markdown(f"🔴 [Hard] **{v.hard.channel}**: [{v.hard.title}]({v.hard.url})")
                            st.caption(f"_{v.hard.why}_")

                        st.markdown("---")
                        st.success(f"🛠️ **Milestone:** {week.hands_on}")
                        st.caption(f"Verification: {week.milestone}")

    # Footer Controls
    st.markdown("<br>", unsafe_allow_html=True)
    f_col1, f_col2, f_col3 = st.columns([1, 1, 3])
    
    if f_col1.button("← Back to Assessment"):
        st.session_state.current_step = 1
        st.rerun()

    if f_col2.button("↩ Start New Assessment"):
        for k in list(st.session_state.keys()):
            if k.startswith("w_idx_") or k.startswith("chk_"): del st.session_state[k]
        if "learning_plan" in st.session_state: del st.session_state["learning_plan"]
        st.session_state.current_step = 0
        st.session_state.setup_complete = False
        st.session_state.assessment_complete = False
        st.rerun()
