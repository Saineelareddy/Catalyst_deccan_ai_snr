from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class ExperienceItem(BaseModel):
    role: Optional[Any] = Field(None, alias="title")
    company: Optional[Any] = None
    duration: Optional[Any] = None
    description: Optional[Any] = ""

    class Config:
        populate_by_name = True

class ProjectItem(BaseModel):
    name: Optional[Any] = None
    description: Optional[Any] = ""
    technologies: List[Any] = []

class EducationItem(BaseModel):
    degree: Optional[Any] = None
    institution: Optional[Any] = None
    year: Optional[Any] = None

class ParsedDocument(BaseModel):
    name: Optional[Any] = Field(None)
    skills: List[Any] = Field(default=[])
    experience: List[Dict[str, Any]] = Field(default=[])
    projects: List[Dict[str, Any]] = Field(default=[])
    education: List[Dict[str, Any]] = Field(default=[])

class ParserAgent:
    """
    Parses unstructured text (like a Resume or JD) into a normalized, structured JSON schema.
    """
    SYSTEM_PROMPT = (
        "You are an expert HR Data Extraction AI. Extract key information and return ONLY valid JSON.\n"
        "Rules:\n"
        "- 'skills': flat list of strings (e.g. ['Python', 'Docker'])\n"
        "- 'experience': list of objects with keys: role, company, duration, description\n"
        "- 'projects': list of objects with keys: name, description, technologies (list of strings)\n"
        "- 'education': list of objects with keys: degree, institution, year\n"
        "- If any section is empty, return an empty list [].\n"
        "- Do NOT invent data. Return only what is explicitly stated.\n"
        "Output ONLY the JSON object, no markdown fences."
    )

    def __init__(self):
        self.system_prompt = self.SYSTEM_PROMPT

    def parse_resume(self, resume_text: str) -> ParsedDocument:
        """Parses a candidate's resume."""
        prompt = (
            f"Extract name, skills, experience, projects, and education from this Resume.\n\n"
            f"Resume:\n{resume_text}"
        )
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=ParsedDocument
        )

    def parse_job_description(self, jd_text: str) -> ParsedDocument:
        """Parses a job description."""
        prompt = (
            f"Extract required skills, experience, projects, and education expectations from this Job Description.\n\n"
            f"Job Description:\n{jd_text}"
        )
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=ParsedDocument
        )
