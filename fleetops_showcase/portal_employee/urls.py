from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('drivers/', views.EmployeeDriverListView.as_view(), name='employee_driver_list'),
    path('drivers/add/', views.EmployeeDriverAddView.as_view(), name='employee_driver_add'),
    path('deductions/add/', views.EmployeeDeductionAddView.as_view(), name='employee_deduction_add'),
]
