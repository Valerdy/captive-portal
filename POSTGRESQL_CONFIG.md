# 🐘 Configuration PostgreSQL - Guide Complet

Ce guide vous explique comment configurer PostgreSQL pour le portail captif sur **Windows**.

---

## 📋 Table des Matières

1. [Installation PostgreSQL](#installation-postgresql)
2. [Configuration avec pgAdmin](#configuration-avec-pgadmin)
3. [Configuration du Backend Django](#configuration-du-backend-django)
4. [Tests de Connexion](#tests-de-connexion)
5. [Migrations et Démarrage](#migrations-et-démarrage)
6. [Résolution de Problèmes](#résolution-de-problèmes)
7. [Commandes Utiles](#commandes-utiles)

---

## 📥 Installation PostgreSQL

### Option 1: Installation PostgreSQL + pgAdmin (Recommandé)

**Téléchargez PostgreSQL pour Windows:**
https://www.postgresql.org/download/windows/

**Lors de l'installation:**

1. **Composants à installer:**
   - ✅ PostgreSQL Server
   - ✅ pgAdmin 4 (interface graphique)
   - ✅ Command Line Tools
   - ❌ Stack Builder (optionnel)

2. **Configuration:**
   - **Port:** 5432 (par défaut)
   - **Mot de passe superuser:** Choisissez un mot de passe sécurisé et **notez-le**
   - **Locale:** French, France (ou votre locale)

3. **Installation:**
   - Chemin par défaut: `C:\Program Files\PostgreSQL\16\`
   - Durée: ~5 minutes

4. **Vérification:**
   - Cherchez "pgAdmin 4" dans le menu Démarrer
   - Lancez pgAdmin
   - Connectez-vous avec le mot de passe défini

---

### Option 2: pgAdmin uniquement (si PostgreSQL déjà installé)

Si PostgreSQL est déjà installé, installez juste pgAdmin:
https://www.pgadmin.org/download/pgadmin-4-windows/

---

## 🔧 Configuration avec pgAdmin

### Étape 1: Démarrer pgAdmin

1. **Lancez pgAdmin 4** depuis le menu Démarrer
2. **Entrez le master password** (pour protéger vos credentials)
3. **Connectez-vous au serveur PostgreSQL:**
   - Dans l'arbre à gauche, clic sur "PostgreSQL 16" (ou votre version)
   - Entrez le mot de passe superuser défini lors de l'installation

---

### Étape 2: Créer la Base de Données

**Méthode Graphique (pgAdmin):**

1. **Développez** "Servers" → "PostgreSQL 16" (ou votre version)
2. **Clic droit** sur "Databases" → **Create** → **Database**
3. **Remplissez le formulaire:**
   - **Database:** `captive_portal_db`
   - **Owner:** `postgres`
   - **Encoding:** `UTF8`
   - **Template:** `template0`
   - **Collation:** `French_France.1252` (ou `C`)
   - **Character type:** `French_France.1252` (ou `C`)
4. **Cliquez sur "Save"**

✅ **Résultat:** Vous devriez voir `captive_portal_db` dans la liste des bases de données

**Méthode SQL (alternative):**

1. **Clic droit** sur "PostgreSQL 16" → **Query Tool**
2. **Exécutez:**
   ```sql
   CREATE DATABASE captive_portal_db
       WITH OWNER = postgres
       ENCODING = 'UTF8'
       CONNECTION LIMIT = -1;
   ```
3. **Cliquez sur ▶️ Execute**

---

### Étape 3: Vérifier la Connexion

**Dans pgAdmin:**

1. **Développez** `captive_portal_db`
2. **Clic droit** sur `captive_portal_db` → **Query Tool**
3. **Exécutez:**
   ```sql
   SELECT version();
   SELECT current_database();
   SELECT current_user;
   ```

✅ **Résultat attendu:**
```
PostgreSQL 16.x on x86_64-pc-windows-msvc
captive_portal_db
postgres
```

---

## ⚙️ Configuration du Backend Django

### Étape 1: Copier le Fichier de Configuration PostgreSQL

**Option A: Script Automatique (Recommandé)**

Double-cliquez sur: **`setup_postgresql.bat`**

Ou dans PowerShell/CMD:
```bash
cd C:\Users\nguim\OneDrive\Bureau\captive-portal
setup_postgresql.bat
```

**Option B: Manuelle**

```bash
cd backend
copy .env.postgresql .env
```

Puis **éditez `.env`** et modifiez:
```env
DB_PASSWORD=VotreMotDePassePostgreSQL
```

---

### Étape 2: Vérifier la Configuration

**Fichier:** `backend\.env`

```env
# Database Configuration - PostgreSQL
DB_ENGINE=django.db.backends.postgresql
DB_NAME=captive_portal_db
DB_USER=postgres
DB_PASSWORD=votre_mot_de_passe    # ⚠️ MODIFIEZ ICI
DB_HOST=localhost
DB_PORT=5432
```

**Points importants:**
- ✅ `DB_ENGINE` doit être `django.db.backends.postgresql`
- ✅ `DB_NAME` doit correspondre à la base créée (`captive_portal_db`)
- ✅ `DB_USER` est généralement `postgres`
- ✅ `DB_PASSWORD` est celui défini lors de l'installation PostgreSQL
- ✅ `DB_HOST` est `localhost` pour une installation locale
- ✅ `DB_PORT` est `5432` par défaut

---

## 🧪 Tests de Connexion

### Test 1: Script Python de Test

```bash
cd backend
venv\Scripts\activate
python test_postgresql_connection.py
```

**Résultat attendu:**
```
============================================
   TEST DE CONNEXION POSTGRESQL
============================================

✅ Django configuré avec succès

============================================
   CONFIGURATION DATABASE
============================================

ℹ️  Engine:   django.db.backends.postgresql
ℹ️  Database: captive_portal_db
ℹ️  User:     postgres
ℹ️  Host:     localhost
ℹ️  Port:     5432

✅ Configuration PostgreSQL détectée

============================================
   TEST DE CONNEXION
============================================

✅ Connexion PostgreSQL établie!
ℹ️  Version: PostgreSQL 16.x
✅ Base de données connectée: captive_portal_db
✅ Utilisateur connecté: postgres

...
```

---

### Test 2: Connexion avec psql (optionnel)

Si vous avez installé Command Line Tools:

```bash
# Ouvrir PowerShell ou CMD
psql -U postgres -h localhost -d captive_portal_db
```

**Entrez le mot de passe PostgreSQL**

```sql
-- Tester quelques commandes
\l          -- Liste des bases de données
\dt         -- Liste des tables (vide pour l'instant)
\q          -- Quitter
```

---

### Test 3: Connexion avec pgAdmin

1. **Ouvrez pgAdmin**
2. **Développez** Servers → PostgreSQL 16 → Databases → captive_portal_db
3. **Clic droit** sur `captive_portal_db` → **Query Tool**
4. **Exécutez:**
   ```sql
   SELECT 'Connexion réussie!' AS message;
   ```

✅ **Si vous voyez le message, la connexion fonctionne !**

---

## 🚀 Migrations et Démarrage

### Étape 1: Appliquer les Migrations

**Script Automatique:**
```bash
start_with_postgresql.bat
```

**Ou Manuellement:**

```bash
cd backend
venv\Scripts\activate

# Appliquer les migrations
python manage.py migrate
```

**Résultat attendu:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, core, mikrotik, radius, sessions, token_blacklist
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying auth.0001_initial... OK
  Applying core.0001_initial... OK
  Applying mikrotik.0001_initial... OK
  Applying radius.0001_initial... OK
  ...
```

✅ **Les tables Django sont maintenant créées dans PostgreSQL !**

---

### Étape 2: Vérifier les Tables dans pgAdmin

1. **Rafraîchissez** pgAdmin (clic droit sur `captive_portal_db` → Refresh)
2. **Développez** captive_portal_db → Schemas → public → Tables
3. **Vous devriez voir:**
   - `auth_user`
   - `core_device`
   - `core_session`
   - `core_user`
   - `core_voucher`
   - `mikrotik_mikrotikrouter`
   - `mikrotik_mikrotikhotspotuser`
   - `radius_radiusserver`
   - `radius_radiusauthlog`
   - Et environ 30+ tables au total

---

### Étape 3: Créer un Superuser

**Script Automatique:**
```bash
create_admin.bat
```

**Ou Manuellement:**

```bash
python manage.py createsuperuser
```

**Remplissez:**
- **Username:** `admin`
- **Email:** `admin@example.com`
- **Password:** `admin123` (ou votre choix)

✅ **Superuser créé !**

---

### Étape 4: Démarrer le Backend

```bash
python manage.py runserver 0.0.0.0:8000
```

**Résultat attendu:**
```
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
November 20, 2025 - 10:30:00
Django version 5.2.8, using settings 'backend.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CTRL-BREAK.
```

✅ **Backend démarré avec PostgreSQL !**

**Testez:** http://localhost:8000/admin

---

### Étape 5: Démarrer le Frontend

**Nouveau terminal:**
```bash
cd frontend\portail-captif
npm run dev
```

**Testez:** http://localhost:5173

---

## 🐛 Résolution de Problèmes

### Problème 1: "could not connect to server"

**Symptôme:**
```
could not connect to server: Connection refused (0x0000274D/10061)
Is the server running on host "localhost" (::1) and accepting
TCP/IP connections on port 5432?
```

**Solutions:**

**1. Vérifier que PostgreSQL est démarré**

```powershell
# PowerShell en administrateur
Get-Service -Name postgresql*
```

**Si "Stopped":**
```powershell
Start-Service -Name postgresql-x64-16  # ou votre version
```

**Ou via services.msc:**
- Appuyez sur `Win+R` → `services.msc`
- Cherchez "postgresql-x64-16"
- Clic droit → Démarrer

**2. Vérifier que le port 5432 est ouvert**

```powershell
netstat -ano | findstr :5432
```

Vous devriez voir:
```
TCP    0.0.0.0:5432           0.0.0.0:0              LISTENING       1234
TCP    [::]:5432              [::]:0                 LISTENING       1234
```

---

### Problème 2: "password authentication failed"

**Symptôme:**
```
FATAL:  password authentication failed for user "postgres"
```

**Solutions:**

**1. Vérifier le mot de passe dans .env**

Éditez `backend\.env` et assurez-vous que `DB_PASSWORD` est correct.

**2. Réinitialiser le mot de passe PostgreSQL**

**Via pgAdmin:**
- Clic droit sur "PostgreSQL 16" → Properties
- Login/Group Roles → postgres → Definition
- Nouveau mot de passe

**Via SQL:**
```sql
-- Dans pgAdmin Query Tool (connecté en superuser)
ALTER USER postgres WITH PASSWORD 'nouveau_mot_de_passe';
```

**3. Vérifier pg_hba.conf**

Fichier: `C:\Program Files\PostgreSQL\16\data\pg_hba.conf`

Cherchez la ligne:
```
# IPv4 local connections:
host    all             all             127.0.0.1/32            scram-sha-256
```

Si c'est `trust`, changez en `md5` ou `scram-sha-256`:
```
host    all             all             127.0.0.1/32            md5
```

**Redémarrez PostgreSQL après modification.**

---

### Problème 3: "database does not exist"

**Symptôme:**
```
FATAL:  database "captive_portal_db" does not exist
```

**Solution:**

**Créez la base de données avec pgAdmin:**

1. Clic droit sur "Databases" → Create → Database
2. Name: `captive_portal_db`
3. Save

**Ou avec SQL:**
```sql
CREATE DATABASE captive_portal_db
    WITH OWNER = postgres
    ENCODING = 'UTF8';
```

---

### Problème 4: "role does not exist"

**Symptôme:**
```
FATAL:  role "votre_user" does not exist
```

**Solution:**

Changez `DB_USER` dans `.env` pour `postgres` (utilisateur par défaut).

Ou créez un nouvel utilisateur:
```sql
-- Dans pgAdmin
CREATE USER captive_user WITH PASSWORD 'votre_password';
GRANT ALL PRIVILEGES ON DATABASE captive_portal_db TO captive_user;
```

Puis dans `.env`:
```env
DB_USER=captive_user
DB_PASSWORD=votre_password
```

---

### Problème 5: "psycopg2 not installed"

**Symptôme:**
```
Error loading psycopg2 module: No module named 'psycopg2'
```

**Solution:**

```bash
cd backend
venv\Scripts\activate
pip install psycopg2-binary
```

Si erreur d'installation:
```bash
pip install --upgrade pip
pip install psycopg2-binary
```

---

### Problème 6: Performances lentes

**Symptôme:** Les requêtes sont lentes (>1s)

**Solutions:**

**1. Créer des index (après migrations)**

```sql
-- Dans pgAdmin Query Tool
CREATE INDEX IF NOT EXISTS idx_core_session_user_id ON core_session(user_id);
CREATE INDEX IF NOT EXISTS idx_core_device_user_id ON core_device(user_id);
CREATE INDEX IF NOT EXISTS idx_core_session_status ON core_session(status);
```

**2. Analyser les tables**

```sql
ANALYZE;
VACUUM ANALYZE;
```

**3. Vérifier les logs lents**

Fichier: `C:\Program Files\PostgreSQL\16\data\postgresql.conf`
```
log_min_duration_statement = 1000  # Log queries > 1s
```

Redémarrez PostgreSQL et consultez les logs:
`C:\Program Files\PostgreSQL\16\data\log\`

---

## 📊 Commandes Utiles

### Commandes PostgreSQL (psql)

```bash
# Se connecter
psql -U postgres -d captive_portal_db

# Lister les bases de données
\l

# Se connecter à une base
\c captive_portal_db

# Lister les tables
\dt

# Décrire une table
\d core_user

# Lister les utilisateurs
\du

# Quitter
\q
```

---

### Commandes SQL Utiles

```sql
-- Taille de la base de données
SELECT pg_size_pretty(pg_database_size('captive_portal_db'));

-- Nombre de connexions actives
SELECT count(*) FROM pg_stat_activity;

-- Tables et leur taille
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Nombre d'enregistrements par table
SELECT
    schemaname,
    tablename,
    n_tup_ins AS inserted,
    n_tup_upd AS updated,
    n_tup_del AS deleted
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Vacuum et analyze (maintenance)
VACUUM ANALYZE;

-- Requêtes lentes en cours
SELECT pid, now() - pg_stat_activity.query_start AS duration, query
FROM pg_stat_activity
WHERE (now() - pg_stat_activity.query_start) > interval '5 seconds'
ORDER BY duration DESC;
```

---

### Commandes Django

```bash
# Créer des migrations
python manage.py makemigrations

# Appliquer les migrations
python manage.py migrate

# Afficher les migrations
python manage.py showmigrations

# Créer un superuser
python manage.py createsuperuser

# Shell Django (pour tester)
python manage.py shell

# Exporter les données
python manage.py dumpdata > backup.json

# Importer les données
python manage.py loaddata backup.json

# Créer des données de test
python manage.py create_test_data
```

---

## 🔐 Sécurité & Bonnes Pratiques

### 1. Sauvegardes

**Automatique avec pgAdmin:**
1. Clic droit sur `captive_portal_db` → Backup
2. Fichier de sortie: `C:\Backups\captive_portal_backup.sql`
3. Format: Plain (pour lisibilité) ou Custom (compressé)

**Avec pg_dump:**
```bash
pg_dump -U postgres -d captive_portal_db > backup.sql
```

**Restauration:**
```bash
psql -U postgres -d captive_portal_db < backup.sql
```

---

### 2. Utilisateur dédié (Production)

Ne pas utiliser `postgres` en production. Créez un utilisateur dédié:

```sql
-- Créer un utilisateur pour l'application
CREATE USER captive_app WITH PASSWORD 'secure_password_here';

-- Donner les permissions sur la base
GRANT ALL PRIVILEGES ON DATABASE captive_portal_db TO captive_app;

-- Permissions sur toutes les tables
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO captive_app;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO captive_app;
```

Dans `.env`:
```env
DB_USER=captive_app
DB_PASSWORD=secure_password_here
```

---

### 3. Connexions SSL (Production)

Dans `postgresql.conf`:
```
ssl = on
ssl_cert_file = 'server.crt'
ssl_key_file = 'server.key'
```

Dans `.env`:
```env
DB_OPTIONS=sslmode=require
```

---

## ✅ Checklist de Configuration

- [ ] PostgreSQL installé et démarré
- [ ] pgAdmin installé et accessible
- [ ] Base de données `captive_portal_db` créée
- [ ] Fichier `.env` configuré avec PostgreSQL
- [ ] Mot de passe PostgreSQL correct dans `.env`
- [ ] Script de test `test_postgresql_connection.py` passe ✅
- [ ] Migrations appliquées: `python manage.py migrate`
- [ ] Superuser créé: `python manage.py createsuperuser`
- [ ] Backend démarre sans erreur
- [ ] http://localhost:8000/admin accessible
- [ ] Frontend démarre et communique avec le backend

---

## 🎯 Résumé

**Pour démarrer avec PostgreSQL:**

1. ✅ Installez PostgreSQL + pgAdmin
2. ✅ Créez la base `captive_portal_db` dans pgAdmin
3. ✅ Copiez `.env.postgresql` → `.env`
4. ✅ Modifiez le mot de passe dans `.env`
5. ✅ Testez: `python test_postgresql_connection.py`
6. ✅ Migrations: `python manage.py migrate`
7. ✅ Superuser: `python manage.py createsuperuser`
8. ✅ Démarrez: `python manage.py runserver`

**C'est prêt ! 🎉**

---

## 📚 Ressources

- **Documentation PostgreSQL:** https://www.postgresql.org/docs/
- **pgAdmin Documentation:** https://www.pgadmin.org/docs/
- **Django + PostgreSQL:** https://docs.djangoproject.com/en/5.2/ref/databases/#postgresql-notes
- **psycopg2 Documentation:** https://www.psycopg.org/docs/

---

**Besoin d'aide ?** Consultez la section "Résolution de Problèmes" ou les logs PostgreSQL dans:
`C:\Program Files\PostgreSQL\16\data\log\`
