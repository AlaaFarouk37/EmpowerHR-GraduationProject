from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver




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

    # Identification Field
    user_id  = models.CharField(max_length=50, null=True, blank=True, unique=True)


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
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """
        Assigns the unified user_id automatically upon creation based on the user's role.
        """
        if not self.pk:  # Only trigger for new registrations
            
            # Ensure we only generate if user_id hasn't been manually set
            if not self.user_id:
                # 1. Handle Candidates (Prefix C)
                if self.role == self.Role.CANDIDATE:
                    self.user_id = generate_portal_id("C", "user_id")
                
                # 2. Handle Team Members (Prefix TM)
                elif self.role == self.Role.TEAM_MEMBER:
                    self.user_id = generate_portal_id("TM", "user_id")
                
                # 3. Handle Team Leaders (Prefix TL)
                elif self.role == self.Role.TEAM_LEADER:
                    self.user_id = generate_portal_id("TL", "user_id")
                
                # 4. Handle HR Managers and Admins (Prefix HR)
                elif self.role in [self.Role.HR_MANAGER, self.Role.ADMIN]:
                    self.user_id = generate_portal_id("HR", "user_id")

        super().save(*args, **kwargs)
        
        super().save(*args, **kwargs)



# accounts/models.py
# @receiver(post_save, sender=User)
# def create_user_profile(sender, instance, created, **kwargs):
#     if created:
#         if instance.role == 'Candidate':
#             Candidate.objects.create(user=instance)
#         elif instance.role in ['Team Member', 'Team Leader', 'HR Manager']:
#             Employee.objects.create(user=instance)  