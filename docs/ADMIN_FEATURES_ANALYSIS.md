# Analyse des fonctionnalités Admin - Problèmes et Erreurs

**Date:** 2025-12-10
**Projet:** Captive Portal (UCAC-ICAM)
**Portée:** Fonctionnalités d'administration Backend + Frontend

---

## 🔴 PROBLÈMES DE SÉCURITÉ CRITIQUES

### 1. **Stockage de mots de passe en clair** ⚠️ CRITIQUE

**Fichier:** `backend/core/models.py:48-53`

**Problème:**
Le champ `cleartext_password` stocke les mots de passe utilisateur en clair dans la base de données Django, pour permettre leur copie dans la table RADIUS `radcheck`.

```python
cleartext_password = models.CharField(
    max_length=128,
    blank=True,
    null=True,
    help_text="Mot de passe en clair (UNIQUEMENT pour activation RADIUS - RISQUE DE SÉCURITÉ)"
)
```

**Risques:**
- ❌ Si la base de données est compromise, **TOUS les mots de passe** sont exposés
- ❌ Violation des standards de sécurité (OWASP, GDPR, PCI-DSS)
- ❌ Les utilisateurs réutilisant le même mot de passe ailleurs sont vulnérables
- ❌ Impossibilité d'obtenir des certifications de sécurité

**Impact:** CRITIQUE - Compromission potentielle de tous les comptes utilisateurs

**Recommandation:**
- Utiliser un algorithme de hachage compatible avec RADIUS (MD5, SHA1) au lieu du stockage en clair
- Implémenter le chiffrement au niveau base de données si le stockage en clair est absolument nécessaire
- Ajouter un audit trail pour toute consultation de ce champ

---

### 2. **Absence de rate limiting sur certains endpoints admin**

**Fichiers concernés:**
- `backend/core/views.py:346` - `monitoring_metrics()` n'a pas de rate limiting
- `backend/core/viewsets.py` - Actions RADIUS sans rate limiting

**Problème:**
Certains endpoints admin sensibles ne sont pas protégés par rate limiting, permettant:
- Énumération d'informations système via monitoring
- Abus des actions d'activation/désactivation RADIUS

**Recommandation:**
Ajouter `@rate_limit()` sur tous les endpoints admin sensibles

---

## 🟠 PROBLÈMES FONCTIONNELS MAJEURS

### 3. **Duplication du PromotionViewSet** ❌ BUG

**Fichier:** `backend/core/viewsets.py`

**Problème:**
Le fichier contient **DEUX définitions** de `PromotionViewSet`:
- Ligne 17-118: Première définition (incomplète, pas de `serializer_class`)
- Ligne 423-456: Deuxième définition (avec `serializer_class`)

```python
# PREMIÈRE DÉFINITION (ligne 17)
class PromotionViewSet(viewsets.ModelViewSet):
    """ViewSet for Promotion model"""
    queryset = Promotion.objects.all()
    permission_classes = [IsAdmin]

    def get_serializer_class(self):
        if self.action == 'list':
            return PromotionListSerializer  # PromotionListSerializer n'existe pas!
        return PromotionSerializer

# DEUXIÈME DÉFINITION (ligne 423) - ÉCRASE LA PREMIÈRE
class PromotionViewSet(viewsets.ModelViewSet):
    """ViewSet pour gérer les promotions..."""
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAdmin]
```

**Impact:**
- ⚠️ La première définition est ignorée (écrasée par la seconde)
- ⚠️ Les actions `activate_users`, `deactivate_users`, `toggle_status` de la première définition sont PERDUES
- ⚠️ Le frontend appelle probablement des endpoints qui n'existent plus
- ⚠️ Référence à `PromotionListSerializer` qui n'est pas importé

**Recommandation:**
- Fusionner les deux ViewSets en un seul
- Importer et définir `PromotionListSerializer` ou utiliser `PromotionSerializer` partout
- Vérifier que toutes les actions sont présentes dans la version finale

---

### 4. **Erreur dans le formulaire d'ajout d'utilisateur** ❌ BUG

**Fichier:** `frontend/portail-captif/src/views/AdminUsersView.vue:261`

**Problème:**
Le code fait référence à `newUser.value.promotion_id` qui **n'existe pas** dans l'objet `newUser`:

```typescript
// Ligne 41-48: Définition de newUser
const newUser = ref({
  password: '',
  password2: '',
  first_name: '',
  last_name: '',
  promotion: null as number | null,  // ❌ Le champ s'appelle "promotion", pas "promotion_id"
  matricule: '',
  is_staff: false
})

// Ligne 261: Utilisation incorrecte
if (!newUser.value.promotion_id || ...) {  // ❌ ERREUR: promotion_id n'existe pas
  // ...
}
```

**Impact:**
- ❌ La validation échoue systématiquement
- ❌ Impossible d'ajouter un utilisateur depuis l'interface admin

**Correction:**
```typescript
// Remplacer ligne 261:
if (!newUser.value.promotion || ...)
```

---

### 5. **Logique contradictoire dans l'activation par promotion** ⚠️

