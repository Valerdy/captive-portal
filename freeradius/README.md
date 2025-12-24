# Configuration FreeRADIUS pour Captive Portal

Ce dossier contient les fichiers de configuration FreeRADIUS nécessaires pour le système de quotas et le refus d'accès automatique.

## Fichiers inclus

### 1. `queries.conf` - Requêtes SQL personnalisées
Contient les requêtes SQL pour:
- Vérification du quota avant authentification
- Récupération des attributs utilisateur
- Comptabilisation de la consommation

### 2. `policy.d/captive_portal_quota` - Politique de quota
Contient les règles unlang pour:
- Vérifier si l'utilisateur a dépassé son quota
- Vérifier si le compte a expiré
- Retourner Access-Reject si nécessaire

## Installation

### Étape 1: Copier les fichiers
```bash
# Copier queries.conf vers le module SQL
sudo cp queries.conf /etc/freeradius/3.0/mods-config/sql/main/mysql/

# Copier la politique de quota
sudo cp policy.d/captive_portal_quota /etc/freeradius/3.0/policy.d/
```

### Étape 2: Modifier la configuration SQL
Éditer `/etc/freeradius/3.0/mods-available/sql` et ajouter:
```
$INCLUDE ${modconfdir}/${.:name}/main/${dialect}/queries.conf
```

### Étape 3: Activer la politique
Éditer `/etc/freeradius/3.0/sites-available/default` et ajouter dans la section `authorize`:
```
captive_portal_quota
```

### Étape 4: Redémarrer FreeRADIUS
```bash
sudo systemctl restart freeradius
```

## Fonctionnement

### Vérification du quota
Lors de chaque tentative de connexion, FreeRADIUS:
1. Vérifie si le statut est actif dans radcheck (statut=1)
2. Calcule la consommation totale depuis radacct
3. Compare avec le quota défini dans radcheck
4. Retourne Access-Reject si quota dépassé

### Vérification de la validité
La durée de validité est gérée par Django via les tâches périodiques qui:
1. Vérifient chaque jour si les profils ont expiré
2. Mettent à jour le statut dans radcheck (statut=0)
3. FreeRADIUS refuse ensuite l'accès automatiquement

## Attributs RADIUS utilisés

| Attribut | Table | Description |
|----------|-------|-------------|
| Cleartext-Password | radcheck | Mot de passe utilisateur |
| statut | radcheck | 1=actif, 0=désactivé |
| quota | radcheck | Quota en octets (NULL=illimité) |
| Simultaneous-Use | radcheck | Connexions simultanées max |
| Max-Total-Octets | radcheck | Quota total en octets |
| WISPr-Bandwidth-Max-Up | radreply | Bande passante upload (bps) |
| WISPr-Bandwidth-Max-Down | radreply | Bande passante download (bps) |
| Mikrotik-Rate-Limit | radreply | Format MikroTik (ex: "10M/5M") |
| Session-Timeout | radreply | Timeout session (secondes) |
| Idle-Timeout | radreply | Timeout inactivité (secondes) |

## Dépannage

### Vérifier les logs FreeRADIUS
```bash
sudo tail -f /var/log/freeradius/radius.log
```

### Tester l'authentification
```bash
radtest username password localhost 0 testing123
```

### Vérifier le quota d'un utilisateur
```sql
SELECT username, quota,
       (SELECT COALESCE(SUM(acctinputoctets + acctoutputoctets), 0)
        FROM radacct WHERE radacct.username = radcheck.username) as used
FROM radcheck
WHERE username = 'testuser' AND attribute = 'Cleartext-Password';
```
