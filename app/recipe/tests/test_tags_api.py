'''
Tests for the tags API
'''
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')

def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a user'''
    return get_user_model().objects.create_user(email=email, password=password)

class PublicTagsApiTests(TestCase):
    '''Test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Tests auth is required for retrieving tags'''
        # hacemos un request sin autenticar ningun usuario
        res = self.client.get(TAGS_URL)
        # comprobamos que la respuesta devuelve un statuscode 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

class PrivateTagsApiTests(TestCase):
    '''Test authenticated API requests'''

    def setUp(self):
        self.user = create_user()
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        '''Test retrieving a list of tags'''
        # creamos las tags
        Tag.objects.create(user=self.user, name='Vegan')
        Tag.objects.create(user=self.user, name='Dessert')
        # hacemos la peticion para ver la lista
        res = self.client.get(TAGS_URL)
        # hacemos la consulta directa y la serializamos
        tags = Tag.objects.all().order_by('-name')
        serializer = TagSerializer(tags, many=True)
        # comprobamos el estado de la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que los valores devueltos por la peticion
        # coincidan con los de la consulta directa
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        '''Test list of tags is limited to authenticated users'''
        # creamos un usuario y una tag creada por el
        user2 = create_user(email='user@example.com')
        Tag.objects.create(user=user2, name= 'Fruity')
        # creamos una segunda receta usando el usuario especificado
        tag = Tag.objects.create(user=self.user, name='Comfort Food')
        # hacemos la peticion para listar las tags
        res = self.client.get(TAGS_URL)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos la cantidad de elementos de la respuesta
        self.assertEqual(len(res.data),1)
        # comprobamos que la tag coincida con la respuesta de la peticion
        self.assertEqual(res.data[0]['name'], tag.name)
        # comprobamos que los id de la tag en la base de datos coincida con
        # la respuesta de la peticion
        self.assertEqual(res.data[0]['id'], tag.id)