**Fichier:** `backend/core/viewsets.py:31`

**Problème:**
La fonction `activate_users` filtre les utilisateurs **déjà activés** (`is_radius_activated=True`) au lieu de ceux **à activer**:

```python
def activate_users(self, request, pk=None):
    """Activer tous les utilisateurs d'une promotion dans RADIUS"""
    promotion = self.get_object()
    users = promotion.users.filter(is_active=True, is_radius_activated=True)  # ❌ Logique inversée
```

**Impact:**
- ⚠️ Tente d'activer des utilisateurs déjà activés
- ⚠️ Ne cible pas les bons utilisateurs

**Correction probable:**
```python
# Si l'objectif est d'activer les utilisateurs en attente:
users = promotion.users.filter(is_active=True, is_radius_activated=False)

# OU si l'objectif est de réactiver (changer le statut):
users = promotion.users.filter(is_active=True, is_radius_activated=True)
# Mais alors renommer la fonction en `enable_users` ou `toggle_users_status`
```

---

### 6. **Méthodes dupliquées dans le service utilisateur** ❌ BUG

**Fichier:** `frontend/portail-captif/src/services/user.service.ts`

**Problème:**
Deux paires de méthodes sont définies deux fois avec des commentaires légèrement différents:

```typescript
// PREMIÈRE DÉFINITION (lignes 61-72)
async activateUserRadius(userId: number): Promise<void> { ... }
async deactivateUserRadius(userId: number): Promise<void> { ... }

// DEUXIÈME DÉFINITION (lignes 90-102) - ÉCRASE LA PREMIÈRE
async activateUserRadius(userId: number): Promise<any> { ... }
async deactivateUserRadius(userId: number): Promise<any> { ... }
```

**Impact:**
- ⚠️ Confusion dans le code
- ⚠️ La première définition est inutile (écrasée)
- ⚠️ Type de retour incohérent (`void` vs `any`)

**Recommandation:**
Supprimer les définitions dupliquées (lignes 61-72) et conserver uniquement la version finale

---

## 🟡 PROBLÈMES D'ARCHITECTURE ET DE CONCEPTION

### 7. **Gestion confuse des états RADIUS**

**Fichiers:** `backend/core/models.py`, `backend/core/viewsets.py`

**Problème:**
Deux champs booléens gèrent l'état RADIUS avec une sémantique floue:

```python
is_radius_activated = models.BooleanField(default=False,
    help_text="Utilisateur activé dans RADIUS par un administrateur")
is_radius_enabled = models.BooleanField(default=True,
    help_text="Utilisateur activé/désactivé dans RADIUS (contrôle l'accès Internet)")
```

**Confusion:**
- ❓ `is_radius_activated=True` signifie que l'utilisateur a été créé dans RADIUS (une seule fois)
- ❓ `is_radius_enabled=True/False` signifie que l'utilisateur peut/ne peut pas se connecter
- ⚠️ Un utilisateur peut être `is_radius_activated=True` mais `is_radius_enabled=False`
- ⚠️ La logique n'est pas clairement documentée
- ⚠️ Risque d'incohérence entre les deux états

**Impact:**
- Confusion pour les développeurs et les administrateurs
- Risque d'erreurs dans la gestion des accès
- Difficulté de maintenance

**Recommandation:**
- Renommer pour clarifier: `is_created_in_radius` et `radius_access_enabled`
- Documenter clairement le cycle de vie d'un utilisateur RADIUS
- Ajouter une méthode `can_access_radius()` qui vérifie les deux conditions

---

### 8. **Absence de transactions atomiques complètes**

**Fichier:** `backend/core/views.py:456-550`

**Problème:**
L'activation RADIUS utilise une transaction mais pas la totalité du processus d'activation/désactivation par promotion:

```python
# views.py:457 - Activation individuelle avec transaction ✅
with transaction.atomic():
    user = User.objects.select_for_update().get(id=user_id)
    # ... modifications RADIUS + User

# viewsets.py:38-51 - Activation par promotion SANS transaction ❌
for user in users:
    try:
        radcheck_entries = RadCheck.objects.filter(username=user.username)
        radcheck_entries.update(statut=True)  # Pas de transaction globale
        user.is_radius_enabled = True
        user.save()
```

**Risque:**
- ⚠️ En cas d'erreur pendant le processus, certains utilisateurs peuvent être partiellement activés
- ⚠️ Incohérence entre `radcheck` et la table `users`

**Recommandation:**
Utiliser `transaction.atomic()` pour toutes les opérations de modification RADIUS

---

### 9. **Gestion inadéquate de la dépendance psutil**

**Fichier:** `backend/core/views.py:21-25, 352-361`

**Problème:**
Le monitoring système dépend de `psutil`, mais en son absence retourne simplement `0`:

```python
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Dans monitoring_metrics():
if PSUTIL_AVAILABLE:
    cpu_usage = psutil.cpu_percent(interval=0.1)
    memory_usage = memory.percent
else:
    cpu_usage = 0  # ❌ Valeur trompeuse
    memory_usage = 0
```

