from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import (
    Profile, Driver, DriverInvoice, Deduction, Message,
    ROLE_CHOICES, POSITION_CHOICES, BANK_CHOICES, COMPANY_CHOICES,
    CONTRACT_CHOICES, VEHICLE_CHOICES, Task,
)


# ─── Tailwind form widget helper ────────────────────────────────────────────

TW_INPUT = 'w-full px-4 py-2.5 bg-gray-800 border border-gray-700 rounded-lg text-gray-100 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent transition-colors'
TW_SELECT = TW_INPUT
TW_TEXTAREA = TW_INPUT + ' min-h-[100px]'
TW_FILE = 'w-full text-sm text-gray-400 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-orange-600 file:text-white file:cursor-pointer hover:file:bg-orange-700 bg-gray-800 border border-gray-700 rounded-lg py-2 px-3'
TW_DATE = TW_INPUT
TW_CHECKBOX = 'w-4 h-4 rounded bg-gray-800 border-gray-600 text-orange-500 focus:ring-orange-500'


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': TW_INPUT,
            'placeholder': 'Email address',
            'autofocus': True,
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': TW_INPUT,
            'placeholder': 'Password',
            'x-bind:type': "showPass ? 'text' : 'password'",
        })
    )


class ProfileForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password', required=False,
        widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': 'Leave blank to keep current'})
    )
    password2 = forms.CharField(
        label='Confirm Password', required=False,
        widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = Profile
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'role', 'position',
            'identification_number', 'passport', 'contract_expiry_date',
            'base_salary_kd', 'iban_number', 'bank_name', 'avatar', 'supporting_document',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'First name'}),
            'last_name': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Last name'}),
            'email': forms.EmailInput(attrs={'class': TW_INPUT, 'placeholder': 'Email'}),
            'phone': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Phone'}),
            'role': forms.Select(attrs={'class': TW_SELECT}),
            'position': forms.Select(attrs={'class': TW_SELECT}),
            'identification_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'ID Number'}),
            'passport': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Passport'}),
            'contract_expiry_date': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'base_salary_kd': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.001'}),
            'iban_number': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'IBAN'}),
            'bank_name': forms.Select(attrs={'class': TW_SELECT}),
            'avatar': forms.FileInput(attrs={'class': TW_FILE}),
            'supporting_document': forms.FileInput(attrs={'class': TW_FILE}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        if not user.username:
            user.username = self.cleaned_data['email']
        p1 = self.cleaned_data.get('password1')
        if p1:
            user.set_password(p1)
        if commit:
            user.save()
        return user


class DriverForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password', required=False,
        widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': 'Leave blank if already linked'})
    )
    password2 = forms.CharField(
        label='Confirm Password', required=False,
        widget=forms.PasswordInput(attrs={'class': TW_INPUT, 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = Driver
        fields = [
            'first_name', 'last_name', 'email', 'phone',
            'civil_id_number', 'civil_id_expiry', 'passport_number', 'passport_expiry',
            'working_permit_expiry', 'driver_license_expiry',
            'health_insurance_expiry', 'criminal_certificate_expiry',
            'vehicle_registration', 'vehicle_registration_expiry',
            'vehicle_plate_number', 'vehicle_name', 'vehicle_type',
            'zone', 'petrol_card_number', 'employee_serial_number', 'working_id',
            'company_name', 'contract_type', 'position',
            'iban_number', 'bank_name', 'basic_salary_wp',
            'supporting_document',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'last_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'email': forms.EmailInput(attrs={'class': TW_INPUT}),
            'phone': forms.TextInput(attrs={'class': TW_INPUT}),
            'civil_id_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'civil_id_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'passport_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'passport_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'working_permit_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'driver_license_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'health_insurance_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'criminal_certificate_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'vehicle_registration': forms.TextInput(attrs={'class': TW_INPUT}),
            'vehicle_registration_expiry': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'vehicle_plate_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'vehicle_name': forms.TextInput(attrs={'class': TW_INPUT}),
            'vehicle_type': forms.Select(attrs={'class': TW_SELECT}),
            'zone': forms.TextInput(attrs={'class': TW_INPUT}),
            'petrol_card_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'employee_serial_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'working_id': forms.TextInput(attrs={'class': TW_INPUT}),
            'company_name': forms.Select(attrs={'class': TW_SELECT}),
            'contract_type': forms.Select(attrs={'class': TW_SELECT}),
            'position': forms.TextInput(attrs={'class': TW_INPUT}),
            'iban_number': forms.TextInput(attrs={'class': TW_INPUT}),
            'bank_name': forms.Select(attrs={'class': TW_SELECT}),
            'basic_salary_wp': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.001'}),
            'supporting_document': forms.FileInput(attrs={'class': TW_FILE}),
        }

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password1')
        p2 = cleaned.get('password2')
        if p1 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned

    def save(self, commit=True):
        driver = super().save(commit=False)
        email = self.cleaned_data['email']
        
        # Create or update profile
        profile, created = Profile.objects.get_or_create(
            email=email,
            defaults={
                'username': email,
                'first_name': self.cleaned_data['first_name'],
                'last_name': self.cleaned_data['last_name'],
                'role': 'driver',
            }
        )
        
        p1 = self.cleaned_data.get('password1')
        if p1:
            profile.set_password(p1)
            profile.save()
        elif created:
            # If created without password, set a default or handled by user later
            # For now, we assume password is required for new drivers
            pass

        driver.profile = profile
        if commit:
            driver.save()
        return driver


class DriverInvoiceForm(forms.ModelForm):
    class Meta:
        model = DriverInvoice
        fields = ['driver', 'cash', 'main_orders', 'additional_orders', 'hours', 'specified_date']
        widgets = {
            'driver': forms.Select(attrs={'class': TW_SELECT}),
            'cash': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.001', 'placeholder': '0.000'}),
            'main_orders': forms.NumberInput(attrs={'class': TW_INPUT, 'placeholder': '0'}),
            'additional_orders': forms.NumberInput(attrs={'class': TW_INPUT, 'placeholder': '0'}),
            'hours': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.01', 'placeholder': '0.00'}),
            'specified_date': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
        }


class DeductionForm(forms.ModelForm):
    class Meta:
        model = Deduction
        fields = [
            'driver', 'employee', 'reason', 'deduction_date',
            'contracting_company', 'contractor_deduction_kd',
            'company_deduction_kd', 'pdf_proof',
        ]
        widgets = {
            'driver': forms.Select(attrs={'class': TW_SELECT}),
            'employee': forms.Select(attrs={'class': TW_SELECT}),
            'reason': forms.Textarea(attrs={'class': TW_TEXTAREA, 'rows': 3}),
            'deduction_date': forms.DateInput(attrs={'class': TW_DATE, 'type': 'date'}),
            'contracting_company': forms.Select(attrs={'class': TW_SELECT}),
            'contractor_deduction_kd': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.001'}),
            'company_deduction_kd': forms.NumberInput(attrs={'class': TW_INPUT, 'step': '0.001'}),
            'pdf_proof': forms.FileInput(attrs={'class': TW_FILE}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('driver') and not cleaned.get('employee'):
            raise forms.ValidationError('At least one of Driver or Employee must be selected.')
        return cleaned


class EmployeeDeductionForm(DeductionForm):
    """Employee version — no employee field, only driver deductions."""
    class Meta(DeductionForm.Meta):
        fields = [
            'driver', 'reason', 'deduction_date',
            'contracting_company', 'contractor_deduction_kd',
            'company_deduction_kd', 'pdf_proof',
        ]

    def clean(self):
        cleaned = super(forms.ModelForm, self).clean()
        if not cleaned.get('driver'):
            raise forms.ValidationError('Driver must be selected.')
        return cleaned


class MessageForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(
        queryset=Profile.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'text-orange-500'}),
        label='To',
    )

    class Meta:
        model = Message
        fields = ['subject', 'body', 'attachment']
        widgets = {
            'subject': forms.TextInput(attrs={'class': TW_INPUT, 'placeholder': 'Subject'}),
            'body': forms.Textarea(attrs={'class': TW_TEXTAREA, 'placeholder': 'Write your message...', 'rows': 5}),
            'attachment': forms.FileInput(attrs={'class': TW_FILE}),
        }


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': TW_INPUT,
                'placeholder': 'Add a new task...',
            }),
        }
