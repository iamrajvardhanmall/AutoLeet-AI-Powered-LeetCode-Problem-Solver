"""
Groq AI integration module.

Sends the LeetCode problem description to Groq (Llama 3.3 70B)
and receives a Python solution back.

Groq has a COMPLETELY FREE tier (no credit card needed):
  → Get your free API key at: https://console.groq.com/keys
"""

import os
import re
from groq import Groq
from dotenv import load_dotenv

# Load API key from .env file
load_dotenv()


def generate_solution(problem_description):
    """
    Send the problem description to Groq and get a Python solution.

    Args:
        problem_description (str): Full LeetCode problem description text

    Returns:
        str: Python code as a string.
             Returns an error message string if API call fails.
    """
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        return '# Error: GROQ_API_KEY not set in .env file. Get a free key at https://console.groq.com/keys'

    client = Groq(api_key=api_key)

    system_prompt = (
        'You are a competitive programmer. '
        'Solve the given LeetCode problem in Python. '
        'Follow the correct function signature from the problem. '
        'Return ONLY the Python code — no explanations, no markdown, no backticks. '
        'The code must be complete and ready to run.'
    )

    user_prompt = f'Solve this LeetCode problem in Python:\n\n{problem_description}'

    try:
        print('[Groq] Sending problem to Groq (Llama 3.3 70B)...')

        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',   # Best free model on Groq for code
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user',   'content': user_prompt},
            ],
            temperature=0.2,      # Low = more deterministic code
            max_tokens=2000,
        )

        solution_code = response.choices[0].message.content.strip()

        # Strip markdown code fences if the model includes them anyway
        solution_code = re.sub(r'^```[\w]*\n?', '', solution_code)
        solution_code = re.sub(r'\n?```$', '', solution_code).strip()

        print(f'[Groq] Solution received ({len(solution_code)} chars)')
        return solution_code

    except Exception as e:
        error_msg = f'# Groq API Error: {str(e)}'
        print(f'[Groq] Error: {e}')
        return error_msg
