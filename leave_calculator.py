from __future__ import annotations
import datetime
from dataclasses import dataclass, field
from typing import List, Optional

from .models import (
    WeekendConfig,
    WorkingHoursConfig,
    JobRole,
    LeaveType,
    SpecialLeaveCase,
)
@dataclass
class LeaveEntitlement:
    """Resolved entitlement for a single leave type."""
    leave_type_id:        str
    leave_type_name:      str
    category:             str          # Paid / Unpaid / Special
    days_entitled:        Optional[int]  # None = variable
    requires_medical_cert: bool
    counts_toward_service: bool
    is_legally_mandated:  bool
    source:               str          # 'law' | 'role_override' | 'special_case' | 'policy'
    notes:                str = ''


@dataclass
class SpecialCaseSummary:
    case_id:    str
    leave_type: str
    start_date: datetime.date
    end_date:   datetime.date
    duration:   int    # calendar days
    status:     str
    notes:      str


@dataclass
class WorkingDayInfo:
    weekend_days:        List[int]   # 0=Mon … 6=Sun
    work_start:          datetime.time
    work_end:            datetime.time
    break_minutes:       int
    working_hours_per_day: float


@dataclass
class LeaveCalculationResult:
    employee_id:         str
    employee_name:       str
    years_of_service:    float
    is_senior:           bool           # ≥ 10 years
    job_role:            Optional[str]
    working_day_info:    WorkingDayInfo
    entitlements:        List[LeaveEntitlement]
    special_cases:       List[SpecialCaseSummary]
    warnings:            List[str]

