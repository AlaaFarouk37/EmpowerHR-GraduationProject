import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from accounts.permissions import IsHRManager, IsCandidate
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Job, Submission
from .serializers import JobSerializer, SubmissionSerializer, SubmissionUploadSerializer
from .pipeline import run_pipeline, extract_skills

logger = logging.getLogger(__name__)


# ── Jobs ──────────────────────────────────────────────────────────────────────


class JobListCreateView(ListCreateAPIView):
    
    queryset         = Job.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        # Auto-extract required_skills from JD text when job is created
        description = serializer.validated_data.get("description", "")
        required_skills = extract_skills(description)
        serializer.save(required_skills=required_skills)
    def get_permissions(self):
        if self.request.method == 'GET':
            return [IsAuthenticated()]
        return [IsHRManager()] 


class JobDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsHRManager]
    queryset         = Job.objects.all()
    serializer_class = JobSerializer


class JobWeightsView(APIView):
    """PATCH /api/jobs/{id}/weights/ — update only the four weights."""
    permission_classes = [IsHRManager]

    def patch(self, request, pk):
        try:
            job = Job.objects.get(pk=pk)
        except Job.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        fields = ["weight_skills", "weight_experience", "weight_education", "weight_semantic"]
        for f in fields:
            if f in request.data:
                setattr(job, f, float(request.data[f]))

        total = round(job.weight_skills + job.weight_experience +
                      job.weight_education + job.weight_semantic, 10)
        if abs(total - 1.0) > 0.001:
            return Response(
                {"detail": f"Weights must sum to 1.0. Got: {total:.3f}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        job.save()
        return Response(JobSerializer(job).data)


# ── Submissions ───────────────────────────────────────────────────────────────

class SubmitResumeView(APIView):
    """
    POST /api/submit/
    Public endpoint — no auth required.
    Accepts multipart/form-data with: job, candidate_name, candidate_email, resume_file
    Runs the full pipeline synchronously and returns results.
    """
    permission_classes = [IsCandidate]
    def post(self, request):
        serializer = SubmissionUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission = serializer.save(status=Submission.Status.PENDING)

        try:
            run_pipeline(submission)
            submission.refresh_from_db()
            return Response(
                SubmissionSerializer(submission).data,
                status=status.HTTP_201_CREATED,
            )
        except Exception as exc:
            return Response(
                {"detail": f"Pipeline failed: {str(exc)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class JobSubmissionsView(APIView):
    """GET /api/jobs/{id}/submissions/ — all results for a job, ranked by ATS score."""
    permission_classes = [IsHRManager]
    def get(self, request, pk):
        submissions = (
            Submission.objects
            .filter(job_id=pk, status=Submission.Status.DONE)
            .order_by("-ats_score")
        )
        return Response(SubmissionSerializer(submissions, many=True).data)


class SubmissionDetailView(APIView):
    """GET /api/submissions/{id}/"""
    permission_classes = [IsHRManager]
    def get(self, request, pk):
        try:
            sub = Submission.objects.get(pk=pk)
        except Submission.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubmissionSerializer(sub).data)
