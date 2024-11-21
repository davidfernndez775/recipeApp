'''
Test for the ingredients API
'''
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


# *creamos el usuario de pruebas


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return user'''
    return get_user_model().objects.create_user(email=email, password=password)


# *creamos la clase para hacer los tests de las peticiones sin autenticacion
class PublicIngredientsApiTests(TestCase):
    '''Test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required for retrieving ingredients'''
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


# *creamos la clase para hacer los tests de las peticiones autenticadas
class PrivateIngredientsApiTests(TestCase):
    '''Test authenticated API requests'''

    # definimos el usuario, el servicio y lo autenticamos
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.client.force_authenticate(self.user)

    # test para chequear el retorno de la lista de ingredientes
    def test_retrieve_ingredients(self):
        '''Test retrieving a list of ingredients'''
        # creamos los ingredientes
        Ingredient.objects.create(user=self.user, name='sugar')
        Ingredient.objects.create(user=self.user, name='flour')
        # hacemos la peticion para crear la lista
        res = self.client.get(INGREDIENTS_URL)
        # hacemos la consulta a la base de datos y la serializamos
        ingredients = Ingredient.objects.all().order_by('-name')
        serializer = IngredientSerializer(ingredients, many=True)
        # comprobamos el estado de la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos los valores de la peticion con los de la consulta
        self.assertEqual(res.data, serializer.data)

    # test para chequear que los ingredientes solo sean vistos por
    # usuario que los crea
    def test_ingredients_limited_to_user(self):
        '''Test list of ingredients are limited to the authenticated user'''
        # creamos un usuario con un ingrediente propio, el password no se especifica
        # porque podemos tomar el por defecto
        user2 = create_user(email='user2@example.com')
        Ingredient.objects.create(user=user2, name='pepper')
        # creamos un ingrediente con el primer usuario
        ingredient = Ingredient.objects.create(user=self.user, name='apple')
        # hacemos la peticion donde se autentica el primer usuario por defecto
        res = self.client.get(INGREDIENTS_URL)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que el usuario solo vea su ingrediente
        self.assertEqual(len(res.data), 1)
        # comprobamos que los valores del ingrediente de la peticion se corresponden
        # a los valores del ingrediente creado por el usuario autenticado
        self.assertEqual(res.data[0]['name'], ingredient.name)
        self.assertEqual(res.data[0]['id'], ingredient.id)
