import os
import sys
import django

# ── Django setup ──────────────────────────────────────────────────────────
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# ── Imports (after django setup) ──────────────────────────────────────────
from config.models import (
    WeekendConfig,
    WorkingHoursConfig,
    Skill,
    JobRole,
    LeaveType,
    SpecialLeaveCase,
)
from config.leave_calculator import LeaveCalculator, count_working_days
from feedback.models import Employee

SEP  = "=" * 65
SEP2 = "-" * 65

DAY_NAMES = {
    0: 'Monday',
    1: 'Tuesday',
    2: 'Wednesday',
    3: 'Thursday',
    4: 'Friday',
    5: 'Saturday',
    6: 'Sunday',
}


# ── STEP 1: Weekend Configuration ─────────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 1: Weekend Configuration")
print(SEP)

weekends = WeekendConfig.objects.all()
if not weekends.exists():
    print("  WARNING: No weekend days configured in DB.")
    print("  Defaulting to Friday (4) + Saturday (5) in the pipeline.")
else:
    for w in weekends:
        print(f"  Weekend day : {w.day_of_week} = {DAY_NAMES.get(w.day_of_week, '?')}")


# ── STEP 2: Working Hours Configuration ───────────────────────────────────
print(f"\n{SEP}")
print("  STEP 2: Working Hours Configuration")
print(SEP)

hours_cfg = WorkingHoursConfig.objects.filter(isActive=True).order_by('-createdAt').first()
if not hours_cfg:
    print("  WARNING: No active WorkingHoursConfig found.")
    print("  Pipeline will default to 09:00-17:00 with 60 min break.")
else:
    print(f"  Config ID         : {hours_cfg.configID}")
    print(f"  Work Start        : {hours_cfg.work_start}")
    print(f"  Work End          : {hours_cfg.work_end}")
    print(f"  Break (minutes)   : {hours_cfg.break_minutes}")
    print(f"  Effective hrs/day : {hours_cfg.working_hours_per_day}")
    print(f"  Is Active         : {hours_cfg.isActive}")


# ── STEP 3: Skills ─────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 3: Skills Library")
print(SEP)

skills = Skill.objects.filter(isActive=True)
print(f"  Active skills found: {skills.count()}")
if not skills.exists():
    print("  WARNING: No active skills in DB.")
else:
    print(f"  {'Name':<30} {'Category':<20} {'Level'}")
    print(f"  {'-'*30} {'-'*20} {'-'*5}")
    for s in skills:
        stars = '★' * s.level + '☆' * (5 - s.level)
        print(f"  {s.name:<30} {s.category:<20} {stars}")


# ── STEP 4: Job Roles ──────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 4: Job Roles")
print(SEP)

roles = JobRole.objects.filter(isActive=True)
print(f"  Active job roles found: {roles.count()}")
if not roles.exists():
    print("  WARNING: No active job roles in DB.")
else:
    print(f"  {'Title':<25} {'Department':<20} {'Level':<10} {'Leave Override'}")
    print(f"  {'-'*25} {'-'*20} {'-'*10} {'-'*14}")
    for r in roles:
        override = f"{r.annual_leave_override} days" if r.annual_leave_override else "default (21)"
        print(f"  {r.title:<25} {r.department or 'N/A':<20} {r.level:<10} {override}")


# ── STEP 5: Leave Types ────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 5: Leave Types")
print(SEP)

leave_types = LeaveType.objects.all()
active_count   = leave_types.filter(isActive=True).count()
inactive_count = leave_types.filter(isActive=False).count()
print(f"  Total leave types : {leave_types.count()} ({active_count} active, {inactive_count} inactive)")

if not leave_types.filter(isActive=True).exists():
    print("  ERROR: No active leave types. Pipeline will return empty entitlements.")
else:
    print()
    print(f"  {'Name':<25} {'Cat':<8} {'Days':<6} {'Senior':<8} {'Cert':<5} {'Mandated':<9} {'Active'}")
    print(f"  {'-'*25} {'-'*8} {'-'*6} {'-'*8} {'-'*5} {'-'*9} {'-'*6}")
    for lt in leave_types.order_by('category', 'name'):
        days   = str(lt.days_entitlement)   if lt.days_entitlement   else '—'
        senior = str(lt.days_entitlement_senior) if lt.days_entitlement_senior else '—'
        cert   = 'Yes' if lt.requires_medical_cert  else 'No'
        mand   = 'Yes' if lt.is_legally_mandated     else 'No'
        active = 'Yes' if lt.isActive                else 'No'
        print(f"  {lt.name:<25} {lt.category:<8} {days:<6} {senior:<8} {cert:<5} {mand:<9} {active}")


# ── STEP 6: Special Leave Cases ────────────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 6: Special Leave Cases (Active)")
print(SEP)

active_cases = SpecialLeaveCase.objects.filter(
    status=SpecialLeaveCase.STATUS_ACTIVE
).select_related('employeeID')

