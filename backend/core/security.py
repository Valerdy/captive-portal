"""
Module de sécurité centralisé pour le portail captif.

Contient:
- Fix #1: Protection CSRF pour actions admin
- Fix #2: Rate limiting pour login admin
- Fix #3: Middleware de validation des paramètres sensibles
- Fix #8: Validation de complexité de mot de passe renforcée
- Fix #9: Validation des entrées pour opérations bulk
"""

import re
import hashlib
import logging
from functools import wraps
from typing import List, Optional, Any, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.utils import timezone

logger = logging.getLogger(__name__)


# =============================================================================
# FIX #1: CSRF Protection for Admin Actions
# =============================================================================

def csrf_protect_admin_action(func):
    """
    Décorateur pour protéger explicitement les actions admin avec CSRF.

    Django Admin protège déjà les actions via le middleware CSRF,
    mais ce décorateur ajoute une couche de vérification explicite.

    Usage:
        @admin.action(description="Mon action")
        @csrf_protect_admin_action
        def mon_action(self, request, queryset):
            ...
    """
    @wraps(func)
    @csrf_protect
    def wrapper(modeladmin, request, queryset, *args, **kwargs):
        # Vérifier que la requête vient bien d'un formulaire POST
        if request.method != 'POST':
            from django.contrib import messages
            messages.error(request, "Cette action nécessite une requête POST.")
            return None

        # Vérifier que le referer correspond au site
        referer = request.META.get('HTTP_REFERER', '')
        host = request.get_host()

        if referer and host not in referer:
            from django.contrib import messages
            messages.error(request, "Requête invalide: referer non autorisé.")
            logger.warning(
                f"CSRF protection: referer mismatch for admin action. "
                f"Host: {host}, Referer: {referer}, User: {request.user}"
            )
            return None

        return func(modeladmin, request, queryset, *args, **kwargs)

    return wrapper


# =============================================================================
# FIX #2: Rate Limiting for Admin Login
# =============================================================================

