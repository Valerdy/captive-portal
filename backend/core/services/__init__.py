"""
Services pour l'application core.

Ce module contient les services métier réutilisables:
- NotificationService: Envoi de notifications (email, SMS, système)
"""

from .notifications import NotificationService

__all__ = ['NotificationService']
