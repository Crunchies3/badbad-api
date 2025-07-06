# chatgpt_translate.py

import os
import openai
from dotenv import load_dotenv
from _sys import build_system_prompt

# Load API key
load_dotenv()
openai.api_key = os.getenv("KEY")

def service(message, memory):
    response = openai.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": build_system_prompt(memory)
            },
            {
                "role": "user",
                "content": message
            }
        ]
    )
    return response.choices[0].message.content.strip()