class AdminLoginRateLimiter:
    """
    Rate limiter spécifique pour la page de login admin.

    Protège contre les attaques brute-force sur /admin/login/.

    Configuration:
        - MAX_ATTEMPTS: Nombre max de tentatives avant blocage
        - BLOCK_DURATION: Durée du blocage en secondes
        - WINDOW: Fenêtre de temps pour compter les tentatives
    """

    MAX_ATTEMPTS = 5
    BLOCK_DURATION = 900  # 15 minutes
    WINDOW = 300  # 5 minutes

    @classmethod
    def get_client_ip(cls, request) -> str:
        """Récupère l'IP du client (gère les proxies)."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip

    @classmethod
    def get_cache_keys(cls, ip: str, username: str = None) -> Tuple[str, str, str]:
        """Génère les clés de cache pour le rate limiting."""
        ip_hash = hashlib.md5(ip.encode()).hexdigest()[:16]
        attempt_key = f"admin_login_attempts:{ip_hash}"
        block_key = f"admin_login_blocked:{ip_hash}"

        # Clé supplémentaire par username pour éviter le brute-force distribué
        user_key = None
        if username:
            user_hash = hashlib.md5(username.encode()).hexdigest()[:16]
            user_key = f"admin_login_user:{user_hash}"

        return attempt_key, block_key, user_key

    @classmethod
    def is_blocked(cls, request, username: str = None) -> Tuple[bool, int]:
        """
        Vérifie si l'IP/username est bloqué.

        Returns:
            Tuple (is_blocked, remaining_seconds)
        """
        ip = cls.get_client_ip(request)
        attempt_key, block_key, user_key = cls.get_cache_keys(ip, username)

        # Vérifier le blocage par IP
        if cache.get(block_key):
            ttl = cache.ttl(block_key) if hasattr(cache, 'ttl') else cls.BLOCK_DURATION
            return True, ttl or cls.BLOCK_DURATION

        # Vérifier le blocage par username
        if user_key and cache.get(f"{user_key}:blocked"):
            ttl = cache.ttl(f"{user_key}:blocked") if hasattr(cache, 'ttl') else cls.BLOCK_DURATION
            return True, ttl or cls.BLOCK_DURATION

        return False, 0

    @classmethod
    def record_attempt(cls, request, username: str = None, success: bool = False):
        """
        Enregistre une tentative de connexion.

        Args:
            request: Requête HTTP
            username: Nom d'utilisateur tenté
            success: True si connexion réussie
        """
        ip = cls.get_client_ip(request)
        attempt_key, block_key, user_key = cls.get_cache_keys(ip, username)

        if success:
            # Réinitialiser les compteurs en cas de succès
            cache.delete(attempt_key)
            if user_key:
                cache.delete(user_key)
            logger.info(f"Admin login success: {username} from {ip}")
            return

        # Incrémenter le compteur d'échecs par IP
        attempts = cache.get(attempt_key, 0)
        attempts += 1
        cache.set(attempt_key, attempts, cls.WINDOW)

        # Incrémenter le compteur par username
        if user_key:
            user_attempts = cache.get(user_key, 0)
            user_attempts += 1
            cache.set(user_key, user_attempts, cls.WINDOW)

            # Blocage par username si trop de tentatives
            if user_attempts >= cls.MAX_ATTEMPTS:
                cache.set(f"{user_key}:blocked", True, cls.BLOCK_DURATION)
                logger.warning(
                    f"Admin login rate limit: username '{username}' blocked for "
                    f"{cls.BLOCK_DURATION}s after {user_attempts} attempts"
                )

        # Blocage par IP si trop de tentatives
        if attempts >= cls.MAX_ATTEMPTS:
            cache.set(block_key, True, cls.BLOCK_DURATION)
            logger.warning(
                f"Admin login rate limit: IP {ip} blocked for "
                f"{cls.BLOCK_DURATION}s after {attempts} attempts"
            )

    @classmethod
    def get_remaining_attempts(cls, request, username: str = None) -> int:
        """Retourne le nombre de tentatives restantes."""
        ip = cls.get_client_ip(request)
        attempt_key, _, user_key = cls.get_cache_keys(ip, username)

        ip_attempts = cache.get(attempt_key, 0)
        user_attempts = cache.get(user_key, 0) if user_key else 0

        max_attempts = max(ip_attempts, user_attempts)
        return max(0, cls.MAX_ATTEMPTS - max_attempts)


class AdminLoginRateLimitMiddleware:
    """
    Middleware pour limiter les tentatives de connexion admin.

    À ajouter dans settings.MIDDLEWARE après AuthenticationMiddleware.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier uniquement pour la page de login admin
        if request.path == '/admin/login/' and request.method == 'POST':
            username = request.POST.get('username', '')

            is_blocked, remaining = AdminLoginRateLimiter.is_blocked(request, username)

            if is_blocked:
                logger.warning(
                    f"Blocked admin login attempt from {AdminLoginRateLimiter.get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'Trop de tentatives de connexion',
                    'detail': f'Veuillez réessayer dans {remaining} secondes.',
                    'retry_after': remaining
                }, status=429)

        response = self.get_response(request)

        # Après la réponse, enregistrer le résultat
        if request.path == '/admin/login/' and request.method == 'POST':
            username = request.POST.get('username', '')
            # Si redirection vers /admin/, c'est un succès
            success = (
                response.status_code == 302 and
                '/admin/' in response.get('Location', '') and
                '/login/' not in response.get('Location', '')
            )
            AdminLoginRateLimiter.record_attempt(request, username, success)

        return response


# =============================================================================
# FIX #8: Enhanced Password Complexity Validation
# =============================================================================

