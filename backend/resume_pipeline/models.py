from django.db import models
from core import settings


class Job(models.Model):
    """A job posting with its JD text and scoring weights."""
    title                = models.CharField(max_length=255)
    description          = models.TextField(help_text="Full job description text")
    required_skills      = models.JSONField(default=list)   # extracted from JD automatically
    min_experience_years = models.FloatField(default=0)
    required_degree      = models.CharField(max_length=20, default="Unknown")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_jobs')

    # User-defined weights (must sum to 1.0)
    weight_skills     = models.FloatField(default=0.40)
    weight_experience = models.FloatField(default=0.30)
    weight_education  = models.FloatField(default=0.10)
    weight_semantic   = models.FloatField(default=0.20)

    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Submission(models.Model):
    """A candidate resume submitted against a Job."""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('shortlisted', 'Shortlisted'),
        ('in-progress', 'In-Progress'),
        ('rejected', 'Rejected'),
        ('approved', 'Approved'),
    ]

    constraints = [
            models.UniqueConstraint(
                fields=['candidate_id', 'job'], 
                name='unique_application'
            )
    ]

    job             = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="submissions")
    candidate_id = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True, blank=True,
                    related_name='applying')
    candidate_name  = models.CharField(max_length=255, blank=True)
    candidate_email = models.EmailField(blank=True)
    resume_file     = models.FileField(upload_to="resumes/")
    status = models.CharField(choices=STATUS_CHOICES, default='pending', max_length=20)  
    # ── Extracted fields ──────────────────────────────────────────────────────
    raw_text               = models.TextField(blank=True)
    candidate_skills       = models.JSONField(default=list)
    candidate_degree       = models.CharField(max_length=20, default="Unknown")
    candidate_years_exp    = models.FloatField(default=0.0)
    exp_extraction_method  = models.CharField(max_length=50, blank=True)

    # ── Scores (0–100) ────────────────────────────────────────────────────────
    skills_score     = models.FloatField(null=True)
    experience_score = models.FloatField(null=True)
    education_score  = models.FloatField(null=True)
    semantic_score   = models.FloatField(null=True)   # stored as 0–100
    ats_score        = models.FloatField(null=True)

    submitted_at = models.DateTimeField(auto_now_add=True)
    scored_at    = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-ats_score"]

    def __str__(self):
        return f"{self.candidate_name or 'Candidate'} → {self.job.title}"
