# Generated manually on 2025-11-26

from django.db import migrations, models


def migrate_role_data(apps, schema_editor):
    """Migrate role data from ForeignKey to CharField"""
    User = apps.get_model('core', 'User')
    db_alias = schema_editor.connection.alias

    # Update all users to copy role.name to role_temp
    for user in User.objects.using(db_alias).all():
        if user.role_id:
            # Get the role name from the roles table
            Role = apps.get_model('core', 'Role')
            try:
                role = Role.objects.using(db_alias).get(id=user.role_id)
                user.role_temp = role.name
            except Role.DoesNotExist:
                user.role_temp = 'user'
        else:
            user.role_temp = 'user'
        user.save()


def reverse_migrate_role_data(apps, schema_editor):
    """Reverse migration - recreate role relationships"""
    # This is a destructive operation, so we just set a default
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_userquota_blockedsite'),
    ]

    operations = [
        # Step 1: Add temporary CharField for role
        migrations.AddField(
            model_name='user',
            name='role_temp',
            field=models.CharField(
                choices=[('admin', 'Administrator'), ('user', 'User')],
                db_index=True,
                default='user',
                max_length=50
            ),
        ),
        # Step 2: Copy data from role ForeignKey to role_temp CharField
        migrations.RunPython(migrate_role_data, reverse_migrate_role_data),
        # Step 3: Remove the old role ForeignKey field
        migrations.RemoveField(
            model_name='user',
            name='role',
        ),
        # Step 4: Rename role_temp to role
        migrations.RenameField(
            model_name='user',
            old_name='role_temp',
            new_name='role',
        ),
        # Step 5: Delete the Role model/table
        migrations.DeleteModel(
            name='Role',
        ),
    ]
