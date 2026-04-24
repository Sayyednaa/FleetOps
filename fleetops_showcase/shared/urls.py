from django.urls import path
from . import views

urlpatterns = [
    # Invoices
    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/add/', views.InvoiceAddView.as_view(), name='invoice_add'),
    path('invoices/<uuid:pk>/edit/', views.InvoiceEditView.as_view(), name='invoice_edit'),
    path('invoices/<uuid:pk>/delete/', views.InvoiceDeleteView.as_view(), name='invoice_delete'),
    path('invoices/archive/', views.InvoiceArchiveActionView.as_view(), name='invoice_archive_action'),
    path('invoices/export/', views.InvoiceExportView.as_view(), name='invoice_export'),

    # Archive
    path('archive/', views.ArchiveListView.as_view(), name='archive_list'),
    path('archive/export/', views.ArchiveExportView.as_view(), name='archive_export'),

    # Notifications
    path('notifications/', views.NotificationListView.as_view(), name='notification_list'),
    path('notifications/<uuid:pk>/read/', views.NotificationReadView.as_view(), name='notification_read'),
    path('notifications/read-all/', views.NotificationReadAllView.as_view(), name='notification_read_all'),

    # Messages
    path('messages/', views.MessageInboxView.as_view(), name='message_inbox'),
    path('messages/compose/', views.MessageComposeView.as_view(), name='message_compose'),
    path('messages/<uuid:pk>/', views.MessageDetailView.as_view(), name='message_detail'),
    path('messages/<uuid:pk>/read/', views.MessageReadView.as_view(), name='message_read'),

    # Contact
    path('contact/', views.ContactView.as_view(), name='contact'),

    # Tasks
    path('tasks/add/', views.TaskAddView.as_view(), name='task_add'),
    path('tasks/<uuid:pk>/toggle/', views.TaskToggleView.as_view(), name='task_toggle'),
    path('tasks/<uuid:pk>/delete/', views.TaskDeleteView.as_view(), name='task_delete'),
]
