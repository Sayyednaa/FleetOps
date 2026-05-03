from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from core.models import Driver, TalabatSalaryDetail, ContractSalaryDetail, MonthlyProfitLoss

class AccountantMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return getattr(self.request.user, 'role', '') in ('accountant', 'superadmin', 'admin')

class AccountantDashboardView(AccountantMixin, TemplateView):
    template_name = 'accountant_portal/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['talabat_count'] = Driver.objects.filter(contract_type='talabat', is_active=True).count()
        context['pharmazone_count'] = Driver.objects.filter(contract_type='pharmazone', is_active=True).count()
        context['burgerking_count'] = Driver.objects.filter(contract_type='burger_king', is_active=True).count()
        context['other_count'] = Driver.objects.filter(contract_type='other', is_active=True).count()
        context['recent_reports'] = MonthlyProfitLoss.objects.order_by('-created_at')[:5]
        return context

class AccountantTalabatView(AccountantMixin, ListView):
    model = Driver
    template_name = 'accountant_portal/talabat.html'
    context_object_name = 'drivers'

    def get_queryset(self):
        return Driver.objects.filter(is_active=True).order_by('full_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['saved_records'] = TalabatSalaryDetail.objects.select_related('driver').order_by('-created_at')[:50]
        return context

    def post(self, request, *args, **kwargs):
        from decimal import Decimal
        driver_id = request.POST.get('driver_id')
        month_str = request.POST.get('month')  # e.g. "2026-04"
        
        if not driver_id or not month_str:
            messages.error(request, 'Please select a driver and month.')
            return redirect('accountant_talabat')
        
        try:
            driver = Driver.objects.get(id=driver_id)
        except Driver.DoesNotExist:
            messages.error(request, 'Selected driver not found.')
            return redirect('accountant_talabat')
        
        month_date = f"{month_str}-01"  # convert "2026-04" to "2026-04-01"
        
        defaults = {
            'batch_1_orders': int(request.POST.get('batch_1_orders', 0) or 0),
            'batch_1_amount': Decimal(request.POST.get('batch_1_amount', 0) or 0),
            'batch_1_net_amount': Decimal(request.POST.get('batch_1_net_amount', 0) or 0),
            'batch_2_orders': int(request.POST.get('batch_2_orders', 0) or 0),
            'batch_2_amount': Decimal(request.POST.get('batch_2_amount', 0) or 0),
            'batch_2_net_amount': Decimal(request.POST.get('batch_2_net_amount', 0) or 0),
            'batch_3_orders': int(request.POST.get('batch_3_orders', 0) or 0),
            'batch_3_amount': Decimal(request.POST.get('batch_3_amount', 0) or 0),
            'batch_3_net_amount': Decimal(request.POST.get('batch_3_net_amount', 0) or 0),
            'batch_4_orders': int(request.POST.get('batch_4_orders', 0) or 0),
            'batch_4_amount': Decimal(request.POST.get('batch_4_amount', 0) or 0),
            'batch_4_net_amount': Decimal(request.POST.get('batch_4_net_amount', 0) or 0),
            'batch_5_orders': int(request.POST.get('batch_5_orders', 0) or 0),
            'batch_5_amount': Decimal(request.POST.get('batch_5_amount', 0) or 0),
            'batch_5_net_amount': Decimal(request.POST.get('batch_5_net_amount', 0) or 0),
            'batch_6_orders': int(request.POST.get('batch_6_orders', 0) or 0),
            'batch_6_amount': Decimal(request.POST.get('batch_6_amount', 0) or 0),
            'batch_6_net_amount': Decimal(request.POST.get('batch_6_net_amount', 0) or 0),
            'batch_7_orders': int(request.POST.get('batch_7_orders', 0) or 0),
            'batch_7_amount': Decimal(request.POST.get('batch_7_amount', 0) or 0),
            'batch_7_net_amount': Decimal(request.POST.get('batch_7_net_amount', 0) or 0),
            'deduction': Decimal(request.POST.get('deduction', 0) or 0),
        }
        
        obj, created = TalabatSalaryDetail.objects.update_or_create(
            driver=driver,
            month=month_date,
            defaults=defaults
        )
        
        # Handle file attachment
        if request.FILES.get('attachment'):
            obj.attachment = request.FILES['attachment']
            obj.save()
        
        action = 'updated' if not created else 'saved'
        messages.success(request, f'Salary record {action} for {driver.full_name}.')
        return redirect('accountant_talabat')

class AccountantPharmazoneView(AccountantMixin, ListView):
    model = Driver
    template_name = 'accountant_portal/contract_salary.html'
    context_object_name = 'drivers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_title'] = 'Pharma Zone'
        context['contract_type'] = 'pharmazone'
        context['saved_records'] = ContractSalaryDetail.objects.filter(contract_type='pharmazone').order_by('-created_at')[:50]
        return context

    def get_queryset(self):
        return Driver.objects.filter(is_active=True).order_by('full_name')

    def post(self, request, *args, **kwargs):
        return _save_contract_salary(request, 'pharmazone', 'accountant_pharmazone')

