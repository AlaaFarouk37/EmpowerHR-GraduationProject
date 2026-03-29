from django.contrib import admin
from django.utils.html import format_html
from .models import (
    WeekendConfig,
    WorkingHoursConfig,
    Skill,
    JobRole,
    LeaveType,
    SpecialLeaveCase,
)


@admin.register(WeekendConfig)
class WeekendConfigAdmin(admin.ModelAdmin):
    list_display  = ['get_day_name', 'day_of_week', 'createdAt']
    ordering      = ['day_of_week']
    readonly_fields = ['configID', 'createdAt', 'updatedAt']

    def get_day_name(self, obj):
        return obj.get_day_of_week_display()
    get_day_name.short_description = 'Weekend Day'


@admin.register(WorkingHoursConfig)
class WorkingHoursConfigAdmin(admin.ModelAdmin):
    list_display    = ['work_start', 'work_end', 'break_minutes', 'get_daily_hours', 'isActive']
    list_filter     = ['isActive']
    readonly_fields = ['configID', 'createdAt', 'updatedAt']

    def get_daily_hours(self, obj):
        return f"{obj.working_hours_per_day} hrs/day"
    get_daily_hours.short_description = 'Effective Hours'

@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display    = ['name', 'category', 'get_level_stars', 'isActive', 'createdAt']
    list_filter     = ['category', 'level', 'isActive']
    search_fields   = ['name', 'description']
    readonly_fields = ['skillID', 'createdAt', 'updatedAt']
    ordering        = ['category', 'name']
    list_editable   = ['isActive']

    def get_level_stars(self, obj):
        return '★' * obj.level + '☆' * (5 - obj.level)
    get_level_stars.short_description = 'Level'

@admin.register(JobRole)
class JobRoleAdmin(admin.ModelAdmin):
    list_display    = ['title', 'department', 'level', 'annual_leave_override', 'isActive']
    list_filter     = ['level', 'department', 'isActive']
    search_fields   = ['title', 'department', 'description']
    readonly_fields = ['roleID', 'createdAt', 'updatedAt']
    ordering        = ['department', 'title']
    list_editable   = ['isActive']
    fieldsets = (
        ('Role Info', {
            'fields': ('roleID', 'title', 'department', 'level', 'description')
        }),
        ('Leave Policy', {
            'fields': ('annual_leave_override',),
            'description': 'Override annual leave days for this role. '
                           'Leave blank to use the system default (21 or 30 days per Egyptian law).'
        }),
        ('Status & Timestamps', {
            'fields': ('isActive', 'createdAt', 'updatedAt'),
            'classes': ('collapse',),
        }),
    )


@admin.register(LeaveType)
class LeaveTypeAdmin(admin.ModelAdmin):
    list_display  = [
        'name', 'category', 'get_days', 'requires_medical_cert',
        'counts_toward_service', 'is_legally_mandated', 'isActive'
    ]
    list_filter   = ['category', 'requires_medical_cert', 'is_legally_mandated', 'isActive']
    search_fields = ['name', 'description']
    readonly_fields = ['leaveTypeID', 'createdAt', 'updatedAt']
    list_editable = ['isActive']
    ordering      = ['category', 'name']
    fieldsets = (
        ('Leave Type Info', {
            'fields': ('leaveTypeID', 'name', 'category', 'description')
        }),
        ('Entitlement', {
            'fields': ('days_entitlement', 'days_entitlement_senior'),
            'description': 'days_entitlement_senior applies when the employee has ≥10 years of service.'
        }),
        ('Policy Rules', {
            'fields': (
                'requires_medical_cert',
                'counts_toward_service',
                'is_legally_mandated',
            )
        }),
        ('Status & Timestamps', {
            'fields': ('isActive', 'createdAt', 'updatedAt'),
            'classes': ('collapse',),
        }),
    )

    def get_days(self, obj):
        if obj.days_entitlement is None:
            return '—'
        label = f"{obj.days_entitlement} days"
        if obj.days_entitlement_senior:
            label += f" / {obj.days_entitlement_senior} (senior)"
        return label
    get_days.short_description = 'Days Entitlement'

    def has_delete_permission(self, request, obj=None):
        # Prevent deletion of legally-mandated leave types
        if obj and obj.is_legally_mandated:
            return False
        return super().has_delete_permission(request, obj)

@admin.register(SpecialLeaveCase)
class SpecialLeaveCaseAdmin(admin.ModelAdmin):
    list_display    = [
        'caseID', 'get_employee_name', 'leave_type',
        'start_date', 'end_date', 'get_duration', 'status'
    ]
    list_filter     = ['leave_type', 'status']
    search_fields   = ['employeeID__fullName', 'employeeID__employeeID', 'notes']
    readonly_fields = ['caseID', 'createdAt', 'updatedAt']
    ordering        = ['-start_date']
    list_editable   = ['status']
    date_hierarchy  = 'start_date'

    def get_employee_name(self, obj):
        return obj.employeeID.fullName
    get_employee_name.short_description = 'Employee'

    def get_duration(self, obj):
        return f"{obj.duration_days} days"
    get_duration.short_description = 'Duration'

    def get_colored_status(self, obj):
        colors = {
            'Active':    'green',
            'Completed': 'gray',
            'Cancelled': 'red',
        }
        color = colors.get(obj.status, 'black')
        return format_html(
            '<span style="color:{}; font-weight:bold;">{}</span>',
            color, obj.status
        )
    get_colored_status.short_description = 'Status'