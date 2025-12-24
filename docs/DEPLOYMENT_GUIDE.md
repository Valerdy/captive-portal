# 🚀 Guide de Déploiement - Portail Captif UCAC-ICAM

Guide complet pour déployer le portail captif avec connexion à votre serveur FreeRADIUS/MySQL.

## 📋 Architecture du Système

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│   Frontend      │◄────►│    Backend       │◄────►│   FreeRADIUS    │
│   Vue.js        │      │    Django        │      │   + MySQL       │
│   Port 5173     │      │    Port 8000     │      │   Port 3306     │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

## 🔧 Prérequis

### Serveur FreeRADIUS
- FreeRADIUS 3.x installé et fonctionnel
- MySQL/MariaDB configuré avec FreeRADIUS
- phpMyAdmin (optionnel mais recommandé)
- Port 3306 accessible (firewall configuré)

### Machine de développement
- Python 3.10+
- Node.js 18+ et npm
- Git

## 📦 Étape 1: Cloner et Préparer le Projet

```bash
cd /home/user
git clone <votre-repo> captive-portal
cd captive-portal
```

## 🔐 Étape 2: Configurer MySQL (FreeRADIUS)

### 2.1 Trouver les informations de connexion MySQL

Sur votre serveur FreeRADIUS :

```bash
# Se connecter au serveur FreeRADIUS
ssh user@ip-serveur-freeradius

# Afficher la configuration SQL
sudo cat /etc/freeradius/3.0/mods-available/sql
# OU
sudo cat /etc/raddb/mods-available/sql
```

Notez ces informations :
- **Host** : IP du serveur (ex: 192.168.1.100)
- **Database** : Nom de la base (généralement `radius`)
- **User** : Utilisateur MySQL (généralement `radius`)
- **Password** : Mot de passe MySQL
- **Port** : Port MySQL (généralement `3306`)

### 2.2 Autoriser les connexions distantes (si nécessaire)

Sur le serveur FreeRADIUS :

```bash
# Modifier la configuration MySQL
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# Commenter la ligne:
# bind-address = 127.0.0.1

# Redémarrer MySQL
sudo systemctl restart mysql

# Créer un utilisateur pour connexion distante
mysql -u root -p

CREATE USER 'radius'@'%' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON radius.* TO 'radius'@'%';
FLUSH PRIVILEGES;
EXIT;

# Ouvrir le port dans le firewall
sudo ufw allow 3306/tcp
```

## 🐍 Étape 3: Configurer le Backend Django

### 3.1 Créer l'environnement virtuel

```bash
cd /home/user/captive-portal/backend
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# OU
venv\Scripts\activate  # Windows
```

### 3.2 Installer les dépendances

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3.3 Configurer le fichier .env

Éditez `/home/user/captive-portal/backend/.env` :

```bash
# Django Configuration
SECRET_KEY=django-insecure-dev-key-change-in-production-!uwv@971di86)lw6c!=85n+uclltw$g2*y0_17$%y#1ln0@mzc
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,votre-ip-serveur

# Database Configuration (MySQL for FreeRADIUS integration)
DB_ENGINE=django.db.backends.mysql
DB_NAME=radius                    # ← Votre nom de base
DB_USER=radius                    # ← Votre utilisateur MySQL
DB_PASSWORD=VOTRE_MOT_DE_PASSE    # ← À CHANGER !
DB_HOST=192.168.x.x               # ← IP de votre serveur FreeRADIUS
DB_PORT=3306

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173

# JWT Token Lifetimes (in minutes)
JWT_ACCESS_TOKEN_LIFETIME=60
JWT_REFRESH_TOKEN_LIFETIME=1440

# RADIUS Configuration
RADIUS_SERVER=192.168.x.x         # ← IP de votre serveur FreeRADIUS
RADIUS_SECRET=testing123          # ← Secret RADIUS
RADIUS_AUTH_PORT=1812
RADIUS_ACCT_PORT=1813
```

### 3.4 Tester la connexion MySQL

```bash
python test_mysql_connection.py
```

Vous devriez voir :
```
✅ Connexion MySQL réussie!
✅ Version MySQL: 8.0.x
📊 Tables disponibles (10):
   [✓] radacct
   [✓] radcheck
   [✓] radgroupcheck
   ...
```

### 3.5 Créer les migrations et la base de données

```bash
# Créer les migrations pour les modèles Django
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Créer un superutilisateur admin
python manage.py createsuperuser
# Username: admin
# Email: admin@ucac-icam.com
# Password: (choisir un mot de passe fort)
```

### 3.6 Lancer le serveur backend

```bash
python manage.py runserver 0.0.0.0:8000
```

Le backend devrait être accessible sur `http://localhost:8000`

Testez : `http://localhost:8000/` → Devrait afficher le JSON de l'API root

## 🎨 Étape 4: Configurer le Frontend Vue.js

### 4.1 Installer les dépendances

```bash
cd /home/user/captive-portal/frontend/portail-captif
npm install
```

### 4.2 Vérifier la configuration API

Éditez `src/services/api.ts` si nécessaire pour pointer vers votre backend :

```typescript
const API_URL = 'http://localhost:8000'
```

### 4.3 Lancer le serveur frontend

```bash
npm run dev
```

Le frontend devrait être accessible sur `http://localhost:5173`

## ✅ Étape 5: Tester l'Application

### 5.1 Vérifications backend

```bash
# API Root
curl http://localhost:8000/

# Endpoints disponibles
curl http://localhost:8000/api/core/

# Admin Django
open http://localhost:8000/admin/
```

### 5.2 Vérifications frontend