class LeaveCalculator:
    SENIORITY_THRESHOLD = 10   # years of service for enhanced annual leave

    def __init__(self, employee, reference_date: Optional[datetime.date] = None):
        self.employee       = employee
        self.reference_date = reference_date or datetime.date.today()
        self.warnings: List[str] = []


    def calculate(self) -> LeaveCalculationResult:
        working_day_info  = self._step1_working_day_info()
        years_of_service  = self._step2_years_of_service()
        is_senior         = years_of_service >= self.SENIORITY_THRESHOLD
        job_role          = self._step3_resolve_job_role()
        entitlements      = self._step4_resolve_entitlements(is_senior, job_role)
        special_cases     = self._step5_special_cases()

        return LeaveCalculationResult(
            employee_id       = self.employee.employeeID,
            employee_name     = self.employee.fullName,
            years_of_service  = round(years_of_service, 2),
            is_senior         = is_senior,
            job_role          = job_role.title if job_role else None,
            working_day_info  = working_day_info,
            entitlements      = entitlements,
            special_cases     = special_cases,
            warnings          = self.warnings,
        )

    # ── STEP 1: Working day info ──────────────────────────────────
    def _step1_working_day_info(self) -> WorkingDayInfo:
        # Weekend days
        weekend_days = list(
            WeekendConfig.objects.values_list('day_of_week', flat=True)
        )
        if not weekend_days:
            self.warnings.append(
                "No weekend days configured. Defaulting to Friday (4) and Saturday (5)."
            )
            weekend_days = [4, 5]

        # Working hours
        hours_cfg = (
            WorkingHoursConfig.objects
            .filter(isActive=True)
            .order_by('-createdAt')
            .first()
        )
        if not hours_cfg:
            self.warnings.append(
                "No active WorkingHoursConfig found. Using default 09:00–17:00."
            )
            return WorkingDayInfo(
                weekend_days         = weekend_days,
                work_start           = datetime.time(9, 0),
                work_end             = datetime.time(17, 0),
                break_minutes        = 60,
                working_hours_per_day= 7.0,
            )

        return WorkingDayInfo(
            weekend_days          = weekend_days,
            work_start            = hours_cfg.work_start,
            work_end              = hours_cfg.work_end,
            break_minutes         = hours_cfg.break_minutes,
            working_hours_per_day = hours_cfg.working_hours_per_day,
        )

    # ── STEP 2: Years of service ──────────────────────────────────
    def _step2_years_of_service(self) -> float:
        years = getattr(self.employee, 'yearsAtCompany', None)
        if years is not None:
            return float(years)

        # Fallback: compute from hire_date if available
        hire_date = getattr(self.employee, 'hireDate', None)
        if hire_date:
            delta = self.reference_date - hire_date
            return delta.days / 365.25

        self.warnings.append(
            "Could not determine years of service; defaulting to 0."
        )
        return 0.0

    # ── STEP 3: Resolve job role ──────────────────────────────────
    def _step3_resolve_job_role(self) -> Optional[JobRole]:
        job_title = getattr(self.employee, 'jobTitle', None)
        department = getattr(self.employee, 'department', None)
        if not job_title:
            return None
        qs = JobRole.objects.filter(isActive=True, title=job_title)
        if department:
            qs_dept = qs.filter(department=department)
            if qs_dept.exists():
                return qs_dept.first()
        return qs.first()

    # ── STEP 4: Resolve all entitlements ─────────────────────────
    def _step4_resolve_entitlements(
        self,
        is_senior: bool,
        job_role: Optional[JobRole],
    ) -> List[LeaveEntitlement]:

        active_leave_types = LeaveType.objects.filter(isActive=True)
        entitlements: List[LeaveEntitlement] = []

        for lt in active_leave_types:
            days   = lt.days_entitlement
            source = 'law' if lt.is_legally_mandated else 'policy'
            notes  = ''

            # ── Egyptian law: seniority upgrade for annual leave ──
            if (
                lt.is_legally_mandated
                and 'annual' in lt.name.lower()
                and is_senior
                and lt.days_entitlement_senior is not None
            ):
                days   = lt.days_entitlement_senior
                source = 'law'
                notes  = f"Senior employee (≥{self.SENIORITY_THRESHOLD} yrs): entitlement upgraded to {days} days."

            # ── Job role override ──────────────────────────────────
            if (
                job_role
                and job_role.annual_leave_override is not None
                and 'annual' in lt.name.lower()
            ):
                days   = job_role.annual_leave_override
                source = 'role_override'
                notes  = (
                    f"Role override applied ({job_role.title}): {days} days. "
                    + (notes or '')
                ).strip()

            entitlements.append(LeaveEntitlement(
                leave_type_id         = lt.leaveTypeID,
                leave_type_name       = lt.name,
                category              = lt.category,
                days_entitled         = days,
                requires_medical_cert = lt.requires_medical_cert,
                counts_toward_service = lt.counts_toward_service,
                is_legally_mandated   = lt.is_legally_mandated,
                source                = source,
                notes                 = notes,
            ))

        if not entitlements:
            self.warnings.append("No active leave types found in the database.")

        return entitlements

    # ── STEP 5: Special leave cases ───────────────────────────────
    def _step5_special_cases(self) -> List[SpecialCaseSummary]:
        cases = SpecialLeaveCase.objects.filter(
            employeeID=self.employee,
            status=SpecialLeaveCase.STATUS_ACTIVE,
        ).order_by('-start_date')

        result: List[SpecialCaseSummary] = []
        for c in cases:
            result.append(SpecialCaseSummary(
                case_id    = c.caseID,
                leave_type = c.get_leave_type_display(),
                start_date = c.start_date,
                end_date   = c.end_date,
                duration   = c.duration_days,
                status     = c.status,
                notes      = c.notes or '',
            ))
        return result


def count_working_days(
    start_date: datetime.date,
    end_date: datetime.date,
    weekend_days: Optional[List[int]] = None,
) -> int:
    if weekend_days is None:
        weekend_days = list(
            WeekendConfig.objects.values_list('day_of_week', flat=True)
        ) or [4, 5]

    count = 0
    current = start_date
    while current <= end_date:
        if current.weekday() not in weekend_days:
            count += 1
        current += datetime.timedelta(days=1)
    return count


def get_annual_leave_days(employee) -> int:
    result = LeaveCalculator(employee).calculate()
    for e in result.entitlements:
        if 'annual' in e.leave_type_name.lower():
            return e.days_entitled or 21
    return 21  