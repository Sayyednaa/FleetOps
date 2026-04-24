from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required

def home_redirect(request):
    if not request.user.is_authenticated:
        return redirect('login')
    
    role = getattr(request.user, 'role', None)
    if role == 'admin':
        return redirect('admin_dashboard')
    elif role == 'manager':
        return redirect('manager_dashboard')
    elif role == 'employee':
        return redirect('employee_dashboard')
    elif role == 'driver':
        return redirect('driver_dashboard')
    
    return redirect('login')

def access_denied(request):
    return render(request, 'auth/access_denied.html')
