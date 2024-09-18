'''
Test custom Django management commands
'''

from unittest.mock import patch   # para que simule una base de datos

from psycopg2 import OperationalError as Psycopg2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase

# se pone el decorador @patch para simular para ese comando la respuesta
# de una base de datos


@patch('core.management.commands.wait_for_db.Command.check')
class CommandTests(SimpleTestCase):
    '''Test commands'''

    # Para testear se analiza cada caso probable, primero se testea si la
    # base de datos esta lista, despues se testean las demoras en la conexion

    def test_wait_for_db_ready(self, patched_check):
        '''Test waiting for database if database is ready'''
        # definimos el comportamiento del mock que simula la base de datos
        # para que devuelva un True
        patched_check.return_value = True

        # invocamos el comando a testear
        call_command('wait_for_db')

        # definimos el resultado esperado y se define la base de datos
        patched_check.assert_called_once_with(databases=['default'])

    @patch('time.sleep')
    def test_wait_for_db_delay(self, patched_sleep, patched_check):
        '''Test waiting for database when getting OperationalError'''

        # definimos el comportamiento del mock de la base de datos
        # el metodo side_effect se usa para invocar un error, en este caso
        # las primeras dos veces devuelve el error de que postgresql no
        # esta inicializado. Las siguientes tres devuelve un error de la
        # configuracion de la base de datos, por ultimo devuelve un True
        patched_check.side_effect = [
            Psycopg2Error]*2 + [OperationalError]*3+[True]

        # invocamos el comando a testear
        call_command('wait_for_db')

        # definimos el resultado esperado y la accion a realizar
        self.assertEqual(patched_check.call_count, 6)
        patched_check.assert_called_with(databases=['default'])
