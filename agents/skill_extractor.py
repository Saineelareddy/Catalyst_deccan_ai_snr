from typing import List
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class ExtractedSkill(BaseModel):
    skill_name: str = Field(description="The name of the skill")
    required_proficiency: int = Field(description="Required proficiency level from 1 (beginner) to 10 (expert)", ge=1, le=10)
    importance_weight: int = Field(description="Importance weight from 1 (nice to have) to 5 (critical)", ge=1, le=5)
    context: str = Field(description="Brief context of why this skill is needed based on the JD")

class JDSkillsExtraction(BaseModel):
    skills: List[ExtractedSkill]

class SkillExtractorAgent:
    """
    Extracts core required skills, proficiency levels, and importance weights from a Job Description.
    """
    def __init__(self):
        self.system_prompt = (
            "You are an expert Technical Recruiter AI. Your task is to extract the core skills required "
            "from the provided Job Description. For each skill, determine:\n"
            "- The required proficiency on a scale of 1-10.\n"
            "- The importance weight on a scale of 1-5 (1=nice-to-have, 5=critical).\n"
            "- A brief context of how it is used in the role.\n"
            "Only extract genuine hard/soft skills, not general responsibilities."
        )

    def extract_skills(self, jd_text: str) -> JDSkillsExtraction:
        """Extracts weighted skills from JD."""
        prompt = f"Analyze the following Job Description and extract the weighted skills required:\n\n{jd_text}"
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=JDSkillsExtraction
        )
