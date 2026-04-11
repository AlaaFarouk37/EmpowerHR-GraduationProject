import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateAPIView
from accounts.permissions import IsHRManager, IsCandidate
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Job, Submission
from .serializers import JobSerializer, SubmissionSerializer, SubmissionUploadSerializer,CandidateJobSerializer
from .pipeline import run_pipeline, extract_skills

logger = logging.getLogger(__name__)


# ── Jobs ──────────────────────────────────────────────────────────────────────


class JobListCreateView(ListCreateAPIView):
    permission_classes = [IsAuthenticated, IsHRManager]

    queryset         = Job.objects.filter(is_active=True).order_by("-created_at")
    serializer_class = JobSerializer

    def perform_create(self, serializer):
        # Auto-extract required_skills from JD text when job is created
        description = serializer.validated_data.get("description", "")
        required_skills = extract_skills(description)
        serializer.save(required_skills=required_skills)



class JobDetailView(RetrieveUpdateAPIView):
    permission_classes = [IsHRManager]
    queryset         = Job.objects.all()
    serializer_class = JobSerializer


class JobWeightsView(APIView):
    """PATCH /api/jobs/{id}/weights/ — update only the four weights."""
    permission_classes = [IsAuthenticated, IsHRManager] 
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
    —Candidate-only endpoint. Requires JWT authentication with role='Candidate'. 
    """
    permission_classes = [IsCandidate]
    def post(self, request):
        serializer = SubmissionUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        submission = serializer.save(status=Submission.Status.PENDING, candidate_id=request.user)

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



class CandidateJobListView(APIView):
    """
    GET /api/resume_pipeline/jobs/
    — Candidate endpoint to see available openings.
    """
    # Use IsAuthenticated so we know who is applying, 
    # or AllowAny if you want the job board to be public.
    permission_classes = [AllowAny]

    def get(self, request):
        # We only want to show jobs that are active
        jobs = Job.objects.filter(is_active=True).order_by('-created_at')
        serializer = CandidateJobSerializer(jobs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class JobSubmissionsView(APIView):
    """GET /api/jobs/{id}/submissions/ — all results for a job, ranked by ATS score."""
    permission_classes = [IsAuthenticated, IsHRManager]
    def get(self, request, pk):
        submissions = (
            Submission.objects
            .filter(job_id=pk)
            .order_by("-ats_score")
        )
        return Response(SubmissionSerializer(submissions, many=True).data)


class SubmissionDetailView(APIView):
    permission_classes = [IsAuthenticated, IsHRManager]
    
    def get(self, request, pk):
        try:
            sub = Submission.objects.get(pk=pk)
            return Response(SubmissionSerializer(sub).data)
        except Submission.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    def patch(self, request, pk):
        try:
            sub = Submission.objects.get(pk=pk)
            # FIX: partial=True is mandatory for status updates
            serializer = SubmissionSerializer(sub, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Submission.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)