from pydantic import BaseModel
from typing import List, Dict, Optional
from agents.parser_agent import ParsedDocument
from agents.skill_extractor import ExtractedSkill
from agents.assessment_agent import AssessmentQuestion
from agents.scoring_agent import SkillScore
from agents.gap_analysis_agent import SkillGap
from agents.learning_plan_agent import PersonalizedLearningPlan

class InitSessionRequest(BaseModel):
    jd_text: str
    resume_text: str

class InitSessionResponse(BaseModel):
    session_id: str
    parsed_jd: ParsedDocument
    parsed_resume: ParsedDocument
    extracted_skills: List[ExtractedSkill]

class NextQuestionRequest(BaseModel):
    session_id: str
    skill_name: str
    target_proficiency: int
    chat_history: List[Dict[str, str]]

class SubmitAnswerRequest(BaseModel):
    session_id: str
    skill_name: str
    chat_history: List[Dict[str, str]]  # Includes the candidate's latest answer

class ScoreSkillRequest(BaseModel):
    session_id: str
    skill_name: str
    chat_history: List[Dict[str, str]]

class GeneratePlanRequest(BaseModel):
    session_id: str
    required_skills: List[ExtractedSkill]
    actual_scores: List[SkillScore]