class EnhancedPasswordValidator:
    """
    Validateur de mot de passe renforcé.

    Combine les validateurs Django avec des règles supplémentaires:
    - Longueur minimale: 8 caractères
    - Au moins une majuscule
    - Au moins une minuscule
    - Au moins un chiffre
    - Au moins un caractère spécial
    - Pas de séquences courantes (123, abc, etc.)
    """

    MIN_LENGTH = 8
    SPECIAL_CHARS = r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]'

    # Séquences courantes à bloquer
    COMMON_SEQUENCES = [
        '123456', '654321', 'abcdef', 'fedcba', 'qwerty', 'azerty',
        'password', 'motdepasse', '111111', '000000', 'aaaaaa'
    ]

    @classmethod
    def validate(cls, password: str, user=None) -> List[str]:
        """
        Valide un mot de passe et retourne la liste des erreurs.

        Args:
            password: Mot de passe à valider
            user: Instance utilisateur (optionnel)

        Returns:
            Liste des messages d'erreur (vide si valide)
        """
        errors = []

        if not password:
            return ["Le mot de passe est requis."]

        # Longueur minimale
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Le mot de passe doit contenir au moins {cls.MIN_LENGTH} caractères.")

        # Majuscule requise
        if not re.search(r'[A-Z]', password):
            errors.append("Le mot de passe doit contenir au moins une majuscule.")

        # Minuscule requise
        if not re.search(r'[a-z]', password):
            errors.append("Le mot de passe doit contenir au moins une minuscule.")

        # Chiffre requis
        if not re.search(r'\d', password):
            errors.append("Le mot de passe doit contenir au moins un chiffre.")

        # Caractère spécial requis
        if not re.search(cls.SPECIAL_CHARS, password):
            errors.append("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*...).")

        # Vérifier les séquences courantes
        password_lower = password.lower()
        for seq in cls.COMMON_SEQUENCES:
            if seq in password_lower:
                errors.append(f"Le mot de passe contient une séquence trop courante ({seq[:3]}...).")
                break

        # Utiliser aussi les validateurs Django
        try:
            validate_password(password, user)
        except ValidationError as e:
            errors.extend(e.messages)

        return list(set(errors))  # Dédupliquer

    @classmethod
    def is_valid(cls, password: str, user=None) -> bool:
        """Vérifie si le mot de passe est valide."""
        return len(cls.validate(password, user)) == 0

    @classmethod
    def get_requirements(cls) -> dict:
        """Retourne les exigences de mot de passe pour l'affichage UI."""
        return {
            'min_length': cls.MIN_LENGTH,
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digit': True,
            'require_special': True,
            'special_chars': '!@#$%^&*(),.?":{}|<>_-+=[]\\\/~`',
            'message': (
                f"Le mot de passe doit contenir au moins {cls.MIN_LENGTH} caractères, "
                "une majuscule, une minuscule, un chiffre et un caractère spécial."
            )
        }


# =============================================================================
# FIX #9: Bulk Operation Input Validation
# =============================================================================

