from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core.views import home_redirect, access_denied

urlpatterns = [
    path('admin-django/', admin.site.urls),
    
    # Auth
    path('', home_redirect, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('access-denied/', access_denied, name='access_denied'),

    # Portals
    path('admin-portal/', include('portal_admin.urls')),
    path('manager-portal/', include('portal_manager.urls')),
    path('employee-portal/', include('portal_employee.urls')),
    path('driver-portal/', include('portal_driver.urls')),

    # Shared
    path('shared/', include('shared.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
