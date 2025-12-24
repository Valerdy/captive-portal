# 🔧 Guide de Résolution - Windows

## ❌ Problème Actuel

**Erreur Backend:**
```
Can't connect to MySQL server on '10.242.52.100' (timed out)
```

**Erreur Frontend:**
```
POST http://localhost:8000/api/core/auth/register/ net::ERR_CONNECTION_REFUSED
```

### 🔍 Diagnostic

1. **Le backend ne démarre pas** car il ne peut pas se connecter au serveur MySQL distant (10.242.52.100)
2. **Le frontend ne peut pas communiquer** car le backend n'est pas démarré

---

## 🎯 Solutions (Choisissez-en une)

### Solution 1: Utiliser SQLite (⚡ Recommandé pour commencer)

**Avantages:** Rapide, pas besoin de serveur MySQL, parfait pour tester
**Inconvénients:** Pas connecté à FreeRADIUS (vous pourrez le faire plus tard)

#### Étapes:

**1. Modifier le fichier `.env` du backend**

Fichier: `backend\.env`

```env
# Database Configuration (SQLite pour développement local)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=db.sqlite3
# Commentez les lignes MySQL suivantes:
# DB_USER=radius
# DB_PASSWORD=radpass
# DB_HOST=10.242.52.100
# DB_PORT=3306
```

**2. Appliquer les migrations**

```bash
cd backend
venv\Scripts\activate
python manage.py migrate
```

**3. Créer un superuser**

```bash
python manage.py createsuperuser
```
Entrez:
- Username: `admin`
- Email: `admin@example.com`
- Password: `admin123` (ou autre)

**4. Démarrer le backend**

```bash
python manage.py runserver 0.0.0.0:8000
```

**5. Dans un nouveau terminal, démarrer le frontend**

```bash
cd frontend\portail-captif
npm install
npm run dev
```

**6. Ouvrir dans le navigateur**

- Frontend: http://localhost:5173
- Backend Admin: http://localhost:8000/admin

✅ **Votre application fonctionnera et vous pourrez tester toutes les fonctionnalités !**

---

### Solution 2: Configurer MySQL Distant (Pour se connecter à FreeRADIUS)

Si vous voulez vraiment vous connecter au serveur MySQL distant (10.242.52.100), suivez ces étapes:

#### A. Vérifier que le serveur MySQL est accessible

**1. Tester avec ping**

```bash
ping 10.242.52.100
```

**Résultat attendu:**
```
Réponse de 10.242.52.100 : octets=32 temps=10ms TTL=64
```

Si ça ne ping pas, le serveur n'est pas accessible depuis votre réseau.

**2. Tester le port MySQL**

**Option A: Avec PowerShell**

```powershell
Test-NetConnection -ComputerName 10.242.52.100 -Port 3306
```

**Résultat attendu:**
```
TcpTestSucceeded : True
```

**Option B: Avec telnet**

```bash
telnet 10.242.52.100 3306
```

Si vous avez une erreur "telnet n'est pas reconnu", activez-le:
- Panneau de configuration → Programmes → Activer/Désactiver des fonctionnalités Windows
- Cochez "Client Telnet"

---

#### B. Configurer MySQL sur le serveur distant

**Connectez-vous au serveur FreeRADIUS (10.242.52.100) en SSH ou directement**

**1. Vérifier les credentials MySQL**

```bash
# Sur le serveur FreeRADIUS
sudo cat /etc/freeradius/3.0/mods-available/sql
```

Recherchez:
```
database = "radius"
login = "radius"
password = "radpass"
```

**2. Autoriser les connexions distantes**

```bash
# Sur le serveur FreeRADIUS
sudo mysql -u root -p
```

Dans MySQL:
```sql
-- Créer l'utilisateur avec accès distant (depuis votre IP Windows)
CREATE USER 'radius'@'%' IDENTIFIED BY 'radpass';
GRANT ALL PRIVILEGES ON radius.* TO 'radius'@'%';
FLUSH PRIVILEGES;

-- Vérifier
SELECT user, host FROM mysql.user WHERE user='radius';
```

**3. Configurer MySQL pour écouter sur toutes les interfaces**

```bash
# Sur le serveur FreeRADIUS
sudo nano /etc/mysql/mysql.conf.d/mysqld.cnf
```

Cherchez la ligne:
```
bind-address = 127.0.0.1
```

Modifiez en:
```
bind-address = 0.0.0.0
```

**4. Ouvrir le port 3306 dans le firewall**

```bash
# Sur le serveur FreeRADIUS
sudo ufw allow 3306/tcp
sudo ufw status
```

**5. Redémarrer MySQL**

```bash
sudo systemctl restart mysql
```

---

#### C. Tester la connexion depuis Windows

**1. Installer MySQL Client pour Windows**

Téléchargez depuis: https://dev.mysql.com/downloads/mysql/
Ou utilisez chocolatey:
```powershell
choco install mysql
```

**2. Tester la connexion**

```bash
mysql -h 10.242.52.100 -u radius -p
# Entrez le mot de passe: radpass
```

**Si ça fonctionne:**
```
mysql> SHOW DATABASES;
mysql> USE radius;
mysql> SHOW TABLES;
```

Vous devriez voir les tables FreeRADIUS (radcheck, radreply, etc.)

**3. Mettre à jour backend\.env**

```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=radius
DB_USER=radius
DB_PASSWORD=radpass
DB_HOST=10.242.52.100
DB_PORT=3306
```