class BulkOperationValidator:
    """
    Validateur pour les opérations en masse.

    Assure que les entrées sont valides avant traitement:
    - IDs sont des entiers positifs
    - Taille de lot respecte les limites
    - Pas de valeurs nulles ou invalides
    """

    MAX_BULK_SIZE = 100

    @classmethod
    def validate_ids(
        cls,
        ids: Any,
        field_name: str = 'ids',
        max_size: int = None
    ) -> Tuple[List[int], List[str]]:
        """
        Valide une liste d'IDs.

        Args:
            ids: Liste d'IDs à valider
            field_name: Nom du champ pour les messages d'erreur
            max_size: Taille maximale (défaut: MAX_BULK_SIZE)

        Returns:
            Tuple (valid_ids, errors)
        """
        errors = []
        valid_ids = []
        max_size = max_size or cls.MAX_BULK_SIZE

        # Vérifier que c'est une liste
        if ids is None:
            return [], [f"Le champ '{field_name}' est requis."]

        if not isinstance(ids, list):
            return [], [f"Le champ '{field_name}' doit être une liste."]

        # Vérifier la taille
        if len(ids) == 0:
            return [], [f"Le champ '{field_name}' ne peut pas être vide."]

        if len(ids) > max_size:
            errors.append(f"Maximum {max_size} éléments par opération (reçu: {len(ids)}).")

        # Valider chaque ID
        seen_ids = set()
        for i, id_value in enumerate(ids[:max_size]):  # Limiter au max
            # Vérifier le type
            if id_value is None:
                errors.append(f"ID à l'index {i} est null.")
                continue

            # Convertir en entier si possible
            try:
                if isinstance(id_value, str):
                    id_int = int(id_value)
                elif isinstance(id_value, (int, float)):
                    id_int = int(id_value)
                else:
                    errors.append(f"ID à l'index {i} n'est pas un nombre valide: {type(id_value).__name__}")
                    continue
            except (ValueError, TypeError):
                errors.append(f"ID à l'index {i} n'est pas un nombre valide: '{id_value}'")
                continue

            # Vérifier que c'est positif
            if id_int <= 0:
                errors.append(f"ID à l'index {i} doit être positif: {id_int}")
                continue

            # Vérifier les doublons
            if id_int in seen_ids:
                errors.append(f"ID en doublon: {id_int}")
                continue

            seen_ids.add(id_int)
            valid_ids.append(id_int)

        return valid_ids, errors

    @classmethod
    def validate_bulk_request(
        cls,
        data: dict,
        id_field: str = 'ids',
        required_fields: List[str] = None,
        max_size: int = None
    ) -> Tuple[dict, List[str]]:
        """
        Valide une requête d'opération bulk complète.

        Args:
            data: Données de la requête
            id_field: Nom du champ contenant les IDs
            required_fields: Champs requis supplémentaires
            max_size: Taille maximale

        Returns:
            Tuple (validated_data, errors)
        """
        errors = []
        validated = {}

        # Valider les IDs
        ids = data.get(id_field)
        valid_ids, id_errors = cls.validate_ids(ids, id_field, max_size)
        errors.extend(id_errors)
        validated[id_field] = valid_ids

        # Valider les champs requis
        if required_fields:
            for field in required_fields:
                value = data.get(field)
                if value is None or value == '':
                    errors.append(f"Le champ '{field}' est requis.")
                else:
                    validated[field] = value

        return validated, errors


# =============================================================================
# FIX #3: Sensitive Data Protection Middleware
# =============================================================================

class SensitiveDataProtectionMiddleware:
    """
    Middleware pour protéger les données sensibles.

    - Bloque les requêtes avec mots de passe dans les paramètres GET
    - Log les tentatives suspectes
    - Nettoie les données sensibles des logs
    """

    SENSITIVE_PARAMS = [
        'password', 'passwd', 'pwd', 'secret', 'token', 'api_key',
        'apikey', 'auth', 'credential', 'cleartext_password'
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Vérifier les paramètres GET pour données sensibles
        for param in self.SENSITIVE_PARAMS:
            if param in request.GET:
                logger.warning(
                    f"Sensitive data in GET params blocked: "
                    f"param={param}, path={request.path}, "
                    f"ip={self._get_client_ip(request)}"
                )
                return JsonResponse({
                    'error': 'Requête invalide',
                    'detail': 'Les données sensibles ne peuvent pas être transmises via URL.'
                }, status=400)

        return self.get_response(request)

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


# =============================================================================
# Utility Functions
# =============================================================================

def sanitize_log_data(data: dict, sensitive_fields: List[str] = None) -> dict:
    """
    Nettoie les données sensibles avant logging.

    Args:
        data: Dictionnaire à nettoyer
        sensitive_fields: Champs à masquer (défaut: mots de passe, tokens)

    Returns:
        Dictionnaire avec données sensibles masquées
    """
    if sensitive_fields is None:
        sensitive_fields = [
            'password', 'cleartext_password', 'token', 'secret',
            'api_key', 'refresh_token', 'access_token'
        ]

    if not isinstance(data, dict):
        return data

    sanitized = {}
    for key, value in data.items():
        key_lower = key.lower()

        if any(s in key_lower for s in sensitive_fields):
            sanitized[key] = '***REDACTED***'
        elif isinstance(value, dict):
            sanitized[key] = sanitize_log_data(value, sensitive_fields)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_log_data(item, sensitive_fields) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value

    return sanitized
