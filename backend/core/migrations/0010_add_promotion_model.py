from django.db import migrations, models


def forward_fill_promotions(apps, schema_editor):
    """
    Crée des promotions à partir des valeurs texte existantes (si colonne encore présente).
    On ignore silencieusement si la colonne texte n'existe plus.
    """
    User = apps.get_model('core', 'User')
    Promotion = apps.get_model('core', 'Promotion')

    # Si la colonne texte a déjà disparu, on n'a rien à faire
    if 'promotion' not in [f.name for f in User._meta.fields]:
        return

    # Les anciennes valeurs étaient du texte; on tente de migrer vers la FK
    for user in User.objects.all().iterator():
        value = getattr(user, 'promotion', None)
        if value:
            promo, _ = Promotion.objects.get_or_create(name=value, defaults={'is_active': True})
            user.promotion = promo
            user.save(update_fields=['promotion'])


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_promotion_user_is_radius_enabled_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Promotion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(db_index=True, max_length=100, unique=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'promotions',
                'ordering': ['name'],
            },
        ),
        migrations.AlterField(
            model_name='user',
            name='promotion',
            field=models.ForeignKey(blank=True, help_text="Promotion de l'étudiant", null=True, on_delete=models.SET_NULL, related_name='users', to='core.promotion'),
        ),
        migrations.RunPython(forward_fill_promotions, migrations.RunPython.noop),
    ]

