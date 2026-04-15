from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class EmployeeCreationForm(UserCreationForm):
    class Meta:
        model  = User
        fields = ["email", "full_name", "role"]

class EmployeeChangeForm(UserChangeForm):
    class Meta:
        model  = User
        fields = ["email", "full_name", "role", "user_id", "is_active"]

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form     = EmployeeChangeForm
    add_form = EmployeeCreationForm

    list_display  = ["email", "full_name", "role", "user_id", "is_active", "created_at"]
    list_filter   = ["role", "is_active"]
    search_fields = ["email", "full_name", "user_id"]
    ordering      = ["-created_at"]

    # FIX: Changed inner tuples to lists [] to avoid admin.E008
    fieldsets = (
        (None,             {"fields": ["email", "password"]}),
        ("Personal info",  {"fields": ["full_name", "role"]}),
        ("Identifications",{"fields": ["user_id"]}), # This was the specific error!
        ("Permissions",    {"fields": ["is_active", "is_staff", "is_superuser"]}),
    )

    # FIX: Standardizing add_fieldsets
    add_fieldsets = (
        (None, {
            "classes": ["wide"],
            "fields":  ["email", "full_name", "role", "password1", "password2"],
        }),
    )

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)