1. Ouvrez `http://localhost:5173`
2. Vous devriez voir la page d'accueil UCAC-ICAM
3. Cliquez sur "Admin" (en haut à droite)
4. Connectez-vous avec le superuser créé
5. Vous devriez voir le dashboard admin

### 5.3 Test du flux complet

```bash
# Test 1: Inscription d'un utilisateur
curl -X POST http://localhost:8000/api/core/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@ucac-icam.com",
    "password": "testpass123",
    "first_name": "Test",
    "last_name": "User"
  }'

# Test 2: Connexion
curl -X POST http://localhost:8000/api/core/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'

# Test 3: Obtenir le profil (utilisez le token reçu)
curl http://localhost:8000/api/core/auth/profile/ \
  -H "Authorization: Bearer VOTRE_ACCESS_TOKEN"
```

## 🔒 Étape 6: Configuration de Sécurité

### 6.1 Pour la production

Modifiez `.env` :

```bash
# Générer une nouvelle SECRET_KEY
SECRET_KEY=une-cle-secrete-tres-longue-et-aleatoire-que-vous-devez-generer

# Désactiver le mode debug
DEBUG=False

# Ajouter votre domaine
ALLOWED_HOSTS=localhost,127.0.0.1,votre-domaine.com,votre-ip

# Mettre à jour CORS
CORS_ALLOWED_ORIGINS=https://votre-domaine.com
```

### 6.2 Configuration HTTPS (Recommandé)

```bash
# Installer certbot pour Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Obtenir un certificat SSL
sudo certbot --nginx -d votre-domaine.com
```

## 📊 Étape 7: Monitoring et Logs

### 7.1 Logs Django

```bash
# Logs du serveur Django
tail -f /home/user/captive-portal/backend/logs/django.log
```

### 7.2 Logs FreeRADIUS

```bash
# Sur le serveur FreeRADIUS
sudo tail -f /var/log/freeradius/radius.log
```

### 7.3 Logs MySQL

```bash
# Sur le serveur FreeRADIUS
sudo tail -f /var/log/mysql/error.log
```

## 🐛 Résolution des Problèmes

### Erreur: "Can't connect to MySQL server"

**Solution :**
1. Vérifiez que MySQL est démarré : `sudo systemctl status mysql`
2. Vérifiez l'IP et le port dans `.env`
3. Testez depuis la machine Django : `telnet IP_SERVEUR 3306`
4. Vérifiez le firewall : `sudo ufw status`

### Erreur: "Access denied for user 'radius'@'host'"

**Solution :**
1. Vérifiez le mot de passe dans `.env`
2. Vérifiez les permissions MySQL :
   ```sql
   SHOW GRANTS FOR 'radius'@'%';
   ```
3. Recréez l'utilisateur si nécessaire

### Erreur CORS sur le frontend

**Solution :**
1. Vérifiez `CORS_ALLOWED_ORIGINS` dans `.env`
2. Redémarrez le serveur Django
3. Videz le cache du navigateur

### Frontend ne peut pas se connecter au backend

**Solution :**
1. Vérifiez que le backend est lancé : `curl http://localhost:8000/`
2. Vérifiez l'URL dans `frontend/portail-captif/src/services/api.ts`
3. Vérifiez la console navigateur (F12) pour les erreurs

## 📚 Commandes Utiles

```bash
# Backend
cd /home/user/captive-portal/backend
source venv/bin/activate
python manage.py runserver                # Démarrer le serveur
python manage.py makemigrations           # Créer migrations
python manage.py migrate                  # Appliquer migrations
python manage.py createsuperuser          # Créer admin
python manage.py shell                    # Shell Django
python test_mysql_connection.py           # Tester MySQL

# Frontend
cd /home/user/captive-portal/frontend/portail-captif
npm run dev                               # Mode développement
npm run build                             # Build production
npm run preview                           # Prévisualiser build

# Git
git status                                # Voir les changements
git add .                                 # Ajouter tous les fichiers
git commit -m "message"                   # Créer un commit
git push                                  # Pousser vers le dépôt
```

## 🎯 Prochaines Étapes

1. **Tester avec de vrais utilisateurs FreeRADIUS**
   - Créer des comptes dans phpMyAdmin (table `radcheck`)
   - Tester l'authentification RADIUS

2. **Configurer le Mikrotik** (si applicable)
   - Configurer le Hotspot Mikrotik
   - Pointer vers le portail captif
   - Tester le flux de redirection

3. **Personnaliser l'interface**
   - Modifier les couleurs dans `frontend/portail-captif/src/views/`
   - Ajouter le logo UCAC-ICAM
   - Personnaliser les messages

4. **Mettre en production**
   - Configurer Nginx comme reverse proxy
   - Configurer PM2 pour le backend (ou Gunicorn)
   - Mettre en place des sauvegardes automatiques
   - Configurer le monitoring

## 📞 Support

- **Documentation Django** : https://docs.djangoproject.com/
- **Documentation Vue.js** : https://vuejs.org/guide/
- **Documentation FreeRADIUS** : https://freeradius.org/documentation/

## ✅ Checklist de Déploiement

- [ ] Serveur FreeRADIUS opérationnel
- [ ] MySQL accessible depuis la machine Django
- [ ] Backend Django installé et configuré
- [ ] Test de connexion MySQL réussi
- [ ] Migrations Django appliquées
- [ ] Superuser créé
- [ ] Backend accessible sur port 8000
- [ ] Frontend installé
- [ ] Frontend accessible sur port 5173
- [ ] Test d'inscription utilisateur réussi
- [ ] Test de connexion réussi
- [ ] Dashboard admin accessible
- [ ] CORS configuré correctement
- [ ] Logs fonctionnels
- [ ] Sécurité configurée (production)

---

**Félicitations ! Votre portail captif UCAC-ICAM est maintenant opérationnel ! 🎉**
