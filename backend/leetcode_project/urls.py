"""
Main URL configuration for leetcode_project.
Routes requests to the correct app.
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    # Django admin panel
    path('admin/', admin.site.urls),

    # API routes for the solver app (e.g., /api/solver/solve/)
    path('api/solver/', include('solver.urls')),

    # API routes for the dashboard app (e.g., /api/dashboard/history/)
    path('api/dashboard/', include('dashboard.urls')),
]
