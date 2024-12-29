'''
Tests for the tags API
'''
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag

from recipe.serializers import TagSerializer


# *DEFINIMOS LAS FUNCIONES Y VARIABLES PARA LOS TEST
TAGS_URL = reverse('recipe:tag-list')


def detail_url(tag_id):
    '''Create and return a tag detail url'''
    return reverse('recipe:tag-detail', args=[(tag_id)])


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a user'''
    return get_user_model().objects.create_user(email=email, password=password)


# *DEFINIMOS LOS TEST PUBLICOS
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

# *DEFINIMOS LOS TEST PRIVADOS


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
        user2 = create_user(email='user2@example.com')
        Tag.objects.create(user=user2, name='Fruity')
        # creamos una segunda receta usando el usuario especificado
        tag = Tag.objects.create(user=self.user, name='Comfort Food')
        # hacemos la peticion para listar las tags
        res = self.client.get(TAGS_URL)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos la cantidad de elementos de la respuesta
        self.assertEqual(len(res.data), 1)
        # comprobamos que la tag coincida con la respuesta de la peticion
        self.assertEqual(res.data[0]['name'], tag.name)
        # comprobamos que los id de la tag en la base de datos coincida con
        # la respuesta de la peticion
        self.assertEqual(res.data[0]['id'], tag.id)

    def test_update_tag(self):
        '''Test updating a tag'''
        # creamos una tag en la base de datos
        tag = Tag.objects.create(user=self.user, name='After Dinner')
        # creamos una informacion para actualizarla
        payload = {'name': 'Dessert'}
        url = detail_url(tag.id)
        res = self.client.patch(url, payload)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # refrescamos la consulta a la base de datos
        tag.refresh_from_db()
        # comprobamos que la consulta a la base de datos coincida con la informacion
        self.assertEqual(tag.name, payload['name'])

    def test_delete_tag(self):
        '''Test deleting a tag'''
        # creamos una tag
        tag = Tag.objects.create(user=self.user, name='Breakfast')
        # hacemos la peticion de borrado
        url = detail_url(tag.id)
        res = self.client.delete(url)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # hacemos una consulta a la base de datos para comprobar que la tag no esta
        tag = Tag.objects.filter(user=self.user)
        self.assertFalse(tag.exists())

    def test_filter_tags_assigned_to_recipes(self):
        '''Test listing tags to those assigned to recipes'''
        # creamos dos ingredientes
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Lunch')
        # creamos una receta
        recipe = Recipe.objects.create(
            title='Green Eggs on Toast', time_minutes=10, price=Decimal('2.50'), user=self.user)
        # agregamos un ingrediente a la receta
        recipe.tags.add(tag1)
        # realizamos una peticion para los ingredientes asignados en al menos una receta,
        # por eso se usa el assigned_only: 1, si no se pone se devuelven todos los ingredientes
        # esten asignados o no
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        # serializamos los ingredientes desde la base de datos
        s1 = TagSerializer(tag1)
        s2 = TagSerializer(tag2)
        # chequeamos que en la respuesta solo se devuelva el ingrediente asignado a la receta
        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filtered_tags_unique(self):
        '''Test filtered tags returns a unique list'''
        # creamos dos ingredientes
        tag1 = Tag.objects.create(user=self.user, name='Breakfast')
        tag2 = Tag.objects.create(user=self.user, name='Dinner')
        # creamos dos recetas
        recipe1 = Recipe.objects.create(
            title='Pancakes', time_minutes=5, price=Decimal('5.00'), user=self.user,)
        recipe2 = Recipe.objects.create(
            title='Porridge', time_minutes=3, price=Decimal('2.00'), user=self.user,)
        # asignamos solo el primer ingrediente a las dos recetas
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag1)
        # realizamos la peticion para ver los ingredientes asignados
        res = self.client.get(TAGS_URL, {'assigned_only': 1})
        # comprobamos que la respuesta solo contenga un ingrediente, a pesar de que este asignado a varias
        # recetas
        self.assertEqual(len(res.data), 1)
