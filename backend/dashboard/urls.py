"""
URL patterns for the dashboard app.
"""

from django.urls import path
from .views import HistoryListView, HistoryDetailView

urlpatterns = [
    # GET /api/dashboard/history/ → all problems
    path('history/', HistoryListView.as_view(), name='history-list'),

    # GET /api/dashboard/history/1/ → single problem by DB id
    path('history/<int:problem_id>/', HistoryDetailView.as_view(), name='history-detail'),
]
