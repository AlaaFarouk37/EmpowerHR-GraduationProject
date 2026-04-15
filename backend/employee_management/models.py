from django.db import models

from django.conf import settings


# --- INFRASTRUCTURE TABLES (Admin Only) ---
class Department(models.Model):
    department_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Team(models.Model):
    team_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='teams')

    def __str__(self):
        return self.name

class Job(models.Model):
    job_id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    level = models.PositiveIntegerField(default=1)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2)
    benchmark_salary = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.title} (Level {self.level})"

class LeaveType(models.Model):
    leave_type_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50) # e.g. Sick, Annual, Casual
    max_days_per_year = models.PositiveIntegerField()

    def __str__(self):
        return self.name
    
class LeaveEntitlement(models.Model):
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)
    employee_profile = models.ForeignKey(
        'Employee', 
        on_delete=models.CASCADE, 
        related_name='leave_entitlements'
    )
    used_days = models.PositiveIntegerField(default=0)
    remaining_days = models.PositiveIntegerField(default=0)
    max_days_per_year = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='Active')

    def save(self, *args, **kwargs):
        # Automatically calculate remaining days before saving
        self.remaining_days = self.max_days_per_year - self.used_days
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee.full_name} - {self.leave_type.name}"    
    
# 1. BASE EMPLOYEE (HR, TM, TL)
class Employee(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='employee_profile')
    
    # Base Professional Fields
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=20)
    marital_status = models.CharField(max_length=30)
    number_of_dependents = models.PositiveIntegerField(default=0)
    has_disability = models.BooleanField(default=False)
    Location = models.CharField(max_length=100)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True)
    team = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True)
    job = models.ForeignKey(Job, on_delete=models.SET_NULL, null=True)
    education_level = models.CharField(max_length=100) # High School, Bachelor's, Master's, PhD

    # Employment Data
    employment_type = models.CharField(max_length=50) # Full-time, Part-time
    hire_date = models.DateField(null=True, blank=True)
    years_at_company = models.PositiveIntegerField(default=0)
    number_of_promotions = models.PositiveIntegerField(default=0)
    monthly_income = models.DecimalField(max_digits=10, decimal_places=2)
    PhoneNumber = models.CharField(max_length=20, null=True, blank=True)
    
    # Scheduling
    default_clock_in = models.TimeField(null=True, blank=True)
    default_clock_out = models.TimeField(null=True, blank=True)
    contracted_hours = models.PositiveIntegerField(default=40)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"    