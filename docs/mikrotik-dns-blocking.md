# Configuration MikroTik pour le Blocage DNS

Ce document décrit la configuration complète du blocage DNS via MikroTik pour le portail captif.

## Vue d'ensemble

Le blocage DNS fonctionne en créant des entrées DNS statiques sur le routeur MikroTik qui redirigent les domaines bloqués vers `0.0.0.0`. Cette méthode est efficace pour HTTP et HTTPS car le blocage intervient au niveau de la résolution DNS, avant même l'établissement de la connexion.

### Avantages
- Fonctionne pour HTTP et HTTPS
- Pas de proxy nécessaire
- Pas de Layer7 (peu performant)
- Simple à maintenir
- Faible impact sur les performances

### Limitations
- Les utilisateurs peuvent contourner avec des DNS alternatifs (solution: redirection DNS forcée)
- Les applications mobiles avec DNS hardcodé peuvent contourner (rare)
- DNS over HTTPS (DoH) peut contourner (solution: bloquer les serveurs DoH connus)

## Configuration MikroTik

### 1. Configuration du serveur DNS

```routeros
# Activer le serveur DNS avec cache
/ip dns set allow-remote-requests=yes cache-size=4096KiB

# Définir les serveurs DNS upstream
/ip dns set servers=1.1.1.1,8.8.8.8

# Vérifier la configuration
/ip dns print
```

### 2. Redirection DNS forcée

Ces règles NAT redirigent toutes les requêtes DNS vers le routeur, empêchant le contournement.

```routeros
# Rediriger DNS UDP (port 53)
/ip firewall nat add chain=dstnat protocol=udp dst-port=53 \
    in-interface=bridge action=redirect to-ports=53 \
    comment="Force DNS to router (UDP)"

# Rediriger DNS TCP (port 53)
/ip firewall nat add chain=dstnat protocol=tcp dst-port=53 \
    in-interface=bridge action=redirect to-ports=53 \
    comment="Force DNS to router (TCP)"

# Bloquer DNS over TLS (DoT) - port 853
/ip firewall filter add chain=forward protocol=tcp dst-port=853 \
    in-interface=bridge action=drop \
    comment="Block DNS over TLS"
```

**Note:** Remplacez `bridge` par le nom de votre interface LAN.

### 3. Bloquer les serveurs DoH connus (optionnel)

Pour empêcher le contournement via DNS over HTTPS:

```routeros
# Liste d'adresses des serveurs DoH connus
/ip firewall address-list add list=doh-servers address=1.1.1.1 comment="Cloudflare DoH"
/ip firewall address-list add list=doh-servers address=1.0.0.1 comment="Cloudflare DoH"
/ip firewall address-list add list=doh-servers address=8.8.8.8 comment="Google DoH"
/ip firewall address-list add list=doh-servers address=8.8.4.4 comment="Google DoH"
/ip firewall address-list add list=doh-servers address=9.9.9.9 comment="Quad9 DoH"

# Bloquer les connexions HTTPS vers ces serveurs
/ip firewall filter add chain=forward protocol=tcp dst-port=443 \
    dst-address-list=doh-servers action=drop \
    comment="Block DNS over HTTPS"
```

## Configuration de l'utilisateur API

### Création d'un compte API avec permissions minimales

```routeros
# Créer un groupe avec permissions minimales
/user group add name=captive-portal-dns \
    policy=api,read,write,!ftp,!local,!password,!policy,!reboot,!sensitive,!sniff,!ssh,!telnet,!test,!web,!winbox

# Créer l'utilisateur API
# IMPORTANT: Changez le mot de passe!
/user add name=captive-portal-api password="VOTRE_MOT_DE_PASSE_SECURISE" \
    group=captive-portal-dns \
    address=192.168.88.0/24 \
    comment="API user for Captive Portal DNS blocking"

# Activer le service API REST
/ip service enable api
/ip service set api port=8728

# Pour la production avec SSL (recommandé):
# /ip service enable api-ssl
# /ip service set api-ssl port=8729
```

**Recommandations de sécurité:**
- Limitez `address` à l'IP du serveur Django
- Utilisez un mot de passe fort (min. 16 caractères)
- Activez SSL en production (port 8729)
- Surveillez les logs d'authentification

## Variables d'environnement Django

Ajoutez ces variables à votre fichier `.env`:

```bash
# Configuration MikroTik
MIKROTIK_HOST=192.168.88.1
MIKROTIK_PORT=8728
MIKROTIK_USERNAME=captive-portal-api
MIKROTIK_PASSWORD=votre_mot_de_passe_securise
MIKROTIK_USE_SSL=false

# URL de l'agent MikroTik (si utilisé)
MIKROTIK_AGENT_URL=http://localhost:3001
MIKROTIK_AGENT_TIMEOUT=10
```

## Exemples d'entrées DNS statiques

### Blocage simple

