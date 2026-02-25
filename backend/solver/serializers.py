"""
Serializers for the solver app.
Converts Django model instances to JSON for API responses.
"""

from rest_framework import serializers
from .models import Problem, Solution


class SolutionSerializer(serializers.ModelSerializer):
    """Serializer for Solution model."""
    class Meta:
        model = Solution
        fields = ['id', 'generated_code', 'submission_status', 'created_at']


class ProblemSerializer(serializers.ModelSerializer):
    """
    Serializer for Problem model.
    Also includes the related solutions.
    """
    solutions = SolutionSerializer(many=True, read_only=True)

    class Meta:
        model = Problem
        fields = ['id', 'problem_number', 'title', 'description', 'created_at', 'solutions']
