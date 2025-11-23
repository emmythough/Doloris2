import logging
from openai import OpenAI
from app.config import OPENAI_API_KEY

logger = logging.getLogger(__name__)

client = OpenAI(api_key=OPENAI_API_KEY)

def get_completion(
    messages: list,
    tools: list = None,
    model: str = "gpt-4o",
    temperature: float = 0.7
):
    """
    Call OpenAI ChatCompletion API.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            temperature=temperature
        )
        return response.choices[0].message
    except Exception as e:
        logger.error(f"OpenAI API Error: {e}")
        # Return a dummy message or re-raise depending on strategy
        # For now, re-raise to be handled upstream
        raise e
