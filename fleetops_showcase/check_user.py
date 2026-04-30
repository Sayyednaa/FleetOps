import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "fleetops.settings")
django.setup()

from core.models import Profile

u = Profile.objects.filter(email='hassan@sayyednaalogistics.com').first()
if u:
    print(f'User: {u}')
    print(f'Username: {u.username}')
    print(f'Email: {u.email}')
    print(f'Has usable password: {u.has_usable_password()}')
    print(f'Check pass 123: {u.check_password("123")}')
    print(f'Is Active: {u.is_active}')
else:
    print("User not found")
