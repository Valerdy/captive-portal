"""
Service de notifications pour le portail captif.

Ce service gère l'envoi de notifications aux utilisateurs via différents canaux:
- Email (Django mail)
- SMS (via API externe - configurable)
- Notifications système (stockées en base)

Configuration dans settings.py:
    NOTIFICATION_CONFIG = {
        'EMAIL_ENABLED': True,
        'SMS_ENABLED': False,
        'SMS_API_URL': 'https://api.sms-provider.com/send',
        'SMS_API_KEY': 'your-api-key',
        'FROM_EMAIL': 'noreply@captive-portal.local',
        'ADMIN_EMAIL': 'admin@captive-portal.local',
    }
"""

from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from typing import Optional, Dict, Any, List
import logging
import requests

logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service principal pour l'envoi de notifications multi-canaux.

    Méthodes principales:
    - send_alert(): Envoie une alerte de quota/expiration
    - send_notification(): Envoie une notification générique
    - send_email(): Envoie un email
    - send_sms(): Envoie un SMS
    - send_system_notification(): Crée une notification système
    """

    # Configuration par défaut
    DEFAULT_CONFIG = {
        'EMAIL_ENABLED': True,
        'SMS_ENABLED': False,
        'SYSTEM_ENABLED': True,
        'SMS_API_URL': '',
        'SMS_API_KEY': '',
        'FROM_EMAIL': 'noreply@captive-portal.local',
        'ADMIN_EMAIL': 'admin@captive-portal.local',
    }

    # Templates de messages par type d'alerte
    ALERT_TEMPLATES = {
        'quota_warning': {
            'subject': 'Attention: Votre quota approche de la limite',
            'template': 'notifications/quota_warning.html',
            'sms_template': (
                "Captive Portal: Vous avez utilisé {percent}% de votre quota. "
                "Il vous reste {remaining_gb} Go."
            ),
        },
        'quota_critical': {
            'subject': 'URGENT: Votre quota est presque épuisé',
            'template': 'notifications/quota_critical.html',
            'sms_template': (
                "URGENT Captive Portal: {percent}% de quota utilisé! "
                "Reste: {remaining_gb} Go. Votre accès sera bientôt suspendu."
            ),
        },
        'quota_exceeded': {
            'subject': 'Votre quota est épuisé - Accès suspendu',
            'template': 'notifications/quota_exceeded.html',
            'sms_template': (
                "Captive Portal: Votre quota est épuisé. "
                "Votre accès WiFi a été suspendu. Contactez l'administrateur."
            ),
        },
        'expiry_warning': {
            'subject': 'Votre abonnement expire bientôt',
            'template': 'notifications/expiry_warning.html',
            'sms_template': (
                "Captive Portal: Votre abonnement expire dans {days_remaining} jours. "
                "Pensez à le renouveler."
            ),
        },
        'expiry_imminent': {
            'subject': 'URGENT: Votre abonnement expire demain',
            'template': 'notifications/expiry_imminent.html',
            'sms_template': (
                "URGENT: Votre abonnement Captive Portal expire dans {days_remaining} jour(s)!"
            ),
        },
        'account_activated': {
            'subject': 'Votre compte WiFi a été activé',
            'template': 'notifications/account_activated.html',
            'sms_template': (
                "Bienvenue! Votre compte WiFi Captive Portal a été activé. "
                "Vous pouvez maintenant vous connecter."
            ),
        },
        'account_suspended': {
            'subject': 'Votre accès WiFi a été suspendu',
            'template': 'notifications/account_suspended.html',
            'sms_template': (
                "Captive Portal: Votre accès WiFi a été suspendu. "
                "Raison: {reason}. Contactez l'administrateur."
            ),
        },
        'account_reactivated': {
            'subject': 'Votre accès WiFi a été rétabli',
            'template': 'notifications/account_reactivated.html',
            'sms_template': (
                "Captive Portal: Votre accès WiFi a été rétabli. "
                "Vous pouvez maintenant vous connecter."
            ),
        },
    }

    @classmethod
    def get_config(cls) -> dict:
        """Récupère la configuration des notifications."""
        config = cls.DEFAULT_CONFIG.copy()
        config.update(getattr(settings, 'NOTIFICATION_CONFIG', {}))
        return config

    @classmethod
    def send_alert(cls, user, alert, usage) -> Dict[str, Any]:
        """
        Envoie une alerte de quota/expiration à un utilisateur.

        Args:
            user: Instance User Django
            alert: Instance ProfileAlert
            usage: Instance UserProfileUsage

        Returns:
            Dict avec le résultat de l'envoi
        """
        profile = user.get_effective_profile()

        # Calculer les métriques
        context = cls._build_alert_context(user, profile, usage, alert)

        results = {
            'user': user.username,
            'alert_type': alert.alert_type,
            'methods': [],
            'success': False
        }

        # Envoyer selon la méthode configurée
        notification_method = alert.notification_method

        if notification_method in ('email', 'all'):
            email_result = cls._send_alert_email(user, alert, context)
            results['methods'].append({'type': 'email', **email_result})

        if notification_method in ('sms', 'all'):
            sms_result = cls._send_alert_sms(user, alert, context)
            results['methods'].append({'type': 'sms', **sms_result})

        if notification_method in ('system', 'all'):
            system_result = cls._send_system_notification(user, alert, context)
            results['methods'].append({'type': 'system', **system_result})

        # Succès si au moins une méthode a fonctionné
        results['success'] = any(m.get('success') for m in results['methods'])

        return results

    @classmethod
    def send_notification(
        cls,
        user,
        notification_type: str,
        context: Dict[str, Any] = None,
        methods: List[str] = None
    ) -> Dict[str, Any]:
        """
        Envoie une notification générique à un utilisateur.

        Args:
            user: Instance User Django
            notification_type: Type de notification (clé dans ALERT_TEMPLATES)
            context: Contexte additionnel pour le template
            methods: Liste des méthodes d'envoi ['email', 'sms', 'system']

        Returns:
            Dict avec le résultat de l'envoi
        """
        if notification_type not in cls.ALERT_TEMPLATES:
            logger.warning(f"Unknown notification type: {notification_type}")
            return {'success': False, 'error': 'Unknown notification type'}

        template_config = cls.ALERT_TEMPLATES[notification_type]
        methods = methods or ['email', 'system']

        # Construire le contexte complet
        full_context = {
            'user': user,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'notification_type': notification_type,
            'timestamp': timezone.now(),
            **(context or {})
        }

        results = {
            'user': user.username,
            'notification_type': notification_type,
            'methods': [],
            'success': False
        }

        config = cls.get_config()

        if 'email' in methods and config.get('EMAIL_ENABLED'):
            email_result = cls.send_email(
                to_email=user.email,
                subject=template_config['subject'],
                template=template_config.get('template'),
                context=full_context
            )
            results['methods'].append({'type': 'email', **email_result})

        if 'sms' in methods and config.get('SMS_ENABLED'):
            sms_template = template_config.get('sms_template', '')
            sms_message = sms_template.format(**full_context) if sms_template else None
            if sms_message and user.phone_number:
                sms_result = cls.send_sms(
                    phone_number=user.phone_number,
                    message=sms_message
                )
                results['methods'].append({'type': 'sms', **sms_result})

        if 'system' in methods and config.get('SYSTEM_ENABLED'):
            system_result = cls.send_system_notification(
                user=user,
                title=template_config['subject'],
                message=template_config.get('sms_template', '').format(**full_context),
                notification_type=notification_type
            )
            results['methods'].append({'type': 'system', **system_result})

        results['success'] = any(m.get('success') for m in results['methods'])
        return results

    @classmethod
    def send_email(
        cls,
        to_email: str,
        subject: str,
        template: str = None,
        context: Dict[str, Any] = None,
        plain_message: str = None
    ) -> Dict[str, Any]:
        """
        Envoie un email.

        Args:
            to_email: Adresse email destinataire
            subject: Sujet de l'email
            template: Chemin vers le template HTML (optionnel)
            context: Contexte pour le rendu du template
            plain_message: Message en texte brut (utilisé si pas de template)

        Returns:
            Dict avec success=True/False et details
        """
        config = cls.get_config()

        if not config.get('EMAIL_ENABLED'):
            return {'success': False, 'error': 'Email disabled'}

        if not to_email:
            return {'success': False, 'error': 'No email address'}

        try:
            from_email = config.get('FROM_EMAIL', settings.DEFAULT_FROM_EMAIL)

            # Générer le contenu HTML si template fourni
            if template:
                try:
                    html_content = render_to_string(template, context or {})
                    text_content = strip_tags(html_content)
                except Exception as e:
                    logger.warning(f"Template {template} not found, using plain text: {e}")
                    html_content = None
                    text_content = plain_message or cls._generate_plain_message(context)
            else:
                html_content = None
                text_content = plain_message or cls._generate_plain_message(context)

            # Créer l'email
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=from_email,
                    to=[to_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send(fail_silently=False)
            else:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=from_email,
                    recipient_list=[to_email],
                    fail_silently=False
                )

            logger.info(f"Email sent to {to_email}: {subject}")
            return {'success': True, 'to': to_email}

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def send_sms(cls, phone_number: str, message: str) -> Dict[str, Any]:
        """
        Envoie un SMS via l'API configurée.

        Args:
            phone_number: Numéro de téléphone destinataire
            message: Message SMS

        Returns:
            Dict avec success=True/False et details
        """
        config = cls.get_config()

        if not config.get('SMS_ENABLED'):
            return {'success': False, 'error': 'SMS disabled'}

        if not phone_number:
            return {'success': False, 'error': 'No phone number'}

        api_url = config.get('SMS_API_URL')
        api_key = config.get('SMS_API_KEY')

        if not api_url or not api_key:
            return {'success': False, 'error': 'SMS API not configured'}

        try:
            # Format générique - à adapter selon votre fournisseur SMS
            response = requests.post(
                api_url,
                json={
                    'to': phone_number,
                    'message': message,
                    'api_key': api_key
                },
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"SMS sent to {phone_number}")
                return {'success': True, 'to': phone_number}
            else:
                error = f"SMS API error: {response.status_code}"
                logger.error(error)
                return {'success': False, 'error': error}

        except requests.RequestException as e:
            logger.error(f"Failed to send SMS to {phone_number}: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def send_system_notification(
        cls,
        user,
        title: str,
        message: str,
        notification_type: str = 'info'
    ) -> Dict[str, Any]:
        """
        Crée une notification système stockée en base de données.

        Args:
            user: Instance User Django
            title: Titre de la notification
            message: Corps de la notification
            notification_type: Type (info, warning, error, success)

        Returns:
            Dict avec success=True/False
        """
        try:
            from core.models import SystemNotification

            SystemNotification.objects.create(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type
            )

            logger.info(f"System notification created for {user.username}")
            return {'success': True}

        except ImportError:
            # Le modèle SystemNotification n'existe pas encore
            logger.warning("SystemNotification model not found, skipping")
            return {'success': True, 'note': 'Model not implemented'}
        except Exception as e:
            logger.error(f"Failed to create system notification: {e}")
            return {'success': False, 'error': str(e)}

    @classmethod
    def send_admin_alert(
        cls,
        subject: str,
        message: str,
        alert_level: str = 'warning'
    ) -> Dict[str, Any]:
        """
        Envoie une alerte aux administrateurs.

        Args:
            subject: Sujet de l'alerte
            message: Corps de l'alerte
            alert_level: Niveau (info, warning, error, critical)

        Returns:
            Dict avec success=True/False
        """
        config = cls.get_config()
        admin_email = config.get('ADMIN_EMAIL')

        if not admin_email:
            return {'success': False, 'error': 'No admin email configured'}

        prefix_map = {
            'info': '[INFO]',
            'warning': '[WARNING]',
            'error': '[ERROR]',
            'critical': '[CRITICAL]'
        }
        prefix = prefix_map.get(alert_level, '[ALERT]')

        return cls.send_email(
            to_email=admin_email,
            subject=f"{prefix} Captive Portal: {subject}",
            plain_message=message
        )

    # =========================================================================
    # Méthodes privées
    # =========================================================================

    @classmethod
    def _build_alert_context(cls, user, profile, usage, alert) -> Dict[str, Any]:
        """Construit le contexte pour les templates d'alerte."""
        # Calculer le pourcentage utilisé
        if profile and profile.data_volume:
            percent = round((usage.used_total / profile.data_volume) * 100, 1)
            remaining_bytes = max(0, profile.data_volume - usage.used_total)
            remaining_gb = round(remaining_bytes / (1024**3), 2)
        else:
            percent = 0
            remaining_gb = 0

        # Calculer les jours restants
        if profile and usage.activation_date:
            from datetime import timedelta
            expiry_date = usage.activation_date + timedelta(days=profile.validity_duration)
            days_remaining = max(0, (expiry_date - timezone.now()).days)
        else:
            days_remaining = 0
            expiry_date = None

        return {
            'user': user,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'email': user.email,
            'profile': profile,
            'profile_name': profile.name if profile else 'N/A',
            'usage': usage,
            'percent': percent,
            'remaining_gb': remaining_gb,
            'used_gb': round(usage.used_total / (1024**3), 2),
            'total_gb': round(profile.data_volume / (1024**3), 2) if profile else 0,
            'days_remaining': days_remaining,
            'expiry_date': expiry_date,
            'alert_type': alert.alert_type,
            'threshold': alert.threshold_percent,
            'timestamp': timezone.now(),
        }

    @classmethod
    def _send_alert_email(cls, user, alert, context) -> Dict[str, Any]:
        """Envoie un email d'alerte."""
        template_config = cls.ALERT_TEMPLATES.get(alert.alert_type, {})

        return cls.send_email(
            to_email=user.email,
            subject=template_config.get('subject', 'Alerte Captive Portal'),
            template=template_config.get('template'),
            context=context
        )

    @classmethod
    def _send_alert_sms(cls, user, alert, context) -> Dict[str, Any]:
        """Envoie un SMS d'alerte."""
        if not user.phone_number:
            return {'success': False, 'error': 'No phone number'}

        template_config = cls.ALERT_TEMPLATES.get(alert.alert_type, {})
        sms_template = template_config.get('sms_template', '')

        if not sms_template:
            return {'success': False, 'error': 'No SMS template'}

        try:
            message = sms_template.format(**context)
        except KeyError as e:
            logger.error(f"Missing context key for SMS template: {e}")
            message = f"Captive Portal: Alerte {alert.alert_type}"

        return cls.send_sms(user.phone_number, message)

    @classmethod
    def _send_system_notification(cls, user, alert, context) -> Dict[str, Any]:
        """Crée une notification système pour l'alerte."""
        template_config = cls.ALERT_TEMPLATES.get(alert.alert_type, {})

        return cls.send_system_notification(
            user=user,
            title=template_config.get('subject', 'Alerte'),
            message=template_config.get('sms_template', '').format(**context),
            notification_type='warning' if 'warning' in alert.alert_type else 'error'
        )

    @classmethod
    def _generate_plain_message(cls, context: Dict[str, Any]) -> str:
        """Génère un message texte brut à partir du contexte."""
        if not context:
            return "Notification du Captive Portal"

        parts = []
        if context.get('username'):
            parts.append(f"Utilisateur: {context['username']}")
        if context.get('percent'):
            parts.append(f"Quota utilisé: {context['percent']}%")
        if context.get('remaining_gb'):
            parts.append(f"Restant: {context['remaining_gb']} Go")
        if context.get('days_remaining'):
            parts.append(f"Jours restants: {context['days_remaining']}")

        return "\n".join(parts) if parts else "Notification du Captive Portal"
