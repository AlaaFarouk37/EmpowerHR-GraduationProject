from django.urls import path
from .views import (
    # HR Manager
    HRFormListCreateView,
    HRFormDetailView,
    HRFormActivateView,
    HRQuestionListCreateView,
    HRQuestionDetailView,
    HRSubmissionsView,
    # Employee
    FeedbackFormListView,
    FeedbackFormDetailView,
    FeedbackSubmitView,
)

urlpatterns = [
    # ── HR Manager endpoints ──────────────────────────────────────────────
    #     # 1. Static/Base HR paths (No variables)
    path('hr/forms/', HRFormListCreateView.as_view(), name='hr-form-list-create'),
    path('hr/submissions/', HRSubmissionsView.as_view(), name='hr-submissions'),

    # 2. Specific Question Detail (different base path 'hr/questions/')
    path('hr/questions/<str:question_id>/', HRQuestionDetailView.as_view(), name='hr-question-detail'),

    # 3. Three-segment paths (Must be ABOVE two-segment paths)
    path('hr/forms/<str:form_id>/questions/', HRQuestionListCreateView.as_view(), name='hr-question-list-create'),
    path('hr/forms/<str:form_id>/<str:action>/', HRFormActivateView.as_view(), name='hr-form-activate'),

    # 4. Two-segment path (The "Catch-all" for HR forms)
    path('hr/forms/<str:form_id>/', HRFormDetailView.as_view(), name='hr-form-detail'),


    # ── Employee endpoints ────────────────────────────────────────────────

    # 2. Specific Actions (Three-segment path)
    path('forms/<str:form_id>/submit/', FeedbackSubmitView.as_view(), name='feedback-submit'),

    # 3. Generic Detail (Two-segment path - must be LAST)
    path('forms/<str:form_id>/', FeedbackFormDetailView.as_view(), name='feedback-form-detail'),

        # 1. Static/Base Employee paths
    path('forms/', FeedbackFormListView.as_view(), name='feedback-form-list'),
]