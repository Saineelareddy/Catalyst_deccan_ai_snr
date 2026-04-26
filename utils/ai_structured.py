import json
import re
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError

T = TypeVar('T', bound=BaseModel)

class AIStructuredExtractionError(Exception):
    pass

def extract_json_from_text(text: str) -> str:
    """
    Attempts to extract a JSON block from a raw string, handling markdown formatting.
    """
    # Look for ```json ... ``` blocks
    match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # If no markdown blocks, try finding the first { or [ and the last } or ]
    start_idx = text.find('{')
    array_start_idx = text.find('[')
    
    # Decide whether it's an object or an array
    is_array = False
    if array_start_idx != -1 and (start_idx == -1 or array_start_idx < start_idx):
        start_idx = array_start_idx
        is_array = True
        
    if start_idx == -1:
        raise AIStructuredExtractionError("No JSON object or array found in text.")
        
    end_char = ']' if is_array else '}'
    end_idx = text.rfind(end_char)
    
    if end_idx == -1:
        raise AIStructuredExtractionError(f"Missing closing {end_char} in text.")
        
    return text[start_idx:end_idx+1].strip()

def parse_structured_response(response_text: str, schema: Type[T]) -> T:
    """
    Parses an AI response text into a validated Pydantic model.
    """
    try:
        json_str = extract_json_from_text(response_text)
        data = json.loads(json_str)
        return schema.model_validate(data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise AIStructuredExtractionError(f"Failed to parse response into {schema.__name__}: {e}\nRaw Response: {response_text}")

def generate_schema_prompt(schema: Type[BaseModel]) -> str:
    """
    Generates a prompt instruction appending the JSON schema of a Pydantic model.
    """
    schema_json = schema.model_json_schema()
    prompt = (
        "You must respond ONLY with valid JSON that strictly adheres to the following JSON schema.\n"
        "Do not include any additional commentary or markdown formatting outside the JSON.\n\n"
        f"SCHEMA:\n{json.dumps(schema_json, indent=2)}"
    )
    return prompt
