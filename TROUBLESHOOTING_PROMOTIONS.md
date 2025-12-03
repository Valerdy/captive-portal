# Guide de dépannage - Promotions et Modal Admin

## Problème 1 : Le modal de création d'utilisateur ne s'ouvre pas

### Vérifications à faire :

1. **Ouvrir la console du navigateur** (F12) et vérifier s'il y a des erreurs JavaScript

2. **Vérifier que le bouton existe** - Recherchez dans la page admin :
   - Bouton "Nouvel utilisateur" avec une icône +

3. **Test manuel** :
   - Ouvrir la console du navigateur
   - Tapez : `document.querySelector('.btn-primary')`
   - Cela devrait afficher l'élément du bouton

### Solution si le modal ne s'ouvre pas :

Le bouton dans `AdminUsersView.vue` devrait déclencher `@click="openAddModal"`. Vérifiez que :
- La fonction `openAddModal()` existe dans le script
- `showAddModal` est défini comme `ref(false)`
- Le modal a la condition `v-if="showAddModal"`

---

## Problème 2 : Les promotions ne s'affichent pas dans le dropdown

### Étapes de résolution :

### Étape 1 : Vérifier les migrations

```bash
cd /home/user/captive-portal/backend
python manage.py showmigrations core
```

Vous devriez voir :
```
core
 [X] 0001_initial
 [X] 0002_...
 ...
 [X] 0009_create_promotion_model
```

Si `0009_create_promotion_model` n'a PAS de `[X]`, exécutez :

```bash
python manage.py migrate
```

### Étape 2 : Vérifier que la table promotions existe

Connectez-vous à MySQL :

```bash
mysql -u [votre_user] -p [votre_database]
```

Puis exécutez :

```sql
SHOW TABLES LIKE 'promotions';
DESCRIBE promotions;
SELECT COUNT(*) FROM promotions;
```

Si la table n'existe pas :
```bash
python manage.py migrate core 0009
```

### Étape 3 : Insérer les promotions

**Option A - Via script Python** (recommandé) :

```bash
cd /home/user/captive-portal/backend
python init_promotions.py
```

**Option B - Via Django shell** :

```bash
python manage.py shell
```

Puis dans le shell Python :

```python
from core.models import Promotion

promotions = [
    {'name': 'L1', 'description': 'Licence 1ère année'},
    {'name': 'L2', 'description': 'Licence 2ème année'},
    {'name': 'L3', 'description': 'Licence 3ème année'},
    {'name': 'M1', 'description': 'Master 1ère année'},
    {'name': 'M2', 'description': 'Master 2ème année'},
    {'name': 'ING1', 'description': 'Ingénieur 1ère année'},
    {'name': 'ING2', 'description': 'Ingénieur 2ème année'},
    {'name': 'ING3', 'description': 'Ingénieur 3ème année'},
    {'name': 'ING4', 'description': 'Ingénieur 4ème année'},
    {'name': 'ING5', 'description': 'Ingénieur 5ème année'},
    {'name': 'PREPA1', 'description': 'Prépa 1ère année'},
    {'name': 'PREPA2', 'description': 'Prépa 2ème année'},
    {'name': 'DOCTORAT', 'description': 'Doctorat'},
]

for p in promotions:
    Promotion.objects.get_or_create(
        name=p['name'],
        defaults={'description': p['description'], 'is_active': True}
    )

# Vérifier
print(f"Total promotions: {Promotion.objects.count()}")
for promo in Promotion.objects.all():
    print(f"  - {promo.name}: {promo.description}")
```

**Option C - Via SQL direct** :

```bash
mysql -u [votre_user] -p [votre_database] < /home/user/captive-portal/backend/insert_promotions.sql
```

### Étape 4 : Tester l'API

**Via le navigateur** :
1. Ouvrez : `http://localhost:8000/api/core/promotions/`
2. Vous devriez voir un JSON avec la liste des promotions

**Via curl** :
```bash
curl http://localhost:8000/api/core/promotions/
```

**Résultat attendu** :
```json
[
    {
        "id": 1,
        "name": "L1",
        "description": "Licence 1ère année",
        "is_active": true,
        "created_at": "...",
        "updated_at": "..."
    },
    ...
]
```

Si vous obtenez une erreur 404, vérifiez :
- Le serveur Django est démarré : `python manage.py runserver`
- Le fichier `core/urls.py` contient bien : `router.register(r'promotions', PromotionViewSet, basename='promotion')`

### Étape 5 : Vérifier la console du frontend

Dans le navigateur, ouvrez la console (F12) et recherchez :
- Erreurs réseau (onglet Network)
- Erreurs JavaScript (onglet Console)

Erreurs possibles :
- **CORS error** : Vérifiez les paramètres CORS dans Django
- **404 Not Found** : L'endpoint n'existe pas ou le serveur n'est pas démarré
- **500 Internal Server Error** : Erreur côté serveur, vérifiez les logs Django

### Étape 6 : Redémarrer les services

```bash
# Terminal 1 : Backend Django
cd /home/user/captive-portal/backend
python manage.py runserver

# Terminal 2 : Frontend Vue (si en dev)
cd /home/user/captive-portal/frontend/portail-captif
npm run dev
```

---

## Vérification rapide - Checklist

- [ ] Migrations appliquées (`python manage.py migrate`)
- [ ] Table `promotions` existe dans MySQL
- [ ] Au moins 10 promotions dans la table (L1-L3, M1-M2, ING1-ING5, etc.)
- [ ] L'endpoint `/api/core/promotions/` retourne du JSON
- [ ] Serveur Django démarré sur port 8000
- [ ] Frontend démarré (si en dev)
- [ ] Console du navigateur ne montre pas d'erreurs
- [ ] Le bouton "Nouvel utilisateur" est visible
- [ ] Le dropdown "Promotion" affiche "Sélectionnez une promotion"

---

## Debugging avancé

### Tester l'endpoint avec les dev tools du navigateur :

1. Ouvrez la console du navigateur (F12)
2. Allez dans l'onglet Console
3. Tapez :

```javascript
fetch('http://localhost:8000/api/core/promotions/')
  .then(res => res.json())
  .then(data => console.log(data))
  .catch(err => console.error(err))
```

Si cela fonctionne, le problème est dans le frontend.
Si cela échoue, le problème est côté backend.

### Vérifier le service promotions dans Vue :

Dans la console du navigateur sur la page admin :

```javascript
// Vérifier que le service est accessible
import('/src/services/promotion.service.ts').then(module => {
  module.default.getPromotions()
    .then(data => console.log('Promotions:', data))
    .catch(err => console.error('Erreur:', err))
})
```

---

## Contact et Support

Si le problème persiste après toutes ces étapes :

1. **Collectez les informations suivantes** :
   - Sortie de `python manage.py showmigrations core`
   - Sortie de `SELECT * FROM promotions;` dans MySQL
   - Résultat de `curl http://localhost:8000/api/core/promotions/`
   - Erreurs dans la console du navigateur (F12)
   - Logs du serveur Django

2. **Vérifiez les fichiers** :
   - `backend/core/models.py` contient bien la classe `Promotion`
   - `backend/core/serializers.py` contient bien `PromotionSerializer`
   - `backend/core/viewsets.py` contient bien `PromotionViewSet`
   - `backend/core/urls.py` enregistre bien le router avec promotions
   - `frontend/portail-captif/src/services/promotion.service.ts` existe
