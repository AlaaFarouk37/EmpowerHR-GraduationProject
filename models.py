import uuid
from django.db import models


def gen_id():
    return uuid.uuid4().hex[:20]

class WeekendConfig(models.Model):
    """
    Stores which days of the week are weekends (non-working).
    """
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    configID    = models.CharField(max_length=50, primary_key=True, default=gen_id)
    day_of_week = models.IntegerField(choices=DAY_CHOICES, unique=True)
    createdAt   = models.DateTimeField(auto_now_add=True)
    updatedAt   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'WeekendConfig'
        ordering = ['day_of_week']

    def __str__(self):
        return self.get_day_of_week_display()


class WorkingHoursConfig(models.Model):
    configID       = models.CharField(max_length=50, primary_key=True, default=gen_id)
    work_start     = models.TimeField(default='09:00')
    work_end       = models.TimeField(default='17:00')
    break_minutes  = models.PositiveIntegerField(default=60)
    isActive       = models.BooleanField(default=True)
    createdAt      = models.DateTimeField(auto_now_add=True)
    updatedAt      = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'WorkingHoursConfig'

    def __str__(self):
        return f"Working hours: {self.work_start}–{self.work_end} ({self.break_minutes} min break)"

    @property
    def working_hours_per_day(self):
        from datetime import datetime, date
        start = datetime.combine(date.today(), self.work_start)
        end   = datetime.combine(date.today(), self.work_end)
        total_minutes = (end - start).seconds // 60 - self.break_minutes
        return round(total_minutes / 60, 2)

class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('Technical',        'Technical'),
        ('Soft Skills',      'Soft Skills'),
        ('Management',       'Management'),
        ('Domain Knowledge', 'Domain Knowledge'),
        ('Certification',    'Certification'),
    ]
    LEVEL_CHOICES = [(i, str(i)) for i in range(1, 6)]

    skillID     = models.CharField(max_length=50, primary_key=True, default=gen_id)
    name        = models.CharField(max_length=100, unique=True)
    category    = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Technical')
    level       = models.IntegerField(choices=LEVEL_CHOICES, default=1)
    description = models.TextField(blank=True, null=True)
    isActive    = models.BooleanField(default=True)
    createdAt   = models.DateTimeField(auto_now_add=True)
    updatedAt   = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Skill'
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.name} ({self.category} – L{self.level})"


class JobRole(models.Model):
    LEVEL_CHOICES = [
        ('Junior',    'Junior'),
        ('Mid',       'Mid'),
        ('Senior',    'Senior'),
        ('Lead',      'Lead'),
        ('Manager',   'Manager'),
        ('Director',  'Director'),
        ('C-Level',   'C-Level'),
    ]

    roleID              = models.CharField(max_length=50, primary_key=True, default=gen_id)
    title               = models.CharField(max_length=150)
    department          = models.CharField(max_length=100, blank=True, null=True)
    level               = models.CharField(max_length=20, choices=LEVEL_CHOICES, default='Mid')
    description         = models.TextField(blank=True, null=True)

    annual_leave_override = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Override the system annual leave days for this role. Leave blank to use the default."
    )
    isActive            = models.BooleanField(default=True)
    createdAt           = models.DateTimeField(auto_now_add=True)
    updatedAt           = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'JobRole'
        ordering = ['department', 'title']
        unique_together = [('title', 'department')]

    def __str__(self):
        return f"{self.title} – {self.department or 'No dept'} ({self.level})"

class LeaveType(models.Model):
    CATEGORY_PAID    = 'Paid'
    CATEGORY_UNPAID  = 'Unpaid'
    CATEGORY_SPECIAL = 'Special'
    CATEGORY_CHOICES = [
        (CATEGORY_PAID,    'Paid'),
        (CATEGORY_UNPAID,  'Unpaid'),
        (CATEGORY_SPECIAL, 'Special'),
    ]

    leaveTypeID              = models.CharField(max_length=50, primary_key=True, default=gen_id)
    name                     = models.CharField(max_length=100, unique=True)
    category                 = models.CharField(max_length=20, choices=CATEGORY_CHOICES)

    days_entitlement         = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Number of days per year.  NULL = variable / governed by policy."
    )

    days_entitlement_senior  = models.PositiveIntegerField(
        blank=True, null=True,
        help_text="Entitlement for employees with ≥10 years of service (annual leave rule)."
    )
    requires_medical_cert    = models.BooleanField(default=False)
    counts_toward_service    = models.BooleanField(default=True)
    is_legally_mandated      = models.BooleanField(default=False)
    description              = models.TextField(blank=True, null=True)
    isActive                 = models.BooleanField(default=True)
    createdAt                = models.DateTimeField(auto_now_add=True)
    updatedAt                = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'LeaveType'
        ordering = ['category', 'name']

    def __str__(self):
        days = f"{self.days_entitlement}d" if self.days_entitlement else "variable"
        return f"{self.name} ({self.category}, {days})"

class SpecialLeaveCase(models.Model):
    TYPE_PAID      = 'paid'
    TYPE_PREGNANCY = 'pregnancy'
    TYPE_EMERGENCY = 'emergency'

    TYPE_CHOICES = [
        (TYPE_PAID,      'Paid special leave (disability)'),
        (TYPE_PREGNANCY, 'Pregnancy leave'),
        (TYPE_EMERGENCY, 'Emergency leave'),
    ]

    STATUS_ACTIVE    = 'Active'
    STATUS_COMPLETED = 'Completed'
    STATUS_CANCELLED = 'Cancelled'
    STATUS_CHOICES = [
        (STATUS_ACTIVE,    'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    caseID     = models.CharField(max_length=50, primary_key=True, default=gen_id)
    employeeID = models.ForeignKey(
        'feedback.Employee',
        on_delete=models.CASCADE,
        db_column='employeeID',
        related_name='special_leave_cases'
    )
    leave_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    start_date = models.DateField()
    end_date   = models.DateField()
    notes      = models.TextField(blank=True, null=True)
    status     = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    createdAt  = models.DateTimeField(auto_now_add=True)
    updatedAt  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'SpecialLeaveCase'
        ordering = ['-start_date']

    def __str__(self):
        return (f"{self.get_leave_type_display()} – "
                f"{self.employeeID_id} "
                f"({self.start_date} → {self.end_date})")

    @property
    def duration_days(self):
        return (self.end_date - self.start_date).days + 1