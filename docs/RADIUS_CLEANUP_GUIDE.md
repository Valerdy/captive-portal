# Guide de nettoyage des entrées RADIUS orphelines

## Problème

Lorsque vous activez une promotion, vous voyez des utilisateurs qui n'existent pas dans votre base de données (comme "EUIN030" avec l'ID 27). Ceci arrive quand:

1. Des utilisateurs ont été créés dans RADIUS (tables `radcheck`, `radreply`, `radusergroup`)
2. Ces utilisateurs ont été supprimés de la table `User` de Django
3. Mais leurs entrées RADIUS n'ont pas été supprimées (pas de cascade delete)
4. Ces "entrées orphelines" restent dans la base et peuvent causer des problèmes

## Solution

Un script de nettoyage a été créé pour supprimer automatiquement toutes les entrées RADIUS orphelines.

### Étape 1: Mode test (DRY-RUN)

D'abord, exécutez le script en mode test pour voir quelles entrées seront supprimées **sans les supprimer réellement**:

```bash
cd /home/user/captive-portal/backend
python manage.py cleanup_orphaned_radius_entries --dry-run
```

Ce mode vous montrera:
- Combien d'utilisateurs valides existent dans votre table User
- Tous les usernames orphelins trouvés dans les tables RADIUS
- Le nombre d'entrées orphelines dans chaque table (radcheck, radreply, radusergroup)
- Un exemple des premières entrées qui seraient supprimées

**Exemple de sortie:**

```
======================================================================
NETTOYAGE DES ENTRÉES RADIUS ORPHELINES
======================================================================

🔍 MODE DRY-RUN: Aucune donnée ne sera supprimée

✓ 15 utilisateurs valides trouvés dans User

[1/3] Analyse de RadCheck...
  ⚠️  3 entrées orphelines trouvées:
      - EUIN030: Cleartext-Password := motdepasse123
      - EUIN030: Simultaneous-Use := 1
      - OLD_USER: Cleartext-Password := pass456

[2/3] Analyse de RadReply...
  ⚠️  2 entrées orphelines trouvées:
      - EUIN030: Session-Timeout = 3600
      - OLD_USER: Session-Timeout = 7200

[3/3] Analyse de RadUserGroup...
  ⚠️  2 entrées orphelines trouvées:
      - EUIN030 -> groupe: student
      - OLD_USER -> groupe: student

📋 2 utilisateur(s) orphelin(s) détecté(s):
    - EUIN030
    - OLD_USER

💡 Exécutez sans --dry-run pour supprimer ces entrées
```

### Étape 2: Nettoyage réel

Si vous êtes satisfait de ce qui sera supprimé, exécutez le script **sans** `--dry-run`:

```bash
python manage.py cleanup_orphaned_radius_entries
```

Le script vous demandera confirmation avant de supprimer:

```
⚠️  Confirmer la suppression de 2 utilisateur(s) orphelin(s)? (yes/no):
```

Tapez `yes` pour confirmer la suppression.

**Exemple de sortie après suppression:**

```
🗑️  Suppression en cours...

  ✓ RadCheck: 3 entrées supprimées
  ✓ RadReply: 2 entrées supprimées
  ✓ RadUserGroup: 2 entrées supprimées

✅ Nettoyage terminé avec succès!
📊 Total: 7 entrées supprimées
```

### Étape 3: Vérification

Après le nettoyage, vous pouvez:

1. Réexécuter le script en mode dry-run pour vérifier qu'il ne reste plus d'orphelins:
   ```bash
   python manage.py cleanup_orphaned_radius_entries --dry-run
   ```

   Vous devriez voir: `✅ Aucune entrée orpheline trouvée! Base de données propre.`

2. Tester à nouveau l'activation d'une promotion dans l'interface admin

## Sécurité

- Le script utilise une **transaction atomique**: si une erreur se produit, toutes les suppressions sont annulées
- Le mode **dry-run** vous permet de vérifier avant de supprimer
- Une **confirmation explicite** est requise avant toute suppression
- Seules les entrées **sans utilisateur correspondant** dans la table User sont supprimées

## Quand utiliser ce script

Utilisez ce script:
- ✅ Après avoir supprimé manuellement des utilisateurs de la base de données
- ✅ Avant une migration importante
- ✅ Quand vous voyez des utilisateurs inexistants apparaître lors de l'activation
- ✅ Pour nettoyer périodiquement votre base RADIUS

## Prévention

Pour éviter ce problème à l'avenir:

1. **Toujours supprimer les utilisateurs via l'API/Admin Django** plutôt que directement en SQL
2. Le code d'activation vérifie déjà `user.cleartext_password` avant de créer les entrées RADIUS
3. Lors de la suppression d'un utilisateur, ses entrées RADIUS devraient être supprimées automatiquement (à améliorer avec des signals Django)

## Fichier du script

Le script se trouve dans:
```
/home/user/captive-portal/backend/core/management/commands/cleanup_orphaned_radius_entries.py
```

## Support

Si vous rencontrez des problèmes:
1. Vérifiez que votre environnement virtuel est activé
2. Vérifiez que vous êtes dans le bon répertoire (`backend/`)
3. Vérifiez les logs du script pour identifier l'erreur
4. En cas de doute, utilisez toujours `--dry-run` d'abord
