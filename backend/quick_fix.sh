#!/bin/bash

echo "=========================================="
echo "SCRIPT DE RÉPARATION RAPIDE"
echo "=========================================="
echo ""

# Couleurs
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonction pour afficher les étapes
step() {
    echo -e "${YELLOW}[ÉTAPE]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

error() {
    echo -e "${RED}[ERREUR]${NC} $1"
}

# Étape 1 : Appliquer les migrations
step "Application des migrations..."
python manage.py migrate
if [ $? -eq 0 ]; then
    success "Migrations appliquées"
else
    error "Échec des migrations"
    exit 1
fi

echo ""

# Étape 2 : Initialiser les promotions
step "Initialisation des promotions..."
python init_promotions.py
if [ $? -eq 0 ]; then
    success "Promotions initialisées"
else
    error "Échec de l'initialisation des promotions"
fi

echo ""

# Étape 3 : Vérifier le système
step "Vérification du système..."
python check_system.py

echo ""
echo "=========================================="
echo "SCRIPT TERMINÉ"
echo "=========================================="
echo ""
echo "Prochaines étapes :"
echo "1. Redémarrez le serveur Django : python manage.py runserver"
echo "2. Rechargez la page admin dans votre navigateur"
echo "3. Essayez de créer un utilisateur"
