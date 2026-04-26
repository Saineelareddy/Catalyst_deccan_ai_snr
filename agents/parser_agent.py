from typing import List, Optional
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: Optional[str] = None
    description: str

class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str]

class EducationItem(BaseModel):
    degree: str
    institution: str
    year: Optional[str] = None

class ParsedDocument(BaseModel):
    name: Optional[str] = Field(None, description="Full name of the candidate or contact person")
    skills: List[str] = Field(description="List of raw skills extracted from the document")
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    education: List[EducationItem]

class ParserAgent:
    """
    Parses unstructured text (like a Resume or JD) into a normalized, structured JSON schema.
    """
    def __init__(self):
        self.system_prompt = (
            "You are an expert HR Data Extraction AI. Your goal is to extract key information "
            "from the provided text and normalize it into a structured format. "
            "Do not invent information. If a section is missing from the text, return an empty list or null for that field."
        )

    def parse_resume(self, resume_text: str) -> ParsedDocument:
        """Parses a candidate's resume."""
        prompt = f"Please extract the candidate's name, skills, experience, projects, and education from the following Resume:\n\n{resume_text}"
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=ParsedDocument
        )
        
    def parse_job_description(self, jd_text: str) -> ParsedDocument:
        """Parses a job description to extract the required profile structure."""
        prompt = f"Please extract the expected name (if any), required skills, experience, projects, and education expectations from the following Job Description:\n\n{jd_text}"
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=ParsedDocument
        )
