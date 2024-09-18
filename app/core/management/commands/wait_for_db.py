'''
Django command to wait for the database to be available
'''

import time
from psycopg2 import OperationalError as Psycopg2Error
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    '''Django command to wait for database'''

    def handle(self, *args, **options):
        '''Entry point for command'''
        # se muestra en la consola el mensaje
        self.stdout.write('Waiting for database...')
        # inicialmente la base de datos no esta conectada
        db_up = False
        # se espera por la base de datos
        while db_up is False:
            try:
                self.check(databases=['default'])
                db_up = True
            except (Psycopg2Error, OperationalError):
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
        # una vez se conecta muestra el mensaje de exito
        self.stdout.write(self.style.SUCCESS('Database available!'))
