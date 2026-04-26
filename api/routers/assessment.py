from fastapi import APIRouter, HTTPException, Depends
from typing import List
import uuid

from api.schemas import (
    InitSessionRequest, InitSessionResponse, NextQuestionRequest, 
    ScoreSkillRequest, GeneratePlanRequest
)
from agents.parser_agent import ParserAgent
from agents.skill_extractor import SkillExtractorAgent
from agents.assessment_agent import AssessmentAgent
from agents.scoring_agent import ScoringAgent
from agents.gap_analysis_agent import GapAnalysisAgent
from agents.learning_plan_agent import LearningPlanAgent

router = APIRouter()

# Instantiate agents
parser_agent = ParserAgent()
skill_extractor_agent = SkillExtractorAgent()
assessment_agent = AssessmentAgent()
scoring_agent = ScoringAgent()
gap_analysis_agent = GapAnalysisAgent()
learning_plan_agent = LearningPlanAgent()

@router.post("/init_session", response_model=InitSessionResponse)
async def init_session(request: InitSessionRequest):
    """
    Parses JD and Resume, and extracts required skills.
    """
    try:
        parsed_jd = parser_agent.parse_job_description(request.jd_text)
        parsed_resume = parser_agent.parse_resume(request.resume_text)
        extracted_skills = skill_extractor_agent.extract_skills(request.jd_text).skills
        
        session_id = str(uuid.uuid4())
        
        return InitSessionResponse(
            session_id=session_id,
            parsed_jd=parsed_jd,
            parsed_resume=parsed_resume,
            extracted_skills=extracted_skills
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/next_question")
async def get_next_question(request: NextQuestionRequest):
    """
    Generates the next assessment question dynamically.
    """
    try:
        # Pass empty string for candidate context for simplicity in this endpoint, 
        # or it could be retrieved from a DB if we persisted the parsed resume.
        next_q = assessment_agent.generate_question(
            skill_name=request.skill_name,
            target_proficiency=request.target_proficiency,
            candidate_resume_context="Context omitted for API",
            chat_history=request.chat_history
        )
        return next_q
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/score_skill")
async def score_skill(request: ScoreSkillRequest):
    """
    Grades a skill based on the interview transcript.
    """
    try:
        score = scoring_agent.evaluate_skill(request.skill_name, request.chat_history)
        return score
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate_plan")
async def generate_plan(request: GeneratePlanRequest):
    """
    Generates a personalized learning plan based on gaps.
    """
    try:
        gaps = gap_analysis_agent.analyze_gaps(request.required_skills, request.actual_scores)
        plan = learning_plan_agent.generate_plan(gaps)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
