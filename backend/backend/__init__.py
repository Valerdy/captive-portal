import pymysql

pymysql.install_as_MySQLdb()

# Import Celery app pour qu'il soit disponible globalement
from .celery import app as celery_app

__all__ = ('celery_app',)
