# 📊 Guide complet du système de quotas FreeRADIUS

Ce guide explique comment utiliser le système de quotas basé sur `radcheck.quota` et `radacct`.

## 📋 Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Installation](#installation)
3. [Définir des quotas](#définir-des-quotas)
4. [Vérification automatique](#vérification-automatique)
5. [Gestion des utilisateurs](#gestion-des-utilisateurs)
6. [Surveillance](#surveillance)
7. [Intégration avec les profils](#intégration-avec-les-profils)

---

## Vue d'ensemble

### Principe de fonctionnement

Le système de quotas fonctionne de manière simple et efficace:

1. **Quota défini**: Le quota de chaque utilisateur est stocké dans `radcheck.quota` (en octets)
2. **Consommation calculée**: La consommation réelle est calculée depuis `radacct` (acctinputoctets + acctoutputoctets)
3. **Vérification automatique**: Une commande Django vérifie périodiquement si consommation ≥ quota
4. **Désactivation automatique**: Quand le quota est atteint, `statut=0` est défini dans radcheck
5. **Réactivation manuelle**: Un admin peut réactiver l'utilisateur et ajuster le quota

### Schéma

```
┌─────────────────┐
│   radcheck      │
├─────────────────┤
│ username        │
│ attribute       │
│ value (pass)    │
│ statut (1/0)    │  ← Contrôle l'accès
│ quota (octets)  │  ← Limite autorisée
└─────────────────┘
        │
        ▼
    Vérification
        │
        ▼
┌─────────────────┐
│   radacct       │
├─────────────────┤
│ username        │
│ acctinputoctets │  ← Download
│ acctoutputoctets│  ← Upload
└─────────────────┘
        │
        ▼
  Consommation = Sum(input + output)
        │
        ▼
  Si consommation ≥ quota
    → statut = 0 (désactivé)
```

---

## Installation

### Étape 1: Appliquer les migrations

#### Option A: Via Django migrations (recommandé)

```bash
cd /home/user/captive-portal/backend

# Activer l'environnement virtuel si nécessaire
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows

# Appliquer la migration
python manage.py migrate radius
```

#### Option B: Via SQL direct

Si vous préférez ou si les migrations ne fonctionnent pas:

```bash
# MySQL/MariaDB
mysql -u radius_user -p radius_db < add_quota_field.sql

# PostgreSQL
psql -U radius_user -d radius_db -f add_quota_field.sql
```

### Étape 2: Vérifier l'installation

```sql
-- Vérifier que le champ quota existe
DESCRIBE radcheck;  -- MySQL
-- OU
\d radcheck  -- PostgreSQL
```

Vous devriez voir une colonne `quota` de type `BIGINT NULL`.

---

## Définir des quotas

### Conversion Go → Octets

```
1 Go  = 1,073,741,824 octets (1024³)
5 Go  = 5,368,709,120 octets
10 Go = 10,737,418,240 octets
50 Go = 53,687,091,200 octets
100 Go = 107,374,182,400 octets
```

### Méthode 1: Via SQL

```sql
-- Définir un quota de 50 Go pour un utilisateur
UPDATE radcheck
SET quota = 53687091200
WHERE username = 'john.doe' AND attribute = 'Cleartext-Password';

-- Définir un quota de 100 Go pour une promotion entière
UPDATE radcheck r
INNER JOIN core_user u ON r.username = u.username
INNER JOIN core_promotion p ON u.promotion_id = p.id
SET r.quota = 107374182400
WHERE p.name = 'Promo2024' AND r.attribute = 'Cleartext-Password';

-- Quota illimité (NULL)
UPDATE radcheck
SET quota = NULL
WHERE username = 'admin.user';
```

### Méthode 2: Via Django Shell

```python
from radius.models import RadCheck

# Définir un quota de 50 Go (53687091200 octets)
RadCheck.objects.filter(
    username='john.doe',
    attribute='Cleartext-Password'
).update(quota=53687091200)

# Quota illimité
RadCheck.objects.filter(
    username='admin.user',
    attribute='Cleartext-Password'
).update(quota=None)
```

### Méthode 3: Lors de l'activation RADIUS

Modifiez `core/viewsets.py` dans la fonction `activate_radius()`:

```python
def activate_radius(user, profile, promotion=None):
    # ... code existant ...

    # Définir le quota depuis le profil
    quota_bytes = None
    if profile.quota_type == 'limited':
        quota_bytes = profile.data_volume

    RadCheck.objects.update_or_create(
        username=user.username,
        attribute='Cleartext-Password',
        defaults={
            'value': user.cleartext_password,
            'statut': True,
            'quota': quota_bytes  # ← Ajouter ici
        }
    )
```

---

## Vérification automatique

### Commande Django

Le système inclut une commande de management pour vérifier les quotas:

```bash
# Mode test (aucune modification)
python manage.py check_radcheck_quotas --dry-run

# Mode détaillé
python manage.py check_radcheck_quotas --dry-run --verbose

# Mode réel (désactive les utilisateurs)
python manage.py check_radcheck_quotas

# Mode réel avec détails
python manage.py check_radcheck_quotas --verbose
```

### Sortie attendue

```
======================================================================
VÉRIFICATION DES QUOTAS RADCHECK
======================================================================

🔍 MODE DRY-RUN: Aucune modification ne sera effectuée

✓ 42 utilisateurs avec quota trouvés

[1] Vérification: john.doe
  📊 Quota: 48.23 Go / 50.00 Go (96.5%)
  ✓ OK: 1.77 Go restants (3.5%)

[2] Vérification: jane.smith
  📊 Quota: 52.15 Go / 50.00 Go (104.3%)
  [DRY-RUN] Désactiverait: jane.smith - Quota dépassé: 52.15 Go / 50.00 Go

======================================================================
STATISTIQUES
======================================================================

📊 Utilisateurs vérifiés: 42
⊘ Sans quota défini: 5
⊘ Sans consommation: 3
⊗ Déjà déconnectés: 2

🟡 Seraient désactivés: 1

✅ Vérification terminée
======================================================================

💡 Exécutez sans --dry-run pour effectuer les désactivations
```

### Configuration Cron

Pour vérifier automatiquement toutes les 10 minutes:

#### Linux/Mac

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne:
*/10 * * * * cd /home/user/captive-portal/backend && /path/to/venv/bin/python manage.py check_radcheck_quotas >> /var/log/quota_check.log 2>&1
```

#### Windows (Planificateur de tâches)

1. Créer un fichier `check_quotas.bat`:

```batch
@echo off
cd C:\Users\nguim\OneDrive\Bureau\captive-portal\backend
call venv\Scripts\activate
python manage.py check_radcheck_quotas >> C:\logs\quota_check.log 2>&1
```

2. Dans le Planificateur de tâches Windows:
   - Nom: "Vérification Quotas RADIUS"
   - Déclencheur: Répéter toutes les 10 minutes
   - Action: Démarrer un programme → `check_quotas.bat`

---

## Gestion des utilisateurs

### Voir la consommation d'un utilisateur

```sql
SELECT
    username,
    SUM(acctinputoctets + acctoutputoctets) AS total_octets,
    ROUND(SUM(acctinputoctets + acctoutputoctets) / 1073741824, 2) AS total_go
FROM radacct
WHERE username = 'john.doe'
GROUP BY username;
```

### Comparer consommation et quota

```sql
SELECT
    rc.username,
    ROUND(rc.quota / 1073741824, 2) AS quota_go,
    ROUND(COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) / 1073741824, 2) AS consomme_go,
    ROUND((COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) / rc.quota * 100), 1) AS pourcentage,
    CASE
        WHEN rc.quota IS NULL THEN 'ILLIMITÉ'
        WHEN COALESCE(SUM(ra.acctinputoctets + ra.acctoutputoctets), 0) >= rc.quota THEN 'DÉPASSÉ'
        ELSE 'OK'
    END AS statut
FROM radcheck rc
LEFT JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
  AND rc.username = 'john.doe'
GROUP BY rc.username, rc.quota;
```

### Réactiver un utilisateur

#### Option 1: Via SQL

```sql
-- Réactiver l'utilisateur
UPDATE radcheck
SET statut = 1
WHERE username = 'john.doe';

-- Optionnel: Augmenter le quota
UPDATE radcheck
SET quota = 107374182400,  -- 100 Go
    statut = 1
WHERE username = 'john.doe' AND attribute = 'Cleartext-Password';
```

#### Option 2: Via l'interface admin

Si vous avez déjà le système de déconnexion:

1. Aller dans `/admin/disconnections`
2. Trouver l'utilisateur
3. Cliquer sur "Réactiver"

#### Option 3: Via Django Shell

```python
from radius.models import RadCheck
from core.models import User, UserDisconnectionLog

username = 'john.doe'

# Réactiver dans radcheck
RadCheck.objects.filter(username=username).update(statut=True)

# Marquer le log comme résolu
try:
    user = User.objects.get(username=username)
    UserDisconnectionLog.objects.filter(
        user=user,
        is_active=True
    ).update(is_active=False)
except User.DoesNotExist:
    pass
```

### Remettre à zéro la consommation

⚠️ **ATTENTION**: Ceci supprime l'historique de consommation!

```sql
-- Supprimer toutes les sessions d'un utilisateur
DELETE FROM radacct WHERE username = 'john.doe';

-- OU supprimer seulement les anciennes sessions (>30 jours)
DELETE FROM radacct
WHERE username = 'john.doe'
  AND acctstarttime < DATE_SUB(NOW(), INTERVAL 30 DAY);
```

---

## Surveillance

### Top 10 des plus gros consommateurs

```sql
SELECT
    username,
    ROUND(SUM(acctinputoctets + acctoutputoctets) / 1073741824, 2) AS total_go,
    COUNT(*) AS nb_sessions
FROM radacct
GROUP BY username
ORDER BY total_go DESC
LIMIT 10;
```

### Utilisateurs qui ont dépassé leur quota

```sql
SELECT
    rc.username,
    ROUND(rc.quota / 1073741824, 2) AS quota_go,
    ROUND(SUM(ra.acctinputoctets + ra.acctoutputoctets) / 1073741824, 2) AS consomme_go,
    ROUND((SUM(ra.acctinputoctets + ra.acctoutputoctets) - rc.quota) / 1073741824, 2) AS depassement_go,
    rc.statut AS actif
FROM radcheck rc
INNER JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
  AND rc.quota IS NOT NULL
GROUP BY rc.username, rc.quota, rc.statut
HAVING SUM(ra.acctinputoctets + ra.acctoutputoctets) >= rc.quota
ORDER BY depassement_go DESC;
```

### Utilisateurs proches du quota (>80%)

```sql
SELECT
    rc.username,
    ROUND(rc.quota / 1073741824, 2) AS quota_go,
    ROUND(SUM(ra.acctinputoctets + ra.acctoutputoctets) / 1073741824, 2) AS consomme_go,
    ROUND(SUM(ra.acctinputoctets + ra.acctoutputoctets) / rc.quota * 100, 1) AS pourcentage
FROM radcheck rc
INNER JOIN radacct ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password'
  AND rc.quota IS NOT NULL
GROUP BY rc.username, rc.quota
HAVING SUM(ra.acctinputoctets + ra.acctoutputoctets) / rc.quota >= 0.8
   AND SUM(ra.acctinputoctets + ra.acctoutputoctets) < rc.quota
ORDER BY pourcentage DESC;
```

### Dashboard SQL complet

```sql
SELECT
    -- Compteurs généraux
    COUNT(DISTINCT rc.username) AS total_utilisateurs,
    SUM(CASE WHEN rc.quota IS NOT NULL THEN 1 ELSE 0 END) AS avec_quota,
    SUM(CASE WHEN rc.quota IS NULL THEN 1 ELSE 0 END) AS illimites,
    SUM(CASE WHEN rc.statut = 1 THEN 1 ELSE 0 END) AS actifs,
    SUM(CASE WHEN rc.statut = 0 THEN 1 ELSE 0 END) AS desactives,

    -- Consommation totale
    ROUND(SUM(COALESCE(ra.total, 0)) / 1073741824, 2) AS consommation_totale_go,

    -- Quota total alloué
    ROUND(SUM(COALESCE(rc.quota, 0)) / 1073741824, 2) AS quota_total_go
FROM radcheck rc
LEFT JOIN (
    SELECT username, SUM(acctinputoctets + acctoutputoctets) as total
    FROM radacct
    GROUP BY username
) ra ON rc.username = ra.username
WHERE rc.attribute = 'Cleartext-Password';
```

---

## Intégration avec les profils

### Définir automatiquement le quota depuis le profil

Modifiez `core/viewsets.py`:

```python
from radius.models import RadCheck

def activate_radius(user, profile, promotion=None):
    """
    Active RADIUS pour un utilisateur avec son profil
    """
    # Calculer le quota
    quota_bytes = None
    if profile.quota_type == 'limited':
        quota_bytes = profile.data_volume

    # Créer/Mettre à jour l'entrée dans radcheck
    RadCheck.objects.update_or_create(
        username=user.username,
        attribute='Cleartext-Password',
        defaults={
            'op': ':=',
            'value': user.cleartext_password,
            'statut': True,
            'quota': quota_bytes  # ← Définir le quota
        }
    )

    # ... reste du code (radreply, radusergroup, etc.)
```

### Mettre à jour le quota lors du changement de profil

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models import User
from radius.models import RadCheck

@receiver(post_save, sender=User)
def update_user_quota(sender, instance, **kwargs):
    """
    Met à jour le quota RADIUS quand le profil de l'utilisateur change
    """
    if instance.is_radius_activated:
        profile = instance.get_effective_profile()

        if profile:
            quota_bytes = None
            if profile.quota_type == 'limited':
                quota_bytes = profile.data_volume

            RadCheck.objects.filter(
                username=instance.username,
                attribute='Cleartext-Password'
            ).update(quota=quota_bytes)
```

---

## Exemples pratiques

### Scénario 1: Nouvel utilisateur avec quota 50 Go

```python
from core.models import User, Promotion
from radius.models import RadCheck

# Créer l'utilisateur
user = User.objects.create(
    username='new.student',
    first_name='New',
    last_name='Student',
    email='new.student@ucac-icam.com'
)
user.set_password('SecurePass123!')
user.save()

# Activer RADIUS avec quota 50 Go
RadCheck.objects.create(
    username='new.student',
    attribute='Cleartext-Password',
    op=':=',
    value='SecurePass123!',
    statut=True,
    quota=53687091200  # 50 Go
)
```

### Scénario 2: Promotion entière avec quota 100 Go

```sql
-- Créer/Mettre à jour toutes les entrées radcheck pour une promotion
UPDATE radcheck r
INNER JOIN core_user u ON r.username = u.username
INNER JOIN core_promotion p ON u.promotion_id = p.id
SET r.quota = 107374182400,  -- 100 Go
    r.statut = 1
WHERE p.name = 'Promo2025'
  AND r.attribute = 'Cleartext-Password';
```

### Scénario 3: Alerter les utilisateurs proches du quota

```python
from django.core.mail import send_mail
from radius.models import RadCheck, RadAcct
from core.models import User

# Trouver les utilisateurs à plus de 90% du quota
for radcheck in RadCheck.objects.filter(attribute='Cleartext-Password', quota__isnull=False):
    usage = RadAcct.objects.filter(username=radcheck.username).aggregate(
        total=Sum('acctinputoctets') + Sum('acctoutputoctets')
    )['total'] or 0

    if usage / radcheck.quota >= 0.9:
        # Envoyer un email d'avertissement
        try:
            user = User.objects.get(username=radcheck.username)
            percent = (usage / radcheck.quota * 100)

            send_mail(
                subject='Avertissement: Quota proche',
                message=f'Vous avez utilisé {percent:.1f}% de votre quota.',
                from_email='noreply@ucac-icam.com',
                recipient_list=[user.email],
            )
        except User.DoesNotExist:
            pass
```

---

## Dépannage

### Problème: Les utilisateurs ne sont pas désactivés

**Vérifications:**

1. Le cron est-il actif?
```bash
# Linux
systemctl status cron

# Voir les logs
grep check_radcheck_quotas /var/log/syslog
```

2. La commande fonctionne-t-elle manuellement?
```bash
python manage.py check_radcheck_quotas --dry-run --verbose
```

3. Les quotas sont-ils définis?
```sql
SELECT COUNT(*) FROM radcheck WHERE quota IS NOT NULL;
```

### Problème: La consommation n'est pas comptée

**Vérifications:**

1. Les sessions sont-elles enregistrées dans radacct?
```sql
SELECT COUNT(*) FROM radacct;
SELECT * FROM radacct ORDER BY acctstarttime DESC LIMIT 5;
```

2. FreeRADIUS envoie-t-il les accounting packets?
```bash
# Vérifier les logs FreeRADIUS
tail -f /var/log/freeradius/radius.log | grep Accounting
```

3. La configuration accounting est-elle activée?
```bash
# Vérifier raddb/sites-enabled/default
grep accounting /etc/freeradius/3.0/sites-enabled/default
```

### Problème: Quota dépassé mais utilisateur toujours actif

**Solution:**

```sql
-- Forcer la désactivation
UPDATE radcheck
SET statut = 0
WHERE username = 'problematic.user';

-- Vérifier
SELECT username, statut FROM radcheck WHERE username = 'problematic.user';
```

---

## Ressources supplémentaires

- **Script SQL**: `backend/add_quota_field.sql`
- **Commande Django**: `backend/core/management/commands/check_radcheck_quotas.py`
- **Modèles**: `backend/radius/models.py`
- **Guide de déploiement**: `DEPLOYMENT_AUTO_DISCONNECT.md`

---

**🎉 Votre système de quotas est prêt à l'emploi!**
