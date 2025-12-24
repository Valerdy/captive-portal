#!/usr/bin/env python
"""
Script to create test data for the Captive Portal backend
Run with: python manage.py shell < create_test_data.py
or: python create_test_data.py
"""
import os
import sys
import django
from datetime import timedelta
from django.utils import timezone

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from core.models import User, Device, Session, Voucher
from mikrotik.models import MikrotikRouter, MikrotikHotspotUser, MikrotikActiveConnection
from radius.models import RadiusServer, RadiusClient


def create_test_data():
    """Create test data for all models"""

    print("🚀 Creating test data for Captive Portal...")

    # Create admin user
    print("\n📝 Creating admin user...")
    admin_user, created = User.objects.get_or_create(
        username='admin',
        defaults={
            'email': 'admin@captiveportal.local',
            'is_staff': True,
            'is_superuser': True,
            'first_name': 'Admin',
            'last_name': 'User'
        }
    )
    if created:
        admin_user.set_password('admin123')
        admin_user.save()
        print(f"✓ Admin user created: {admin_user.username}")
    else:
        print(f"⚠ Admin user already exists: {admin_user.username}")

    # Create regular users
    print("\n📝 Creating regular users...")
    users_data = [
        {
            'username': 'john.doe',
            'email': 'john.doe@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'phone_number': '+1234567890',
            'password': 'password123'
        },
        {
            'username': 'jane.smith',
            'email': 'jane.smith@example.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'phone_number': '+1987654321',
            'password': 'password123'
        },
        {
            'username': 'guest.user',
            'email': 'guest@example.com',
            'first_name': 'Guest',
            'last_name': 'User',
            'is_voucher_user': True,
            'voucher_code': 'GUEST2024',
            'password': 'guest123'
        }
    ]

    users = []
    for user_data in users_data:
        password = user_data.pop('password')
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults=user_data
        )
        if created:
            user.set_password(password)
            user.save()
            print(f"✓ User created: {user.username}")
        else:
            print(f"⚠ User already exists: {user.username}")
        users.append(user)

    # Create devices
    print("\n📱 Creating devices...")
    devices_data = [
        {
            'user': users[0],
            'mac_address': '00:11:22:33:44:55',
            'device_type': 'mobile',
            'hostname': 'iPhone-John',
            'user_agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        },
        {
            'user': users[1],
            'mac_address': 'AA:BB:CC:DD:EE:FF',
            'device_type': 'desktop',
            'hostname': 'Jane-MacBook',
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'
        },
        {
            'user': users[2],
            'mac_address': '11:22:33:44:55:66',
            'device_type': 'tablet',
            'hostname': 'iPad-Guest',
            'user_agent': 'Mozilla/5.0 (iPad; CPU OS 13_0 like Mac OS X)'
        }
    ]

    devices = []
    for device_data in devices_data:
        device, created = Device.objects.get_or_create(
            mac_address=device_data['mac_address'],
            defaults=device_data
        )
        if created:
            print(f"✓ Device created: {device.mac_address} ({device.device_type})")
        else:
            print(f"⚠ Device already exists: {device.mac_address}")
        devices.append(device)

    # Create sessions
    print("\n🔗 Creating sessions...")
    import uuid
    sessions_data = [
        {
            'user': users[0],
            'device': devices[0],
            'session_id': str(uuid.uuid4()),
            'mac_address': devices[0].mac_address,
            'status': 'active',
            'ip_address': '192.168.1.100',
            'bytes_in': 1048576,  # 1 MB
            'bytes_out': 524288,  # 512 KB
            'packets_in': 1000,
            'packets_out': 500
        },
        {
            'user': users[1],
            'device': devices[1],
            'session_id': str(uuid.uuid4()),
            'mac_address': devices[1].mac_address,
            'status': 'expired',
            'ip_address': '192.168.1.101',
            'bytes_in': 5242880,  # 5 MB
            'bytes_out': 2621440,  # 2.5 MB
            'packets_in': 5000,
            'packets_out': 2500,
            'start_time': timezone.now() - timedelta(hours=2),
            'end_time': timezone.now() - timedelta(hours=1)
        }
    ]

    for session_data in sessions_data:
        session, created = Session.objects.get_or_create(
            session_id=session_data['session_id'],
            defaults=session_data
        )
        if created:
            print(f"✓ Session created: {session.user.username} - {session.status}")
        else:
            print(f"⚠ Session already exists for {session.user.username}")

    # Create vouchers
    print("\n🎟️ Creating vouchers...")
    vouchers_data = [
        {
            'code': 'WELCOME2024',
            'duration': 3600,  # 1 hour
            'max_devices': 1,
            'status': 'active',
            'valid_until': timezone.now() + timedelta(days=30),
            'created_by': admin_user
        },
        {
            'code': 'PREMIUM7DAY',
            'duration': 604800,  # 7 days
            'max_devices': 3,
            'status': 'active',
            'valid_until': timezone.now() + timedelta(days=90),
            'created_by': admin_user
        },
        {
            'code': 'GUEST2024',
            'duration': 1800,  # 30 minutes
            'max_devices': 1,
            'status': 'used',
            'valid_until': timezone.now() + timedelta(days=7),
            'created_by': admin_user,
            'used_by': users[2],
            'used_at': timezone.now() - timedelta(hours=1),
            'used_count': 1
        }
    ]

    for voucher_data in vouchers_data:
        voucher, created = Voucher.objects.get_or_create(
            code=voucher_data['code'],
            defaults=voucher_data
        )
        if created:
            print(f"✓ Voucher created: {voucher.code} ({voucher.status})")
        else:
            print(f"⚠ Voucher already exists: {voucher.code}")

    # Create Mikrotik router
    print("\n🌐 Creating Mikrotik router...")
    router, created = MikrotikRouter.objects.get_or_create(
        name='Main Router',
        defaults={
            'host': '192.168.88.1',
            'port': 8728,
            'username': 'admin',
            'is_active': True
        }
    )
    if created:
        print(f"✓ Mikrotik router created: {router.name}")
    else:
        print(f"⚠ Mikrotik router already exists: {router.name}")

    # Create RADIUS server
    print("\n🔐 Creating RADIUS server...")
    radius_server, created = RadiusServer.objects.get_or_create(
        name='Main RADIUS Server',
        defaults={
            'host': '127.0.0.1',
            'auth_port': 1812,
            'acct_port': 1813,
            'secret': 'testing123',
            'is_active': True
        }
    )
    if created:
        print(f"✓ RADIUS server created: {radius_server.name}")
    else:
        print(f"⚠ RADIUS server already exists: {radius_server.name}")

    # Create RADIUS client
    print("\n📡 Creating RADIUS client...")
    radius_client, created = RadiusClient.objects.get_or_create(
        shortname='mikrotik-main',
        defaults={
            'name': 'Main Mikrotik NAS',
            'ip_address': '192.168.88.1',
            'secret': 'testing123',
            'is_active': True,
            'nas_type': 'other'
        }
    )
    if created:
        print(f"✓ RADIUS client created: {radius_client.name}")
    else:
        print(f"⚠ RADIUS client already exists: {radius_client.name}")

    print("\n" + "="*50)
    print("✅ Test data creation completed!")
    print("="*50)
    print("\n📊 Summary:")
    print(f"  Users: {User.objects.count()}")
    print(f"  Devices: {Device.objects.count()}")
    print(f"  Sessions: {Session.objects.count()}")
    print(f"  Vouchers: {Voucher.objects.count()}")
    print(f"  Mikrotik Routers: {MikrotikRouter.objects.count()}")
    print(f"  RADIUS Servers: {RadiusServer.objects.count()}")
    print(f"  RADIUS Clients: {RadiusClient.objects.count()}")
    print("\n🔑 Test Credentials:")
    print("  Admin: admin / admin123")
    print("  User 1: john.doe / password123")
    print("  User 2: jane.smith / password123")
    print("  Guest: guest.user / guest123")
    print("\n🎟️ Test Vouchers:")
    print("  WELCOME2024 - 1 hour, 1 device (active)")
    print("  PREMIUM7DAY - 7 days, 3 devices (active)")
    print("  GUEST2024 - 30 min, 1 device (used)")
    print()


if __name__ == '__main__':
    create_test_data()
