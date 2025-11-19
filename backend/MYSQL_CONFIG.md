# Configuration MySQL pour FreeRADIUS

Ce guide vous aide à configurer la connexion MySQL entre le portail captif et votre serveur FreeRADIUS.

## 📋 Prérequis

- Serveur FreeRADIUS avec MySQL/MariaDB
- phpMyAdmin installé (optionnel mais recommandé)
- Accès SSH au serveur FreeRADIUS

## 🔍 Étape 1: Trouver les informations de connexion MySQL

### Sur votre serveur FreeRADIUS

Les informations de connexion MySQL sont généralement dans le fichier de configuration FreeRADIUS :

```bash
# Se connecter au serveur FreeRADIUS via SSH
ssh user@votre-serveur-freeradius

# Chercher les informations de connexion MySQL
sudo cat /etc/freeradius/3.0/mods-available/sql

# OU
sudo cat /etc/raddb/mods-available/sql
```

Vous devriez voir quelque chose comme :
```
sql {
    driver = "rlm_sql_mysql"
    dialect = "mysql"

    server = "localhost"
    port = 3306
    login = "radius"
    password = "radpass"
    radius_db = "radius"
}
```

### Informations typiques de FreeRADIUS

Par défaut, FreeRADIUS utilise :
- **Base de données** : `radius`
- **Utilisateur** : `radius`
- **Mot de passe** : `radpass` (à vérifier !)
- **Host** : `localhost` ou adresse IP du serveur
- **Port** : `3306`

## 🔐 Étape 2: Vérifier l'accès MySQL

### Option A: Depuis le serveur FreeRADIUS

```bash
mysql -u radius -p radius
# Entrez le mot de passe quand demandé

# Une fois connecté, testez:
SHOW TABLES;
SELECT * FROM radcheck LIMIT 5;
```

### Option B: Via phpMyAdmin

1. Ouvrez phpMyAdmin dans votre navigateur
2. Utilisez les identifiants MySQL trouvés
3. Vérifiez que vous voyez la base `radius` avec les tables FreeRADIUS

## ⚙️ Étape 3: Configurer le portail captif

### 1. Modifier le fichier `.env`

Éditez `/home/user/captive-portal/backend/.env` :

```bash
# Database Configuration (MySQL for FreeRADIUS integration)
DB_ENGINE=django.db.backends.mysql
DB_NAME=radius                    # Nom de votre base FreeRADIUS
DB_USER=radius                    # Utilisateur MySQL FreeRADIUS
DB_PASSWORD=votre_mot_de_passe    # À REMPLACER !
DB_HOST=192.168.x.x               # IP de votre serveur FreeRADIUS
DB_PORT=3306
```

### 2. Installer les dépendances Python

```bash
cd /home/user/captive-portal/backend
pip install -r requirements.txt
```

### 3. Tester la connexion

```bash
python manage.py dbshell
# Si ça fonctionne, vous êtes connecté à MySQL !
```

## 🔥 Accès distant à MySQL

Si votre serveur FreeRADIUS est sur une machine distante, vous devez autoriser les connexions distantes :

### Sur le serveur FreeRADIUS

```bash
# 1. Modifier la configuration MySQL
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf

# 2. Commenter cette ligne:
# bind-address = 127.0.0.1

# 3. Redémarrer MySQL
sudo systemctl restart mysql

# 4. Créer un utilisateur pour connexion distante
mysql -u root -p

CREATE USER 'radius'@'%' IDENTIFIED BY 'votre_mot_de_passe';
GRANT ALL PRIVILEGES ON radius.* TO 'radius'@'%';
FLUSH PRIVILEGES;
EXIT;

# 5. Ouvrir le port 3306 dans le firewall
sudo ufw allow 3306/tcp
```

## ✅ Étape 4: Vérifier la connexion

### Script de test

Créez un fichier `test_mysql_connection.py` :

```python
import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.db import connection

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT VERSION();")
        version = cursor.fetchone()
        print(f"✅ Connexion MySQL réussie!")
        print(f"Version MySQL: {version[0]}")

        cursor.execute("SHOW TABLES;")
        tables = cursor.fetchall()
        print(f"\n📊 Tables disponibles ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
except Exception as e:
    print(f"❌ Erreur de connexion: {e}")
    sys.exit(1)
```

Exécutez:
```bash
cd /home/user/captive-portal/backend
python test_mysql_connection.py
```

## 🔧 Résolution des problèmes

### Erreur: "Can't connect to MySQL server"

- Vérifiez que MySQL est démarré : `sudo systemctl status mysql`
- Vérifiez l'adresse IP et le port
- Vérifiez le firewall

### Erreur: "Access denied for user"

- Vérifiez le nom d'utilisateur et mot de passe
- Vérifiez les permissions : `SHOW GRANTS FOR 'radius'@'%';`

### Erreur: "Unknown database 'radius'"

- Vérifiez le nom de la base : `SHOW DATABASES;`
- Créez la base si nécessaire : `CREATE DATABASE radius;`

## 📚 Informations complémentaires

### Tables importantes de FreeRADIUS

```sql
-- Comptes utilisateurs
SELECT * FROM radcheck;

-- Groupes
SELECT * FROM radgroupcheck;

-- Sessions actives
SELECT * FROM radacct WHERE acctstoptime IS NULL;

-- Statistiques
SELECT username, SUM(acctinputoctets + acctoutputoctets) as total_bytes
FROM radacct
GROUP BY username;
```

### Configuration recommandée pour le portail

Dans `settings.py`, ajoutez ces options MySQL :

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

## 🚀 Prochaines étapes

Une fois la connexion établie :

1. Créer les migrations Django : `python manage.py makemigrations`
2. Appliquer les migrations : `python manage.py migrate`
3. Créer un superutilisateur : `python manage.py createsuperuser`
4. Démarrer le serveur : `python manage.py runserver`

## 📞 Besoin d'aide ?

Si vous rencontrez des problèmes, vérifiez :
- Les logs MySQL : `/var/log/mysql/error.log`
- Les logs FreeRADIUS : `/var/log/freeradius/radius.log`
- La configuration réseau entre les machines
