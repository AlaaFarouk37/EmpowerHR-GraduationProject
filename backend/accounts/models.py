from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


def generate_portal_id(prefix, field_name):
    """
    Generates the next ID based on a specific prefix (e.g., TM, TL, HR, C).
    """
    from .models import User
    
    # Dynamically filter based on the field (employee_id or candidate_id)
    filter_kwargs = {f"{field_name}__startswith": prefix}
    last = User.objects.filter(**filter_kwargs).order_by(field_name).last()
    
    if not last:
        return f"{prefix}00001"
    
    # Get the actual value from the field
    last_id = getattr(last, field_name)
    
    try:
        # Strip the prefix to get the number and increment
        num_part = last_id.replace(prefix, "")
        num = int(num_part)
        return f"{prefix}{num + 1:05d}"
    except ValueError:
        return f"{prefix}00001"

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", "Admin")
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

class User(AbstractBaseUser, PermissionsMixin):
    """
    Single auth table for Empower HR.
    IDs are auto-generated based on role:
    Candidate -> C00001, TeamMember -> TM00001, TeamLeader -> TL00001, HR/Admin -> HR00001
    """

    class Role(models.TextChoices):
        CANDIDATE    = "Candidate",   "Candidate"
        TEAM_MEMBER  = "TeamMember",  "Team Member"
        TEAM_LEADER  = "TeamLeader",  "Team Leader"
        HR_MANAGER   = "HRManager",   "HR Manager"
        ADMIN        = "Admin",       "Admin"

    # Core Fields
    email       = models.EmailField(unique=True)
    full_name   = models.CharField(max_length=150)
    role        = models.CharField(max_length=20, choices=Role.choices)

    # Identification Fields
    employee_id  = models.CharField(max_length=50, null=True, blank=True, unique=True)
    candidate_id = models.CharField(max_length=50, null=True, blank=True, unique=True)

    # Status & Metadata
    is_active   = models.BooleanField(default=True)
    is_staff    = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    class Meta:
        db_table = "auth_user"

    def __str__(self):
        return f"{self.email} ({self.role})"

    def save(self, *args, **kwargs):
        """
        Assigns IDs automatically upon creation based on the user's role.
        """
        if not self.pk:  # Only trigger for new registrations
            
            # 1. Handle Candidates
            if self.role == self.Role.CANDIDATE:
                if not self.candidate_id:
                    self.candidate_id = generate_portal_id("C", "candidate_id")
            
            # 2. Handle Team Members
            elif self.role == self.Role.TEAM_MEMBER:
                if not self.employee_id:
                    self.employee_id = generate_portal_id("TM", "employee_id")
            
            # 3. Handle Team Leaders
            elif self.role == self.Role.TEAM_LEADER:
                if not self.employee_id:
                    self.employee_id = generate_portal_id("TL", "employee_id")
            
            # 4. Handle HR Managers and Admins (Shared HR Prefix)
            elif self.role in [self.Role.HR_MANAGER, self.Role.ADMIN]:
                if not self.employee_id:
                    self.employee_id = generate_portal_id("HR", "employee_id")
        
        super().save(*args, **kwargs)

    @property
    def is_candidate(self):
        return self.role == self.Role.CANDIDATE

    @property
    def is_employee(self):
        return self.role != self.Role.CANDIDATE