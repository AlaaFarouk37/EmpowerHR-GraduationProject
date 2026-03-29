from rest_framework import serializers
from .models import (
    WeekendConfig,
    WorkingHoursConfig,
    Skill,
    JobRole,
    LeaveType,
    SpecialLeaveCase,
)
from .leave_calculator import (
    LeaveCalculationResult,
    LeaveEntitlement,
    SpecialCaseSummary,
    WorkingDayInfo,
)

class WeekendConfigSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model  = WeekendConfig
        fields = ['configID', 'day_of_week', 'day_name', 'createdAt', 'updatedAt']
        read_only_fields = ['configID', 'createdAt', 'updatedAt']


class WeekendConfigBulkSerializer(serializers.Serializer):
    weekend_days = serializers.ListField(
        child=serializers.IntegerField(min_value=0, max_value=6),
        allow_empty=True,
    )

class WorkingHoursConfigSerializer(serializers.ModelSerializer):
    working_hours_per_day = serializers.FloatField(read_only=True)

    class Meta:
        model  = WorkingHoursConfig
        fields = [
            'configID', 'work_start', 'work_end',
            'break_minutes', 'working_hours_per_day',
            'isActive', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['configID', 'working_hours_per_day', 'createdAt', 'updatedAt']

    def validate(self, data):
        start = data.get('work_start', getattr(self.instance, 'work_start', None))
        end   = data.get('work_end',   getattr(self.instance, 'work_end',   None))
        if start and end and start >= end:
            raise serializers.ValidationError(
                "work_end must be later than work_start."
            )
        return data

class SkillSerializer(serializers.ModelSerializer):
    level_display = serializers.SerializerMethodField()

    class Meta:
        model  = Skill
        fields = [
            'skillID', 'name', 'category', 'level',
            'level_display', 'description', 'isActive',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = ['skillID', 'createdAt', 'updatedAt']

    def get_level_display(self, obj):
        return '★' * obj.level + '☆' * (5 - obj.level)


class JobRoleSerializer(serializers.ModelSerializer):
    effective_annual_leave = serializers.SerializerMethodField()

    class Meta:
        model  = JobRole
        fields = [
            'roleID', 'title', 'department', 'level',
            'description', 'annual_leave_override',
            'effective_annual_leave', 'isActive',
            'createdAt', 'updatedAt',
        ]
        read_only_fields = ['roleID', 'createdAt', 'updatedAt']

    def get_effective_annual_leave(self, obj):
        return obj.annual_leave_override if obj.annual_leave_override is not None else 21


class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model  = LeaveType
        fields = [
            'leaveTypeID', 'name', 'category',
            'days_entitlement', 'days_entitlement_senior',
            'requires_medical_cert', 'counts_toward_service',
            'is_legally_mandated', 'description',
            'isActive', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['leaveTypeID', 'createdAt', 'updatedAt']

    def validate(self, data):

        instance = self.instance
        if instance and instance.is_legally_mandated:
            if data.get('isActive') is False:
                raise serializers.ValidationError(
                    f"'{instance.name}' is legally mandated and cannot be disabled."
                )
        return data

class SpecialLeaveCaseSerializer(serializers.ModelSerializer):
    employeeName     = serializers.CharField(source='employeeID.fullName',   read_only=True)
    employeeIDStr    = serializers.CharField(source='employeeID.employeeID', read_only=True)
    leave_type_label = serializers.CharField(source='get_leave_type_display', read_only=True)
    duration_days    = serializers.IntegerField(read_only=True)

    class Meta:
        model  = SpecialLeaveCase
        fields = [
            'caseID', 'employeeID', 'employeeName', 'employeeIDStr',
            'leave_type', 'leave_type_label',
            'start_date', 'end_date', 'duration_days',
            'notes', 'status', 'createdAt', 'updatedAt',
        ]
        read_only_fields = ['caseID', 'createdAt', 'updatedAt']

    def validate(self, data):
        start = data.get('start_date', getattr(self.instance, 'start_date', None))
        end   = data.get('end_date',   getattr(self.instance, 'end_date',   None))
        if start and end and end < start:
            raise serializers.ValidationError("end_date must be on or after start_date.")
        return data

class WorkingDayInfoSerializer(serializers.Serializer):
    weekend_days          = serializers.ListField(child=serializers.IntegerField())
    work_start            = serializers.TimeField()
    work_end              = serializers.TimeField()
    break_minutes         = serializers.IntegerField()
    working_hours_per_day = serializers.FloatField()


class LeaveEntitlementSerializer(serializers.Serializer):
    leave_type_id         = serializers.CharField()
    leave_type_name       = serializers.CharField()
    category              = serializers.CharField()
    days_entitled         = serializers.IntegerField(allow_null=True)
    requires_medical_cert = serializers.BooleanField()
    counts_toward_service = serializers.BooleanField()
    is_legally_mandated   = serializers.BooleanField()
    source                = serializers.CharField()
    notes                 = serializers.CharField()


class SpecialCaseSummarySerializer(serializers.Serializer):
    case_id    = serializers.CharField()
    leave_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date   = serializers.DateField()
    duration   = serializers.IntegerField()
    status     = serializers.CharField()
    notes      = serializers.CharField()


class LeaveCalculationResultSerializer(serializers.Serializer):
    employee_id      = serializers.CharField()
    employee_name    = serializers.CharField()
    years_of_service = serializers.FloatField()
    is_senior        = serializers.BooleanField()
    job_role         = serializers.CharField(allow_null=True)
    working_day_info = WorkingDayInfoSerializer()
    entitlements     = LeaveEntitlementSerializer(many=True)
    special_cases    = SpecialCaseSummarySerializer(many=True)
    warnings         = serializers.ListField(child=serializers.CharField())