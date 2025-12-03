# Diagnostic Frontend - Promotions et Modal

## Problème : Le modal de création ne s'ouvre pas

### Test 1 : Vérifier que le bouton existe

Ouvrez la page admin des utilisateurs, puis ouvrez la console du navigateur (F12) et tapez :

```javascript
// Trouver le bouton "Nouvel utilisateur"
const button = document.querySelector('button.btn-primary');
console.log('Bouton trouvé:', button);

// Simuler un clic
if (button) {
    button.click();
    console.log('Clic simulé sur le bouton');
}
```

**Résultat attendu** : Le modal devrait s'ouvrir

**Si le modal ne s'ouvre pas** :
- Vérifiez qu'il n'y a pas d'erreurs JavaScript dans la console
- Le bouton pourrait avoir un autre sélecteur CSS

### Test 2 : Vérifier l'état de Vue

Dans la console, tapez :

```javascript
// Accéder à l'instance Vue (si en mode dev)
const app = document.querySelector('#app').__vueParentComponent;
console.log('App:', app);
```

### Test 3 : Forcer l'ouverture du modal

Si vous avez accès aux Vue DevTools, trouvez le composant `AdminUsersView` et modifiez manuellement :
- `showAddModal` → `true`

Ou dans la console :

```javascript
// Cela ne fonctionnera que si vous utilisez Vue DevTools
// ou si vous avez exposé les refs
```

---

## Problème : Les promotions ne s'affichent pas

### Test 1 : Vérifier que l'API répond

Dans la console du navigateur (sur n'importe quelle page) :

```javascript
fetch('http://localhost:8000/api/core/promotions/')
    .then(response => {
        console.log('Status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Promotions reçues:', data);
        console.log('Nombre de promotions:', data.length);
    })
    .catch(error => {
        console.error('Erreur:', error);
    });
```

**Résultats possibles** :

1. **Succès** : Vous voyez un tableau de promotions
   ```javascript
   Promotions reçues: [{id: 1, name: "L1", ...}, ...]
   Nombre de promotions: 13
   ```
   → Le backend fonctionne, le problème est dans le frontend

2. **Erreur CORS** :
   ```
   Access to fetch at 'http://localhost:8000/...' from origin 'http://localhost:5173'
   has been blocked by CORS policy
   ```
   → Configurez CORS dans Django

3. **Erreur 404** :
   ```
   Status: 404
   ```
   → L'endpoint n'existe pas ou n'est pas enregistré

4. **Erreur réseau** :
   ```
   Failed to fetch
   ```
   → Le serveur Django n'est pas démarré

### Test 2 : Vérifier le service promotions

Sur la page d'inscription ou admin, dans la console :

```javascript
// Charger le service
import('http://localhost:5173/src/services/promotion.service.ts')
    .then(module => {
        const promotionService = module.default;
        return promotionService.getPromotions();
    })
    .then(promotions => {
        console.log('Promotions via service:', promotions);
    })
    .catch(error => {
        console.error('Erreur service:', error);
    });
```

### Test 3 : Vérifier l'état du composant

Sur la page d'inscription, utilisez Vue DevTools :

1. Ouvrez Vue DevTools (onglet Vue dans les DevTools)
2. Trouvez le composant `RegisterView` ou `AdminUsersView`
3. Inspectez les données :
   - `promotions` : devrait contenir un tableau
   - `loadingPromotions` : devrait être `false` après chargement
   - `formData.promotion` : devrait être une chaîne vide initialement

---

## Solutions rapides

### Solution 1 : Le modal ne s'ouvre pas

Ajoutez temporairement un `console.log` dans le code pour débugger.

Dans `AdminUsersView.vue`, modifiez la fonction `openAddModal` :

```vue
function openAddModal() {
  console.log('openAddModal appelée');
  console.log('showAddModal avant:', showAddModal.value);

  newUser.value = {
    password: '',
    password2: '',
    first_name: '',
    last_name: '',
    promotion: '',
    matricule: '',
    is_staff: false
  }
  showAddModal.value = true;

  console.log('showAddModal après:', showAddModal.value);
}
```

Puis cliquez sur le bouton et vérifiez la console.

### Solution 2 : Les promotions ne se chargent pas

Ajoutez des logs dans le `onMounted` :

```vue
onMounted(async () => {
  console.log('Composant monté, chargement des promotions...');

  try {
    const data = await promotionService.getPromotions();
    console.log('Données reçues:', data);
    promotions.value = data || [];
    console.log('Promotions après assignment:', promotions.value);
  } catch (error) {
    console.error('Erreur lors du chargement:', error);
    promotions.value = [];
  } finally {
    loadingPromotions.value = false;
    console.log('Chargement terminé, loadingPromotions:', loadingPromotions.value);
  }
});
```

---

## Vérification de l'URL de l'API

Vérifiez que l'URL de base de l'API est correcte dans `src/services/api.ts` :

```typescript
const api = axios.create({
  baseURL: 'http://localhost:8000', // ou votre URL Django
  // ...
});
```

---

## Rechargement et cache

Parfois le cache du navigateur peut causer des problèmes :

1. **Rechargement forcé** : Ctrl + Shift + R (Windows/Linux) ou Cmd + Shift + R (Mac)
2. **Vider le cache** : F12 → Onglet Application → Clear storage → Clear site data
3. **Mode incognito** : Testez en mode navigation privée

---

## Checklist finale

- [ ] Serveur Django démarré sur http://localhost:8000
- [ ] Serveur Vite démarré sur http://localhost:5173 (ou autre port)
- [ ] `/api/core/promotions/` retourne du JSON
- [ ] Console du navigateur ne montre pas d'erreurs réseau
- [ ] Console du navigateur ne montre pas d'erreurs JavaScript
- [ ] Vue DevTools installé et fonctionnel
- [ ] Cache du navigateur vidé
