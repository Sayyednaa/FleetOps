"""Shared Views — Invoices, Archive, Notifications, Messages, Contact, Tasks."""
from datetime import date, timedelta
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages as django_messages
from django.db.models import Sum, Q
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
from core.mixins import AnyAuthenticatedMixin, StaffRequiredMixin, AdminManagerRequiredMixin
from core.models import (
    Driver, DriverInvoice, InvoiceArchive, Notification,
    Message, MessageRecipient, Profile, Task,
    COMPANY_CHOICES, CONTRACT_CHOICES,
)
from core.forms import DriverInvoiceForm, MessageForm, TaskForm
from core.excel_utils import export_invoices_excel, export_archive_excel
from django.views import View


def _parse_month(request):
    """Parse month from query string, default to current month."""
    month_str = request.GET.get('month', '')
    today = date.today()
    if month_str:
        try:
            parts = month_str.split('-')
            return int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            pass
    return today.year, today.month


def _month_label(year, month):
    return date(year, month, 1).strftime('%B %Y')


def _prev_month(year, month):
    d = date(year, month, 1) - timedelta(days=1)
    return f"{d.year}-{d.month:02d}"


def _next_month(year, month):
    if month == 12:
        return f"{year + 1}-01"
    return f"{year}-{month + 1:02d}"


class InvoiceListView(StaffRequiredMixin, View):
    def get(self, request):
        year, month = _parse_month(request)
        invoices = DriverInvoice.objects.filter(
            specified_date__year=year, specified_date__month=month,
        ).select_related('driver', 'created_by').order_by('driver__first_name', 'specified_date')

        # Group by driver
        driver_groups = {}
        for inv in invoices:
            did = str(inv.driver_id)
            if did not in driver_groups:
                driver_groups[did] = {
                    'driver': inv.driver,
                    'invoices': [],
                    'total_cash': Decimal('0'),
                    'total_main': 0,
                    'total_additional': 0,
                    'total_hours': Decimal('0'),
                }
            driver_groups[did]['invoices'].append(inv)
            driver_groups[did]['total_cash'] += inv.cash
            driver_groups[did]['total_main'] += inv.main_orders
            driver_groups[did]['total_additional'] += inv.additional_orders
            driver_groups[did]['total_hours'] += inv.hours

        grand = invoices.aggregate(
            cash=Sum('cash'), main=Sum('main_orders'),
            additional=Sum('additional_orders'), hours=Sum('hours'),
        )

        form = DriverInvoiceForm()
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)

        return render(request, 'shared/driver_invoices.html', {
            'driver_groups': driver_groups.values(),
            'grand_cash': grand['cash'] or Decimal('0'),
            'grand_main': grand['main'] or 0,
            'grand_additional': grand['additional'] or 0,
            'grand_hours': grand['hours'] or Decimal('0'),
            'month_label': _month_label(year, month),
            'current_month': f"{year}-{month:02d}",
            'prev_month': _prev_month(year, month),
            'next_month': _next_month(year, month),
            'form': form,
        })


class InvoiceAddView(StaffRequiredMixin, View):
    def post(self, request):
        form = DriverInvoiceForm(request.POST)
        if form.is_valid():
            invoice = form.save(commit=False)
            invoice.created_by = request.user
            invoice.save()
            django_messages.success(request, 'Invoice entry added.')
        else:
            django_messages.error(request, 'Error adding invoice entry. Check form fields.')
        month = request.POST.get('current_month', '')
        return redirect(f'/shared/invoices/?month={month}' if month else '/shared/invoices/')


class InvoiceEditView(StaffRequiredMixin, View):
    def get(self, request, pk):
        invoice = get_object_or_404(DriverInvoice, pk=pk)
        # Employee can only edit own
        if request.user.role == 'employee' and invoice.created_by != request.user:
            return redirect('access_denied')
        form = DriverInvoiceForm(instance=invoice)
        form.fields['driver'].queryset = Driver.objects.filter(is_active=True)
        return render(request, 'shared/invoice_edit.html', {'form': form, 'invoice': invoice})

    def post(self, request, pk):
        invoice = get_object_or_404(DriverInvoice, pk=pk)
        if request.user.role == 'employee' and invoice.created_by != request.user:
            return redirect('access_denied')
        form = DriverInvoiceForm(request.POST, instance=invoice)
        if form.is_valid():
            form.save()
            django_messages.success(request, 'Invoice updated.')
            return redirect('/shared/invoices/')
        return render(request, 'shared/invoice_edit.html', {'form': form, 'invoice': invoice})


class InvoiceDeleteView(StaffRequiredMixin, View):
    def post(self, request, pk):
        invoice = get_object_or_404(DriverInvoice, pk=pk)
        if request.user.role == 'employee' and invoice.created_by != request.user:
            return redirect('access_denied')
        invoice.delete()
        django_messages.success(request, 'Invoice entry deleted.')
        return redirect('/shared/invoices/')


class InvoiceArchiveActionView(AdminManagerRequiredMixin, View):
    def post(self, request):
        month_str = request.POST.get('month', '')
        try:
            parts = month_str.split('-')
            year, month = int(parts[0]), int(parts[1])
        except (ValueError, IndexError):
            django_messages.error(request, 'Invalid month.')
            return redirect('/shared/invoices/')

        invoices = DriverInvoice.objects.filter(
            specified_date__year=year, specified_date__month=month,
        )
        if not invoices.exists():
            django_messages.warning(request, 'No invoices to archive for this month.')
            return redirect('/shared/invoices/')

        with transaction.atomic():
            # Aggregate per driver
            drivers_in_month = invoices.values('driver').distinct()
            for d in drivers_in_month:
                driver = Driver.objects.get(pk=d['driver'])
                driver_invoices = invoices.filter(driver=driver)
                totals = driver_invoices.aggregate(
                    cash=Sum('cash'), main=Sum('main_orders'),
                    additional=Sum('additional_orders'), hours=Sum('hours'),
                )
                InvoiceArchive.objects.create(
                    driver=driver,
                    driver_name=driver.full_name,
                    cash=totals['cash'] or 0,
                    main_orders=totals['main'] or 0,
                    additional_orders=totals['additional'] or 0,
                    hours=totals['hours'] or 0,
                    archive_date=date(year, month, 1),
                    archived_by=request.user,
                )
            invoices.delete()

        django_messages.success(request, f'{_month_label(year, month)} invoices archived successfully.')
        return redirect('/shared/archive/')


