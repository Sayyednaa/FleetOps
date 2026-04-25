"""Manager Portal Views — Same dashboard as admin, driver management (no delete), deductions."""
import json
from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q
from django.core.paginator import Paginator
from core.mixins import AdminManagerRequiredMixin
from core.models import (
    Driver, DriverInvoice, Deduction, Notification, Task,
    Profile, COMPANY_CHOICES, CONTRACT_CHOICES, VEHICLE_CHOICES,
)
from core.forms import DriverForm, DeductionForm, DeductionInstallmentForm
from django.views import View
from portal_admin.views import get_chart_data


class ManagerDashboardView(AdminManagerRequiredMixin, View):
    def get(self, request):
        today = date.today()
        month_invoices = DriverInvoice.objects.filter(
            specified_date__year=today.year,
            specified_date__month=today.month,
        )
        totals = month_invoices.aggregate(
            total_orders=Sum('main_orders'),
            total_additional=Sum('additional_orders'),
            total_cash=Sum('cash'),
            total_hours=Sum('hours'),
        )
        total_orders = (totals['total_orders'] or 0) + (totals['total_additional'] or 0)
        tasks = Task.objects.filter(user=request.user)
        recent_notifs = Notification.objects.filter(user=request.user, is_read=False)[:5]

        return render(request, 'manager_portal/dashboard.html', {
            'total_orders': total_orders,
            'total_cash': totals['total_cash'] or Decimal('0.000'),
            'total_hours': totals['total_hours'] or Decimal('0.00'),
            'chart_data': get_chart_data(),
            'tasks': tasks,
            'recent_notifs': recent_notifs,
            'active_drivers': Driver.objects.filter(is_active=True).count(),
            'expiring_docs': sum(1 for d in Driver.objects.filter(is_active=True) if d.has_expiry_warning()),
        })


class ManagerDriverListView(AdminManagerRequiredMixin, View):
    def get(self, request):
        qs = Driver.objects.all()
        q = request.GET.get('q', '')
        company = request.GET.get('company', '')
        contract = request.GET.get('contract', '')
        vehicle = request.GET.get('vehicle', '')

        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(phone__icontains=q))
        if company:
            qs = qs.filter(company_name=company)
        if contract:
            qs = qs.filter(contract_type=contract)
        if vehicle:
            qs = qs.filter(vehicle_type=vehicle)

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'admin_portal/driver_list.html', {
            'page_obj': page_obj,
            'q': q,
            'company': company,
            'contract': contract,
            'vehicle': vehicle,
            'company_choices': COMPANY_CHOICES,
            'contract_choices': CONTRACT_CHOICES,
            'vehicle_choices': VEHICLE_CHOICES,
            'portal': 'manager',
        })


class ManagerDriverEditView(AdminManagerRequiredMixin, View):
    def get(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(instance=driver)
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': True, 'driver': driver, 'portal': 'manager'})

    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f'Driver {driver.full_name} updated.')
            return redirect('manager_driver_list')
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': True, 'driver': driver, 'portal': 'manager'})


class ManagerDriverToggleView(AdminManagerRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.is_active = not driver.is_active
        driver.save()
        status = 'activated' if driver.is_active else 'deactivated'
        messages.success(request, f'Driver {driver.full_name} {status}.')
        return redirect('manager_driver_list')


class ManagerSalarySlipView(AdminManagerRequiredMixin, View):
    def get(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        today = date.today()
        invoices = DriverInvoice.objects.filter(
            driver=driver, specified_date__year=today.year, specified_date__month=today.month,
        )
        totals = invoices.aggregate(cash=Sum('cash'), main=Sum('main_orders'), additional=Sum('additional_orders'), hours=Sum('hours'))
        deductions = Deduction.objects.filter(driver=driver, deduction_date__year=today.year, deduction_date__month=today.month)
        total_deductions = deductions.aggregate(total=Sum('contractor_deduction_kd'))['total'] or Decimal('0.000')
        cash = totals['cash'] or Decimal('0.000')
        return render(request, 'pdf/salary_slip.html', {
            'driver': driver, 'cash': cash,
            'main_orders': totals['main'] or 0, 'additional_orders': totals['additional'] or 0,
            'total_orders': (totals['main'] or 0) + (totals['additional'] or 0),
            'hours': totals['hours'] or Decimal('0.00'),
            'deductions': deductions, 'total_deductions': total_deductions,
            'net_payable': cash - total_deductions,
            'month_label': today.strftime('%B %Y'), 'generated_date': today,
        })


class ManagerDeductionListView(AdminManagerRequiredMixin, View):
    def get(self, request):
        form = DeductionForm()
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        deductions = Deduction.objects.select_related('driver', 'employee', 'submitted_by').all()
        return render(request, 'admin_portal/deduction_invoices.html', {'form': form, 'deductions': deductions, 'portal': 'manager'})

    def post(self, request):
        form = DeductionForm(request.POST, request.FILES)
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        if form.is_valid():
            deduction = form.save(commit=False)
            deduction.submitted_by = request.user
            deduction.save()

            # Create installments logic
            if deduction.is_installment_plan and deduction.total_installments > 1:
                total_kd = deduction.total_amount
                count = deduction.total_installments
                base_amount = total_kd / count
                
                for i in range(count):
                    due_date = deduction.deduction_date
                    month = (due_date.month + i - 1) % 12 + 1
                    year = due_date.year + (due_date.month + i - 1) // 12
                    actual_due_date = date(year, month, min(due_date.day, 28))
                    
                    from core.models import DeductionInstallment
                    DeductionInstallment.objects.create(
                        deduction=deduction,
                        amount=base_amount,
                        due_date=actual_due_date,
                        status='pending'
                    )
            elif not deduction.is_installment_plan:
                from core.models import DeductionInstallment
                DeductionInstallment.objects.create(
                    deduction=deduction,
                    amount=deduction.total_amount,
                    due_date=deduction.deduction_date,
                    status='pending'
                )

            messages.success(request, 'Deduction recorded successfully.')
            return redirect('manager_deductions')
        deductions = Deduction.objects.select_related('driver', 'employee', 'submitted_by').all()
        return render(request, 'admin_portal/deduction_invoices.html', {'form': form, 'deductions': deductions, 'portal': 'manager'})


class ManagerPendingDuesView(AdminManagerRequiredMixin, View):
    def get(self, request):
        from core.models import DeductionInstallment
        installments = DeductionInstallment.objects.select_related(
            'deduction__driver', 'deduction__employee'
        ).order_by('status', 'due_date')
        
        q = request.GET.get('q', '')
        if q:
            installments = installments.filter(
                Q(deduction__driver__first_name__icontains=q) |
                Q(deduction__driver__last_name__icontains=q) |
                Q(deduction__reason__icontains=q)
            )

        return render(request, 'admin_portal/pending_dues.html', {
            'installments': installments,
            'q': q,
            'portal': 'manager',
        })


class ManagerMarkInstallmentPaidView(AdminManagerRequiredMixin, View):
    def post(self, request, pk):
        from core.models import DeductionInstallment
        installment = get_object_or_404(DeductionInstallment, pk=pk)
        
        if 'mark_paid' in request.POST:
            installment.status = 'paid'
            installment.paid_at = date.today()
            sig_data = request.POST.get('signature_data')
            if sig_data:
                installment.signature_data = sig_data
            if 'signature_image' in request.FILES:
                installment.signature_image = request.FILES['signature_image']
            installment.save()
            messages.success(request, f'Installment of {installment.amount} KD marked as paid.')
        
        return redirect('manager_pending_dues')
