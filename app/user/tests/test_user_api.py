'''
Test for the user API
'''

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')


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

    def test_create_token_for_user(self):
        '''Test generates token for valid credentials'''
        # definimos los datos del usuario
        user_details = {
            'name': 'Test Name',
            'email': 'test@example.com',
            'password': 'test-user-password123',
        }
        # creamos el usuario en la base de datos
        create_user(**user_details)
        # definimos los datos para crear el token de acceso
        payload = {
            'email': user_details['email'],
            'password': user_details['password']
        }
        # solicitamos el token correspondiente al usuario en la base de datos
        res = self.client.post(TOKEN_URL, payload)
        # comprobamos que se devuelve un token en la respuesta
        self.assertIn('token', res.data)
        # comprobamos que la solicitud se ejecuta correctamente
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_bad_credentials(self):
        '''Test returns an error if credentials invalid'''
        # creamos el usuario
        create_user(email='test@example.com', password='goodpass')
        # creamos los datos de la solicitud, con el password incorrecto
        payload = {'email': 'test@example.com', 'password': 'badpass'}
        # enviamos la solicitud
        res = self.client.post(TOKEN_URL, payload)
        # comprobamos que no exista un token en la respuesta
        self.assertNotIn('token', res.data)
        # comprobamos que devuelva un error en la solicitud
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_blank_password(self):
        '''Test posting a blank password returns an error'''
        # creamos el usuario
        payload = {'email': 'test@example.com', 'password': ''}
        # enviamos la solicitud
        res = self.client.post(TOKEN_URL, payload)
        # comprobamos que no exista un token en la respuesta
        self.assertNotIn('token', res.data)
        # comprobamos que devuelva un error en la solicitud
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        '''Test authentication is required for users'''
        res = self.client.get(ME_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    '''Test API requests that require authentication'''

    def setUp(self):
        # se define y autentica el usuario en el setup porque vamos a usar
        # el mismo usuario para cada test
        self.user = create_user(
            email='test@example.com',
            password='testpass123',
            name='Test Name',
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        '''Test retrieving profile for logged in user'''
        # como hemos forzado en el setUp la autenticacion de un usuario
        # vamos a obtener los datos del mismo cuando haga una solicitud
        res = self.client.get(ME_URL)
        # comprobamos que el status de la response
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comparamos los datos de la response con los del usuario definido
        # en el setUp
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email,
        })

    def test_post_me_not_allowed(self):
        '''Test POST is not allowed for the me endpoint'''
        # enviamos una solicitud post a un endpoint que no lo permite
        res = self.client.post(ME_URL, {})
        # chequeamos la respuesta
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        '''Test updating the user profile for the authenticated user'''
        # pasamos los datos para la actualizacion del usuario
        payload = {'name': 'Updated name', 'password': 'newpassword123'}
        # hacemos la peticion
        res = self.client.patch(ME_URL, payload)
        # actualizamos el user desde la base de datos
        self.user.refresh_from_db()
        # comprobamos que el name y el password se hayan actualizado
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        # comprobamos el status de la response
        self.assertEqual(res.status_code, status.HTTP_200_OK)
