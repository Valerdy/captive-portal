# 🚀 Démarrage Rapide - Windows

## ⚡ Méthode Automatique (Recommandée)

### Étape 1: Démarrer le backend avec SQLite

Double-cliquez sur: **`start_with_sqlite.bat`**

Ou dans un terminal:
```bash
start_with_sqlite.bat
```

Ce script va automatiquement:
- ✅ Configurer SQLite (pas besoin de MySQL pour commencer)
- ✅ Appliquer les migrations
- ✅ Démarrer le serveur Django sur http://localhost:8000

### Étape 2: Créer un admin

**Pendant que le backend tourne**, ouvrez un nouveau terminal et double-cliquez sur: **`create_admin.bat`**

Ou:
```bash
create_admin.bat
```

Cela crée un superuser:
- **Username:** `admin`
- **Password:** `admin123`

### Étape 3: Démarrer le frontend

Ouvrez un nouveau terminal:
```bash
cd frontend\portail-captif
npm install
npm run dev
```

### Étape 4: Tester !

- **Frontend:** http://localhost:5173
- **Admin Django:** http://localhost:8000/admin (admin / admin123)

---

## 🔧 Méthode Manuelle

### Backend

```bash
# Terminal 1
cd backend
venv\Scripts\activate

# Configurer SQLite dans .env
# Modifiez DB_ENGINE=django.db.backends.sqlite3
# et DB_NAME=db.sqlite3

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```

### Frontend

```bash
# Terminal 2
cd frontend\portail-captif
npm install
npm run dev
```

---

## ❌ Problèmes ?

### Le backend ne démarre pas

**Erreur MySQL ?** → Utilisez SQLite (voir `WINDOWS_TROUBLESHOOTING.md`)

### "venv\Scripts\activate" ne fonctionne pas

**Dans PowerShell:**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
venv\Scripts\Activate.ps1
```

**Dans CMD:**
```bash
venv\Scripts\activate.bat
```

### Port 8000 déjà utilisé

```bash
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

---

## 📚 Documentation Complète

- **WINDOWS_TROUBLESHOOTING.md** - Solutions détaillées pour Windows
- **COMMUNICATION_TEST_GUIDE.md** - Tests de communication Backend ↔ Frontend
- **DEPLOYMENT_GUIDE.md** - Déploiement en production
- **MYSQL_CONFIG.md** - Configuration MySQL/FreeRADIUS

---

## ✅ Checklist

- [ ] Backend démarre sans erreur
- [ ] Frontend démarre sans erreur
- [ ] http://localhost:8000/admin accessible
- [ ] http://localhost:5173 accessible
- [ ] Inscription fonctionne
- [ ] Connexion fonctionne
- [ ] Dashboard s'affiche

---

## 🎯 Prochaines Étapes

1. ✅ Testez l'application avec SQLite
2. ✅ Vérifiez toutes les fonctionnalités
3. 🔧 Configurez MySQL distant (voir WINDOWS_TROUBLESHOOTING.md)
4. 🚀 Déployez en production (voir DEPLOYMENT_GUIDE.md)

---

**Besoin d'aide ?** Consultez `WINDOWS_TROUBLESHOOTING.md` pour des solutions détaillées.
