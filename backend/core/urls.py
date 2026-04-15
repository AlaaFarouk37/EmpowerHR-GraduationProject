from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/resume_pipeline/', include('resume_pipeline.urls')),
    path('api/feedback/',    include('feedback.urls')),
    path('api/attrition/',   include('attrition.urls')),
    path("api/auth/", include("accounts.urls")),
    path("api/employee_management/", include("employee_management.urls")),
]
