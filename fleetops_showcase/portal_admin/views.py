"""Admin Portal Views — Full CRUD for team and drivers, dashboard with charts."""
import json
from datetime import date
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Sum, Q, Count
from django.core.paginator import Paginator
from core.mixins import AdminRequiredMixin
from core.models import (
    Profile, Driver, DriverInvoice, Deduction, Notification, Task,
    ROLE_CHOICES, COMPANY_CHOICES, CONTRACT_CHOICES, VEHICLE_CHOICES,
)
from core.forms import ProfileForm, DriverForm, DeductionForm
from django.views import View


def get_chart_data():
    """Compute chart data for dashboard — revenue & orders by vehicle type per month."""
    current_year = date.today().year
    labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    # Initialize with zeros
    revenue_bike = [0.0] * 12
    revenue_car = [0.0] * 12
    orders_bike = [0] * 12
    orders_car = [0] * 12

    # One query to get all data for the year
    yearly_data = DriverInvoice.objects.filter(
        specified_date__year=current_year
    ).values(
        'specified_date__month', 'driver__vehicle_type'
    ).annotate(
        total_cash=Sum('cash'),
        total_main=Sum('main_orders'),
        total_add=Sum('additional_orders')
    )

    for entry in yearly_data:
        m = entry['specified_date__month'] - 1
        vtype = entry['driver__vehicle_type']
        cash = float(entry['total_cash'] or 0)
        orders = (entry['total_main'] or 0) + (entry['total_add'] or 0)
        
        if vtype == 'bike':
            revenue_bike[m] = cash
            orders_bike[m] = orders
        else:
            revenue_car[m] = cash
            orders_car[m] = orders

    return json.dumps({
        'labels': labels,
        'revenue_bike': revenue_bike,
        'revenue_car': revenue_car,
        'orders_bike': orders_bike,
        'orders_car': orders_car,
    })


class AdminDashboardView(AdminRequiredMixin, View):
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

        # Optimize: Count expiring docs without full object hydration if possible, 
        # or at least avoid property-based recursion if it exists.
        active_drivers = Driver.objects.filter(is_active=True)
        expiring_count = 0
        for d in active_drivers:
            if d.has_expiry_warning():
                expiring_count += 1

        return render(request, 'admin_portal/dashboard.html', {
            'total_orders': total_orders,
            'total_cash': totals['total_cash'] or Decimal('0.000'),
            'total_hours': totals['total_hours'] or Decimal('0.00'),
            'chart_data': get_chart_data(),
            'tasks': tasks,
            'recent_notifs': recent_notifs,
            'active_drivers': active_drivers.count(),
            'expiring_docs': expiring_count,
        })


class TeamListView(AdminRequiredMixin, View):
    def get(self, request):
        qs = Profile.objects.exclude(role='driver')
        q = request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))

        sort = request.GET.get('sort', 'first_name')
        direction = request.GET.get('dir', 'asc')
        order_prefix = '' if direction == 'asc' else '-'
        if sort in ['first_name', 'role', 'email']:
            qs = qs.order_by(f'{order_prefix}{sort}')

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'admin_portal/team_list.html', {
            'page_obj': page_obj,
            'q': q,
            'sort': sort,
            'dir': direction,
        })


class TeamAddView(AdminRequiredMixin, View):
    def get(self, request):
        form = ProfileForm()
        return render(request, 'admin_portal/team_form.html', {'form': form, 'editing': False})

    def post(self, request):
        form = ProfileForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save(commit=False)
            user.username = form.cleaned_data['email']
            p1 = form.cleaned_data.get('password1')
            if p1:
                user.set_password(p1)
            user.save()
            messages.success(request, f'Team member {user.get_full_name()} created successfully.')
            return redirect('admin_team_list')
        return render(request, 'admin_portal/team_form.html', {'form': form, 'editing': False})


class TeamEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        member = get_object_or_404(Profile, pk=pk)
        form = ProfileForm(instance=member)
        return render(request, 'admin_portal/team_form.html', {'form': form, 'editing': True, 'member': member})

    def post(self, request, pk):
        member = get_object_or_404(Profile, pk=pk)
        form = ProfileForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            user = form.save(commit=False)
            p1 = form.cleaned_data.get('password1')
            if p1:
                user.set_password(p1)
            user.save()
            messages.success(request, f'Team member {user.get_full_name()} updated.')
            return redirect('admin_team_list')
        return render(request, 'admin_portal/team_form.html', {'form': form, 'editing': True, 'member': member})


class TeamDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        member = get_object_or_404(Profile, pk=pk)
        name = member.get_full_name()
        member.delete()
        messages.success(request, f'Team member {name} deleted.')
        return redirect('admin_team_list')


class DriverListView(AdminRequiredMixin, View):
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
            'portal': 'admin',
        })


class DriverAddView(AdminRequiredMixin, View):
    def get(self, request):
        form = DriverForm()
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': False})

    def post(self, request):
        form = DriverForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.created_by = request.user
            driver.save()
            messages.success(request, f'Driver {driver.full_name} added successfully.')
            return redirect('admin_driver_list')
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': False})


class DriverEditView(AdminRequiredMixin, View):
    def get(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(instance=driver)
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': True, 'driver': driver})

    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        form = DriverForm(request.POST, request.FILES, instance=driver)
        if form.is_valid():
            form.save()
            messages.success(request, f'Driver {driver.full_name} updated.')
            return redirect('admin_driver_list')
        return render(request, 'admin_portal/driver_form.html', {'form': form, 'editing': True, 'driver': driver})


class DriverDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        name = driver.full_name
        driver.delete()
        messages.success(request, f'Driver {name} deleted.')
        return redirect('admin_driver_list')


class DriverToggleActiveView(AdminRequiredMixin, View):
    def post(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        driver.is_active = not driver.is_active
        driver.save()
        status = 'activated' if driver.is_active else 'deactivated'
        messages.success(request, f'Driver {driver.full_name} {status}.')
        return redirect('admin_driver_list')


class DriverSalarySlipView(AdminRequiredMixin, View):
    def get(self, request, pk):
        driver = get_object_or_404(Driver, pk=pk)
        today = date.today()
        invoices = DriverInvoice.objects.filter(
            driver=driver,
            specified_date__year=today.year,
            specified_date__month=today.month,
        )
        totals = invoices.aggregate(
            cash=Sum('cash'),
            main=Sum('main_orders'),
            additional=Sum('additional_orders'),
            hours=Sum('hours'),
        )
        deductions = Deduction.objects.filter(
            driver=driver,
            deduction_date__year=today.year,
            deduction_date__month=today.month,
        )
        total_deductions = deductions.aggregate(
            total=Sum('contractor_deduction_kd')
        )['total'] or Decimal('0.000')

        cash = totals['cash'] or Decimal('0.000')
        net = cash - total_deductions

        return render(request, 'pdf/salary_slip.html', {
            'driver': driver,
            'cash': cash,
            'main_orders': totals['main'] or 0,
            'additional_orders': totals['additional'] or 0,
            'total_orders': (totals['main'] or 0) + (totals['additional'] or 0),
            'hours': totals['hours'] or Decimal('0.00'),
            'deductions': deductions,
            'total_deductions': total_deductions,
            'net_payable': net,
            'month_label': today.strftime('%B %Y'),
            'generated_date': today,
        })


class DeductionListView(AdminRequiredMixin, View):
    def get(self, request):
        form = DeductionForm()
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        deductions = Deduction.objects.select_related('driver', 'employee', 'submitted_by').all()
        return render(request, 'admin_portal/deduction_invoices.html', {
            'form': form,
            'deductions': deductions,
        })

    def post(self, request):
        form = DeductionForm(request.POST, request.FILES)
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        if form.is_valid():
            deduction = form.save(commit=False)
            deduction.submitted_by = request.user
            deduction.save()
            messages.success(request, 'Deduction recorded successfully.')
            return redirect('admin_deductions')
        deductions = Deduction.objects.select_related('driver', 'employee', 'submitted_by').all()
        return render(request, 'admin_portal/deduction_invoices.html', {
            'form': form,
            'deductions': deductions,
        })
