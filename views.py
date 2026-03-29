from rest_framework.views     import APIView
from rest_framework.response  import Response
from rest_framework           import status
from .models import (
    WeekendConfig,
    WorkingHoursConfig,
    Skill,
    JobRole,
    LeaveType,
    SpecialLeaveCase,
)
from .serializers import (
    WeekendConfigSerializer,
    WeekendConfigBulkSerializer,
    WorkingHoursConfigSerializer,
    SkillSerializer,
    JobRoleSerializer,
    LeaveTypeSerializer,
    SpecialLeaveCaseSerializer,
    LeaveCalculationResultSerializer,
)
from .leave_calculator import LeaveCalculator

def _get_object_or_404(model, pk, label='Object'):
    try:
        return model.objects.get(pk=pk)
    except model.DoesNotExist:
        return None


class WeekendConfigView(APIView):
    def get(self, request):
        qs = WeekendConfig.objects.all()
        serializer = WeekendConfigSerializer(qs, many=True)
        return Response({
            'weekend_days': serializer.data,
            'count': qs.count(),
        })

    def post(self, request):
        serializer = WeekendConfigBulkSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_days = set(serializer.validated_data['weekend_days'])

        # Delete days that are being removed
        WeekendConfig.objects.exclude(day_of_week__in=new_days).delete()

        # Create any days that don't already exist
        existing = set(WeekendConfig.objects.values_list('day_of_week', flat=True))
        for day in new_days - existing:
            WeekendConfig.objects.create(day_of_week=day)

        qs = WeekendConfig.objects.all()
        out = WeekendConfigSerializer(qs, many=True)
        return Response({
            'message':      'Weekend configuration updated.',
            'weekend_days': out.data,
        }, status=status.HTTP_200_OK)

