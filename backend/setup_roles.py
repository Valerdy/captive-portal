#!/usr/bin/env python
"""
Script to setup role-based access control system.
This script:
1. Generates and applies migrations for the Role model
2. Creates default roles (admin and user)
3. Syncs existing users' roles based on is_staff/is_superuser
"""
import os
import sys
import django

# Add the backend directory to Python path
backend_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, backend_dir)

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.core.management import call_command
from core.models import Role, User


def create_migrations():
    """Generate new migrations"""
    print("=" * 70)
    print("STEP 1: Generating Migrations")
    print("=" * 70)
    try:
        call_command('makemigrations', 'core')
        print("✅ Migrations generated successfully")
    except Exception as e:
        print(f"❌ Error generating migrations: {e}")
        return False
    return True


def apply_migrations():
    """Apply all pending migrations"""
    print("\n" + "=" * 70)
    print("STEP 2: Applying Migrations")
    print("=" * 70)
    try:
        call_command('migrate')
        print("✅ Migrations applied successfully")
    except Exception as e:
        print(f"❌ Error applying migrations: {e}")
        return False
    return True


def create_default_roles():
    """Create default roles"""
    print("\n" + "=" * 70)
    print("STEP 3: Creating Default Roles")
    print("=" * 70)

    # Create admin role
    admin_role, created = Role.objects.get_or_create(
        name='admin',
        defaults={'description': 'Administrator with full access to all features'}
    )
    if created:
        print("✅ Created 'admin' role")
    else:
        print("ℹ️  'admin' role already exists")

    # Create user role
    user_role, created = Role.objects.get_or_create(
        name='user',
        defaults={'description': 'Standard user with basic access'}
    )
    if created:
        print("✅ Created 'user' role")
    else:
        print("ℹ️  'user' role already exists")

    return admin_role, user_role


def sync_existing_users(admin_role, user_role):
    """Sync roles for existing users"""
    print("\n" + "=" * 70)
    print("STEP 4: Syncing Existing Users")
    print("=" * 70)

    users = User.objects.all()
    if not users.exists():
        print("ℹ️  No users found. Skipping sync.")
        return

    updated_count = 0
    admin_count = 0
    user_count = 0

    for user in users:
        # Determine role based on is_staff/is_superuser
        if user.is_staff or user.is_superuser:
            if user.role != admin_role:
                user.role = admin_role
                user.save()
                print(f"✅ Updated {user.username} to 'admin' role")
                updated_count += 1
            admin_count += 1
        else:
            if user.role != user_role:
                user.role = user_role
                user.save()
                print(f"✅ Updated {user.username} to 'user' role")
                updated_count += 1
            user_count += 1

    print(f"\n📊 Summary:")
    print(f"  - Total users: {users.count()}")
    print(f"  - Admin users: {admin_count}")
    print(f"  - Regular users: {user_count}")
    print(f"  - Updated: {updated_count}")


def verify_setup():
    """Verify the setup"""
    print("\n" + "=" * 70)
    print("STEP 5: Verification")
    print("=" * 70)

    # Check roles
    roles = Role.objects.all()
    print(f"\n✅ Roles in database: {roles.count()}")
    for role in roles:
        user_count = role.users.count()
        print(f"  - {role.get_name_display()}: {user_count} users")

    # Check users
    users = User.objects.all()
    print(f"\n✅ Users in database: {users.count()}")

    # Show sample of users with roles
    if users.exists():
        print("\nSample of users:")
        for user in users[:5]:  # Show first 5 users
            role = user.role.name if user.role else 'None'
            staff_status = "staff" if user.is_staff else ""
            super_status = "superuser" if user.is_superuser else ""
            flags = f"({staff_status} {super_status})".strip("() ")
            print(f"  - {user.username}: {role} {flags if flags else ''}")


def main():
    """Main execution"""
    print("\n" + "=" * 70)
    print("ROLE-BASED ACCESS CONTROL SETUP")
    print("=" * 70)
    print("\nThis script will:")
    print("1. Generate migrations for the Role model")
    print("2. Apply all pending migrations")
    print("3. Create default roles (admin, user)")
    print("4. Sync existing users with appropriate roles")
    print("5. Verify the setup")
    print("\n" + "=" * 70)

    # Confirm
    response = input("\nContinue? (y/n): ")
    if response.lower() != 'y':
        print("Aborted.")
        return

    # Step 1: Generate migrations
    if not create_migrations():
        print("\n❌ Setup failed at migration generation step")
        return

    # Step 2: Apply migrations
    if not apply_migrations():
        print("\n❌ Setup failed at migration apply step")
        return

    # Step 3: Create roles
    try:
        admin_role, user_role = create_default_roles()
    except Exception as e:
        print(f"\n❌ Setup failed at role creation step: {e}")
        return

    # Step 4: Sync existing users
    try:
        sync_existing_users(admin_role, user_role)
    except Exception as e:
        print(f"\n❌ Setup failed at user sync step: {e}")
        return

    # Step 5: Verify
    try:
        verify_setup()
    except Exception as e:
        print(f"\n⚠️  Verification step failed: {e}")

    # Success
    print("\n" + "=" * 70)
    print("✅ ROLE-BASED ACCESS CONTROL SETUP COMPLETED!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Restart your Django development server")
    print("2. Test login with admin and user accounts")
    print("3. Check that redirections work correctly")
    print("\nFor more information, see ROLE_BASED_ACCESS_CONTROL.md")
    print("=" * 70 + "\n")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSetup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
