import json
import os

from dotenv import load_dotenv
from groq import Groq

from prompts import SYSTEM_PROMPT
from schemas import JobAnalysis

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def analyze_job_description(jd_text: str) -> JobAnalysis:

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": (
                    "Extract and classify the skills in "
                    "this job description:\n\n"
                    + jd_text
                )
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "radix_jd_analysis",
                "strict": True,
                "schema": JobAnalysis.model_json_schema()
            }
        }
    )

    content = response.choices[0].message.content

    if not content:
        raise ValueError("The LLM returned an empty response.")

    data = json.loads(content)

    # Validate the output against our Pydantic schema
    result = JobAnalysis.model_validate(data)

    return result