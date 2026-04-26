import json
from dotenv import load_dotenv

# Load environment variables before importing any config/agents
load_dotenv()

from agents.parser_agent import ParserAgent
from agents.skill_extractor import SkillExtractorAgent
from agents.assessment_agent import AssessmentAgent
from agents.scoring_agent import ScoringAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.learning_plan_agent import LearningPlanAgent
from agents.behavioral_agent import BehavioralAgent
from agents.vision_evaluator import VisionEvaluatorAgent

# --- Mock Data ---
MOCK_JD = """
Senior Python Engineer

Responsibilities:
- Design and build scalable microservices.
- Ensure the performance, quality, and responsiveness of applications.

Requirements:
- 5+ years of experience in Python development.
- Strong knowledge of FastAPI and Django.
- Experience with Docker and Kubernetes.
- Excellent understanding of SQL and NoSQL databases (PostgreSQL, MongoDB).
- Good communication skills.
"""

MOCK_RESUME = """
John Doe
Software Engineer

Experience:
- Backend Developer at TechCorp (2020 - Present)
  - Developed REST APIs using Python and Flask.
  - Managed PostgreSQL databases.
- Junior Developer at WebSolutions (2018 - 2020)
  - Built web pages using HTML/CSS/JS.
  - Minor python scripting.

Education:
- B.S. in Computer Science, State University.

Skills:
Python, Flask, JavaScript, PostgreSQL, HTML
"""

# Simulate an interactive chat session for an assessed skill
# In a real app, this would be an interactive loop with a human or UI.
MOCK_CHAT_HISTORY = {
    "FastAPI": [
        {"role": "interviewer", "content": "How would you handle dependency injection in FastAPI?"},
        {"role": "candidate", "content": "I haven't used FastAPI much, I usually use Flask. But I assume it has some decorators for it?"},
        {"role": "interviewer", "content": "That's okay. In Flask, how do you manage application context?"},
        {"role": "candidate", "content": "I use the `g` object or current_app."}
    ],
    "Docker": [
        {"role": "interviewer", "content": "Explain how you would optimize a Dockerfile for a Python application."},
        {"role": "candidate", "content": "I would use a multi-stage build, copy requirements.txt first to cache layers, and use a slim base image."},
        {"role": "interviewer", "content": "Great. What's the difference between CMD and ENTRYPOINT?"},
        {"role": "candidate", "content": "ENTRYPOINT is the executable that runs, CMD provides default arguments."}
    ]
}

def main():
    print("="*50)
    print("Starting AI Skill Assessment Pipeline...")
    print("="*50)

    # 1. Parsing
    print("\n[1/6] Parsing JD and Resume...")
    parser = ParserAgent()
    parsed_jd = parser.parse_job_description(MOCK_JD)
    parsed_resume = parser.parse_resume(MOCK_RESUME)
    print("Resume Parsed. Found Skills:", parsed_resume.skills)

    # 2. Skill Extraction
    print("\n[2/6] Extracting Skills from JD...")
    extractor = SkillExtractorAgent()
    jd_skills = extractor.extract_skills(MOCK_JD).skills
    for s in jd_skills:
        print(f"  - {s.skill_name} (Req: {s.required_proficiency}/10, Imp: {s.importance_weight}/5)")

    # 3 & 4. Assessment & Scoring
    print("\n[3&4/6] Running Assessment & Scoring Engine...")
    assessor = AssessmentAgent()
    scorer = ScoringAgent()
    
    actual_scores = []
    
    # We'll simulate scoring just a couple of skills to save time/tokens.
    # In a real app, we might ask questions for every critical skill.
    skills_to_test = ["FastAPI", "Docker"]
    
    for req_skill in jd_skills:
        skill_name = req_skill.skill_name
        
        # Determine which mock chat history to use (or skip)
        history = MOCK_CHAT_HISTORY.get(skill_name, [])
        if not history:
            # Assume 0 score if we didn't test it, or we could test it live.
            # For this pipeline demo, let's just use what we mocked.
            continue
            
        print(f"\n  Assessing: {skill_name}")
        
        # Simulate generating the NEXT question based on the history
        next_q = assessor.generate_question(
            skill_name=skill_name,
            target_proficiency=req_skill.required_proficiency,
            candidate_resume_context=str(parsed_resume.experience),
            chat_history=history
        )
        print(f"  Generated Next Question (Diff {next_q.difficulty}/10): {next_q.question}")
        
        # Grade the history so far
        score = scorer.evaluate_skill(skill_name, history)
        print(f"  Score for {skill_name}: {score.score}/10 (Conf: {score.confidence:.2f})")
        print(f"  Reasoning: {score.reasoning}")
        actual_scores.append(score)

        # Phase 5: Behavioral Evaluation
        print(f"\n[4.5/6] Running Behavioral Analysis for {skill_name}...")
        behavioral_agent = BehavioralAgent()
        behavioral_score = behavioral_agent.evaluate_behavior(history)
        print(f"  Communication Clarity: {behavioral_score.communication_clarity}/10")
        print(f"  Confidence: {behavioral_score.confidence}/10")
        print(f"  Behavioral Notes: {behavioral_score.behavioral_notes}")

        # Phase 6: Simulated Vision Analysis
        print(f"\n[4.6/6] Simulating Live Vision Evaluation for {skill_name}...")
        vision_agent = VisionEvaluatorAgent()
        vision_feedback = vision_agent.analyze_frame(b"mock_bytes", skill_name)
        print(f"  Is Coding: {vision_feedback.is_coding}")
        print(f"  Code Summary: {vision_feedback.code_summary}")
        print(f"  Issues Spotted: {vision_feedback.issues_spotted}")
        print(f"  Suggested Question: {vision_feedback.suggested_question}")

    # 5. Gap Analysis
    print("\n[5/6] Performing Skill Gap Analysis...")
    analyzer = GapAnalysisAgent()
    gaps = analyzer.analyze_gaps(jd_skills, actual_scores)
    
    for gap in gaps:
        print(f"  - {gap.skill}: Gap of {gap.gap} (Priority: {gap.priority}) -> {gap.summary}")

    # 6. Learning Plan Generation
    print("\n[6/6] Generating Personalized Learning Plan...")
    planner = LearningPlanAgent()
    plan = planner.generate_plan(gaps, weeks_available=2)
    
    print("\nFinal Learning Plan Summary:")
    print(f"Candidate: {plan.candidate_name} | Role: {plan.target_role} | Total Prep: {plan.total_weeks} weeks")
    
    for s_plan in plan.skills:
        print(f"\n◈ Skill: {s_plan.skill_name} ({s_plan.category})")
        print(f"  Feedback: {s_plan.candidate_feedback}")
        for week in s_plan.topics:
            print(f"  [{week.week_label}] {week.title}: {week.objective}")
            print(f"    - Milestone: {week.hands_on}")

    print("\nPipeline Complete!")

if __name__ == "__main__":
    import asyncio
    try:
        main()
    except asyncio.CancelledError:
        print("\nPipeline interrupted by user or system. Exiting gracefully...")
    except Exception as e:
        print(f"\nPipeline failed with error: {e}")
