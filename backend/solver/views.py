"""
Views for the solver app.

Endpoints:
  GET  /api/solver/login-status/  → check if LeetCode session cookies exist
  POST /api/solver/start-login/   → open Chrome for manual login, wait, save cookies
  POST /api/solver/logout/        → clear saved cookies
  POST /api/solver/solve/         → scrape + GPT + submit pipeline
"""

import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Problem, Solution
from .serializers import ProblemSerializer
from .selenium_utils import (
    scrape_problem,
    submit_solution,
    open_browser_for_login,
    check_login_status,
    clear_cookies,
)
from .gpt_utils import generate_solution


class LoginStatusView(APIView):
    """
    GET /api/solver/login-status/
    Returns whether valid LeetCode session cookies are saved.
    Response: { "logged_in": true/false }
    """

    def get(self, request):
        logged_in = check_login_status()
        return Response({'logged_in': logged_in})


class StartLoginView(APIView):
    """
    POST /api/solver/start-login/
    Opens a Chrome browser window for the user to log in to LeetCode manually.
    Blocks until login is detected (up to 3 minutes) or times out.
    Saves session cookies on success.

    Response:
        { "success": true }
        { "success": false, "error": "..." }
    """

    def post(self, request):
        result = open_browser_for_login()
        if result['success']:
            return Response({'success': True, 'message': 'Logged in successfully. Cookies saved.'})
        return Response(
            {'success': False, 'error': result.get('error', 'Login failed.')},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class LogoutView(APIView):
    """
    POST /api/solver/logout/
    Clears saved LeetCode session cookies.
    """

    def post(self, request):
        clear_cookies()
        return Response({'success': True, 'message': 'Logged out. Cookies cleared.'})


class SolveProblemView(APIView):
    """
    POST /api/solver/solve/

    Request body (JSON):
        { "problem_number": 1 }

    Response (JSON):
        {
            "problem_number": 1,
            "title": "Two Sum",
            "description": "...",
            "generated_code": "...",
            "submission_status": "Accepted"
        }
    """

    def post(self, request):
        # ── Step 0: Ensure user is logged in ────────────────────────────
        if not check_login_status():
            return Response(
                {'error': 'Not logged in to LeetCode. Please log in first.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # ── Step 1: Get problem number from request ──────────────────────
        problem_number = request.data.get('problem_number')

        # Validate input
        if not problem_number:
            return Response(
                {'error': 'problem_number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            problem_number = int(problem_number)
        except ValueError:
            return Response(
                {'error': 'problem_number must be an integer.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # ── Step 2: Check if problem already in database ──────────────
            existing_problem = Problem.objects.filter(problem_number=problem_number).first()

            if existing_problem:
                # If we already have a successful solution, return it directly
                latest_solution = existing_problem.solutions.order_by('-created_at').first()
                if latest_solution and latest_solution.submission_status == 'accepted':
                    return Response({
                        'problem_number': existing_problem.problem_number,
                        'title': existing_problem.title,
                        'description': existing_problem.description,
                        'generated_code': latest_solution.generated_code,
                        'submission_status': latest_solution.submission_status,
                        'cached': True,   # Tell frontend this is from cache
                    })

            # ── Step 3: Scrape problem using Selenium ─────────────────────
            print(f"\n[View] Scraping problem #{problem_number}...")
            scraped_data = scrape_problem(problem_number)

            if not scraped_data:
                return Response(
                    {'error': 'Failed to scrape problem from LeetCode. Check Selenium setup.'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            title = scraped_data['title']
            description = scraped_data['description']

            # ── Step 4: Save problem to database ─────────────────────────
            problem_obj, created = Problem.objects.get_or_create(
                problem_number=problem_number,
                defaults={'title': title, 'description': description}
            )

            if not created:
                # Update title and description if problem already exists
                problem_obj.title = title
                problem_obj.description = description
                problem_obj.save()

            # ── Step 5: Generate solution using GPT API ───────────────────
            print(f"[View] Generating solution using GPT...")
            generated_code = generate_solution(description)

            # ── Step 6: Submit solution using Selenium ────────────────────
            print(f"[View] Submitting solution to LeetCode...")
            submission_result = submit_solution(problem_number, generated_code)

            # ── Step 7: Save solution to database ─────────────────────────
            # Map result string to model status choices
            status_map = {
                'accepted': 'accepted',
                'wrong answer': 'wrong_answer',
                'time limit exceeded': 'tle',
                'memory limit exceeded': 'tle',
                'runtime error': 'error',
                'compile error': 'error',
                'output limit exceeded': 'error',
            }
            normalized_status = status_map.get(
                submission_result.lower(), 'error'
            )

            solution_obj = Solution.objects.create(
                problem=problem_obj,
                generated_code=generated_code,
                submission_status=normalized_status
            )

            # ── Step 8: Return result to frontend ─────────────────────────
            return Response({
                'problem_number': problem_obj.problem_number,
                'title': problem_obj.title,
                'description': problem_obj.description,
                'generated_code': solution_obj.generated_code,
                'submission_status': solution_obj.submission_status,
                'cached': False,
            }, status=status.HTTP_200_OK)

        except Exception as e:
            # Log the full error for debugging
            print(f"[View] Unexpected error: {e}")
            traceback.print_exc()
            return Response(
                {'error': f'Server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
