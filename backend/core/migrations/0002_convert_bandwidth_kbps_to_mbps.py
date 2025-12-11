# Generated migration to convert bandwidth from Kbps to Mbps

from django.db import migrations


def convert_kbps_to_mbps(apps, schema_editor):
    """
    Convertit les valeurs de bande passante de Kbps vers Mbps.
    Divise toutes les valeurs existantes par 1024.
    """
    Profile = apps.get_model('core', 'Profile')

    for profile in Profile.objects.all():
        # Convertir Kbps en Mbps (diviser par 1024)
        profile.bandwidth_upload = max(1, profile.bandwidth_upload // 1024)
        profile.bandwidth_download = max(1, profile.bandwidth_download // 1024)
        profile.save(update_fields=['bandwidth_upload', 'bandwidth_download'])

    print(f"✅ Converted {Profile.objects.count()} profiles from Kbps to Mbps")


def convert_mbps_to_kbps(apps, schema_editor):
    """
    Migration inverse: convertit de Mbps vers Kbps.
    Multiplie toutes les valeurs par 1024.
    """
    Profile = apps.get_model('core', 'Profile')

    for profile in Profile.objects.all():
        # Convertir Mbps en Kbps (multiplier par 1024)
        profile.bandwidth_upload = profile.bandwidth_upload * 1024
        profile.bandwidth_download = profile.bandwidth_download * 1024
        profile.save(update_fields=['bandwidth_upload', 'bandwidth_download'])

    print(f"✅ Converted {Profile.objects.count()} profiles from Mbps to Kbps")


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),  # Ajuster selon votre dernière migration
    ]

    operations = [
        migrations.RunPython(convert_kbps_to_mbps, convert_mbps_to_kbps),
    ]