class AccountantBurgerKingView(AccountantMixin, ListView):
    model = Driver
    template_name = 'accountant_portal/contract_salary.html'
    context_object_name = 'drivers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_title'] = 'Burger King'
        context['contract_type'] = 'burger_king'
        context['saved_records'] = ContractSalaryDetail.objects.filter(contract_type='burger_king').order_by('-created_at')[:50]
        return context

    def get_queryset(self):
        return Driver.objects.filter(is_active=True).order_by('full_name')

    def post(self, request, *args, **kwargs):
        return _save_contract_salary(request, 'burger_king', 'accountant_burgerking')

class AccountantOtherContractView(AccountantMixin, ListView):
    model = Driver
    template_name = 'accountant_portal/contract_salary.html'
    context_object_name = 'drivers'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contract_title'] = 'Other Contracts'
        context['contract_type'] = 'other'
        context['saved_records'] = ContractSalaryDetail.objects.filter(contract_type='other').order_by('-created_at')[:50]
        return context

    def get_queryset(self):
        return Driver.objects.filter(is_active=True).order_by('full_name')

    def post(self, request, *args, **kwargs):
        return _save_contract_salary(request, 'other', 'accountant_other_contract')

def _save_contract_salary(request, contract_type, redirect_url):
    from decimal import Decimal
    driver_id = request.POST.get('driver_id')
    month_str = request.POST.get('month')
    
    if not driver_id or not month_str:
        messages.error(request, 'Please select a name and month.')
        return redirect(redirect_url)
    
    try:
        driver = Driver.objects.get(id=driver_id)
    except Driver.DoesNotExist:
        messages.error(request, 'Selected driver not found.')
        return redirect(redirect_url)
    
    name = driver.full_name
    month_date = f"{month_str}-01"
    
    ContractSalaryDetail.objects.create(
        contract_type=contract_type,
        name=name,
        month=month_date,
        total_salary=Decimal(request.POST.get('total_salary', 0) or 0),
        absent=int(request.POST.get('absent', 0) or 0),
        deduction=Decimal(request.POST.get('deduction', 0) or 0),
        remark=request.POST.get('remark', ''),
        attachment=request.FILES.get('attachment')
    )
    messages.success(request, f'Salary record saved for {name}.')
    return redirect(redirect_url)

class AccountantMonthlyDetailsView(AccountantMixin, ListView):
    model = MonthlyProfitLoss
    template_name = 'accountant_portal/monthly_details.html'
    context_object_name = 'records'
    
    def get_queryset(self):
        return MonthlyProfitLoss.objects.all().order_by('-month')

    def post(self, request, *args, **kwargs):
        company_name = request.POST.get('company_name')
        contract_name = request.POST.get('contract_name')
        expense = request.POST.get('expense')
        profit_loss = request.POST.get('profit_loss')
        month = request.POST.get('month')
        report_pdf = request.FILES.get('report_pdf')

        if company_name and contract_name and expense and profit_loss and month:
            MonthlyProfitLoss.objects.create(
                company_name=company_name,
                contract_name=contract_name,
                expense=expense,
                profit_loss=profit_loss,
                month=month,
                report_pdf=report_pdf
            )
        
        return redirect('accountant_monthly_details')

from core.forms import DriverForm, DeductionForm
from django.contrib import messages

