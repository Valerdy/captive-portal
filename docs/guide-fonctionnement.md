# Guide de Fonctionnement du Portail Captif

## Introduction

Ce document explique de manière simple comment fonctionne le système de portail captif. Il est destiné à toute personne souhaitant comprendre le fonctionnement du système, même sans connaissances techniques.

---

## Qu'est-ce qu'un Portail Captif ?

Un **portail captif** est un système qui contrôle l'accès à Internet via WiFi. Quand vous vous connectez au réseau WiFi d'une école ou d'une entreprise, vous devez d'abord vous identifier avant de pouvoir naviguer sur Internet.

Notre système permet de :
- Identifier chaque utilisateur
- Limiter la vitesse de connexion (bande passante)
- Limiter la quantité de données utilisées (quota)
- Bloquer certains sites web

---

## Les Éléments Principaux

### 1. Les Utilisateurs

Chaque personne qui souhaite utiliser le WiFi doit avoir un **compte utilisateur**.

**Informations d'un utilisateur :**
- Nom d'utilisateur et mot de passe
- Matricule (numéro étudiant par exemple)
- Téléphone et email
- Sa promotion (groupe) ou son profil individuel

**États possibles :**
| État | Signification |
|------|---------------|
| Compte créé | L'utilisateur existe mais n'a pas encore accès au WiFi |
| Activé dans RADIUS | L'utilisateur peut se connecter au WiFi |
| Désactivé | L'accès WiFi est temporairement suspendu |

---

### 2. Les Profils

Un **profil** définit les règles d'utilisation du WiFi.

**Ce que définit un profil :**

| Paramètre | Description | Exemple |
|-----------|-------------|---------|
| Bande passante | Vitesse de téléchargement/envoi | 10 Mbps en téléchargement, 5 Mbps en envoi |
| Quota de données | Quantité maximale de données | 50 Go par mois |
| Durée de validité | Combien de temps le quota est valable | 30 jours |
| Timeout de session | Durée maximale d'une connexion | 8 heures |
| Timeout d'inactivité | Déconnexion si inactif | 10 minutes |
| Connexions simultanées | Nombre d'appareils en même temps | 1 appareil |

**Exemples de profils :**
- **Étudiant** : 10 Mbps, 50 Go/mois, 1 appareil
- **Personnel** : 20 Mbps, illimité, 3 appareils
- **Invité** : 5 Mbps, 5 Go/semaine, 1 appareil

---

### 3. Les Promotions

Une **promotion** est un groupe d'utilisateurs (exemple : "Licence 3 Informatique 2024").

**Avantages des promotions :**
- Tous les membres d'une promotion partagent le même profil
- Modification du profil d'une promotion = tous les membres sont mis à jour automatiquement
- Facilite la gestion de groupes d'étudiants

**Hiérarchie des profils :**
```
Utilisateur a un profil individuel ?
    ↓ OUI → Utilise son profil individuel
    ↓ NON → Utilise le profil de sa promotion
```

---

### 4. Le Blocage de Sites

Le système permet de **bloquer l'accès à certains sites web**.

**Types de blocage :**
| Type | Description |
|------|-------------|
| Global | Bloqué pour tous les utilisateurs |
| Par profil | Bloqué uniquement pour un profil spécifique |
| Par promotion | Bloqué uniquement pour une promotion |

**Catégories de sites :**
- Réseaux sociaux (Facebook, Instagram, TikTok...)
- Streaming vidéo (Netflix, YouTube...)
- Jeux en ligne
- Sites pour adultes
- Sites de paris/jeux d'argent

**Comment ça marche :**
1. L'administrateur ajoute un domaine à bloquer (ex: facebook.com)
2. Le système synchronise avec le routeur MikroTik
3. Quand un utilisateur tente d'accéder au site, il est redirigé vers une page blanche

---

## Workflow : Comment ça se passe concrètement ?

### Étape 1 : Création d'un utilisateur

```
┌─────────────────┐    ┌─────────────────┐
│   Administrateur │ ──→│  Interface Web  │
└─────────────────┘    └────────┬────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │ Compte créé     │
                       │ (pas encore     │
                       │  accès WiFi)    │
                       └─────────────────┘
```

### Étape 2 : Attribution d'un profil

L'utilisateur reçoit ses règles d'accès via :
- **Un profil direct** : règles personnalisées pour cet utilisateur
- **Une promotion** : l'utilisateur hérite des règles du groupe

```
┌─────────────────┐
│   Utilisateur   │
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌───────┐ ┌──────────┐
│Profil │ │Promotion │
│direct │ │ (groupe) │
└───────┘ └────┬─────┘
               │
               ▼
          ┌────────┐
          │ Profil │
          │ hérité │
          └────────┘
```

### Étape 3 : Activation dans RADIUS

RADIUS est le système qui vérifie les identifiants lors de la connexion WiFi.

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Clic "Activer   │ ──→│ Création entrée │ ──→│ Utilisateur     │
│ dans RADIUS"    │    │ dans base       │    │ peut se         │
│                 │    │ RADIUS          │    │ connecter       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Étape 4 : Connexion d'un utilisateur

