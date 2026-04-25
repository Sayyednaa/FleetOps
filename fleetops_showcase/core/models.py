import uuid
from django.contrib.auth.models import AbstractUser
from django.db import models


# ─── Choices ─────────────────────────────────────────────────────────────────

ROLE_CHOICES = [
    ('admin', 'Admin'),
    ('manager', 'Manager'),
    ('employee', 'Employee'),
    ('driver', 'Driver'),
]

POSITION_CHOICES = [
    ('car_driver', 'Car Driver'),
    ('bike_driver', 'Bike Driver'),
    ('supervisor', 'Supervisor'),
    ('representative', 'Representative'),
    ('administrative', 'Administrative'),
    ('hp_manager', 'HP Manager'),
    ('accountant', 'Accountant'),
]

BANK_CHOICES = [
    ('nbk', 'National Bank of Kuwait (NBK)'),
    ('kfh', 'Kuwait Finance House (KFH)'),
    ('gulf_bank', 'Gulf Bank'),
    ('burgan', 'Burgan Bank'),
    ('al_ahli', 'Al Ahli Bank of Kuwait'),
    ('commercial', 'Commercial Bank of Kuwait'),
    ('boubyan', 'Boubyan Bank'),
    ('other', 'Other'),
]

COMPANY_CHOICES = [
    ('najmat', 'SAYYEDNAA LOGISTICS'),
    ('speedy', 'Speedy'),
    ('other', 'Other'),
]

CONTRACT_CHOICES = [
    ('talabat', 'Talabat'),
    ('burger_king', 'Burger King'),
    ('pharmazone', 'Pharmazone'),
    ('other', 'Other'),
]

VEHICLE_CHOICES = [
    ('car', 'Car'),
    ('bike', 'Bike'),
    ('motorcycle', 'Motorcycle'),
]

NOTIFICATION_TYPE_CHOICES = [
    ('document_expiry', 'Document Expiry'),
    ('invoice_action', 'Invoice Action'),
    ('new_message', 'New Message'),
    ('deduction', 'Deduction'),
    ('system', 'System'),
]


# ─── Profile (AUTH_USER_MODEL) ──────────────────────────────────────────────

