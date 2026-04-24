import random
from decimal import Decimal
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    Profile, Driver, DriverInvoice, Deduction, Message, MessageRecipient, Task,
)

class Command(BaseCommand):
    help = 'Seed the database with SAYYEDNAA LOGISTICS showcase data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Seeding SAYYEDNAA LOGISTICS data...'))

        if Profile.objects.exists():
            self.stdout.write(self.style.SUCCESS('Data already exists. Skipping seed.'))
            return

        # 1. Create Users
        self.stdout.write('Creating users...')
        admin_user = Profile.objects.create_superuser(
            username='admin@fleetops.com',
            email='admin@fleetops.com',
            password='admin123',
            first_name='Omar',
            last_name='Al-Rashidi',
            role='admin',
            position='general_manager'
        )

        manager_user = Profile.objects.create_user(
            username='manager@fleetops.com',
            email='manager@fleetops.com',
            password='manager123',
            first_name='Sara',
            last_name='Al-Mutairi',
            role='manager',
            position='operation_manager'
        )

        employee_user = Profile.objects.create_user(
            username='employee@fleetops.com',
            email='employee@fleetops.com',
            password='employee123',
            first_name='Khalid',
            last_name='Al-Enezi',
            role='employee',
            position='dispatcher'
        )

        driver_user = Profile.objects.create_user(
            username='driver@fleetops.com',
            email='driver@fleetops.com',
            password='driver123',
            first_name='Ahmed',
            last_name='Hassan',
            role='driver'
        )

        # 2. Create Drivers
        self.stdout.write('Creating drivers...')
        drivers = []
        today = timezone.now().date()
        
        # Ahmed (the linked driver)
        ahmed = Driver.objects.create(
            profile=driver_user,
            first_name='Ahmed', last_name='Hassan',
            phone='96590001001', civil_id_number='290010100011',
            company_name='najmat', contract_type='article_18',
            vehicle_type='bike', zone='Kuwait City',
            civil_id_expiry=today + timedelta(days=200),
            driver_license_expiry=today + timedelta(days=15),
            is_active=True
        )
        drivers.append(ahmed)

        # Some more drivers
        names = [
            ('John', 'Doe', 'car', 'talabat'),
            ('Mohamed', 'Ali', 'bike', 'deliveroo'),
            ('Suresh', 'Kumar', 'bike', 'najmat'),
            ('Ali', 'Reza', 'car', 'talabat'),
        ]
        for f, l, v, c in names:
            d = Driver.objects.create(
                first_name=f, last_name=l,
                phone=f'965{random.randint(10000000, 99999999)}',
                civil_id_number=f'280{random.randint(100000000, 999999999)}',
                company_name=c, contract_type='article_18',
                vehicle_type=v, zone='Salmiya',
                civil_id_expiry=today + timedelta(days=random.randint(-10, 300)),
                is_active=True
            )
            drivers.append(d)

        # 3. Create Invoices for last 30 days
        self.stdout.write('Creating invoices...')
        for d in drivers:
            for i in range(30):
                idate = today - timedelta(days=i)
                DriverInvoice.objects.create(
                    driver=d,
                    specified_date=idate,
                    cash=Decimal(random.randint(5, 25)),
                    main_orders=random.randint(10, 20),
                    additional_orders=random.randint(0, 5),
                    hours=Decimal(random.randint(8, 12)),
                    created_by=admin_user
                )

        # 4. Create Deductions
        self.stdout.write('Creating deductions...')
        Deduction.objects.create(
            driver=ahmed,
            reason='Speeding Ticket #123',
            deduction_date=today - timedelta(days=5),
            contracting_company='talabat',
            contractor_deduction_kd=Decimal('15.000'),
            submitted_by=manager_user
        )

        # 5. Create Messages
        self.stdout.write('Creating messages...')
        msg = Message.objects.create(
            sender=admin_user,
            subject='Welcome to SAYYEDNAA LOGISTICS',
            body='Welcome to the new system. Please ensure your documents are up to date.'
        )
        MessageRecipient.objects.create(message=msg, recipient=driver_user)
        MessageRecipient.objects.create(message=msg, recipient=manager_user)

        # 6. Create Tasks
        self.stdout.write('Creating tasks...')
        Task.objects.create(user=admin_user, title='Review monthly reports')
        Task.objects.create(user=admin_user, title='Approve driver leaves')
        Task.objects.create(user=manager_user, title='Check vehicle maintenance')

        self.stdout.write(self.style.SUCCESS('SAYYEDNAA LOGISTICS data seeded successfully!'))
