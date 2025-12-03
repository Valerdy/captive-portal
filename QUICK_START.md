# Guide de démarrage rapide - Résolution des problèmes

## 🚨 Problèmes actuels

Vous rencontrez deux problèmes :
1. **Le formulaire de création d'utilisateur ne s'ouvre pas**
2. **Les promotions ne s'affichent pas dans les dropdowns**

## ⚡ Solution rapide (5 minutes)

### Étape 1 : Appliquer les migrations et initialiser les promotions

Ouvrez un terminal dans le dossier backend :

```bash
cd /home/user/captive-portal/backend

# Appliquer les migrations
python manage.py migrate

# Initialiser les promotions
python init_promotions.py

# Vérifier que tout fonctionne
python check_system.py
```

**OU** utilisez le script tout-en-un :

```bash
cd /home/user/captive-portal/backend
./quick_fix.sh
```

### Étape 2 : Redémarrer le serveur Django

```bash
# Arrêtez le serveur actuel (Ctrl+C)
# Puis redémarrez :
python manage.py runserver
```

### Étape 3 : Tester l'API

Dans votre navigateur, allez sur :
```
http://localhost:8000/api/core/promotions/
```

Vous devriez voir un JSON avec 13 promotions (L1, L2, L3, M1, M2, ING1-5, PREPA1-2, DOCTORAT).

### Étape 4 : Tester le frontend

1. **Rechargez la page admin** (Ctrl + Shift + R pour forcer le rechargement)
2. **Ouvrez la console du navigateur** (F12)
3. **Cliquez sur "Nouvel utilisateur"**

Si le modal s'ouvre, vérifiez que le dropdown "Promotion" contient les promotions.

---

## 🔍 Si ça ne fonctionne toujours pas

### Pour le problème du modal :

Consultez : `/home/user/captive-portal/frontend/portail-captif/DIAGNOSTIC.md`

**Test rapide dans la console du navigateur :**
```javascript
// Tester si le bouton fonctionne
document.querySelector('button.btn-primary').click();
```

### Pour le problème des promotions :

Consultez : `/home/user/captive-portal/TROUBLESHOOTING_PROMOTIONS.md`

**Test rapide dans la console du navigateur :**
```javascript
// Tester l'API
fetch('http://localhost:8000/api/core/promotions/')
    .then(r => r.json())
    .then(data => console.log('Promotions:', data))
    .catch(err => console.error('Erreur:', err));
```

---

## 📋 Checklist de vérification

Avant de demander de l'aide, vérifiez :

**Backend :**
- [ ] `python manage.py showmigrations core` montre `[X]` pour toutes les migrations
- [ ] `python manage.py shell` puis `from core.models import Promotion; print(Promotion.objects.count())` affiche au moins 13
- [ ] `curl http://localhost:8000/api/core/promotions/` retourne du JSON
- [ ] Le serveur Django tourne sans erreurs

**Frontend :**
- [ ] La page admin se charge sans erreur
- [ ] La console du navigateur (F12) ne montre pas d'erreurs rouges
- [ ] L'onglet Network (F12) montre une requête vers `/api/core/promotions/` avec status 200
- [ ] Le bouton "Nouvel utilisateur" est visible

**Base de données :**
- [ ] La table `promotions` existe
- [ ] Elle contient au moins 13 lignes
- [ ] Le champ `is_active` est à `true` pour toutes

---

## 🆘 Commandes de diagnostic

```bash
# Backend - Vérifier les migrations
cd /home/user/captive-portal/backend
python manage.py showmigrations

# Backend - Vérifier les promotions
python manage.py shell
>>> from core.models import Promotion
>>> print(f"Total: {Promotion.objects.count()}")
>>> for p in Promotion.objects.all():
...     print(f"  - {p.name}: {p.description}")
>>> exit()

# Backend - Tester l'endpoint
curl http://localhost:8000/api/core/promotions/

# Ou avec Python
python -c "import requests; print(requests.get('http://localhost:8000/api/core/promotions/').json())"
```

---

## 📞 Besoin d'aide supplémentaire ?

Si après toutes ces étapes le problème persiste, collectez les informations suivantes :

1. **Logs du backend :**
   - Sortie de `python check_system.py`
   - Erreurs dans le terminal Django

2. **Logs du frontend :**
   - Erreurs dans la console du navigateur (F12 → Console)
   - Erreurs réseau (F12 → Network → filtrer par "promotions")

3. **État de la base de données :**
   ```sql
   SELECT * FROM promotions;
   SELECT COUNT(*) FROM promotions;
   ```

4. **Versions :**
   ```bash
   python --version
   python -m django --version
   node --version
   npm --version
   ```

Partagez ces informations pour obtenir de l'aide ciblée.
