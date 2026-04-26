from typing import List, Dict
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class SkillScore(BaseModel):
    skill: str = Field(description="The name of the skill being evaluated.")
    score: int = Field(description="The evaluated proficiency score from 1-10.", ge=1, le=10)
    confidence: float = Field(description="Confidence in this score from 0.0 to 1.0.", ge=0.0, le=1.0)
    reasoning: str = Field(description="Detailed reasoning for the score based on the candidate's answers and rubric.")

class ScoringAgent:
    """
    Evaluates candidate responses against a rubric to assign a definitive skill score.
    """
    def __init__(self):
        self.system_prompt = (
            "You are a strict, objective AI Assessor. Your job is to grade a candidate's proficiency "
            "on a specific skill based on their interview transcript. "
            "Use a standard rubric: 1-2 (Novice), 3-4 (Beginner), 5-6 (Intermediate), "
            "7-8 (Advanced), 9-10 (Expert). "
            "Base your score ONLY on the evidence provided in the chat history. "
            "If the candidate dodges questions or gives shallow answers, penalize the score."
        )

    def evaluate_skill(self, skill_name: str, chat_history: List[Dict[str, str]]) -> SkillScore:
        """
        Grades a skill based on the conversation history.
        """
        history_str = ""
        for msg in chat_history:
            history_str += f"{msg['role'].capitalize()}: {msg['content']}\n"
            
        prompt = (
            f"Evaluate the candidate's proficiency in the skill: {skill_name}\n\n"
            f"Interview Transcript:\n{history_str}\n\n"
            "Provide the final score, your confidence in this evaluation, and detailed reasoning."
        )

        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=SkillScore
        )
