"""
URL patterns for the solver app.
"""

from django.urls import path
from .views import SolveProblemView, LoginStatusView, StartLoginView, LogoutView

urlpatterns = [
    # GET  /api/solver/login-status/ → check if cookies are saved
    path('login-status/', LoginStatusView.as_view(), name='login-status'),

    # POST /api/solver/start-login/  → open browser, wait for manual login, save cookies
    path('start-login/', StartLoginView.as_view(), name='start-login'),

    # POST /api/solver/logout/       → clear saved cookies
    path('logout/', LogoutView.as_view(), name='logout'),

    # POST /api/solver/solve/        → triggers scrape + GPT + submit pipeline
    path('solve/', SolveProblemView.as_view(), name='solve-problem'),
]
