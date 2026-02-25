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


def _ensure_class_solution(code: str) -> str:
    """
    LeetCode requires solutions to be inside 'class Solution:'.
    If the AI returned a bare top-level function, wrap it automatically.
    If the code already has 'class Solution:', leave it untouched.
    """
    if 'class Solution' in code:
        return code   # already correct

    # Find all top-level def lines and indent the whole block
    lines = code.split('\n')
    indented = ['    ' + line if line.strip() else '' for line in lines]
    wrapped = 'class Solution:\n' + '\n'.join(indented)
    print('[Groq] Warning: AI returned bare function — auto-wrapped in class Solution.')
    return wrapped


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
        'Solve the given LeetCode problem in Python3. '
        'ALWAYS wrap your solution inside a class named Solution, exactly like this:\n\n'
        'class Solution:\n'
        '    def methodName(self, ...args...) -> returnType:\n'
        '        # your solution here\n\n'
        'Rules:\n'
        '1. The class MUST be named "Solution".\n'
        '2. The method inside MUST have "self" as the first parameter.\n'
        '3. Use the exact method name and parameter types shown in the problem.\n'
        '4. Return ONLY the Python code — no explanations, no markdown, no backticks.\n'
        '5. The code must be complete, correct, and ready to submit to LeetCode as-is.'
    )

    user_prompt = (
        'Solve this LeetCode problem in Python3.\n'
        'IMPORTANT: Wrap the solution in "class Solution:" and include "self" in the method signature.\n\n'
        f'{problem_description}'
    )

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

        # Safety net: if the model forgot to wrap in class Solution, do it here
        solution_code = _ensure_class_solution(solution_code)

        print(f'[Groq] Solution received ({len(solution_code)} chars)')
        return solution_code

    except Exception as e:
        error_msg = f'# Groq API Error: {str(e)}'
        print(f'[Groq] Error: {e}')
        return error_msg
