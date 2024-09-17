'''
Archivo tests.py
'''

# importamos el modulo de test a usar
from django.test import SimpleTestCase

# importamos la funcion a testear
from app import calc

# creamos la clase que va a contener el test


class CalcTests(SimpleTestCase):
    '''Test the calculator module'''

    # creamos la funcion para ejecutar el test
    def test_add_numbers(self):
        '''Test adding numbers together'''

        # se invoca la funcion y se le pasan parametros
        res = calc.add(5, 4)

        # se compara el resultado esperado con la devolucion
        self.assertEqual(res, 9)

    def test_sustract_numbers(self):
        res = calc.sustract(10, 15)

        self.assertEqual(res, 5)
