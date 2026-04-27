from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.EmployeeDashboardView.as_view(), name='employee_dashboard'),
    path('drivers/', views.EmployeeDriverListView.as_view(), name='employee_driver_list'),
    path('drivers/add/', views.EmployeeDriverAddView.as_view(), name='employee_driver_add'),
    path('drivers/<uuid:pk>/edit/', views.EmployeeDriverEditView.as_view(), name='employee_driver_edit'),
    path('drivers/<uuid:pk>/delete/', views.EmployeeDriverDeleteView.as_view(), name='employee_driver_delete'),
    path('drivers/<uuid:pk>/toggle-active/', views.EmployeeDriverToggleView.as_view(), name='employee_driver_toggle'),
    path('drivers/<uuid:pk>/salary-slip/', views.EmployeeSalarySlipView.as_view(), name='employee_salary_slip'),
    path('deductions/', views.EmployeeDeductionListView.as_view(), name='employee_deductions'),
    path('deductions/add/', views.EmployeeDeductionAddView.as_view(), name='employee_deduction_add'),
    path('pending-dues/', views.EmployeePendingDuesView.as_view(), name='employee_pending_dues'),
    path('pending-dues/<uuid:pk>/pay/', views.EmployeeMarkPaidView.as_view(), name='employee_mark_paid'),
]
