# Generated manually for creating Promotion model

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0008_add_cleartext_password'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text="Nom de la promotion (ex: ING3, L1, M2, etc.)", max_length=100, unique=True)),
                ('description', models.TextField(blank=True, help_text='Description de la promotion', null=True)),
                ('is_active', models.BooleanField(default=True, help_text='Si la promotion est active et peut être sélectionnée')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Promotion',
                'verbose_name_plural': 'Promotions',
                'db_table': 'promotions',
                'ordering': ['name'],
            },
        ),
    ]