```routeros
# Bloquer facebook.com
/ip dns static add name=facebook.com address=0.0.0.0 \
    comment="captive-portal-block:1| Social network"

# Bloquer www.facebook.com séparément
/ip dns static add name=www.facebook.com address=0.0.0.0 \
    comment="captive-portal-block:2| Social network"
```

### Blocage avec wildcards (sous-domaines)

```routeros
# Bloquer tous les sous-domaines de tiktok.com
/ip dns static add regexp=".*\\.tiktok\\.com$" address=0.0.0.0 \
    comment="captive-portal-block:3| TikTok and subdomains"
```

### Gestion des entrées

```routeros
# Lister toutes les entrées
/ip dns static print

# Lister les entrées gérées par le portail
/ip dns static print where comment~"captive-portal-block"

# Supprimer une entrée par ID
/ip dns static remove [find where comment~"captive-portal-block:1"]

# Désactiver temporairement une entrée
/ip dns static set [find where comment~"captive-portal-block:1"] disabled=yes
```

## Utilisation depuis Django

### Administration Django

1. Accédez à **Admin > Sites bloqués**
2. Cliquez sur **Ajouter site bloqué**
3. Entrez le domaine (ex: `facebook.com` ou `*.tiktok.com`)
4. Sélectionnez la catégorie
5. Sauvegardez → La synchronisation MikroTik est automatique

### Actions en masse

- **Synchroniser avec MikroTik**: Synchronise les entrées sélectionnées
- **Forcer la resynchronisation**: Supprime et recrée les entrées
- **Activer/Désactiver**: Active ou désactive les blocages

### Commande de synchronisation

```bash
# Synchroniser les domaines en attente
python manage.py sync_blocked_domains

# Forcer la resynchronisation de tous
python manage.py sync_blocked_domains --force

# Mode simulation (affiche sans modifier)
python manage.py sync_blocked_domains --dry-run

# Nettoyer les entrées orphelines
python manage.py sync_blocked_domains --cleanup

# Importer les entrées existantes depuis MikroTik
python manage.py sync_blocked_domains --import

# Afficher les statistiques
python manage.py sync_blocked_domains --stats
```

### Tâche cron recommandée

```cron
# Synchroniser toutes les 5 minutes
*/5 * * * * cd /path/to/project && python manage.py sync_blocked_domains 2>&1 | logger -t captive-portal-dns
```

## Dépannage

### Vérifier la connexion MikroTik

```bash
# Test de connexion
curl -X GET http://MIKROTIK_AGENT_URL/api/mikrotik/test
```

### Vérifier les entrées DNS

```routeros
# Sur MikroTik
/ip dns static print where address=0.0.0.0
```

### Vérifier la résolution DNS

```bash
# Depuis un client
nslookup facebook.com MIKROTIK_IP
# Devrait retourner 0.0.0.0 si bloqué
```

### Logs

```bash
# Django logs
tail -f /var/log/captive-portal/django.log | grep dns

# MikroTik logs
/log print where topics~"dns"
```

## Extension future: Blocage par profil

L'architecture supporte le blocage ciblé par profil ou promotion (non implémenté côté MikroTik pour l'instant):

1. **Profil** : Les utilisateurs avec ce profil sont soumis au blocage
2. **Promotion** : Les utilisateurs de cette promotion sont soumis au blocage
3. **Global** : Tous les utilisateurs sont soumis au blocage (défaut)

Pour implémenter le blocage par profil, il faudrait:
- Utiliser des address-lists MikroTik par profil
- Créer des règles firewall conditionnelles
- Synchroniser les utilisateurs avec leur profil/promotion

## Script de configuration complet

```routeros
# ============================================
# Configuration MikroTik pour le blocage DNS
# Portail Captif - Script de configuration
# ============================================

# 1. Configuration du serveur DNS
# --------------------------------
/ip dns set allow-remote-requests=yes cache-size=4096KiB
/ip dns set servers=1.1.1.1,8.8.8.8
/ip dns print

# 2. Redirection DNS forcée
# -------------------------
/ip firewall nat add chain=dstnat protocol=udp dst-port=53 in-interface=bridge action=redirect to-ports=53 comment="Force DNS to router (UDP)"
/ip firewall nat add chain=dstnat protocol=tcp dst-port=53 in-interface=bridge action=redirect to-ports=53 comment="Force DNS to router (TCP)"
/ip firewall filter add chain=forward protocol=tcp dst-port=853 in-interface=bridge action=drop comment="Block DNS over TLS"

# 3. Création de l'utilisateur API
# ---------------------------------
# IMPORTANT: Changez le mot de passe!
/user group add name=captive-portal-dns policy=api,read,write,!ftp,!local,!password,!policy,!reboot,!sensitive,!sniff,!ssh,!telnet,!test,!web,!winbox
/user add name=captive-portal-api password=CHANGE_ME group=captive-portal-dns address=0.0.0.0/0 comment="API user for Captive Portal DNS blocking"
/ip service enable api
/ip service set api port=8728

# 4. Vérification
# ---------------
/ip dns print
/ip firewall nat print where comment~"DNS"
/user print where name=captive-portal-api

# Script terminé
```
