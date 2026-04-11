from django.urls import path
from .views import (
    JobListCreateView, JobDetailView, JobWeightsView,
    SubmitResumeView, JobSubmissionsView, SubmissionDetailView, CandidateJobListView
)


urlpatterns = [
    # Candidate-facing: Publicly viewable list
    path('jobs/', CandidateJobListView.as_view(), name='candidate-job-list'),
    # HR-facing: Protected management views
    path("jobs/", JobListCreateView.as_view()), 
    path("jobs/<int:pk>/", JobDetailView.as_view()),
    path("jobs/<int:pk>/weights/", JobWeightsView.as_view()),
    path("jobs/<int:pk>/submissions/", JobSubmissionsView.as_view()),
    
    # Submissions
    path("submit/", SubmitResumeView.as_view()),
    path("submissions/<int:pk>/", SubmissionDetailView.as_view()),
]
