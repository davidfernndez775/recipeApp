'''
Test for the user API
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')


def create_user(**params):
    '''Create and return a new user'''
    return get_user_model().objects.create_user(**params)


class PublicUserApiTests(TestCase):
    '''Test the public features of the user API'''

    def setUp(self):
        self.client = APIClient()

    def test_create_user_sucess(self):
        '''Test creating a user is successful'''
        # definimos el usuario para el test
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name'
        }
        # enviamos una solicitud http para crear el usuario
        res = self.client.post(CREATE_USER_URL, payload)
        # chequeamos los resultados esperados en el test
        # primero que la response tenga el correcto status_code
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # chequeamos que el usuario haya sido creado
        user = get_user_model().objects.get(email=payload['email'])
        # chequeamos el password
        self.assertTrue(user.check_password(payload['password']))
        # chequeamos que el password no sea enviado de vuelta al usuario en la response
        self.assertNotIn('password', res.data)

    def test_user_with_email_exists_error(self):
        '''Test error returned if user with email exists'''
        payload = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'name': 'Test Name'
        }
        create_user(**payload)
        res = self.client.post(CREATE_USER_URL, payload)
        # chequeamos que cuando queremos agregar un usuario que ya existe a la base de
        # datos devuelve un BAD_REQUEST
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        '''Test an error is returned if password less than 5 chars'''
        payload = {
            'email': 'test@example.com',
            'password': 'pw',
            'name': 'Test Name'
        }
        res = self.client.post(CREATE_USER_URL, payload)
        # chequeamos que devuelva un BAD_REQUEST
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        # chequeamos que el usuario exista en la base de datos
        user_exists = get_user_model().objects.filter(
            email=payload['email']).exists()
        self.assertFalse(user_exists)