```
┌───────────┐    ┌───────────┐    ┌───────────┐    ┌───────────┐
│Utilisateur│    │  MikroTik │    │ FreeRADIUS│    │   Base de │
│ (téléphone│    │  (routeur)│    │ (serveur) │    │  données  │
│  ou PC)   │    │           │    │           │    │           │
└─────┬─────┘    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
      │                │                │                │
      │ 1. Connexion   │                │                │
      │    WiFi        │                │                │
      ├───────────────→│                │                │
      │                │                │                │
      │ 2. Page de     │                │                │
      │    connexion   │                │                │
      │←───────────────┤                │                │
      │                │                │                │
      │ 3. Identifiant │                │                │
      │    + mot de    │                │                │
      │    passe       │                │                │
      ├───────────────→│                │                │
      │                │                │                │
      │                │ 4. Vérification│                │
      │                ├───────────────→│                │
      │                │                │                │
      │                │                │ 5. Recherche   │
      │                │                │    utilisateur │
      │                │                ├───────────────→│
      │                │                │                │
      │                │                │ 6. Infos profil│
      │                │                │←───────────────┤
      │                │                │                │
      │                │ 7. Accès       │                │
      │                │    autorisé    │                │
      │                │    + règles    │                │
      │                │    (vitesse,   │                │
      │                │    quota...)   │                │
      │                │←───────────────┤                │
      │                │                │                │
      │ 8. Accès       │                │                │
      │    Internet    │                │                │
      │    accordé     │                │                │
      │←───────────────┤                │                │
      │                │                │                │
```

---

## Suivi de la Consommation

Le système enregistre automatiquement :
- **Données téléchargées** (videos, images, fichiers...)
- **Données envoyées** (emails, uploads...)
- **Durée des sessions**

### Alertes automatiques

| Seuil | Action |
|-------|--------|
| 80% du quota | Notification d'avertissement |
| 100% du quota | Déconnexion automatique |
| 5 jours avant expiration | Notification de rappel |
| Expiration du profil | Déconnexion automatique |

---

## Résumé des Rôles

### L'Administrateur peut :
- Créer/modifier/supprimer des utilisateurs
- Créer/modifier des profils (vitesse, quota, durée...)
- Créer des promotions et y affecter des utilisateurs
- Activer/désactiver l'accès WiFi d'un utilisateur
- Bloquer/débloquer des sites web
- Consulter les statistiques d'utilisation

### L'Utilisateur peut :
- Se connecter au WiFi avec ses identifiants
- Consulter son quota restant
- Voir ses sessions actives
- Changer son mot de passe

---

## Schéma Global du Système

```
┌────────────────────────────────────────────────────────────────────┐
│                          INTERFACE WEB                             │
│                        (Vue.js Frontend)                           │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │  Gestion     │  │  Gestion     │  │  Gestion     │             │
│  │ Utilisateurs │  │  Profils     │  │ Sites bloqués│             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
└────────────────────────────┬───────────────────────────────────────┘
                             │
                             ▼
┌────────────────────────────────────────────────────────────────────┐
│                        SERVEUR BACKEND                             │
│                       (Django + API REST)                          │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │   Modèle     │  │   Modèle     │  │   Modèle     │             │
│  │    User      │  │   Profile    │  │ BlockedSite  │             │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘             │
│         │                 │                 │                      │
└─────────┼─────────────────┼─────────────────┼──────────────────────┘
          │                 │                 │
          ▼                 ▼                 ▼
┌────────────────────┐ ┌────────────────┐ ┌────────────────┐
│                    │ │                │ │                │
│    FreeRADIUS      │ │  FreeRADIUS    │ │    MikroTik    │
│    (radcheck)      │ │ (radgroupreply)│ │  (DNS static)  │
│                    │ │                │ │                │
│ Vérifie les        │ │ Stocke les     │ │ Bloque les     │
│ identifiants       │ │ paramètres     │ │ domaines       │
│                    │ │ des profils    │ │                │
└────────────────────┘ └────────────────┘ └────────────────┘
          │                    │                  │
          └────────────────────┼──────────────────┘
                               │
                               ▼
                    ┌────────────────────┐
                    │                    │
                    │   ROUTEUR MIKROTIK │
                    │    (Hotspot WiFi)  │
                    │                    │
                    │ - Authentification │
                    │ - Application QoS  │
                    │ - Blocage DNS      │
                    │ - Comptage données │
                    │                    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │                    │
                    │   UTILISATEURS     │
                    │   (Smartphones,    │
                    │    Ordinateurs)    │
                    │                    │
                    └────────────────────┘
```

---

## Glossaire

| Terme | Définition |
|-------|------------|
| **Bande passante** | Vitesse de connexion (en Mbps = mégabits par seconde) |
| **Quota** | Quantité maximale de données (en Go = gigaoctets) |
| **Session** | Période de connexion continue au WiFi |
| **Timeout** | Délai après lequel la connexion est automatiquement coupée |
| **RADIUS** | Protocole standard pour l'authentification réseau |
| **MikroTik** | Marque du routeur qui gère le réseau WiFi |
| **Profil** | Ensemble de règles (vitesse, quota, durée...) |
| **Promotion** | Groupe d'utilisateurs (ex: une classe d'étudiants) |
| **DNS** | Système qui traduit les noms de sites en adresses IP |

---

## Questions Fréquentes

### "Pourquoi ma connexion est lente ?"
Votre vitesse est limitée par votre profil. Contactez l'administrateur pour connaître vos limites.

### "Je ne peux pas accéder à Facebook/YouTube/..."
Ces sites peuvent être bloqués par l'administrateur. C'est une décision institutionnelle.

### "Ma connexion s'est coupée automatiquement"
Plusieurs raisons possibles :
- Vous avez atteint votre quota de données
- Votre session a expiré (durée maximale atteinte)
- Vous êtes resté inactif trop longtemps
- Votre profil a expiré

### "Je ne peux pas me connecter"
Vérifiez que :
- Votre compte a été activé dans RADIUS
- Votre identifiant et mot de passe sont corrects
- Vous n'avez pas dépassé le nombre d'appareils autorisés

---

*Document généré automatiquement - Portail Captif v1.0*
