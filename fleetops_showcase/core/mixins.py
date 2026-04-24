from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.shortcuts import redirect


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Base mixin that checks user role against allowed_roles list."""
    allowed_roles = []

    def test_func(self):
        return self.request.user.role in self.allowed_roles

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('login')
        return redirect('access_denied')


class AdminRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin']


class AdminManagerRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'manager']


class StaffRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['admin', 'manager', 'employee']


class DriverRequiredMixin(RoleRequiredMixin):
    allowed_roles = ['driver']


class AnyAuthenticatedMixin(LoginRequiredMixin):
    """Any logged-in user can access."""
    pass
