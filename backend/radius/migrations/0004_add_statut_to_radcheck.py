from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('radius', '0003_rename_radcheck_username_idx_radcheck_usernam_d6e966_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='radcheck',
            name='statut',
            field=models.BooleanField(default=True, help_text='1 = actif, 0 = désactivé'),
        ),
    ]

