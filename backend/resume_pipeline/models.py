from django.db import models
from django.conf import settings
import employee_management


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

  #  job             = models.ForeignKey(employee_management.models.Job, on_delete=models.CASCADE, related_name="submissions")

    # candidate = models.ForeignKey(
    #               #  Candidate,
    #                 on_delete=models.SET_NULL,
    #                 null=True, blank=True,
    #                 related_name='applying')
    
    # candidate_name  =   candidate.first_name + " " + candidate.last_name if candidate else "Unknown Candidate"
    # candidate_email = candidate.contact_email if candidate else "null"
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
    


class Candidate(models.Model):
    # Link to the User for login credentials (email/pass)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='candidate_profile'
    )

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    contact_email = models.EmailField()
    gender = models.CharField(max_length=20, choices=[('Male', 'Male'), ('Female', 'Female'), ('Other', 'Other')])
    marital_status = models.CharField(max_length=50, blank=True, null=True)
    has_disability = models.BooleanField(default=False)
    location = models.CharField(max_length=255)
    current_job_title = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.full_name
   