class WorkingHoursConfigView(APIView):
    def get(self, request):
        cfg = (
            WorkingHoursConfig.objects
            .filter(isActive=True)
            .order_by('-createdAt')
            .first()
        )
        if not cfg:
            return Response(
                {'error': 'No active working hours configuration found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        return Response(WorkingHoursConfigSerializer(cfg).data)

    def post(self, request):
        serializer = WorkingHoursConfigSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Deactivate all existing configs
        WorkingHoursConfig.objects.filter(isActive=True).update(isActive=False)

        cfg = serializer.save(isActive=True)
        return Response(
            WorkingHoursConfigSerializer(cfg).data,
            status=status.HTTP_201_CREATED,
        )

class SkillListCreateView(APIView):
    def get(self, request):
        qs = Skill.objects.all()
        category = request.query_params.get('category')
        active   = request.query_params.get('active')
        if category:
            qs = qs.filter(category=category)
        if active is not None:
            qs = qs.filter(isActive=(active.lower() == 'true'))
        serializer = SkillSerializer(qs, many=True)
        return Response({'count': qs.count(), 'results': serializer.data})

    def post(self, request):
        serializer = SkillSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        skill = serializer.save()
        return Response(SkillSerializer(skill).data, status=status.HTTP_201_CREATED)


class SkillDetailView(APIView):
    def _get(self, pk):
        return _get_object_or_404(Skill, pk)

    def get(self, request, pk):
        skill = self._get(pk)
        if not skill:
            return Response({'error': 'Skill not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SkillSerializer(skill).data)

    def put(self, request, pk):
        skill = self._get(pk)
        if not skill:
            return Response({'error': 'Skill not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SkillSerializer(skill, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        skill = self._get(pk)
        if not skill:
            return Response({'error': 'Skill not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SkillSerializer(skill, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        skill = self._get(pk)
        if not skill:
            return Response({'error': 'Skill not found.'}, status=status.HTTP_404_NOT_FOUND)
        skill.isActive = False
        skill.save()
        return Response({'message': f"Skill '{skill.name}' deactivated."})


class JobRoleListCreateView(APIView):
    def get(self, request):
        qs = JobRole.objects.all()
        department = request.query_params.get('department')
        level      = request.query_params.get('level')
        active     = request.query_params.get('active')
        if department:
            qs = qs.filter(department__icontains=department)
        if level:
            qs = qs.filter(level=level)
        if active is not None:
            qs = qs.filter(isActive=(active.lower() == 'true'))
        return Response({'count': qs.count(), 'results': JobRoleSerializer(qs, many=True).data})

    def post(self, request):
        serializer = JobRoleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = serializer.save()
        return Response(JobRoleSerializer(role).data, status=status.HTTP_201_CREATED)


class JobRoleDetailView(APIView):
    def _get(self, pk):
        return _get_object_or_404(JobRole, pk)

    def get(self, request, pk):
        role = self._get(pk)
        if not role:
            return Response({'error': 'Job role not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(JobRoleSerializer(role).data)

    def put(self, request, pk):
        role = self._get(pk)
        if not role:
            return Response({'error': 'Job role not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = JobRoleSerializer(role, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        role = self._get(pk)
        if not role:
            return Response({'error': 'Job role not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = JobRoleSerializer(role, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        role = self._get(pk)
        if not role:
            return Response({'error': 'Job role not found.'}, status=status.HTTP_404_NOT_FOUND)
        role.isActive = False
        role.save()
        return Response({'message': f"Job role '{role.title}' deactivated."})

class LeaveTypeListCreateView(APIView):
    def get(self, request):
        qs = LeaveType.objects.all()
        category = request.query_params.get('category')
        active   = request.query_params.get('active')
        if category:
            qs = qs.filter(category=category)
        if active is not None:
            qs = qs.filter(isActive=(active.lower() == 'true'))
        return Response({'count': qs.count(), 'results': LeaveTypeSerializer(qs, many=True).data})

    def post(self, request):
        serializer = LeaveTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lt = serializer.save()
        return Response(LeaveTypeSerializer(lt).data, status=status.HTTP_201_CREATED)


class LeaveTypeDetailView(APIView):
    def _get(self, pk):
        return _get_object_or_404(LeaveType, pk)

    def get(self, request, pk):
        lt = self._get(pk)
        if not lt:
            return Response({'error': 'Leave type not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(LeaveTypeSerializer(lt).data)

    def put(self, request, pk):
        lt = self._get(pk)
        if not lt:
            return Response({'error': 'Leave type not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = LeaveTypeSerializer(lt, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        lt = self._get(pk)
        if not lt:
            return Response({'error': 'Leave type not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = LeaveTypeSerializer(lt, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        lt = self._get(pk)
        if not lt:
            return Response({'error': 'Leave type not found.'}, status=status.HTTP_404_NOT_FOUND)
        if lt.is_legally_mandated:
            return Response(
                {'error': f"'{lt.name}' is legally mandated and cannot be deleted."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        lt.isActive = False
        lt.save()
        return Response({'message': f"Leave type '{lt.name}' deactivated."})


class SpecialLeaveListCreateView(APIView):
    def get(self, request):
        qs = SpecialLeaveCase.objects.select_related('employeeID').all()
        employee_id = request.query_params.get('employee_id')
        leave_type  = request.query_params.get('leave_type')
        status_filter = request.query_params.get('status')
        if employee_id:
            qs = qs.filter(employeeID_id=employee_id)
        if leave_type:
            qs = qs.filter(leave_type=leave_type)
        if status_filter:
            qs = qs.filter(status=status_filter)
        return Response({
            'count':   qs.count(),
            'results': SpecialLeaveCaseSerializer(qs, many=True).data,
        })

    def post(self, request):
        serializer = SpecialLeaveCaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        case = serializer.save()
        return Response(
            SpecialLeaveCaseSerializer(case).data,
            status=status.HTTP_201_CREATED,
        )


class SpecialLeaveDetailView(APIView):

    def _get(self, pk):
        return _get_object_or_404(SpecialLeaveCase, pk)

    def get(self, request, pk):
        case = self._get(pk)
        if not case:
            return Response({'error': 'Case not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SpecialLeaveCaseSerializer(case).data)

    def patch(self, request, pk):
        case = self._get(pk)
        if not case:
            return Response({'error': 'Case not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = SpecialLeaveCaseSerializer(case, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        case = self._get(pk)
        if not case:
            return Response({'error': 'Case not found.'}, status=status.HTTP_404_NOT_FOUND)
        case.delete()
        return Response({'message': 'Special leave case deleted.'}, status=status.HTTP_204_NO_CONTENT)


class LeaveCalculationView(APIView):
    def get(self, request, employee_id):
        from feedback.models import Employee

        try:
            employee = Employee.objects.get(employeeID=employee_id)
        except Employee.DoesNotExist:
            return Response(
                {'error': f"Employee '{employee_id}' not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        result     = LeaveCalculator(employee).calculate()
        serializer = LeaveCalculationResultSerializer(result)
        return Response(serializer.data)