class AccountantDriverAddView(AccountantMixin, View):
    def get(self, request):
        form = DriverForm()
        return render(request, 'admin_portal/driver_form.html', {
            'form': form, 'editing': False, 'portal': 'accountant',
            'title': 'Add New Driver', 'subtitle': 'Register a new driver in the system',
            'breadcrumb': 'Accountant → Drivers → Add', 'icon': '🚗'
        })

    def post(self, request):
        form = DriverForm(request.POST, request.FILES)
        if form.is_valid():
            driver = form.save(commit=False)
            driver.created_by = request.user
            driver.save()
            messages.success(request, f'Driver {driver.full_name} added successfully.')
            return redirect('accountant_talabat') # Or wherever
        return render(request, 'admin_portal/driver_form.html', {
            'form': form, 'editing': False, 'portal': 'accountant',
            'title': 'Add New Driver', 'subtitle': 'Register a new driver in the system',
            'breadcrumb': 'Accountant → Drivers → Add', 'icon': '🚗'
        })

class AccountantDeductionAddView(AccountantMixin, View):
    def get(self, request):
        from core.models import Driver, Profile
        form = DeductionForm()
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        return render(request, 'employee_portal/deduction_form.html', {
            'form': form, 'portal': 'accountant',
            'title': 'Submit Deduction', 'subtitle': 'Process a driver or staff deduction record',
            'breadcrumb': 'Accountant → Deduction → Add', 'icon': '🧾'
        })

    def post(self, request):
        from core.models import Driver, Profile
        form = DeductionForm(request.POST, request.FILES)
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        form.fields['employee'].queryset = Profile.objects.exclude(role='driver')
        if form.is_valid():
            deduction = form.save(commit=False)
            deduction.submitted_by = request.user
            deduction.save()
            messages.success(request, 'Deduction submitted successfully.')
            return redirect('accountant_talabat')
        return render(request, 'employee_portal/deduction_form.html', {
            'form': form, 'portal': 'accountant',
            'title': 'Submit Deduction', 'subtitle': 'Process a driver or staff deduction record',
            'breadcrumb': 'Accountant → Deduction → Add', 'icon': '🧾'
        })

from django.contrib.auth.decorators import login_required, user_passes_test
from core.excel_utils import generate_excel_template, export_talabat_excel, export_contract_excel, import_from_excel

def is_accountant(user):
    return getattr(user, 'role', '') in ('accountant', 'superadmin', 'admin')

@login_required
@user_passes_test(is_accountant)
def accountant_download_template(request, model_type):
    return generate_excel_template(model_type)

@login_required
@user_passes_test(is_accountant)
def accountant_export_excel(request, model_type):
    if model_type == 'talabat_salary':
        queryset = TalabatSalaryDetail.objects.all()
        return export_talabat_excel(queryset, label='talabat_salaries')
    elif model_type == 'contract_salary':
        # the accountant views filter by contract_type but export handles all or specific? 
        # let's export all contract salaries for simplicity, or we can filter by request.GET.get('type')
        contract_type = request.GET.get('type', '')
        queryset = ContractSalaryDetail.objects.all()
        if contract_type:
            queryset = queryset.filter(contract_type=contract_type)
        return export_contract_excel(queryset, label=contract_type or 'all_contracts')
    
    messages.error(request, 'Invalid export type.')
    return redirect('accountant_dashboard')

@login_required
@user_passes_test(is_accountant)
def accountant_upload_excel(request, model_type):
    if request.method == 'POST' and request.FILES.get('excel_file'):
        file = request.FILES['excel_file']
        if not file.name.endswith('.xlsx'):
            messages.error(request, 'Please upload a valid Excel (.xlsx) file.')
        else:
            count, errors = import_from_excel(file, model_type, request.user)
            if errors:
                for error in errors[:5]: # Show up to 5 errors
                    messages.error(request, error)
                if len(errors) > 5:
                    messages.error(request, f"...and {len(errors) - 5} more errors.")
            if count > 0:
                messages.success(request, f'Successfully imported {count} records.')
            elif not errors:
                messages.warning(request, 'No records were imported.')
                
    # redirect back to previous page
    return redirect(request.META.get('HTTP_REFERER', 'accountant_dashboard'))


class AccountantSalarySlipListView(AccountantMixin, ListView):
    model = Driver
    template_name = 'accountant_portal/salary_slips.html'
    context_object_name = 'drivers'

    def get_queryset(self):
        qs = Driver.objects.filter(is_active=True)
        q = self.request.GET.get('q', '')
        if q:
            qs = qs.filter(full_name__icontains=q) | qs.filter(working_id__icontains=q) | qs.filter(phone__icontains=q)
        return qs.order_by('full_name')


from portal_admin.views import DriverSalarySlipView
class AccountantSalarySlipView(DriverSalarySlipView):
    pass
