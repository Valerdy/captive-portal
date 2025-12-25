# Guide d'Administration - Portail Captif

Ce guide détaille toutes les fonctionnalités disponibles dans l'interface d'administration Django.

## Table des matières

1. [Accès à l'administration](#accès-à-ladministration)
2. [Gestion des utilisateurs](#gestion-des-utilisateurs)
3. [Gestion des profils réseau](#gestion-des-profils-réseau)
4. [Gestion des promotions](#gestion-des-promotions)
5. [Gestion des appareils](#gestion-des-appareils)
6. [Gestion des sessions](#gestion-des-sessions)
7. [Gestion des vouchers](#gestion-des-vouchers)
8. [Suivi de consommation](#suivi-de-consommation)
9. [Alertes de profil](#alertes-de-profil)
10. [Sites bloqués (DNS)](#sites-bloqués-dns)
11. [Configuration MikroTik](#configuration-mikrotik)
12. [Configuration RADIUS](#configuration-radius)

---

## Accès à l'administration

### URL d'accès
```
https://votre-domaine.com/admin/
```

### Connexion
1. Entrez votre nom d'utilisateur administrateur
2. Entrez votre mot de passe
3. Cliquez sur "Se connecter"

> **Note**: Seuls les utilisateurs avec `is_staff=True` peuvent accéder à l'admin.

---

## Gestion des utilisateurs

**Chemin**: `Core > Users`

### Liste des utilisateurs

La liste affiche:
- Nom d'utilisateur, email, prénom, nom
- Promotion et profil assignés
- Numéro de téléphone et adresse MAC
- Statut (actif, voucher user)

### Filtres disponibles
- Par statut actif/inactif
- Par statut staff
- Par utilisateur voucher
- Par date d'inscription
- Par promotion
- Par profil

### Recherche
Recherchez par: nom d'utilisateur, email, téléphone, adresse MAC, nom de promotion, nom de profil

### Créer un utilisateur

1. Cliquez sur **"Ajouter User"**
2. Remplissez les champs obligatoires:
   - Nom d'utilisateur
   - Mot de passe (2 fois)
3. Remplissez les informations du portail captif:
   - **Promotion**: Groupe de l'utilisateur (ex: L1 Info, M2 Réseaux)
   - **Profil**: Profil de bande passante/quota (optionnel si promotion a un profil)
   - **Matricule**: Identifiant unique étudiant/employé
   - **Téléphone**: Numéro de contact
   - **Adresse MAC**: MAC de l'appareil principal
   - **Est utilisateur voucher**: Cochez si l'utilisateur utilise un voucher
4. Cliquez sur **"Enregistrer"**

### Modifier un utilisateur

1. Cliquez sur le nom d'utilisateur dans la liste
2. Modifiez les champs souhaités
3. Section **"RADIUS Status"** (cliquez pour déplier):
   - **is_radius_activated**: L'utilisateur est-il activé dans RADIUS?
   - **is_radius_enabled**: RADIUS est-il activé pour cet utilisateur?
   - **cleartext_password**: Mot de passe en clair (utilisé pour radcheck)
4. Cliquez sur **"Enregistrer"**

### Actions en masse
- Sélectionnez plusieurs utilisateurs avec les cases à cocher
- Choisissez une action dans le menu déroulant
- Cliquez sur **"Exécuter"**

---

## Gestion des profils réseau

**Chemin**: `Core > Profiles`

### Qu'est-ce qu'un profil?

Un profil définit les paramètres de connexion d'un utilisateur:
- Bande passante (upload/download)
- Quota de données
- Limites périodiques (journalière, hebdomadaire, mensuelle)
- Paramètres de session RADIUS

### Liste des profils

Affiche:
- Nom du profil
- Type de quota (unlimited, daily, monthly, total)
- Volume de données en Go
- Bande passante UP/DOWN en Mbps
- Durée de validité
- Statut actif

### Créer un profil

1. Cliquez sur **"Ajouter Profile"**
2. **Informations de base**:
   - **Nom**: Nom descriptif (ex: "Étudiant Standard", "Premium")
   - **Description**: Détails du profil
   - **Actif**: Cochez pour activer
   - **Créé par**: Administrateur créateur

3. **Bande passante**:
   - **Bandwidth upload**: Vitesse montante en Mbps (1-1000)
   - **Bandwidth download**: Vitesse descendante en Mbps (1-1000)

   > Exemple: Upload 5 Mbps, Download 10 Mbps

4. **Quota de données**:
   - **Type de quota**:
     - `unlimited`: Pas de limite
     - `daily`: Quota journalier
     - `monthly`: Quota mensuel
     - `total`: Quota total sur la durée
   - **Volume de données**: En octets (1 Go = 1073741824 octets)
   - **Durée de validité**: En jours

5. **Limites périodiques** (optionnel, cliquez pour déplier):
   - **Limite journalière**: Max par jour
   - **Limite hebdomadaire**: Max par semaine
   - **Limite mensuelle**: Max par mois

6. **Paramètres RADIUS** (optionnel, cliquez pour déplier):
   - **Session timeout**: Durée max de session en secondes
   - **Idle timeout**: Déconnexion après inactivité (secondes)
   - **Simultaneous use**: Nombre de connexions simultanées autorisées

7. Cliquez sur **"Enregistrer"**

### Exemples de configuration

| Profil | Upload | Download | Quota | Validité |
|--------|--------|----------|-------|----------|
| Étudiant Basic | 2 Mbps | 5 Mbps | 10 Go/mois | 365 jours |
| Étudiant Premium | 5 Mbps | 20 Mbps | 50 Go/mois | 365 jours |
| Staff | 10 Mbps | 50 Mbps | Illimité | Illimité |
| Invité | 1 Mbps | 2 Mbps | 1 Go/jour | 1 jour |

---

## Gestion des promotions

**Chemin**: `Core > Promotions`

### Qu'est-ce qu'une promotion?

Une promotion est un groupe d'utilisateurs partageant le même profil réseau. Exemples:
- L1 Informatique
- M2 Réseaux
- Personnel administratif
- Invités conférence

### Liste des promotions

Affiche: Nom, profil associé, statut actif, dates de création/modification

### Créer une promotion

1. Cliquez sur **"Ajouter Promotion"**
2. Remplissez:
   - **Nom**: Nom de la promotion (ex: "L3 Informatique 2024")
   - **Profil**: Profil réseau à appliquer aux membres
   - **Actif**: Cochez pour activer
3. Cliquez sur **"Enregistrer"**

### Utilisation

Quand un utilisateur est assigné à une promotion:
- Il hérite automatiquement du profil de la promotion
- Sauf s'il a un profil personnel (prioritaire)

---

## Gestion des appareils

**Chemin**: `Core > Devices`

### Liste des appareils

Affiche:
- Adresse MAC
- Utilisateur propriétaire
- Adresse IP
- Type d'appareil (desktop, laptop, mobile, tablet, other)
- Statut actif
- Première et dernière connexion

### Filtres
- Par statut actif
- Par type d'appareil
- Par date de première connexion

### Créer/Modifier un appareil

Champs disponibles:
- **Utilisateur**: Propriétaire de l'appareil
- **Adresse MAC**: Identifiant unique de l'appareil
- **Adresse IP**: Dernière IP utilisée
- **Hostname**: Nom réseau de l'appareil
- **Type d'appareil**: desktop, laptop, mobile, tablet, other
- **Actif**: Autoriser cet appareil à se connecter

---

## Gestion des sessions

**Chemin**: `Core > Sessions`

### Liste des sessions

Affiche:
- ID de session
- Utilisateur
- Adresse IP et MAC
- Statut (active, expired, terminated)
- Heure de début
- Données totales transférées

### Filtres
- Par statut
- Par date de début

### Détails d'une session

En cliquant sur une session:

1. **Session Info**: Utilisateur, appareil, ID, IP, MAC, statut
2. **Timing**: Début, fin, durée timeout, expiré?
3. **Data Usage**: Octets/paquets entrants et sortants

> **Note**: Les sessions sont en lecture seule car elles sont gérées automatiquement par le système.

---

## Gestion des vouchers

**Chemin**: `Core > Vouchers`

### Qu'est-ce qu'un voucher?

Un voucher est un code d'accès temporaire permettant à un utilisateur de se connecter au réseau.

### Liste des vouchers

Affiche:
- Code du voucher
- Statut (active, used, expired, revoked)
- Durée de validité
- Nombre max d'appareils
- Utilisations
- Dates de validité
- Créateur
- Validité actuelle

### Créer un voucher

1. Cliquez sur **"Ajouter Voucher"**
2. **Voucher Info**:
   - **Code**: Code unique (généré automatiquement ou personnalisé)
   - **Statut**: active, used, expired, revoked
   - **Durée**: Durée de validité en minutes
   - **Max appareils**: Nombre d'appareils pouvant utiliser ce code
   - **Utilisations**: Compteur d'utilisation
3. **Validity**:
   - **Valide à partir de**: Date/heure de début
   - **Valide jusqu'à**: Date/heure de fin
4. **Metadata**:
   - **Créé par**: Administrateur créateur
   - **Notes**: Commentaires internes
5. Cliquez sur **"Enregistrer"**

### Cas d'utilisation

| Scénario | Durée | Max appareils | Validité |
|----------|-------|---------------|----------|
| Invité journée | 480 min | 1 | 1 jour |
| Conférence | 180 min | 50 | Durée événement |
| Étudiant semaine | 10080 min | 3 | 7 jours |

---

## Suivi de consommation

**Chemin**: `Core > User profile usages`

### Liste des consommations

Affiche:
- Utilisateur
- Profil effectif
- Consommation totale en Go
- Consommation du jour (avec %)
- Quota dépassé?
- Expiré?
- Actif?

### Détails de consommation

1. **Utilisateur**: Lien vers l'utilisateur, statut actif, date d'activation
2. **Consommation (octets)**: Valeurs brutes modifiables
   - Aujourd'hui, semaine, mois, total
3. **Consommation (Go)**: Valeurs calculées (lecture seule)
4. **Pourcentages**: % d'utilisation par période
5. **Dates de reset**: Derniers resets journalier/hebdo/mensuel
6. **Statut**: Quota dépassé ou non

### Réinitialiser la consommation

Pour remettre à zéro la consommation d'un utilisateur:
1. Ouvrez la fiche de consommation
2. Mettez les champs `used_today`, `used_week`, `used_month`, `used_total` à 0
3. Cliquez sur **"Enregistrer"**

---

## Alertes de profil

**Chemin**: `Core > Profile alerts`

### Qu'est-ce qu'une alerte?

Une alerte notifie automatiquement quand un seuil est atteint:
- Quota de données à X%
- Expiration dans X jours

### Types d'alertes

| Type | Description |
|------|-------------|
| `quota_warning` | Avertissement quota (ex: 80%) |
| `quota_exceeded` | Quota dépassé (100%) |
| `expiry_warning` | Expiration proche |
| `expiry_critical` | Expiration imminente |

### Méthodes de notification

| Méthode | Description |
|---------|-------------|
| `email` | Notification par email |
| `sms` | Notification par SMS |
| `push` | Notification push |
| `system` | Notification système interne |
| `all` | Tous les canaux |

### Créer une alerte

1. Cliquez sur **"Ajouter Profile alert"**
2. **Profil et type**:
   - **Profil**: Profil concerné
   - **Type d'alerte**: Sélectionnez le type
   - **Actif**: Cochez pour activer
3. **Seuils**:
   - **Threshold percent**: Seuil en % (0-100) pour alertes quota
   - **Threshold days**: Jours avant expiration pour alertes expiry
4. **Notification**:
   - **Méthode**: Canal de notification
   - **Template**: Message personnalisé avec variables:
     - `{username}`: Nom d'utilisateur
     - `{percent}`: Pourcentage utilisé
     - `{remaining_gb}`: Go restants
     - `{days_remaining}`: Jours restants
5. Cliquez sur **"Enregistrer"**

### Exemple de template

```
Bonjour {username},

Vous avez consommé {percent}% de votre quota mensuel.
Il vous reste {remaining_gb} Go.

Cordialement,
L'équipe réseau
```

---

## Sites bloqués (DNS)

**Chemin**: `Core > Blocked sites`

### Fonctionnement

Le blocage DNS fonctionne via MikroTik:
1. Vous ajoutez un domaine à bloquer dans l'admin
2. Le système crée une entrée DNS statique sur MikroTik
3. Le domaine redirige vers 0.0.0.0 (inaccessible)

### Liste des sites bloqués

Affiche:
- Domaine
- Catégorie (social, gaming, streaming, adult, gambling, other)
- Type (domain, subdomain, keyword)
- Actif?
- Statut sync MikroTik (✓ synced, ⏳ pending, ✗ error)
- Portée (Global, Profil, Promotion)
- Date d'ajout

### Indicateurs de synchronisation

| Icône | Statut | Description |
|-------|--------|-------------|
| ✓ Vert | synced | Synchronisé avec MikroTik |
| ⏳ Jaune | pending | En attente de synchronisation |
| ✗ Rouge | error | Erreur de synchronisation |

### Ajouter un site à bloquer

1. Cliquez sur **"Ajouter Blocked site"**
2. **Domaine à bloquer**:
   - **Domaine**: Ex: `facebook.com` ou `*.tiktok.com` (avec sous-domaines)
   - **Catégorie**: Classification du site
   - **Type**:
     - `domain`: Domaine exact
     - `subdomain`: Inclut sous-domaines
     - `keyword`: Mot-clé dans l'URL
   - **Actif**: Cochez pour bloquer immédiatement
3. **Ciblage** (optionnel, cliquez pour déplier):
   - **Profil**: Bloquer uniquement pour ce profil
   - **Promotion**: Bloquer uniquement pour cette promotion
   - Laissez vide pour un blocage global
4. **Informations**:
   - **Raison**: Pourquoi ce site est bloqué
   - **Ajouté par**: Administrateur (auto-rempli)
5. Cliquez sur **"Enregistrer"**

> La synchronisation avec MikroTik s'effectue automatiquement.

### Actions en masse

Sélectionnez plusieurs sites puis:

| Action | Description |
|--------|-------------|
| 🔄 Synchroniser avec MikroTik | Envoie les entrées vers MikroTik |
| 🔃 Forcer la resynchronisation | Supprime et recrée les entrées |
| ✓ Activer | Active les sites sélectionnés |
| ✗ Désactiver | Désactive et retire de MikroTik |

### Dépannage

**Site en statut "error":**
1. Cliquez sur le site pour voir l'erreur
2. Vérifiez la connexion au routeur MikroTik
3. Utilisez l'action "Forcer la resynchronisation"

**Site en statut "pending":**
1. Utilisez l'action "Synchroniser avec MikroTik"
2. Vérifiez les logs MikroTik dans l'admin

---

## Configuration MikroTik

**Chemin**: `Mikrotik`

### Routeurs (Mikrotik routers)

#### Liste
Affiche: Nom, hôte, port, utilisateur, actif, date de création

#### Ajouter un routeur

1. **Router Info**:
   - **Nom**: Nom descriptif
   - **Hôte**: IP ou hostname du routeur
   - **Port**: Port API (par défaut: 8728, SSL: 8729)
   - **Username**: Utilisateur API MikroTik
   - **Mot de passe**: ✓ indique si configuré
2. **Modifier le mot de passe** (cliquez pour déplier):
   - Entrez le nouveau mot de passe API
3. **Settings**:
   - **Use SSL**: Connexion sécurisée
   - **Actif**: Routeur actif
   - **Description**: Notes

> **Sécurité**: Le mot de passe n'est jamais affiché, seul son statut est visible.

### Utilisateurs Hotspot (Mikrotik hotspot users)

Gestion des utilisateurs hotspot synchronisés avec MikroTik.

### Connexions actives (Mikrotik active connections)

Vue en temps réel des connexions actives sur le hotspot.

### Logs MikroTik (Mikrotik logs)

Historique des opérations effectuées sur les routeurs.

---

## Configuration RADIUS

**Chemin**: `Radius`

### Serveurs RADIUS (Radius servers)

#### Ajouter un serveur

1. **Server Info**:
   - **Nom**: Nom du serveur
   - **Hôte**: IP ou hostname
   - **Auth port**: Port authentification (1812)
   - **Acct port**: Port accounting (1813)
   - **Secret**: ✓ indique si configuré
2. **Modifier le secret** (cliquez pour déplier):
   - Entrez le nouveau secret RADIUS
3. **Settings**:
   - **Actif**: Serveur actif
   - **Timeout**: Délai en secondes
   - **Retries**: Nombre de tentatives

### Clients RADIUS (Radius clients)

NAS (Network Access Servers) autorisés à communiquer avec RADIUS.

#### Ajouter un client

1. **Client Info**:
   - **Nom**: Nom complet
   - **Shortname**: Nom court
   - **NAS type**: Type de NAS (cisco, mikrotik, other)
   - **IP address**: Adresse IP du NAS
   - **Secret**: ✓ indique si configuré
2. **Modifier le secret** (cliquez pour déplier)
3. **Additional Info**: Description, actif

### Logs d'authentification (Radius auth logs)

Historique de toutes les tentatives d'authentification:
- Utilisateur
- Serveur
- Statut (accept, reject, challenge)
- Adresses IP/MAC
- NAS

### Accounting (Radius accountings)

Données de comptabilité des sessions:
- ID session
- Utilisateur
- Type (start, interim-update, stop)
- Durée de session
- Données transférées
- Cause de terminaison

---

## Bonnes pratiques

### Sécurité

1. **Mots de passe**: Ne partagez jamais les accès admin
2. **Secrets**: Utilisez des secrets RADIUS forts (min 16 caractères)
3. **Audit**: Consultez régulièrement les logs d'authentification

### Performance

1. **Profils**: Créez des profils adaptés à chaque type d'utilisateur
2. **Quotas**: Définissez des quotas réalistes pour éviter la saturation
3. **Alertes**: Configurez des alertes à 80% pour anticiper les dépassements

### Maintenance

1. **Vouchers**: Révoquez les vouchers expirés régulièrement
2. **Sessions**: Les sessions expirées sont nettoyées automatiquement
3. **Sync DNS**: Vérifiez le statut de synchronisation des sites bloqués

---

## Raccourcis utiles

| Action | Raccourci |
|--------|-----------|
| Rechercher dans la liste | Tapez dans le champ de recherche |
| Filtrer | Utilisez les filtres à droite |
| Sélectionner tout | Case à cocher en haut de la liste |
| Action en masse | Menu déroulant "Action" |
| Revenir à la liste | Lien "Voir le site" en haut |

---

## Support

En cas de problème:
1. Consultez les logs dans l'admin
2. Vérifiez la connectivité réseau vers MikroTik/RADIUS
3. Contactez l'équipe technique