print(f"  Active special leave cases: {active_cases.count()}")

if not active_cases.exists():
    print("  No active special leave cases found.")
else:
    print(f"\n  {'Employee':<25} {'Type':<30} {'Start':<12} {'End':<12} {'Days'}")
    print(f"  {'-'*25} {'-'*30} {'-'*12} {'-'*12} {'-'*5}")
    for c in active_cases:
        print(f"  {c.employeeID.fullName:<25} {c.get_leave_type_display():<30} "
              f"{str(c.start_date):<12} {str(c.end_date):<12} {c.duration_days}")


# ── STEP 7: Run Pipeline for each Employee ─────────────────────────────────
print(f"\n{SEP}")
print("  STEP 7: Leave Calculation Pipeline — All Employees")
print(SEP)

employees = Employee.objects.all()
print(f"  Employees found: {employees.count()}")

if not employees.exists():
    print("  ERROR: No employees found. Add employees before running this.")
    sys.exit(1)

for employee in employees:
    print(f"\n{SEP}")
    print(f"  Employee        : {employee.fullName}")
    print(f"  ID              : {employee.employeeID}")
    print(f"  Job Title       : {employee.jobTitle or 'NOT SET'}")
    print(f"  Department      : {employee.department or 'NOT SET'}")
    print(f"  Years at Company: {employee.yearsAtCompany}")
    print(f"  Gender          : {employee.gender}")
    print(f"  Marital Status  : {employee.maritalStatus}")
    print(SEP2)

    try:
        result = LeaveCalculator(employee).calculate()

        # ── Working day info ───────────────────────────────────────
        print(f"  Working Day Info:")
        wdi = result.working_day_info
        weekend_names = [DAY_NAMES.get(d, str(d)) for d in wdi.weekend_days]
        print(f"    Weekend days        : {', '.join(weekend_names) or 'None'}")
        print(f"    Work hours          : {wdi.work_start} – {wdi.work_end}")
        print(f"    Break               : {wdi.break_minutes} min")
        print(f"    Effective hrs/day   : {wdi.working_hours_per_day}")
        print(SEP2)

        # ── Seniority ──────────────────────────────────────────────
        print(f"  Seniority:")
        print(f"    Years of service    : {result.years_of_service}")
        print(f"    Is senior (≥10 yrs) : {'YES — 30 days annual leave applies' if result.is_senior else 'No'}")
        print(f"    Job role matched    : {result.job_role or 'NOT MATCHED — no role override'}")
        print(SEP2)

        # ── Entitlements ───────────────────────────────────────────
        print(f"  Leave Entitlements ({len(result.entitlements)} types):")
        print(f"  {'#':<4} {'Leave Type':<25} {'Cat':<8} {'Days':>5}  {'Source':<15} {'Notes'}")
        print(f"  {'-'*4} {'-'*25} {'-'*8} {'-'*5}  {'-'*15} {'-'*30}")
        for i, e in enumerate(result.entitlements, 1):
            days  = str(e.days_entitled) if e.days_entitled is not None else '—'
            notes = e.notes[:40] if e.notes else ''
            print(f"  {i:<4} {e.leave_type_name:<25} {e.category:<8} {days:>5}  {e.source:<15} {notes}")

        # ── Special cases ──────────────────────────────────────────
        if result.special_cases:
            print(SEP2)
            print(f"  Active Special Leave Cases ({len(result.special_cases)}):")
            for sc in result.special_cases:
                print(f"    [{sc.leave_type}]  {sc.start_date} → {sc.end_date}  ({sc.duration} days)  {sc.notes or ''}")
        else:
            print(SEP2)
            print(f"  Active Special Leave Cases : None")

        # ── Warnings ──────────────────────────────────────────────
        if result.warnings:
            print(SEP2)
            print(f"  WARNINGS ({len(result.warnings)}):")
            for w in result.warnings:
                print(f"    ! {w}")
        else:
            print(SEP2)
            print(f"  No pipeline warnings.")

    except Exception as e:
        import traceback
        print(f"  ERROR running pipeline for {employee.fullName}:")
        traceback.print_exc()


# ── STEP 8: Working Days Utility Check ────────────────────────────────────
print(f"\n{SEP}")
print("  STEP 8: Working Days Utility — Sample Check")
print(SEP)

import datetime
today      = datetime.date.today()
month_end  = today.replace(day=28)   # safe last day for any month
working_days = count_working_days(today, month_end)
weekend_days = list(WeekendConfig.objects.values_list('day_of_week', flat=True)) or [4, 5]

print(f"  From        : {today}")
print(f"  To          : {month_end}")
print(f"  Weekend days: {[DAY_NAMES[d] for d in weekend_days]}")
print(f"  Working days: {working_days}")


print(f"\n{SEP}")
print("  Done.")
print(SEP)