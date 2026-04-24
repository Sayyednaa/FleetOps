from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def home_view(request):
    """
    Root URL view: 
    - If logged in, redirect to the appropriate portal.
    - If not logged in, show the landing page.
    """
    if request.user.is_authenticated:
        role = getattr(request.user, 'role', None)
        if role == 'admin':
            return redirect('admin_dashboard')
        elif role == 'manager':
            return redirect('manager_dashboard')
        elif role == 'employee':
            return redirect('employee_dashboard')
        elif role == 'driver':
            return redirect('driver_dashboard')
    
    return render(request, 'landing.html')

def access_denied(request):
    return render(request, 'auth/access_denied.html')
