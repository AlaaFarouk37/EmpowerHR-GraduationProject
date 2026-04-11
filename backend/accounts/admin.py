from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model  = User
        # We only ask for the essentials; logic in models.py handles the IDs
        fields = ("email", "full_name", "role")

class EmployeeChangeForm(UserChangeForm):
    class Meta:
        model  = User
        fields = ("email", "full_name", "role", "employee_id", "candidate_id", "is_active")

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form     = EmployeeChangeForm
    add_form = EmployeeCreationForm

    # Updated to include candidate_id in the table view
    list_display  = ["email", "full_name", "role", "employee_id", "candidate_id", "is_active", "created_at"]
    list_filter   = ["role", "is_active"]
    search_fields = ["email", "full_name", "employee_id", "candidate_id"]
    ordering      = ["-created_at"]

    # Updated fieldsets for the "Edit User" page
    fieldsets = (
        (None,             {"fields": ("email", "password")}),
        ("Personal info",  {"fields": ("full_name", "role")}),
        ("Identifications",{"fields": ("employee_id", "candidate_id")}), # Grouped IDs together
        ("Permissions",    {"fields": ("is_active", "is_staff", "is_superuser")}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields":  ("email", "full_name", "role", "password1", "password2"),
        }),
    )

    def save_model(self, request, obj, form, change):
        """
        We don't actually need custom logic here anymore!
        Because we moved the ID generation into the User.save() method in models.py,
        it will happen automatically whether you create a user via React or via Admin.
        """
        super().save_model(request, obj, form, change)