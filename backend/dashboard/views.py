"""
Views for the dashboard app.

Endpoints:
  GET /api/dashboard/history/        → list all solved problems
  GET /api/dashboard/history/<id>/   → detail of a single problem + solutions
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from solver.models import Problem, Solution
from solver.serializers import ProblemSerializer


class HistoryListView(APIView):
    """
    GET /api/dashboard/history/
    Returns all problems that have been processed, ordered by most recent first.
    """

    def get(self, request):
        problems = Problem.objects.all().order_by('-created_at')
        serializer = ProblemSerializer(problems, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoryDetailView(APIView):
    """
    GET /api/dashboard/history/<problem_id>/
    Returns a single problem with all its solutions.
    """

    def get(self, request, problem_id):
        try:
            problem = Problem.objects.get(id=problem_id)
        except Problem.DoesNotExist:
            return Response(
                {'error': 'Problem not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProblemSerializer(problem)
        return Response(serializer.data, status=status.HTTP_200_OK)
