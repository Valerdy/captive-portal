# 🔄 WORKFLOW COMPLET - PORTAIL CAPTIF

## Table des matières
1. [Vue d'ensemble](#vue-densemble)
2. [Workflow Utilisateur Final](#workflow-utilisateur-final)
3. [Workflow Administrateur](#workflow-administrateur)
4. [Workflow Technique](#workflow-technique)
5. [Workflow des Données](#workflow-des-données)
6. [Workflow d'Intégration](#workflow-dintégration)

---

## Vue d'ensemble

Le **Portail Captif** est un système complet de gestion d'authentification WiFi pour établissements d'enseignement supérieur. Il permet la gestion des utilisateurs, des sessions, des quotas, et l'intégration avec FreeRADIUS et Mikrotik RouterOS.

### Acteurs du système
- **Utilisateur Final (Étudiant/Personnel)** : Accède au WiFi, consulte ses quotas
- **Administrateur** : Gère les utilisateurs, profils, quotas et monitoring
- **Système RADIUS** : Authentifie les connexions WiFi
- **Routeur Mikrotik** : Gère le hotspot et les connexions actives

---

## Workflow Utilisateur Final

### 1. Inscription initiale
```
┌──────────────────────────────────────────────────────────────────┐
│                     INSCRIPTION UTILISATEUR                       │
└──────────────────────────────────────────────────────────────────┘

Étape 1 : Accès au portail
├─ Utilisateur accède à http://portail-captif.example.com
├─ Page d'accueil affichée avec option "S'inscrire"
└─ Clic sur "S'inscrire"

Étape 2 : Formulaire d'inscription
├─ Champs requis :
│  ├─ Prénom
│  ├─ Nom
│  ├─ Matricule (identifiant étudiant)
│  ├─ Promotion/Classe
│  ├─ Mot de passe
│  └─ Confirmation mot de passe
│
├─ Champs optionnels :
│  ├─ Email (auto-généré si non fourni)
│  └─ Numéro de téléphone

Étape 3 : Validation backend
├─ Vérification unicité matricule
├─ Validation format email
├─ Vérification force du mot de passe
├─ Génération username automatique (matricule)
└─ Hash Argon2 du mot de passe

Étape 4 : Création compte
├─ Enregistrement dans la base de données
├─ Statut : is_active = True
├─ Statut RADIUS : is_radius_activated = False
├─ Génération tokens JWT (access + refresh)
├─ Stockage tokens dans cookies HttpOnly
└─ ⚠️ IMPORTANT : Compte créé mais pas encore activé pour WiFi

Étape 5 : Redirection
├─ Notification succès : "Compte créé avec succès"
├─ Redirection vers /dashboard
└─ Message info : "En attente d'activation par l'administrateur"

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur inscrit mais ne peut pas se connecter  │
│            au WiFi tant que l'admin n'a pas activé son compte │
└────────────────────────────────────────────────────────────────┘
```

### 2. Activation par l'administrateur
```
┌──────────────────────────────────────────────────────────────────┐
│                    ACTIVATION RADIUS                              │
└──────────────────────────────────────────────────────────────────┘

Admin → Gestion Promotions → Sélectionne promotion de l'étudiant
  ↓
Clic sur "Activer WiFi" (bouton vert)
  ↓
Transaction atomique :
├─ Vérification : Promotion a un profil assigné
├─ Pour chaque utilisateur de la promotion :
│  ├─ Création entrée radcheck (username + password)
│  ├─ Création entrées radreply (quotas, timeouts, bande passante)
│  ├─ Création entrée radusergroup (mapping groupe)
│  ├─ Mise à jour is_radius_activated = True
│  └─ Mise à jour is_radius_enabled = True
│
├─ En cas d'erreur : ROLLBACK complet
└─ Notification admin : "X utilisateurs activés, Y échecs"

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur peut maintenant se connecter au WiFi   │
└────────────────────────────────────────────────────────────────┘
```

### 3. Première connexion WiFi
```
┌──────────────────────────────────────────────────────────────────┐
│                   CONNEXION WIFI (RADIUS)                         │
└──────────────────────────────────────────────────────────────────┘

Étape 1 : Détection du réseau
├─ Utilisateur sélectionne SSID WiFi de l'établissement
└─ Demande de credentials

Étape 2 : Saisie identifiants
├─ Username : matricule (ex: STU2024001)
├─ Password : mot de passe défini lors de l'inscription
└─ Envoi au serveur RADIUS

Étape 3 : Authentification RADIUS
├─ FreeRADIUS reçoit la requête
├─ Requête SQL :
│  └─ SELECT * FROM radcheck WHERE username='STU2024001'
│
├─ Vérification password (Cleartext-Password)
├─ Si valide → Récupération attributs radreply
│  ├─ Session-Timeout (durée max session)
│  ├─ Idle-Timeout (timeout inactivité)
│  ├─ Mikrotik-Rate-Limit (bande passante)
│  └─ Autres attributs du profil
│
└─ Réponse : Access-Accept ou Access-Reject

Étape 4 : Connexion établie
├─ Attribution adresse IP par DHCP
├─ Application des limites de bande passante
├─ Création session dans portail
│  ├─ session_id unique
│  ├─ Timestamp de début
│  ├─ MAC address
│  ├─ IP address
│  └─ Statut : active
│
└─ Création UserProfileUsage si première connexion

Étape 5 : Enregistrement appareil
├─ Détection MAC address
├─ Création/Mise à jour Device
│  ├─ Type d'appareil (mobile/desktop/tablet)
│  ├─ User-Agent
│  ├─ First seen / Last seen
│  └─ is_active = True
│
└─ Lien Device → Session

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur connecté au WiFi avec quotas appliqués │
└────────────────────────────────────────────────────────────────┘
```

### 4. Utilisation quotidienne
```
┌──────────────────────────────────────────────────────────────────┐
│                     UTILISATION QUOTIDIENNE                       │
└──────────────────────────────────────────────────────────────────┘

Connexion portail web :
├─ Accès à http://portail-captif.example.com/login
├─ Saisie username + password
├─ Vérification JWT
├─ Redirection /dashboard
└─ Affichage :
   ├─ Quota utilisé aujourd'hui
   ├─ Quota restant (jour/semaine/mois)
   ├─ Sessions actives
   ├─ Appareils connectés
   └─ Historique des connexions

Navigation dans le portail :
├─ /dashboard : Vue d'ensemble
├─ /profile : Gestion profil (email, téléphone, mot de passe)
├─ /devices : Liste appareils enregistrés
└─ /sessions : Historique des sessions

Consultation quotas :
└─ Graphiques temps réel :
   ├─ Consommation journalière (%)
   ├─ Consommation hebdomadaire (%)
   ├─ Consommation mensuelle (%)
   └─ Progression vers la limite

Gestion appareils :
├─ Visualisation tous les appareils
├─ Activation/Désactivation appareil
└─ Suppression appareil non utilisé

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur suit sa consommation en temps réel     │
└────────────────────────────────────────────────────────────────┘
```

### 5. Déconnexion et fin de session
```
┌──────────────────────────────────────────────────────────────────┐
│                     FIN DE SESSION                                │
└──────────────────────────────────────────────────────────────────┘

Déconnexion WiFi :
├─ Utilisateur déconnecte manuellement
│  OU
├─ Session-Timeout atteint
│  OU
├─ Idle-Timeout atteint (inactivité)
│  ↓
├─ RADIUS Accounting Stop envoyé
├─ Mise à jour Session :
│  ├─ end_time = now()
│  ├─ bytes_in / bytes_out (total)
│  ├─ packets_in / packets_out
│  ├─ session_time (durée totale)
│  └─ status = 'terminated'
│
├─ Mise à jour UserProfileUsage :
│  ├─ used_today += bytes_total
│  ├─ used_week += bytes_total
│  ├─ used_month += bytes_total
│  └─ used_total += bytes_total
│
└─ Vérification alertes :
   ├─ Si quota > 80% → Alerte "quota_warning"
   ├─ Si quota > 95% → Alerte "quota_critical"
   ├─ Si expiration < 7 jours → Alerte "expiry_warning"
   └─ Si expiration < 2 jours → Alerte "expiry_imminent"

Déconnexion portail web :
├─ Utilisateur clique "Déconnexion"
├─ Appel /api/core/auth/logout/
├─ Suppression tokens JWT (cookies)
├─ Nettoyage localStorage
└─ Redirection /login

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Session terminée, données de consommation mises à  │
│            jour, alertes générées si nécessaire                │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow Administrateur

### 1. Connexion administrateur
```
┌──────────────────────────────────────────────────────────────────┐
│                  CONNEXION ADMINISTRATEUR                         │
└──────────────────────────────────────────────────────────────────┘

Accès admin :
├─ URL : /admin/login
├─ Credentials : username admin + password
├─ Vérification role = 'admin'
├─ Génération tokens JWT
└─ Redirection /admin/dashboard

Dashboard admin affiche :
├─ Statistiques globales :
│  ├─ Total utilisateurs (actifs/inactifs)
│  ├─ Sessions en cours
│  ├─ Appareils connectés
│  ├─ Bande passante consommée aujourd'hui
│  ├─ Total profils créés
│  └─ Profils avec quotas limités
│
├─ Graphiques :
│  ├─ Évolution inscriptions (30 jours)
│  ├─ Distribution sessions (actives/expirées/terminées)
│  ├─ Top 5 utilisateurs (consommation)
│  ├─ Top 5 profils les plus utilisés
│  └─ Répartition types de quotas
│
└─ Actions rapides :
   ├─ Ajouter utilisateur
   ├─ Gérer promotions
   ├─ Gérer profils
   ├─ Configurer quotas
   ├─ Bloquer sites
   └─ Monitoring temps réel
```

### 2. Gestion des profils
```
┌──────────────────────────────────────────────────────────────────┐
│                     GESTION DES PROFILS                           │
└──────────────────────────────────────────────────────────────────┘

Navigation : /admin/profiles

Création nouveau profil :
├─ Clic "Nouveau profil"
├─ Formulaire :
│  ├─ Nom du profil (ex: "Étudiant Standard")
│  ├─ Description
│  ├─ Type de quota : Limité / Illimité
│  │
│  ├─ Configuration bande passante :
│  │  ├─ Upload max (Kbps)
│  │  ├─ Download max (Kbps)
│  │  └─ Preview en Mbps
│  │
│  ├─ Configuration quotas (si limité) :
│  │  ├─ Limite journalière (GB)
│  │  ├─ Limite hebdomadaire (GB)
│  │  ├─ Limite mensuelle (GB)
│  │  └─ Volume total (GB)
│  │
│  ├─ Configuration sessions :
│  │  ├─ Timeout session (minutes)
│  │  ├─ Timeout inactivité (minutes)
│  │  └─ Connexions simultanées max
│  │
│  └─ Durée de validité (7-365 jours)
│
├─ Validation :
│  ├─ Nom unique
│  ├─ Valeurs positives
│  └─ Cohérence limites (jour < semaine < mois)
│
└─ Sauvegarde → Profil disponible pour assignation

Liste des profils :
├─ Affichage tableau :
│  ├─ Nom profil
│  ├─ Type quota
│  ├─ Bande passante
│  ├─ Nombre utilisateurs
│  ├─ Nombre promotions
│  └─ Actions (Modifier/Supprimer/Désactiver)
│
└─ Filtres : Type, Statut (actif/inactif)

Modification profil :
├─ Clic "Modifier"
├─ Chargement données actuelles
├─ Modification champs
├─ Sauvegarde → Création ProfileHistory
│  ├─ old_profile → new_profile
│  ├─ changed_by = admin
│  └─ reason (optionnel)
│
└─ Application immédiate aux utilisateurs assignés

Suppression profil :
├─ Vérification : Pas d'utilisateurs assignés
├─ Si utilisateurs → Erreur "Réassigner d'abord"
└─ Si pas d'utilisateurs → Suppression confirmée

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Profils configurés et prêts pour assignation       │
└────────────────────────────────────────────────────────────────┘
```

### 3. Gestion des promotions
```
┌──────────────────────────────────────────────────────────────────┐
│                   GESTION DES PROMOTIONS                          │
└──────────────────────────────────────────────────────────────────┘

Navigation : /admin/promotions

Création promotion :
├─ Clic "Nouvelle promotion"
├─ Formulaire :
│  ├─ Nom (ex: "L3 Informatique 2024")
│  ├─ Profil assigné (sélection dropdown)
│  └─ Statut actif/inactif
│
└─ Sauvegarde → Promotion créée

Vue liste promotions :
├─ Affichage tableau avec rangées expansibles
├─ Pour chaque promotion :
│  ├─ Nom promotion
│  ├─ Profil assigné
│  ├─ Nombre utilisateurs
│  ├─ Statut (actif/inactif)
│  └─ Actions :
│     ├─ ✅ Activer WiFi (vert)
│     ├─ ❌ Désactiver WiFi (rouge)
│     ├─ ✏️ Modifier
│     ├─ 🗑️ Supprimer
│     └─ 🔽 Développer liste utilisateurs
│
└─ Clic sur ligne → Expansion

Expansion promotion (liste utilisateurs) :
├─ Affichage cartes utilisateurs :
│  ├─ Nom complet
│  ├─ Matricule
│  ├─ Email
│  └─ Indicateur statut WiFi :
│     ├─ 🟢 Vert : is_radius_enabled = True
│     └─ 🔴 Rouge : is_radius_enabled = False
│
└─ Actions individuelles par utilisateur

Activation WiFi promotion (IMPORTANT) :
├─ Clic bouton "Activer WiFi" vert
├─ Confirmation : "Activer X utilisateurs ?"
├─ Process d'activation :
│  │
│  ├─ BEGIN TRANSACTION
│  │
│  ├─ Pour chaque utilisateur de la promotion :
│  │  │
│  │  ├─ Récupération profil (promotion.profile)
│  │  │
│  │  ├─ Création radcheck :
│  │  │  ├─ username = user.username
│  │  │  ├─ attribute = 'Cleartext-Password'
│  │  │  └─ value = user.cleartext_password
│  │  │
│  │  ├─ Création radreply (multiple) :
│  │  │  ├─ Session-Timeout = profile.session_timeout
│  │  │  ├─ Idle-Timeout = profile.idle_timeout
│  │  │  ├─ Mikrotik-Rate-Limit = "upload/download"
│  │  │  ├─ Class = promotion.name
│  │  │  └─ Simultaneous-Use = profile.simultaneous_use
│  │  │
│  │  ├─ Création radusergroup :
│  │  │  ├─ username = user.username
│  │  │  ├─ groupname = promotion.name
│  │  │  └─ priority = 1
│  │  │
│  │  ├─ Création UserProfileUsage (si pas existe) :
│  │  │  ├─ user = user
│  │  │  ├─ Compteurs à 0
│  │  │  └─ activation_date = now()
│  │  │
│  │  ├─ Mise à jour User :
│  │  │  ├─ is_radius_activated = True
│  │  │  └─ is_radius_enabled = True
│  │  │
│  │  └─ Si erreur → ROLLBACK complet
│  │
│  └─ COMMIT TRANSACTION
│
├─ Notification résultat :
│  ├─ "✅ X utilisateurs activés avec succès"
│  └─ "⚠️ Y échecs : [détails]"
│
└─ Rafraîchissement liste

Désactivation WiFi promotion :
├─ Clic bouton "Désactiver WiFi" rouge
├─ Confirmation : "Désactiver X utilisateurs ?"
├─ Process de désactivation :
│  │
│  ├─ BEGIN TRANSACTION
│  │
│  ├─ Pour chaque utilisateur :
│  │  ├─ DELETE FROM radcheck WHERE username = ?
│  │  ├─ DELETE FROM radreply WHERE username = ?
│  │  ├─ DELETE FROM radusergroup WHERE username = ?
│  │  ├─ UPDATE users SET is_radius_enabled = False
│  │  └─ Si erreur → ROLLBACK
│  │
│  └─ COMMIT TRANSACTION
│
└─ Notification + rafraîchissement

Modification promotion :
├─ Changement profil assigné :
│  ├─ Sélection nouveau profil
│  ├─ Sauvegarde
│  └─ Option : "Réactiver tous les utilisateurs ?"
│     ├─ Si oui → Suppression + recréation RADIUS entries
│     └─ Si non → Changement enregistré uniquement
│
└─ Création ProfileHistory pour traçabilité

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Promotion configurée avec activation RADIUS        │
│            groupée, traçabilité complète                       │
└────────────────────────────────────────────────────────────────┘
```

### 4. Gestion des utilisateurs
```
┌──────────────────────────────────────────────────────────────────┐
│                   GESTION DES UTILISATEURS                        │
└──────────────────────────────────────────────────────────────────┘

Navigation : /admin/users

Vue liste utilisateurs :
├─ Tableau avec filtres :
│  ├─ Recherche : Nom/Matricule/Email
│  ├─ Filtre promotion
│  ├─ Filtre statut : Tous/Actifs/Inactifs
│  └─ Filtre WiFi : Tous/Activés/Désactivés
│
├─ Colonnes affichées :
│  ├─ Nom complet
│  ├─ Matricule
│  ├─ Email
│  ├─ Promotion
│  ├─ Profil effectif (individuel ou promotion)
│  ├─ Statut compte (Actif/Inactif)
│  ├─ Statut WiFi (Activé/Désactivé)
│  ├─ Dernière connexion
│  └─ Actions
│
└─ Pagination : 20/50/100 par page

Création manuel utilisateur :
├─ Clic "Ajouter utilisateur"
├─ Formulaire complet :
│  ├─ Informations personnelles
│  ├─ Promotion
│  ├─ Profil individuel (optionnel)
│  ├─ Rôle : User/Admin
│  └─ Mot de passe initial
│
├─ Option : "Activer WiFi immédiatement"
│  └─ Si coché → Création RADIUS entries
│
└─ Sauvegarde + notification

Modification utilisateur :
├─ Clic "Modifier"
├─ Formulaire pré-rempli
├─ Changements possibles :
│  ├─ Informations personnelles
│  ├─ Changement promotion → ProfileHistory créé
│  ├─ Assignation profil individuel
│  ├─ Toggle statut actif/inactif
│  └─ Toggle statut WiFi activé/désactivé
│
└─ Sauvegarde → Synchronisation RADIUS si nécessaire

Actions individuelles :
├─ Activer/Désactiver compte :
│  ├─ Toggle is_active
│  └─ Si désactivé → Suppression RADIUS entries
│
├─ Activer/Désactiver WiFi :
│  ├─ Si activer → Création RADIUS entries
│  └─ Si désactiver → Suppression RADIUS entries
│
├─ Réinitialiser mot de passe :
│  ├─ Génération nouveau mot de passe
│  ├─ Email envoyé à l'utilisateur
│  └─ Mise à jour RADIUS si activé
│
└─ Supprimer utilisateur :
   ├─ Confirmation requise
   ├─ Suppression RADIUS entries
   ├─ Archivage données (sessions, devices)
   └─ Suppression compte

Assignation profil individuel :
├─ Sélection utilisateur
├─ Clic "Assigner profil"
├─ Choix profil (dropdown)
├─ Raison du changement (optionnel)
├─ Sauvegarde :
│  ├─ Création ProfileHistory
│  ├─ Mise à jour user.profile
│  └─ Recréation RADIUS entries avec nouveaux attributs
│
└─ Notification utilisateur (email/SMS si configuré)

Export données :
├─ Bouton "Exporter"
├─ Format : CSV / Excel / PDF
├─ Colonnes personnalisables
└─ Download fichier

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateurs gérés individuellement avec contrôle  │
│            granulaire sur accès et quotas                      │
└────────────────────────────────────────────────────────────────┘
```

### 5. Monitoring temps réel
```
┌──────────────────────────────────────────────────────────────────┐
│                   MONITORING TEMPS RÉEL                           │
└──────────────────────────────────────────────────────────────────┘

Navigation : /admin/monitoring

Dashboard monitoring :
├─ Métriques système (refresh auto 10s) :
│  ├─ CPU : Utilisation %
│  ├─ Mémoire : Utilisée / Totale (%)
│  ├─ Disque : Utilisé / Total (%)
│  └─ Réseau : Trafic entrant/sortant (Mbps)
│
├─ Métriques réseau :
│  ├─ Connexions WiFi actives
│  ├─ Sessions RADIUS en cours
│  ├─ Taux d'authentification (success/min)
│  ├─ Taux d'échecs (failures/min)
│  └─ Bande passante totale consommée
│
└─ Graphiques temps réel :
   ├─ Connexions sur dernière heure (line chart)
   ├─ Bande passante sur dernière heure (area chart)
   └─ Distribution authentifications (success/reject)

Logs temps réel :
├─ Onglet "Logs RADIUS"
│  ├─ Stream live des authentifications
│  ├─ Filtres : Status, Username, IP
│  ├─ Auto-scroll
│  └─ Détails :
│     ├─ Timestamp
│     ├─ Username
│     ├─ Status (Accept/Reject)
│     ├─ MAC address
│     ├─ NAS identifier
│     └─ Raison (si reject)
│
├─ Onglet "Sessions actives"
│  ├─ Liste sessions en cours
│  ├─ Détails par session :
│     ├─ Utilisateur
│     ├─ Durée connexion
│     ├─ Données consommées
│     ├─ Bande passante actuelle
│     └─ Action : Terminer session
│
└─ Onglet "Alertes"
   ├─ Alertes quotas critiques
   ├─ Alertes tentatives connexion échouées
   ├─ Alertes expirations imminentes
   └─ Alertes système (CPU, mémoire)

Actions rapides monitoring :
├─ Terminer session utilisateur
├─ Désactiver utilisateur suspect
├─ Blacklist adresse IP
├─ Recharger config RADIUS
└─ Export logs période

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Visibilité complète sur état système et réseau     │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow Technique

### 1. Architecture Frontend → Backend
```
┌──────────────────────────────────────────────────────────────────┐
│                  FLUX REQUÊTE API COMPLÈTE                        │
└──────────────────────────────────────────────────────────────────┘

1. COMPOSANT VUE (ex: AdminUsersView.vue)
   ↓
   Appel action Pinia Store
   ↓
2. PINIA STORE (ex: user.ts)
   ↓
   store.fetchUsers()
   ↓
3. SERVICE LAYER (ex: user.service.ts)
   ↓
   userService.getUsers(filters)
   ↓
4. API CLIENT (api.ts)
   ↓
   axios.get('/api/core/users/', { params: filters })
   ↓
   [Intercepteur REQUEST]
   ├─ Ajout header Authorization si token exists
   ├─ Ajout withCredentials: true (cookies)
   └─ Logging request (dev mode)
   ↓
5. RÉSEAU HTTP → Backend Django
   ↓
6. DJANGO MIDDLEWARE
   ├─ CORS headers (django-cors-headers)
   ├─ CSRF protection (exempt for API)
   ├─ JWT Authentication (simplejwt)
   └─ Rate limiting (django-ratelimit)
   ↓
7. URL ROUTING (urls.py)
   ↓
   /api/core/users/ → CoreViewSet
   ↓
8. VIEWSET (viewsets.py)
   ↓
   UserViewSet.list(request)
   ↓
   [Permission Check]
   ├─ IsAuthenticated ?
   ├─ IsAdmin ?
   └─ IsOwnerOrAdmin ?
   ↓
9. QUERYSET FILTERING
   ├─ Filtrage par promotion
   ├─ Filtrage par statut
   ├─ Recherche par nom/email
   └─ Pagination (limit/offset)
   ↓
10. QUERYSET EXECUTION
    ↓
    SELECT * FROM core_user WHERE ...
    ↓
11. DATABASE (PostgreSQL/MySQL)
    ↓
    Retour résultats
    ↓
12. SERIALIZER (serializers.py)
    ↓
    UserSerializer(users, many=True)
    ├─ Exclusion champs sensibles (password)
    ├─ Calcul champs computed (effective_profile)
    └─ Format JSON
    ↓
13. RESPONSE DJANGO REST
    {
      "count": 150,
      "next": "?limit=20&offset=20",
      "previous": null,
      "results": [...]
    }
    ↓
14. API CLIENT [Intercepteur RESPONSE]
    ├─ Check status 200-299 → Success
    ├─ Status 401 → Token refresh automatique
    │  ├─ Appel /token/refresh/
    │  ├─ Récupération nouveau access token
    │  └─ Retry request original
    ├─ Status 403 → Redirect /login
    ├─ Status 500 → Notification error
    └─ Extraction response.data
    ↓
15. PINIA STORE
    ├─ Mise à jour state
    ├─ state.users = response.data.results
    ├─ state.loading = false
    └─ Notification success (si nécessaire)
    ↓
16. COMPOSANT VUE
    └─ Réactivité Vue 3 → Mise à jour UI

┌────────────────────────────────────────────────────────────────┐
│ TEMPS TOTAL : ~100-300ms (selon complexité requête)           │
└────────────────────────────────────────────────────────────────┘
```

### 2. Gestion tokens JWT
```
┌──────────────────────────────────────────────────────────────────┐
│                     CYCLE DE VIE JWT                              │
└──────────────────────────────────────────────────────────────────┘

Génération tokens (Login) :
├─ User authentifié → Django
├─ RefreshToken.for_user(user)
│  ├─ Access Token (durée: 60 min)
│  │  ├─ Payload : { user_id, username, role, exp }
│  │  ├─ Signature : HMAC-SHA256 avec SECRET_KEY
│  │  └─ Format : eyJ0eXAi... (JWT standard)
│  │
│  └─ Refresh Token (durée: 24h)
│     ├─ Payload : { user_id, exp, jti }
│     ├─ JTI (JWT ID) unique pour blacklist
│     └─ Signature : HMAC-SHA256
│
├─ Tokens placés dans HttpOnly cookies :
│  ├─ access_token (cookie secure, httpOnly, sameSite)
│  └─ refresh_token (cookie secure, httpOnly, sameSite)
│
└─ Response JSON : { user: {...}, message: "Login success" }

Utilisation Access Token :
├─ Chaque requête API → Cookie access_token envoyé auto
├─ Backend JWT Middleware :
│  ├─ Extraction token du cookie
│  ├─ Vérification signature
│  ├─ Vérification expiration
│  ├─ Extraction user_id du payload
│  └─ Chargement User depuis DB
│
├─ Si valide → request.user = User object
└─ Si invalide/expiré → 401 Unauthorized

Refresh automatique (Intercepteur Axios) :
├─ Response 401 détectée
├─ Vérification : Not a /token/refresh/ call
├─ Appel POST /api/core/auth/token/refresh/
│  ├─ Cookie refresh_token envoyé
│  ├─ Backend valide refresh token
│  ├─ Génération nouveau access token
│  └─ Cookie access_token mis à jour
│
├─ Retry request originale avec nouveau token
└─ Si refresh échoue → Redirect /login

Blacklist (Logout / Rotation) :
├─ User logout → /api/core/auth/logout/
├─ Backend :
│  ├─ Extraction JTI du refresh token
│  ├─ Ajout JTI à blacklist (table ou cache)
│  ├─ Suppression cookies (set expired)
│  └─ Response success
│
└─ Frontend : Clear localStorage + redirect

Token Rotation (Sécurité) :
├─ À chaque refresh, nouveau refresh token généré
├─ Ancien refresh token blacklisté
└─ Limite window rotation : 24h

┌────────────────────────────────────────────────────────────────┐
│ SÉCURITÉ : HttpOnly cookies empêchent XSS, CSRF protection    │
│            via SameSite, signatures empêchent tampering        │
└────────────────────────────────────────────────────────────────┘
```

### 3. Synchronisation RADIUS
```
┌──────────────────────────────────────────────────────────────────┐
│              ACTIVATION RADIUS DÉTAILLÉE                          │
└──────────────────────────────────────────────────────────────────┘

Trigger : Admin clique "Activer WiFi" (promotion ou user)
   ↓
Frontend :
├─ Appel API POST /promotions/{id}/activate/
└─ Payload : { user_ids: [...] } (optionnel)

Backend ViewSet :
@action(methods=['post'], detail=True)
def activate(self, request, pk=None):
    promotion = self.get_object()

    # Validation
    if not promotion.profile:
        return error("Aucun profil assigné")

    users = promotion.users.filter(is_active=True)

    with transaction.atomic():  # IMPORTANT : Transaction
        success_count = 0
        failed_users = []

        for user in users:
            try:
                # 1. Créer/Mettre à jour radcheck
                RadCheck.objects.update_or_create(
                    username=user.username,
                    defaults={
                        'attribute': 'Cleartext-Password',
                        'op': ':=',
                        'value': user.cleartext_password
                    }
                )

                # 2. Créer attributs radreply
                profile = promotion.profile

                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Session-Timeout',
                    defaults={'value': str(profile.session_timeout)}
                )

                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Idle-Timeout',
                    defaults={'value': str(profile.idle_timeout)}
                )

                # Bande passante (format Mikrotik)
                rate_limit = f"{profile.upload_bandwidth_kbps}k/{profile.download_bandwidth_kbps}k"
                RadReply.objects.update_or_create(
                    username=user.username,
                    attribute='Mikrotik-Rate-Limit',
                    defaults={'value': rate_limit}
                )

                # Quota (si limité)
                if profile.quota_type == 'limited':
                    RadReply.objects.update_or_create(
                        username=user.username,
                        attribute='Max-Daily-Session',
                        defaults={'value': str(profile.daily_data_limit_gb * 1024)}  # MB
                    )

                # 3. Créer mapping groupe
                RadUserGroup.objects.update_or_create(
                    username=user.username,
                    defaults={
                        'groupname': promotion.name,
                        'priority': 1
                    }
                )

                # 4. Créer UserProfileUsage si pas existe
                UserProfileUsage.objects.get_or_create(
                    user=user,
                    defaults={
                        'activation_date': timezone.now(),
                        'last_reset_daily': timezone.now(),
                        'last_reset_weekly': timezone.now(),
                        'last_reset_monthly': timezone.now()
                    }
                )

                # 5. Mettre à jour statut User
                user.is_radius_activated = True
                user.is_radius_enabled = True
                user.save()

                success_count += 1

            except Exception as e:
                failed_users.append({
                    'username': user.username,
                    'error': str(e)
                })
                # Continue pour tenter autres users

        # Si trop d'échecs, rollback complet
        if len(failed_users) > len(users) * 0.5:  # >50% échecs
            raise Exception("Trop d'échecs, rollback")

    return Response({
        'success': True,
        'users_enabled': success_count,
        'users_failed': len(failed_users),
        'errors': failed_users
    })

Résultat dans base RADIUS :
┌────────────────────────────────────────────────────────────────┐
│ Table : radcheck                                               │
├────────────────┬───────────────────────┬────┬─────────────────┤
│ username       │ attribute             │ op │ value           │
├────────────────┼───────────────────────┼────┼─────────────────┤
│ STU2024001     │ Cleartext-Password    │ := │ P@ssw0rd123     │
└────────────────┴───────────────────────┴────┴─────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Table : radreply                                               │
├────────────────┬───────────────────────┬────┬─────────────────┤
│ username       │ attribute             │ op │ value           │
├────────────────┼───────────────────────┼────┼─────────────────┤
│ STU2024001     │ Session-Timeout       │ := │ 3600            │
│ STU2024001     │ Idle-Timeout          │ := │ 600             │
│ STU2024001     │ Mikrotik-Rate-Limit   │ := │ 2048k/10240k    │
│ STU2024001     │ Max-Daily-Session     │ := │ 2048            │
└────────────────┴───────────────────────┴────┴─────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ Table : radusergroup                                           │
├────────────────┬───────────────────────┬──────────────────────┤
│ username       │ groupname             │ priority             │
├────────────────┼───────────────────────┼──────────────────────┤
│ STU2024001     │ L3 Informatique 2024  │ 1                    │
└────────────────┴───────────────────────┴──────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur peut maintenant s'authentifier WiFi    │
│            FreeRADIUS appliquera automatiquement les attributs │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow des Données

### 1. Tracking consommation quotas
```
┌──────────────────────────────────────────────────────────────────┐
│              TRACKING CONSOMMATION EN TEMPS RÉEL                  │
└──────────────────────────────────────────────────────────────────┘

Flux données session active :

1. User connecté WiFi → Session RADIUS active

2. RADIUS Accounting Interim-Update (toutes les 5 min) :
   ↓
   Mikrotik/NAS envoie :
   ├─ Acct-Input-Octets (bytes reçus)
   ├─ Acct-Output-Octets (bytes envoyés)
   ├─ Acct-Session-Time (durée session)
   └─ Acct-Session-Id (identifiant unique)
   ↓
3. FreeRADIUS traite Accounting packet :
   ↓
   INSERT/UPDATE dans radacct table :
   ├─ acctsessionid
   ├─ username
   ├─ acctinputoctets
   ├─ acctoutputoctets
   ├─ acctsessiontime
   └─ acctupdatetime = NOW()
   ↓
4. Django Signal (post_save sur RadiusAccounting) :
   ↓
   @receiver(post_save, sender=RadiusAccounting)
   def update_user_quota(sender, instance, **kwargs):
       if instance.acctstoptime:  # Session terminée
           user = instance.username.user
           usage = user.userprofileusage

           # Calcul bytes total
           bytes_total = (
               instance.acctinputoctets +
               instance.acctoutputoctets +
               (instance.acctinputgigawords or 0) * 2**32 +
               (instance.acctoutputgigawords or 0) * 2**32
           )

           # Mise à jour compteurs
           usage.used_today += bytes_total
           usage.used_week += bytes_total
           usage.used_month += bytes_total
           usage.used_total += bytes_total
           usage.save()

           # Vérification alertes
           check_quota_alerts(user, usage)
   ↓
5. Mise à jour Session dans portail :
   ↓
   Session.objects.filter(session_id=instance.acctsessionid).update(
       bytes_in=instance.acctinputoctets,
       bytes_out=instance.acctoutputoctets,
       session_time=instance.acctsessiontime
   )
   ↓
6. Frontend (polling toutes les 30s ou WebSocket) :
   ↓
   GET /api/core/profile-usage/me/
   ↓
   Response :
   {
     "used_today": 524288000,  // 500 MB
     "used_week": 2147483648,  // 2 GB
     "used_month": 5368709120, // 5 GB
     "daily_limit": 2147483648, // 2 GB
     "today_percentage": 25,
     "week_percentage": 40,
     "month_percentage": 50,
     "expires_in_days": 22
   }
   ↓
7. UI Update :
   ├─ Graphiques circulaires mis à jour
   ├─ Barres de progression
   └─ Alertes si > 80%

┌────────────────────────────────────────────────────────────────┐
│ TEMPS RÉEL : Mise à jour automatique toutes les 5 minutes     │
│              via RADIUS Accounting Interim-Update              │
└────────────────────────────────────────────────────────────────┘
```

### 2. Réinitialisation automatique quotas
```
┌──────────────────────────────────────────────────────────────────┐
│            RÉINITIALISATION AUTOMATIQUE QUOTAS                    │
└──────────────────────────────────────────────────────────────────┘

Configuration : Tâches Cron Django Management Commands

1. Quota journalier (chaque jour à 00:00) :
   ↓
   Cron : 0 0 * * * python manage.py reset_daily_quotas
   ↓
   Command reset_daily_quotas.py :

   def handle(self):
       now = timezone.now()
       usages = UserProfileUsage.objects.filter(
           user__is_active=True,
           user__is_radius_enabled=True
       )

       for usage in usages:
           # Vérification : Dernier reset > 24h
           if (now - usage.last_reset_daily).days >= 1:
               usage.used_today = 0
               usage.last_reset_daily = now
               usage.save()

               logger.info(f"Reset daily quota for {usage.user.username}")

   ↓
   Logs : "Reset daily quotas for 1,250 users"

2. Quota hebdomadaire (chaque lundi à 00:00) :
   ↓
   Cron : 0 0 * * 1 python manage.py reset_weekly_quotas
   ↓
   Command reset_weekly_quotas.py :

   def handle(self):
       now = timezone.now()
       usages = UserProfileUsage.objects.filter(...)

       for usage in usages:
           if (now - usage.last_reset_weekly).days >= 7:
               usage.used_week = 0
               usage.last_reset_weekly = now
               usage.save()

3. Quota mensuel (1er jour du mois à 00:00) :
   ↓
   Cron : 0 0 1 * * python manage.py reset_monthly_quotas
   ↓
   Command reset_monthly_quotas.py :

   def handle(self):
       now = timezone.now()
       usages = UserProfileUsage.objects.filter(...)

       for usage in usages:
           # Vérification : Différent mois
           if usage.last_reset_monthly.month != now.month:
               usage.used_month = 0
               usage.last_reset_monthly = now
               usage.save()

4. Vérification alertes (toutes les heures) :
   ↓
   Cron : 0 * * * * python manage.py check_profile_alerts
   ↓
   Command check_profile_alerts.py :

   def handle(self):
       alerts = ProfileAlert.objects.filter(is_active=True)

       for alert in alerts:
           users = get_users_for_alert(alert)

           for user in users:
               usage = user.userprofileusage

               # Alerte quota
               if alert.alert_type == 'quota_warning':
                   if usage.today_percentage >= alert.threshold:
                       send_notification(user, alert)

               # Alerte expiration
               elif alert.alert_type == 'expiry_warning':
                   days_remaining = usage.days_remaining()
                   if days_remaining <= alert.threshold:
                       send_notification(user, alert)

┌────────────────────────────────────────────────────────────────┐
│ AUTOMATISATION : 4 tâches cron pour gestion quotas complète   │
└────────────────────────────────────────────────────────────────┘
```

---

## Workflow d'Intégration

### 1. FreeRADIUS → Django
```
┌──────────────────────────────────────────────────────────────────┐
│                 INTÉGRATION FREERADIUS                            │
└──────────────────────────────────────────────────────────────────┘

Configuration FreeRADIUS (radiusd.conf) :

sql {
    driver = "rlm_sql_postgresql"  # ou mysql
    server = "localhost"
    port = 5432
    login = "radius_user"
    password = "radius_password"
    radius_db = "captive_portal_db"

    # Requête autorisation
    authorize_check_query = "
        SELECT attribute, value, op
        FROM radcheck
        WHERE username = '%{SQL-User-Name}'
        ORDER BY id
    "

    # Requête réponse
    authorize_reply_query = "
        SELECT attribute, value, op
        FROM radreply
        WHERE username = '%{SQL-User-Name}'
        ORDER BY id
    "

    # Requête groupe
    authorize_group_check_query = "
        SELECT groupname
        FROM radusergroup
        WHERE username = '%{SQL-User-Name}'
        ORDER BY priority
    "

    # Accounting
    accounting_start_query = "
        INSERT INTO radacct (...) VALUES (...)
    "

    accounting_stop_query = "
        UPDATE radacct
        SET acctstoptime = NOW(), ...
        WHERE acctsessionid = '%{Acct-Session-Id}'
    "
}

Flux authentification WiFi :

1. User entre credentials (matricule + password)
   ↓
2. NAS (Mikrotik/Routeur) envoie Access-Request :
   ↓
   Packet RADIUS :
   ├─ User-Name = "STU2024001"
   ├─ User-Password = "encrypted_password"
   ├─ NAS-IP-Address = "192.168.1.1"
   ├─ NAS-Port = 1
   └─ Calling-Station-Id = "AA:BB:CC:DD:EE:FF"  (MAC)
   ↓
3. FreeRADIUS reçoit Access-Request
   ↓
4. Module SQL exécute authorize_check_query :
   ↓
   SELECT * FROM radcheck
   WHERE username = 'STU2024001'
   ↓
   Résultat : Cleartext-Password = "P@ssw0rd123"
   ↓
5. Vérification password :
   ├─ Comparaison password reçu vs DB
   └─ Si match → Continue
   ↓
6. Module SQL exécute authorize_reply_query :
   ↓
   SELECT * FROM radreply
   WHERE username = 'STU2024001'
   ↓
   Résultat :
   ├─ Session-Timeout = 3600
   ├─ Idle-Timeout = 600
   ├─ Mikrotik-Rate-Limit = "2048k/10240k"
   └─ Class = "L3 Informatique 2024"
   ↓
7. FreeRADIUS construit Access-Accept :
   ↓
   Packet RADIUS Reply :
   ├─ Reply-Message = "Authentication successful"
   ├─ Session-Timeout = 3600
   ├─ Idle-Timeout = 600
   ├─ Mikrotik-Rate-Limit = "2048k/10240k"
   └─ Class = "L3 Informatique 2024"
   ↓
8. NAS applique attributs :
   ├─ Configure rate limit 2/10 Mbps
   ├─ Démarre timer session (3600s)
   ├─ Démarre timer idle (600s)
   └─ Autorise connexion
   ↓
9. Logging dans Django :
   ↓
   RadiusAuthLog.objects.create(
       username=user,
       status='accept',
       mac_address='AA:BB:CC:DD:EE:FF',
       ip_address='192.168.10.50',
       nas_identifier='Mikrotik-Main',
       timestamp=timezone.now()
   )

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Utilisateur authentifié avec quotas appliqués      │
└────────────────────────────────────────────────────────────────┘
```

### 2. Mikrotik → Django (API RouterOS)
```
┌──────────────────────────────────────────────────────────────────┐
│                 INTÉGRATION MIKROTIK ROUTEROS                     │
└──────────────────────────────────────────────────────────────────┘

Configuration Mikrotik :
├─ API RouterOS activée (port 8728)
├─ User API créé avec droits
└─ SSL optionnel (port 8729)

Connexion depuis Django :

from routeros_api import RouterOsApiPool

def connect_mikrotik(router):
    connection = RouterOsApiPool(
        host=router.host,
        username=router.username,
        password=router.password,
        port=router.port,
        use_ssl=router.use_ssl,
        ssl_verify=False,
        plaintext_login=True
    )
    return connection.get_api()

Opérations disponibles :

1. Création Hotspot User :
   ↓
   def create_hotspot_user(router, user, profile):
       api = connect_mikrotik(router)
       hotspot = api.get_resource('/ip/hotspot/user')

       hotspot.add(
           name=user.username,
           password=user.cleartext_password,
           profile='default',
           limit_uptime=f"{profile.session_timeout}s",
           limit_bytes_total=f"{profile.data_volume_bytes}",
           disabled='no',
           comment=f"User {user.get_full_name()}"
       )

2. Récupération connexions actives :
   ↓
   def get_active_connections(router):
       api = connect_mikrotik(router)
       active = api.get_resource('/ip/hotspot/active')

       connections = active.get()

       for conn in connections:
           MikrotikActiveConnection.objects.update_or_create(
               session_id=conn['id'],
               defaults={
                   'router': router,
                   'username': conn['user'],
                   'mac_address': conn['mac-address'],
                   'ip_address': conn['address'],
                   'uptime': conn['uptime'],
                   'bytes_in': conn['bytes-in'],
                   'bytes_out': conn['bytes-out'],
                   'login_time': parse_mikrotik_time(conn['login-by'])
               }
           )

3. Suppression user (désactivation) :
   ↓
   def delete_hotspot_user(router, username):
       api = connect_mikrotik(router)
       hotspot = api.get_resource('/ip/hotspot/user')

       users = hotspot.get(name=username)
       if users:
           hotspot.remove(id=users[0]['id'])

4. Mise à jour rate limit en temps réel :
   ↓
   def update_rate_limit(router, username, upload_kbps, download_kbps):
       api = connect_mikrotik(router)
       active = api.get_resource('/ip/hotspot/active')

       connections = active.get(user=username)
       for conn in connections:
           active.set(
               id=conn['id'],
               rate_limit=f"{upload_kbps}k/{download_kbps}k"
           )

Synchronisation automatique (tâche cron) :
├─ Toutes les 5 minutes : Sync connexions actives
├─ Toutes les heures : Sync users hotspot
└─ À la demande : Activation/Désactivation individuelle

┌────────────────────────────────────────────────────────────────┐
│ RÉSULTAT : Gestion complète hotspot Mikrotik via API          │
└────────────────────────────────────────────────────────────────┘
```

---

## Résumé des Workflows

### Workflows Principaux
1. **Inscription → Activation → Connexion WiFi** (Utilisateur)
2. **Création Profil → Assignation Promotion → Activation RADIUS** (Admin)
3. **Connexion WiFi → Accounting → Mise à jour quotas** (Système)
4. **Monitoring temps réel → Alertes → Actions** (Admin)

### Intégrations Critiques
- **FreeRADIUS** : Authentification WiFi + Accounting
- **Mikrotik RouterOS** : Hotspot management + Rate limiting
- **Django ORM** : Gestion données centralisée
- **Vue 3 + Pinia** : Interface utilisateur réactive

### Automatisations
- Réinitialisation quotas (daily/weekly/monthly)
- Vérification alertes (hourly)
- Synchronisation connexions actives
- Logging RADIUS temps réel

---

**Date de création** : 11 décembre 2025
**Version** : 1.0
**Statut** : Production-ready