class Profile(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='employee')
    phone = models.CharField(max_length=20, blank=True)
    position = models.CharField(max_length=30, choices=POSITION_CHOICES, blank=True)
    identification_number = models.CharField(max_length=50, blank=True)
    passport = models.CharField(max_length=50, blank=True)
    contract_expiry_date = models.DateField(null=True, blank=True)
    base_salary_kd = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    iban_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=30, choices=BANK_CHOICES, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    supporting_document = models.FileField(upload_to='profile_docs/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"


# ─── Driver ─────────────────────────────────────────────────────────────────

class Driver(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20)

    # Identity
    civil_id_number = models.CharField(max_length=50)
    civil_id_expiry = models.DateField(null=True, blank=True)
    passport_number = models.CharField(max_length=50, blank=True)
    passport_expiry = models.DateField(null=True, blank=True)

    # Work Compliance
    working_permit_expiry = models.DateField(null=True, blank=True)
    driver_license_expiry = models.DateField(null=True, blank=True)
    health_insurance_expiry = models.DateField(null=True, blank=True)
    criminal_certificate_expiry = models.DateField(null=True, blank=True)

    # Vehicle
    vehicle_registration = models.CharField(max_length=100, blank=True)
    vehicle_registration_expiry = models.DateField(null=True, blank=True)
    vehicle_plate_number = models.CharField(max_length=30, blank=True)
    vehicle_name = models.CharField(max_length=100, blank=True)
    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_CHOICES, default='bike')

    # Work Assignment
    zone = models.CharField(max_length=100, blank=True)
    petrol_card_number = models.CharField(max_length=50, blank=True)
    employee_serial_number = models.CharField(max_length=50, blank=True)
    working_id = models.CharField(max_length=50, blank=True)
    company_name = models.CharField(max_length=20, choices=COMPANY_CHOICES, default='najmat')
    contract_type = models.CharField(max_length=20, choices=CONTRACT_CHOICES, default='talabat')
    position = models.CharField(max_length=100, blank=True)

    # Financial
    iban_number = models.CharField(max_length=50, blank=True)
    bank_name = models.CharField(max_length=30, choices=BANK_CHOICES, blank=True)
    basic_salary_wp = models.DecimalField(max_digits=10, decimal_places=3, default=0)

    # Documents
    supporting_document = models.FileField(upload_to='driver_docs/', null=True, blank=True)

    # Meta
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name='created_drivers'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Link to login account (optional)
    profile = models.OneToOneField(
        Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_profile'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_expiring_documents(self, days=30):
        from datetime import date, timedelta
        today = date.today()
        warning_date = today + timedelta(days=days)
        docs = [
            ('Civil ID', self.civil_id_expiry),
            ('Passport', self.passport_expiry),
            ('Working Permit', self.working_permit_expiry),
            ('Driver License', self.driver_license_expiry),
            ('Health Insurance', self.health_insurance_expiry),
            ('Criminal Certificate', self.criminal_certificate_expiry),
            ('Vehicle Registration', self.vehicle_registration_expiry),
        ]
        results = []
        for label, expiry in docs:
            if not expiry:
                status = 'missing'
                days_remaining = None
            elif expiry < today:
                status = 'expired'
                days_remaining = (today - expiry).days
            elif expiry <= warning_date:
                status = 'warning'
                days_remaining = (expiry - today).days
            else:
                status = 'ok'
                days_remaining = (expiry - today).days
            results.append({
                'label': label,
                'expiry': expiry,
                'status': status,
                'days_remaining': days_remaining,
            })
        return results

    def has_expiry_warning(self):
        return any(d['status'] in ['warning', 'expired'] for d in self.get_expiring_documents())

    class Meta:
        ordering = ['first_name', 'last_name']


# ─── DriverInvoice ──────────────────────────────────────────────────────────

class DriverInvoice(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='invoices')
    cash = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    main_orders = models.IntegerField(default=0)
    additional_orders = models.IntegerField(default=0)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    specified_date = models.DateField()
    created_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-specified_date']
        indexes = [models.Index(fields=['driver', 'specified_date'])]

    def __str__(self):
        return f"{self.driver} - {self.specified_date}"

    @property
    def total_orders(self):
        return self.main_orders + self.additional_orders


# ─── InvoiceArchive ─────────────────────────────────────────────────────────

class InvoiceArchive(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(Driver, on_delete=models.PROTECT, related_name='archives')
    driver_name = models.CharField(max_length=200)
    cash = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    main_orders = models.IntegerField(default=0)
    additional_orders = models.IntegerField(default=0)
    hours = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    archive_date = models.DateField()
    archived_by = models.ForeignKey(Profile, on_delete=models.SET_NULL, null=True)
    salary_slip_url = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-archive_date']
        indexes = [models.Index(fields=['driver', 'archive_date'])]

    def __str__(self):
        return f"{self.driver_name} - Archive {self.archive_date}"

    @property
    def total_orders(self):
        return self.main_orders + self.additional_orders


# ─── Deduction ──────────────────────────────────────────────────────────────

class Deduction(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True, related_name='deductions'
    )
    employee = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, blank=True, related_name='deductions'
    )
    reason = models.TextField()
    deduction_date = models.DateField()
    contracting_company = models.CharField(max_length=20, choices=CONTRACT_CHOICES)
    contractor_deduction_kd = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    company_deduction_kd = models.DecimalField(max_digits=10, decimal_places=3, default=0)
    
    # New fields for installment plans
    is_installment_plan = models.BooleanField(default=False)
    total_installments = models.IntegerField(default=1)
    
    pdf_proof = models.FileField(upload_to='deduction_pdfs/', null=True, blank=True)
    submitted_by = models.ForeignKey(
        Profile, on_delete=models.SET_NULL, null=True, related_name='submitted_deductions'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-deduction_date']

    def __str__(self):
        target = self.driver or self.employee
        return f"Deduction: {target} - {self.deduction_date}"

    @property
    def total_amount(self):
        return self.contractor_deduction_kd + self.company_deduction_kd

    @property
    def paid_amount(self):
        return sum(i.amount for i in self.installments.filter(status='paid'))

    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount


class DeductionInstallment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    deduction = models.ForeignKey(Deduction, on_delete=models.CASCADE, related_name='installments')
    amount = models.DecimalField(max_digits=10, decimal_places=3)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, 
        choices=[('pending', 'Pending'), ('paid', 'Paid')], 
        default='pending'
    )
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Digital Signature
    signature_data = models.TextField(blank=True, null=True, help_text="Base64 signature data")
    signature_image = models.ImageField(upload_to='signatures/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date']

    def __str__(self):
        return f"Installment {self.amount} for {self.deduction}"


# ─── Message / MessageRecipient ─────────────────────────────────────────────

class Message(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sender = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='sent_messages')
    subject = models.CharField(max_length=200)
    body = models.TextField()
    attachment = models.FileField(upload_to='message_attachments/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.subject} (from {self.sender})"


class MessageRecipient(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='recipients')
    recipient = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='received_messages')
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['recipient', 'is_read'])]

    def __str__(self):
        return f"{self.message.subject} → {self.recipient}"


# ─── Notification ───────────────────────────────────────────────────────────

class Notification(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    body = models.TextField()
    type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES, default='system')
    is_read = models.BooleanField(default=False)
    related_driver = models.ForeignKey(
        Driver, on_delete=models.SET_NULL, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'is_read'])]

    def __str__(self):
        return f"{self.title} ({self.user})"


# ─── Task ───────────────────────────────────────────────────────────────────

class Task(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending'), ('completed', 'Completed')],
        default='pending',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [models.Index(fields=['user'])]
        ordering = ['status', '-created_at']

    def __str__(self):
        return f"{self.title} ({self.status})"