**Problème:**
- ⚠️ `0%` est une valeur valide qui peut être confondue avec "pas de charge"
- ⚠️ Le frontend affiche un warning mais les graphiques montrent quand même `0%`
- ⚠️ Pas de vérification au démarrage de l'application

**Recommandation:**
- Retourner `null` au lieu de `0` si psutil n'est pas disponible
- Ajouter une vérification au démarrage Django
- Documenter `psutil` comme dépendance obligatoire dans requirements.txt

---

## 🟢 PROBLÈMES MINEURS D'UX/UI

### 10. **Sélecteur de promotion sans promotions actives**

**Fichier:** `frontend/portail-captif/src/views/AdminUsersView.vue:786-795`

**Problème:**
Si aucune promotion n'est active, le sélecteur est vide sans message explicite:

```html
<select v-model="newUser.promotion" required>
  <option value="" disabled>Choisir une promotion</option>
  <option v-for="promo in promotions" :key="promo.id" :value="promo.id">
    {{ promo.name }}
  </option>
</select>
```

`promotions` est filtré par `is_active=true` (ligne 50), donc peut être vide.

**Recommandation:**
Ajouter un message si `promotions.length === 0`:
```html
<option v-if="promotions.length === 0" disabled>Aucune promotion active disponible</option>
```

---

### 11. **Pas de confirmation avant les actions de suppression en masse**

**Fichier:** `frontend/portail-captif/src/views/AdminUsersView.vue:409`

**Problème:**
La sélection multiple permet d'activer plusieurs utilisateurs avec une simple confirmation `confirm()`, mais il n'y a pas de vue récapitulative avant l'action.

**Recommandation:**
- Afficher une modale avec la liste des utilisateurs sélectionnés avant l'activation
- Ajouter un résumé des impacts (nombre d'utilisateurs, promotions concernées)

---

### 12. **Pas de feedback lors du chargement des opérations longues**

**Fichier:** `frontend/portail-captif/src/views/AdminUsersView.vue`

**Problème:**
Lors de l'activation de plusieurs utilisateurs, seul un booléen `isActivating` est utilisé, mais pas de progression visible.

**Recommandation:**
- Ajouter une barre de progression pour les opérations par lot
- Afficher le nombre d'utilisateurs traités en temps réel

---

## 📊 RÉSUMÉ DES PROBLÈMES PAR CRITICITÉ

| Criticité | Nombre | Détail |
|-----------|--------|--------|
| 🔴 **CRITIQUE** | 1 | Stockage mot de passe en clair |
| 🟠 **MAJEUR** | 5 | Bugs fonctionnels, duplication code, logique incorrecte |
| 🟡 **MOYEN** | 3 | Architecture, transactions, dépendances |
| 🟢 **MINEUR** | 3 | UX/UI, feedback utilisateur |
| **TOTAL** | **12** | |

---

## 🔧 PLAN D'ACTION RECOMMANDÉ

### Phase 1: Correctifs critiques (Priorité IMMÉDIATE)
1. ✅ Implémenter une solution de chiffrement pour `cleartext_password`
2. ✅ Corriger la duplication du `PromotionViewSet`
3. ✅ Corriger le bug du formulaire d'ajout d'utilisateur (`promotion_id` → `promotion`)
4. ✅ Supprimer les méthodes dupliquées dans `user.service.ts`

### Phase 2: Corrections majeures (Priorité HAUTE)
5. ✅ Clarifier la logique `is_radius_activated` vs `is_radius_enabled`
6. ✅ Corriger la logique d'activation par promotion
7. ✅ Ajouter rate limiting sur tous les endpoints admin
8. ✅ Implémenter des transactions atomiques complètes

### Phase 3: Améliorations (Priorité MOYENNE)
9. ✅ Améliorer la gestion de la dépendance psutil
10. ✅ Ajouter des feedbacks UX pour les opérations longues
11. ✅ Améliorer les confirmations et validations frontend

### Phase 4: Documentation et tests
12. ✅ Documenter le cycle de vie RADIUS
13. ✅ Ajouter des tests unitaires pour les fonctionnalités admin critiques
14. ✅ Créer un guide d'utilisation admin

---

## 📝 NOTES COMPLÉMENTAIRES

### Fichiers concernés à modifier en priorité:
- `backend/core/models.py` (sécurité mots de passe)
- `backend/core/viewsets.py` (duplication PromotionViewSet)
- `backend/core/views.py` (rate limiting)
- `frontend/portail-captif/src/views/AdminUsersView.vue` (bug promotion_id)
- `frontend/portail-captif/src/services/user.service.ts` (duplication méthodes)

### Points d'attention pour les tests:
- Tester l'activation/désactivation RADIUS avec et sans transactions
- Tester les cas limites (promotions vides, utilisateurs déjà activés)
- Tester le comportement sans psutil installé
- Tester les permissions admin sur tous les endpoints

---

**Rapport généré le:** 2025-12-10
**Analysé par:** Claude Code (Sonnet 4.5)
**Fichiers analysés:** 8 fichiers backend + 5 fichiers frontend
