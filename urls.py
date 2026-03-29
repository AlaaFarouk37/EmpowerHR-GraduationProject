from django.urls import path
from .views import (
    WeekendConfigView,
    WorkingHoursConfigView,
    SkillListCreateView,
    SkillDetailView,
    JobRoleListCreateView,
    JobRoleDetailView,
    LeaveTypeListCreateView,
    LeaveTypeDetailView,
    SpecialLeaveListCreateView,
    SpecialLeaveDetailView,
    LeaveCalculationView,
)

urlpatterns = [

    # ── Weekend days ──────────────────────────────────────────────
    path('weekends/', WeekendConfigView.as_view(), name='config-weekends'),

    # ── Working hours ─────────────────────────────────────────────
    path('working-hours/', WorkingHoursConfigView.as_view(), name='config-working-hours'),

    # ── Skills ────────────────────────────────────────────────────
    path('skills/', SkillListCreateView.as_view(), name='config-skill-list'),


    path('skills/<str:pk>/', SkillDetailView.as_view(), name='config-skill-detail'),

    # ── Job roles ─────────────────────────────────────────────────
    path('job-roles/', JobRoleListCreateView.as_view(), name='config-role-list'),


    path('job-roles/<str:pk>/', JobRoleDetailView.as_view(), name='config-role-detail'),

    # ── Leave types ───────────────────────────────────────────────
    path('leave-types/', LeaveTypeListCreateView.as_view(), name='config-leavetype-list'),


    path('leave-types/<str:pk>/', LeaveTypeDetailView.as_view(), name='config-leavetype-detail'),

    # ── Special leave cases ───────────────────────────────────────
    path('special-leave/', SpecialLeaveListCreateView.as_view(), name='config-special-list'),


    path('special-leave/<str:pk>/', SpecialLeaveDetailView.as_view(), name='config-special-detail'),

    # ── Leave calculation pipeline ────────────────────────────────
    path(
        'leave-calculation/<str:employee_id>/',
        LeaveCalculationView.as_view(),
        name='config-leave-calculation',
    ),
]