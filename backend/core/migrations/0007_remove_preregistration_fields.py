# Generated migration

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_add_radius_activation_field'),
    ]

    operations = [
        # Remove the unique constraint on student identity
        migrations.RemoveConstraint(
            model_name='user',
            name='unique_student_identity',
        ),
        # Remove is_pre_registered field
        migrations.RemoveField(
            model_name='user',
            name='is_pre_registered',
        ),
        # Remove registration_completed field
        migrations.RemoveField(
            model_name='user',
            name='registration_completed',
        ),
    ]
