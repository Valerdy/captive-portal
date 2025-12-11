# Profile Management System - Guide d'utilisation

Ce document décrit le système de gestion des profils et quotas utilisateurs.

## Architecture

Le système de profils remplace l'ancien système UserQuota avec une architecture plus cohérente :

- **Profile** : Définit les paramètres d'abonnement (bande passante, quota, durée)
- **UserProfileUsage** : Suit la consommation en temps réel basée sur le profil effectif
- **ProfileHistory** : Historique automatique des changements de profils
- **ProfileAlert** : Système d'alertes configurables

### Hiérarchie des profils

```
Profil individuel utilisateur (priorité 1)
    ↓
Profil de la promotion (priorité 2)
    ↓
Valeurs par défaut (priorité 3)
```

## Management Commands

### 1. Reset des quotas

#### Reset journalier
Réinitialise les compteurs journaliers pour tous les utilisateurs actifs.

```bash
# Test (dry-run)
python manage.py reset_daily_quotas --dry-run

# Exécution
python manage.py reset_daily_quotas
```

**Crontab** : Tous les jours à minuit
```cron
0 0 * * * cd /path/to/backend && python manage.py reset_daily_quotas
```

#### Reset hebdomadaire
Réinitialise les compteurs hebdomadaires (recommandé le lundi).

```bash
# Test (dry-run)
python manage.py reset_weekly_quotas --dry-run

# Exécution
python manage.py reset_weekly_quotas
```

**Crontab** : Tous les lundis à minuit
```cron
0 0 * * 1 cd /path/to/backend && python manage.py reset_weekly_quotas
```

#### Reset mensuel
Réinitialise les compteurs mensuels (1er du mois).

```bash
# Test (dry-run)
python manage.py reset_monthly_quotas --dry-run

# Exécution
python manage.py reset_monthly_quotas
```

**Crontab** : Le 1er de chaque mois à minuit
```cron
0 0 1 * * cd /path/to/backend && python manage.py reset_monthly_quotas
```

### 2. Vérification des alertes

Vérifie les alertes configurées et envoie des notifications.

```bash
# Test (dry-run)
python manage.py check_profile_alerts --dry-run

# Exécution (affiche les alertes sans envoyer d'emails)
python manage.py check_profile_alerts

# Exécution avec envoi d'emails
python manage.py check_profile_alerts --send-email
```

**Crontab** : Toutes les heures
```cron
0 * * * * cd /path/to/backend && python manage.py check_profile_alerts --send-email
```

### 3. Migration UserQuota → UserProfileUsage

**⚠️ Commande à exécuter une seule fois** lors de la transition vers le nouveau système.

```bash
# Aperçu de la migration (dry-run)
python manage.py migrate_quotas_to_profile_usage --dry-run

# Exécution de la migration
python manage.py migrate_quotas_to_profile_usage

# Ignorer les entrées déjà existantes
python manage.py migrate_quotas_to_profile_usage --skip-existing
```

**Après la migration** :
1. Vérifier les données dans Django admin
2. Tester le nouveau système
3. Optionnellement supprimer l'ancienne table UserQuota

## API Endpoints

### Profile Management

#### Lister tous les profils
```http
GET /api/core/profiles/
```

#### Profils actifs uniquement
```http
GET /api/core/profiles/active/
```

#### Statistiques globales
```http
GET /api/core/profiles/statistics/
```

Retourne :
- Résumé (total, actifs, inactifs, limités, illimités)
- Top 5 profils les plus utilisés
- Statistiques pour tous les profils

#### Statistiques détaillées d'un profil
```http
GET /api/core/profiles/{id}/statistics_detail/
```

Retourne :
- Informations du profil
- Nombre d'utilisateurs (directs, via promotion, total)
- Statistiques de consommation (moyenne, max, min, total)
- Distribution par tranches de consommation

#### Utilisateurs d'un profil
```http
GET /api/core/profiles/{id}/users/
```

#### Promotions d'un profil
```http
GET /api/core/profiles/{id}/promotions/
```

### User Profile Usage

#### Mon utilisation (utilisateur connecté)
```http
GET /api/core/profile-usage/my_usage/
```

#### Reset des compteurs (admin)
```http
POST /api/core/profile-usage/{id}/reset_daily/
POST /api/core/profile-usage/{id}/reset_weekly/
POST /api/core/profile-usage/{id}/reset_monthly/
POST /api/core/profile-usage/{id}/reset_all/
```

#### Ajouter de la consommation (pour tests)
```http
POST /api/core/profile-usage/{id}/add_usage/
{
  "bytes_used": 1073741824  // 1 Go
}
```

### Profile History

#### Historique d'un utilisateur
```http
GET /api/core/profile-history/user_history/?user_id={id}
```

#### Tous les changements
```http
GET /api/core/profile-history/
GET /api/core/profile-history/?user={user_id}
GET /api/core/profile-history/?profile={profile_id}
```

### Profile Alerts

#### Vérifier les alertes déclenchées
```http
POST /api/core/profile-alerts/check_alerts/
```

