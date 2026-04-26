from typing import List, Optional
from pydantic import BaseModel, Field
from utils.ai_router import ai_router

class VisionFeedback(BaseModel):
    is_coding: bool = Field(description="Whether the user is currently looking at or writing code in an IDE.")
    code_summary: Optional[str] = Field(description="Summary of what the code on the screen is attempting to do.")
    issues_spotted: List[str] = Field(description="Any syntax errors, logical bugs, or anti-patterns spotted in the frame.")
    suggested_question: Optional[str] = Field(description="A question the interviewer should ask based on what is visible.")

class VisionEvaluatorAgent:
    """
    Evaluates video frames/screen-captures to provide context to the interview, acting as a pair-programmer.
    Requires a multi-modal capable backend like gemini-1.5-pro or gpt-4o.
    """
    def __init__(self):
        self.system_prompt = (
            "You are an expert AI Pair Programmer. You will receive frames from the candidate's screen share. "
            "Your job is to analyze the code visible on screen and provide feedback to the interviewer agent. "
            "Identify if they are stuck, if they have syntax errors, and suggest a leading question to ask them."
        )

    def analyze_frame(self, image_bytes: bytes, current_skill: str) -> VisionFeedback:
        """
        Analyzes a screen capture.
        (In a real implementation, this would pass the image_bytes to the multimodal client).
        """
        # For this execution script, we simulate the multimodal payload
        prompt = f"Analyze the provided screen capture. The candidate is being assessed on {current_skill}."
        
        # In a real environment:
        # response = gemini_client.generate_content([prompt, image_bytes])
        # We rely on the router to parse it to the strict Pydantic model for our scaffolding.
        
        return ai_router.complete(
            prompt=prompt + "\n[Simulated Image Attached]",
            system_prompt=self.system_prompt,
            response_model=VisionFeedback,
            bypass_cache=True
        )
