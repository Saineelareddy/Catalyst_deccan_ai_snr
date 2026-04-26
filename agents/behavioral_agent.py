from typing import List, Dict
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class BehavioralScore(BaseModel):
    communication_clarity: int = Field(description="Score from 1-10 on how clearly the candidate expressed ideas.")
    conciseness: int = Field(description="Score from 1-10 on whether the candidate avoided rambling.")
    confidence: int = Field(description="Score from 1-10 on the perceived confidence in their answers.")
    problem_solving_approach: str = Field(description="Summary of the candidate's methodology (e.g., structured, chaotic, methodical).")
    behavioral_notes: str = Field(description="Overall soft-skills feedback for the recruiter.")

class BehavioralAgent:
    """
    Evaluates the 'soft skills' and structural delivery of the candidate's answers based on transcript history.
    """
    def __init__(self):
        self.system_prompt = (
            "You are an expert HR Behavioral Analyst. Your goal is to evaluate a candidate's soft skills "
            "based purely on their interview transcript. Ignore technical correctness; focus on clarity, "
            "conciseness, structure, and confidence. Be highly critical of rambling or evasive language."
        )

    def evaluate_behavior(self, chat_history: List[Dict[str, str]]) -> BehavioralScore:
        history_str = ""
        for msg in chat_history:
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
            
        prompt = (
            "Evaluate the candidate's behavioral and communication skills based on the following transcript:\n\n"
            f"{history_str}\n\n"
            "Provide scores out of 10 and detailed notes."
        )

        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=BehavioralScore
        )
