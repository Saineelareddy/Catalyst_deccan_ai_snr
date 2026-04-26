from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class AssessmentQuestion(BaseModel):
    question: Optional[Any] = None
    expected_key_points: List[Any] = Field(default=[])
    difficulty: Optional[Any] = 5

class AssessmentAgent:
    """
    Dynamically generates conversational, technical interview questions for a specific skill.
    Adapts based on the conversation history and avoids resume-bias.
    """
    def __init__(self):
        self.system_prompt = (
            "You are an expert Technical Interviewer AI. Your goal is to assess a candidate's REAL "
            "knowledge of a specific skill. Do NOT just ask them to repeat their resume. "
            "Ask scenario-based, deep-dive technical questions. "
            "Adapt the difficulty based on their previous answers: if they answer well, increase difficulty. "
            "If they struggle, simplify or test fundamentals."
        )

    def generate_question(
        self, 
        skill_name: str, 
        target_proficiency: int, 
        candidate_resume_context: str, 
        chat_history: List[Dict[str, str]]
    ) -> AssessmentQuestion:
        """Generates a structured question for the CLI/non-streaming usage."""
        history_str = "".join([f"{msg['role'].capitalize()}: {msg['content']}\n" for msg in chat_history])
        prompt = (
            f"Target Skill: {skill_name}\n"
            f"Target Proficiency: {target_proficiency}/10\n"
            f"Resume Context: {candidate_resume_context}\n"
            f"Conversation History:\n{history_str}\n"
            "Generate the NEXT technical question and identify expected key points."
        )
        return ai_router.complete(
            prompt=prompt,
            system_prompt=self.system_prompt,
            response_model=AssessmentQuestion
        )

    async def astream_question(
        self, 
        skill_name: str, 
        target_proficiency: int, 
        candidate_resume_context: str, 
        chat_history: List[Dict[str, str]]
    ):
        """Streams the question text for immediate display."""
        history_str = "".join([f"{msg['role'].capitalize()}: {msg['content']}\n" for msg in chat_history])
        prompt = (
            f"Target Skill: {skill_name}\n"
            f"Conversation History:\n{history_str}\n"
            "Generate the NEXT technical question. Respond ONLY with the question text."
        )
        async for chunk in ai_router.astream(prompt, self.system_prompt):
            yield chunk
