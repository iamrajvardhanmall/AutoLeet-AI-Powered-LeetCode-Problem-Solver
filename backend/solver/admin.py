"""
Register models with Django admin panel.
Allows viewing/editing data at /admin/
"""

from django.contrib import admin
from .models import Problem, Solution


@admin.register(Problem)
class ProblemAdmin(admin.ModelAdmin):
    # Columns visible in admin list view
    list_display = ['problem_number', 'title', 'created_at']
    search_fields = ['title', 'problem_number']


@admin.register(Solution)
class SolutionAdmin(admin.ModelAdmin):
    list_display = ['problem', 'submission_status', 'created_at']
    list_filter = ['submission_status']