class InvoiceExportView(StaffRequiredMixin, View):
    def get(self, request):
        year, month = _parse_month(request)
        qs = DriverInvoice.objects.filter(
            specified_date__year=year, specified_date__month=month,
        ).select_related('driver').order_by('driver__first_name', 'specified_date')
        return export_invoices_excel(qs, f"{year}-{month:02d}")


class ArchiveListView(StaffRequiredMixin, View):
    def get(self, request):
        qs = InvoiceArchive.objects.select_related('driver').all()
        company = request.GET.get('company', '')
        contract = request.GET.get('contract', '')
        month_str = request.GET.get('month', '')

        if month_str:
            try:
                parts = month_str.split('-')
                qs = qs.filter(archive_date__year=int(parts[0]), archive_date__month=int(parts[1]))
            except (ValueError, IndexError):
                pass
        if company:
            qs = qs.filter(driver__company_name=company)
        if contract:
            qs = qs.filter(driver__contract_type=contract)

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))

        return render(request, 'shared/archive.html', {
            'page_obj': page_obj,
            'company': company,
            'contract': contract,
            'month': month_str,
            'company_choices': COMPANY_CHOICES,
            'contract_choices': CONTRACT_CHOICES,
        })


class ArchiveExportView(StaffRequiredMixin, View):
    def get(self, request):
        qs = InvoiceArchive.objects.all()
        return export_archive_excel(qs, 'all')


class NotificationListView(AnyAuthenticatedMixin, View):
    def get(self, request):
        notifications = Notification.objects.filter(user=request.user)
        return render(request, 'shared/notifications.html', {'notifications': notifications})


class NotificationReadView(AnyAuthenticatedMixin, View):
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, user=request.user)
        notif.is_read = True
        notif.save()
        return redirect('/shared/notifications/')


class NotificationReadAllView(AnyAuthenticatedMixin, View):
    def post(self, request):
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        django_messages.success(request, 'All notifications marked as read.')
        return redirect('/shared/notifications/')


class MessageInboxView(AnyAuthenticatedMixin, View):
    def get(self, request):
        inbox = MessageRecipient.objects.filter(
            recipient=request.user
        ).select_related('message', 'message__sender').order_by('-message__created_at')
        sent = Message.objects.filter(sender=request.user).order_by('-created_at')
        return render(request, 'shared/messages_inbox.html', {
            'inbox': inbox,
            'sent': sent,
        })


class MessageDetailView(AnyAuthenticatedMixin, View):
    def get(self, request, pk):
        msg = get_object_or_404(Message, pk=pk)
        # Mark as read if recipient
        mr = MessageRecipient.objects.filter(message=msg, recipient=request.user).first()
        if mr and not mr.is_read:
            mr.is_read = True
            mr.read_at = timezone.now()
            mr.save()
        return render(request, 'shared/message_detail.html', {'msg': msg, 'mr': mr})


class MessageReadView(AnyAuthenticatedMixin, View):
    def post(self, request, pk):
        mr = get_object_or_404(MessageRecipient, message_id=pk, recipient=request.user)
        mr.is_read = True
        mr.read_at = timezone.now()
        mr.save()
        return redirect('/shared/messages/')


class MessageComposeView(StaffRequiredMixin, View):
    def get(self, request):
        form = MessageForm()
        pre_recipient = request.GET.get('to', '')
        return render(request, 'shared/messages_compose.html', {
            'form': form,
            'pre_recipient': pre_recipient,
        })

    def post(self, request):
        form = MessageForm(request.POST, request.FILES)
        if form.is_valid():
            msg = form.save(commit=False)
            msg.sender = request.user
            msg.save()
            for recipient in form.cleaned_data['recipients']:
                MessageRecipient.objects.create(message=msg, recipient=recipient)
            django_messages.success(request, 'Message sent successfully.')
            return redirect('/shared/messages/')
        return render(request, 'shared/messages_compose.html', {'form': form})


class ContactView(StaffRequiredMixin, View):
    def get(self, request):
        qs = Profile.objects.all()
        q = request.GET.get('q', '')
        if q:
            qs = qs.filter(Q(first_name__icontains=q) | Q(last_name__icontains=q) | Q(email__icontains=q))
        return render(request, 'shared/contact.html', {'team': qs, 'q': q})


class TaskAddView(AnyAuthenticatedMixin, View):
    def post(self, request):
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            django_messages.success(request, 'Task added.')
        redirect_url = request.META.get('HTTP_REFERER', '/')
        return redirect(redirect_url)


class TaskToggleView(AnyAuthenticatedMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        if task.status == 'pending':
            task.status = 'completed'
            task.completed_at = timezone.now()
        else:
            task.status = 'pending'
            task.completed_at = None
        task.save()
        return redirect(request.META.get('HTTP_REFERER', '/'))


class TaskDeleteView(AnyAuthenticatedMixin, View):
    def post(self, request, pk):
        task = get_object_or_404(Task, pk=pk, user=request.user)
        task.delete()
        return redirect(request.META.get('HTTP_REFERER', '/'))