Retourne la liste des alertes déclenchées avec :
- Utilisateur concerné
- Type d'alerte
- Seuil et pourcentage actuel
- Message formaté

#### Lister les alertes
```http
GET /api/core/profile-alerts/
GET /api/core/profile-alerts/?profile={profile_id}
GET /api/core/profile-alerts/?is_active=true
```

## Configuration Email (pour les alertes)

Dans `settings.py` :

```python
# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'noreply@ucac-icam.com'
```

## Signaux Automatiques

Le système utilise des signaux Django pour tracker automatiquement les changements :

### ProfileHistory automatique
Quand le profil d'un utilisateur change :
- Création automatique d'une entrée `ProfileHistory`
- Enregistrement de l'ancien et nouveau profil
- Type de changement (assigned/updated/removed)

### UserProfileUsage automatique
Quand un profil est assigné :
- Création automatique de `UserProfileUsage` si inexistant
- Reset des compteurs lors d'un changement de profil
- Désactivation si le profil est supprimé

## Exemples d'utilisation

### Créer un profil "Étudiant"

Via Django admin ou API :
```json
{
  "name": "Étudiant",
  "description": "Profil standard pour étudiants",
  "bandwidth_upload": 5120,      // 5 Mbps
  "bandwidth_download": 10240,   // 10 Mbps
  "quota_type": "limited",
  "data_volume": 53687091200,    // 50 Go
  "daily_limit": 5368709120,     // 5 Go/jour
  "weekly_limit": 32212254720,   // 30 Go/semaine
  "monthly_limit": 107374182400, // 100 Go/mois
  "validity_duration": 30,       // 30 jours
  "session_timeout": 28800,      // 8 heures
  "idle_timeout": 600,           // 10 minutes
  "simultaneous_use": 1,
  "is_active": true
}
```

### Assigner un profil à un utilisateur

```python
user = User.objects.get(username='john')
profile = Profile.objects.get(name='Étudiant')
user.profile = profile
user.save()
# → ProfileHistory créé automatiquement
# → UserProfileUsage créé automatiquement
```

### Assigner un profil à une promotion

```python
promotion = Promotion.objects.get(name='L3 Info')
profile = Profile.objects.get(name='Étudiant')
promotion.profile = profile
promotion.save()
# → Tous les utilisateurs de la promotion héritent du profil
```

### Configurer une alerte

```python
profile = Profile.objects.get(name='Étudiant')
ProfileAlert.objects.create(
    profile=profile,
    alert_type='quota_warning',
    threshold_percent=80,
    notification_method='email',
    message_template='Attention {username}, vous avez utilisé {percent}% de votre quota. Il reste {remaining_gb} Go.',
    is_active=True
)
```

## Crontab complet recommandé

```cron
# Reset quotas journaliers (tous les jours à minuit)
0 0 * * * cd /path/to/backend && /path/to/venv/bin/python manage.py reset_daily_quotas >> /var/log/quota-reset.log 2>&1

# Reset quotas hebdomadaires (lundi à minuit)
0 0 * * 1 cd /path/to/backend && /path/to/venv/bin/python manage.py reset_weekly_quotas >> /var/log/quota-reset.log 2>&1

# Reset quotas mensuels (1er du mois à minuit)
0 0 1 * * cd /path/to/backend && /path/to/venv/bin/python manage.py reset_monthly_quotas >> /var/log/quota-reset.log 2>&1

# Vérifier les alertes (toutes les heures)
0 * * * * cd /path/to/backend && /path/to/venv/bin/python manage.py check_profile_alerts --send-email >> /var/log/profile-alerts.log 2>&1
```

## Troubleshooting

### Les signaux ne se déclenchent pas
Vérifier que `core.apps.CoreConfig.ready()` importe bien `core.signals`.

### Les emails ne sont pas envoyés
1. Vérifier la configuration EMAIL_* dans settings.py
2. Tester avec `python manage.py shell`:
   ```python
   from django.core.mail import send_mail
   send_mail('Test', 'Message test', 'from@example.com', ['to@example.com'])
   ```

### UserProfileUsage n'existe pas pour un utilisateur
Exécuter :
```bash
python manage.py shell
>>> from core.models import User, UserProfileUsage
>>> for user in User.objects.filter(profile__isnull=False):
...     UserProfileUsage.objects.get_or_create(user=user, defaults={'is_active': True})
```

## Migration depuis l'ancien système

1. **Appliquer les migrations Django**
   ```bash
   python manage.py migrate
   ```

2. **Créer des profils** via Django admin

3. **Assigner des profils** aux utilisateurs/promotions

4. **Migrer les données** UserQuota → UserProfileUsage
   ```bash
   python manage.py migrate_quotas_to_profile_usage --dry-run
   python manage.py migrate_quotas_to_profile_usage
   ```

5. **Configurer les tâches cron**

6. **Tester le système**

7. **Optionnel : Supprimer UserQuota**
   ```python
   UserQuota.objects.all().delete()
   ```