**4. Installer le driver MySQL Python**

```bash
cd backend
venv\Scripts\activate
pip install mysqlclient
```

**Si erreur d'installation de mysqlclient sur Windows, utilisez pymysql:**

```bash
pip install pymysql
```

Puis ajoutez dans `backend\backend\__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

**5. Tester la connexion**

```bash
python test_mysql_connection.py
```

**6. Appliquer les migrations**

```bash
python manage.py migrate
```

**7. Démarrer le serveur**

```bash
python manage.py runserver 0.0.0.0:8000
```

---

### Solution 3: Tunnel SSH (Si MySQL n'accepte pas les connexions distantes)

Si vous ne pouvez/voulez pas ouvrir le port 3306 directement, utilisez un tunnel SSH.

**1. Créer un tunnel SSH**

```bash
# Depuis Windows (avec PuTTY ou OpenSSH)
ssh -L 3306:localhost:3306 user@10.242.52.100
```

**Avec PuTTY:**
- Session → Host: 10.242.52.100
- Connection → SSH → Tunnels:
  - Source port: 3306
  - Destination: localhost:3306
  - Add
- Open

**2. Modifier backend\.env**

```env
DB_HOST=127.0.0.1  # Via le tunnel, pas 10.242.52.100
DB_PORT=3306
```

**3. Garder le tunnel SSH ouvert et démarrer Django**

```bash
python manage.py runserver
```

---

## 🚀 Démarrage Complet (Windows)

Une fois le problème MySQL résolu (avec une des solutions ci-dessus):

### Terminal 1: Backend

```bash
cd C:\Users\nguim\OneDrive\Bureau\captive-portal\backend
venv\Scripts\activate
python manage.py runserver 0.0.0.0:8000
```

### Terminal 2: Frontend

```bash
cd C:\Users\nguim\OneDrive\Bureau\captive-portal\frontend\portail-captif
npm run dev
```

### Terminal 3: Tester la communication (optionnel)

```bash
cd C:\Users\nguim\OneDrive\Bureau\captive-portal
python test_communication.py
```

---

## 🔍 Vérifications

### 1. Backend fonctionne ?

Ouvrez: http://localhost:8000/admin

✅ Vous devriez voir la page de connexion Django admin

### 2. Frontend fonctionne ?

Ouvrez: http://localhost:5173

✅ Vous devriez voir la page d'accueil du portail captif

### 3. Communication fonctionne ?

Depuis le frontend, créez un compte.

✅ Vous devriez être redirigé vers le dashboard

---

## 🐛 Autres Problèmes Courants (Windows)

### Erreur: "python n'est pas reconnu"

```bash
# Vérifiez que Python est dans le PATH
python --version

# Si erreur, utilisez:
py --version
# ou
python3 --version
```

### Erreur: "venv\Scripts\activate" ne fonctionne pas

**Dans PowerShell:**
```powershell
# Autoriser l'exécution de scripts
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Puis activez
venv\Scripts\Activate.ps1
```

**Dans CMD:**
```bash
venv\Scripts\activate.bat
```

### Erreur: Port 8000 déjà utilisé

```bash
# Trouver le processus
netstat -ano | findstr :8000

# Tuer le processus (remplacez PID par le numéro trouvé)
taskkill /PID <PID> /F

# Ou utilisez un autre port
python manage.py runserver 0.0.0.0:8001
```

### Erreur: "npm n'est pas reconnu"

Installez Node.js: https://nodejs.org/

### Erreur d'installation de mysqlclient sur Windows

**Solution 1: Utiliser pymysql**
```bash
pip install pymysql
```

Créer `backend\backend\__init__.py`:
```python
import pymysql
pymysql.install_as_MySQLdb()
```

**Solution 2: Installer Visual C++ Build Tools**
https://visualstudio.microsoft.com/visual-cpp-build-tools/

---

## 📝 Checklist de Démarrage

- [ ] Problème MySQL résolu (SQLite ou MySQL distant configuré)
- [ ] Backend `.env` configuré correctement
- [ ] Migrations appliquées: `python manage.py migrate`
- [ ] Superuser créé: `python manage.py createsuperuser`
- [ ] Backend démarre sans erreur: `python manage.py runserver`
- [ ] Frontend démarre sans erreur: `npm run dev`
- [ ] http://localhost:8000/admin accessible
- [ ] http://localhost:5173 accessible
- [ ] Inscription fonctionne depuis le frontend
- [ ] Pas d'erreur CORS dans la console navigateur

---

## ✅ Recommandation

**Pour commencer rapidement:**
1. Utilisez **Solution 1 (SQLite)** pour tester l'application
2. Vérifiez que tout fonctionne (frontend + backend)
3. Une fois que tout marche, configurez MySQL distant (Solution 2 ou 3)

**SQLite est parfait pour:**
- Développement et tests
- Comprendre comment l'application fonctionne
- Tester toutes les fonctionnalités

**MySQL distant est nécessaire pour:**
- Production
- Intégration avec FreeRADIUS
- Authentification RADIUS réelle

---

## 📞 Prochaines Étapes

1. **Choisissez une solution** (SQLite recommandé pour commencer)
2. **Suivez les étapes** de la solution choisie
3. **Démarrez backend et frontend**
4. **Testez l'application** sur http://localhost:5173
5. **Revenez me dire si ça fonctionne !** 🚀

Si vous rencontrez d'autres erreurs, copiez-les et je vous aiderai à les résoudre.
