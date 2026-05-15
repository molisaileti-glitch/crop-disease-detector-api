# api/urls.py
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# URL patterns for all API endpoints.
# All URLs start with /api/v1/ (set in core/urls.py)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [

    # ── AUTHENTICATION ───────────────────────────────
    # POST /api/v1/auth/register/
    path('auth/register/', views.register, name='register'),

    # POST /api/v1/auth/login/
    path('auth/login/', views.login, name='login'),

    # POST /api/v1/auth/logout/
    path('auth/logout/', views.logout, name='logout'),

    # POST /api/v1/auth/token/refresh/
    # Built-in JWT token refresh
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ── USER ─────────────────────────────────────────
    # GET/PUT /api/v1/user/profile/
    path('user/profile/', views.profile, name='profile'),

    # ── DIAGNOSES ────────────────────────────────────
    # POST /api/v1/diagnose/
    path('diagnose/', views.diagnose, name='diagnose'),

    # GET /api/v1/diagnose/history/
    path('diagnose/history/', views.diagnosis_history, name='diagnosis_history'),

    # GET/DELETE /api/v1/diagnose/<id>/
    path('diagnose/<int:diagnosis_id>/', views.diagnosis_detail, name='diagnosis_detail'),

    # ── FEEDBACK ─────────────────────────────────────
    # POST /api/v1/diagnose/<id>/feedback/
    path('diagnose/<int:diagnosis_id>/feedback/', views.submit_feedback, name='submit_feedback'),

    # ── ADMIN ────────────────────────────────────────
    # GET /api/v1/admin/stats/
    path('admin/stats/', views.stats, name='stats'),
]