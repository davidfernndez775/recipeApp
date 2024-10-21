'''
Tests for recipe APIs
'''
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

# *definimos las urls a las que se van a hacer las peticiones
RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''Create and return a recipe detail URL'''
    # se crea una funcion que devuelva un url para cada elemento en la base de datos
    return reverse('recipe:recipe-detail', args=[recipe_id])


# *definimos el metodo para crear la receta
def create_recipe(user, **params):
    '''Create and return a sample recipe'''
    # se especifican valores por defecto para las recetas
    defaults = {
        'title': 'Sample recipe title',
        'time_minutes': 22,
        'price': Decimal('5.25'),
        'description': 'Sample description',
        'link': 'http://example.com/recipe.pdf',
    }
    # los valores por defecto se actualizan con los que introduce el usuario para el test
    defaults.update(params)
    # creamos la receta tomando el usuario autenticado y los valores
    recipe = Recipe.objects.create(user=user, **defaults)
    return recipe


# *definimos la creacion del usuario
def create_user(**params):
    '''Create and return a new user'''
    return get_user_model().objects.create_user(**params)


# *definimos los tests
class PublicRecipeAPITests(TestCase):
    '''Test unauthenticated API requests'''

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        '''Test auth is required to call API'''
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeApiTests(TestCase):
    '''Test authenticated API requests'''

    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='user@example.com',
            password='testpass123',
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        '''Test retrieving a list of recipes'''
        # creamos dos recetas para hacer la lista
        create_recipe(user=self.user)
        create_recipe(user=self.user)
        # CONSULTA UNO
        # hacemos la peticion http  que contiene la consulta
        # pasando por lo todo el framework
        res = self.client.get(RECIPES_URL)

        # CONSULTA DOS
        # hacemos la consulta directamente a la base de datos
        # se pone -id para que ordene los resultados por antiguedad
        recipes = Recipe.objects.all().order_by('-id')
        # serializamos el resultado de la consulta directa,
        # se especifica many para indicar que es una lista
        serializer = RecipeSerializer(recipes, many=True)

        # comprobamos la ejecucion de la peticion HTTP
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comparamos los resultados de las dos consultas
        self.assertEqual(res.data, serializer.data)

    def test_recipe_list_limit_to_user(self):
        '''Test list of recipes is limited to authenticated user'''
        other_user = create_user(
            email='other@example.com',
            password='password123',
        )
        # creamos dos recetas de diferentes usuarios
        create_recipe(user=other_user)
        create_recipe(user=self.user)
        # hacemos la consulta a traves de la peticion http
        res = self.client.get(RECIPES_URL)
        # hacemos la consulta directa
        # obtenemos y serializamos los datos
        recipes = Recipe.objects.filter(user=self.user)
        serializer = RecipeSerializer(recipes, many=True)

        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que las consultas den el mismo resultado
        self.assertEqual(res.data, serializer.data)

    def test_get_recipe_detail(self):
        '''Test get recipe detail'''
        # creamos la receta
        recipe = create_recipe(user=self.user)
        # tomamos el id de la receta creada para crear la url
        url = detail_url(recipe.id)
        # usando la url hacemos la peticion
        res = self.client.get(url)
        # serializamos la receta creada
        serializer = RecipeDetailSerializer(recipe)
        # comparamos el resultado de la peticion con el de la receta creada
        self.assertEqual(res.data, serializer.data)

    def test_create_recipe(self):
        '''Test creating a recipe'''
        # definimos un metodo para crear la receta a traves del API
        # el metodo create_recipe lo hace directamente en la base de datos
        # funciona para los test
        payload = {
            'title': 'Sample recipe',
            'time_minutes': 30,
            'price': Decimal('5.99'),
        }
        res = self.client.post(RECIPES_URL, payload)
        # comprobamos que la peticion devuelve un estado correcto
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # realizamos una consulta directa a la base de datos usando el id de la
        # receta creada a traves de la API
        recipe = Recipe.objects.get(id=res.data['id'])
        # comprobamos que cada elemento del payload coincide con los de la consulta
        for k, v in payload.items():
            # obtenemos usando getattr el valor correspondiente a cada clave k del objeto
            # creado usando la consulta directa y lo comparamos con el valor correspondiente
            # a esa clave del payload
            self.assertEqual(getattr(recipe, k), v)
        # comprobamos que el usuario que creo la receta usando la API es el mismo de la consulta
        self.assertEqual(recipe.user, self.user)

    def test_partial_update(self):
        '''Test parcial update of a recipe'''
        original_link = 'https://example.com/recipe/pdf'
        # creamos la receta
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link=original_link,
        )
        # creamos la informacion para actualizarla receta
        payload = {'title': 'New recipe title'}
        # direccionamos a la direccion especifica de la receta
        url = detail_url(recipe.id)
        # hacemos la actualizacion via API
        res = self.client.patch(url, payload)

        # comprobamos que la peticion se ejecuto correctamente
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # actualizamos la receta desde la base de datos
        recipe.refresh_from_db()
        # comprobamos los valores de la consulta a la base de datos
        # con los actualizados
        self.assertEqual(recipe.title, payload['title'])
        # comprobamos que los campos no actualizados mantengan sus
        # valores originales
        self.assertEqual(recipe.link, original_link)
        # comprobamos que el usuario coincida
        self.assertEqual(recipe.user, self.user)

    def test_full_update(self):
        '''Test full update of recipe'''
        # se crea la receta
        recipe = create_recipe(
            user=self.user,
            title='Sample recipe title',
            link='https://example.com/recipe.pdf',
            description='Sample recipe description',
        )
        # se crea la informacion a utilizar en la actualizacion
        payload = {
            'title': 'New recipe title',
            'link': 'https://example.com/new-recipe.pdf',
            'description': 'New recipe description',
            'time_minutes': 10,
            'price': Decimal('2.50'),
        }
        # se establece la direccion a la que hacer update
        url = detail_url(recipe.id)
        # se usa put para una actualizacion completa
        res = self.client.put(url, payload)
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # actualizamos la consulta de la base de datos actualizada
        recipe.refresh_from_db()
        # comprobamos que cada elemento del payload coincide con los de la consulta
        for k, v in payload.items():
            # obtenemos usando getattr el valor correspondiente a cada clave k del objeto
            # creado usando la consulta directa y lo comparamos con el valor correspondiente
            # a esa clave del payload
            self.assertEqual(getattr(recipe, k), v)
        # comprobamos que el usuario que creo la receta usando la API es el mismo de la consulta
        self.assertEqual(recipe.user, self.user)

    def test_update_user_returns_error(self):
        '''Test changing the recipe user results in an error'''
        # creamos un nuevo usuario
        new_user = create_user(email='user2@example.com', password='test123')
        # creamos la receta con un usuario distinto al creado arriba
        recipe = create_recipe(user=self.user)
        # creamos la informacion para la actualizacion cambiando el usuario
        payload = {'user': new_user.id}
        url = detail_url(recipe.id)
        # hacemos la peticion
        self.client.patch(url, payload)
        # refrescamos la consulta desde la base de datos
        recipe.refresh_from_db()
        # comprobamos que el usuario no ha sido actualizado
        self.assertEqual(recipe.user, self.user)

    def test_delete_recipe(self):
        '''Test deleting a recipe successful'''
        recipe = create_recipe(user=self.user)
        url = detail_url(recipe.id)
        res = self.client.delete(url)
        # este status indica que el borrado fue exitoso y por tanto
        # no hay contenido que mostrar
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)
        # se comprueba que la receta ya no existe en la base de datos
        # mediante una consulta directa
        self.assertFalse(Recipe.objects.filter(id=recipe.id).exists())

    def test_recipe_other_users_recipe_error(self):
        '''Test trying to delete another users recipe gives error'''
        # se crea un nuevo usuario
        new_user = create_user(email='user2@example.com', password='test123')
        # se crea una receta de ese usuario
        recipe = create_recipe(user=new_user)
        # se define la url de la receta
        url = detail_url(recipe.id)
        # se ejecuta la peticion pero por defecto se usa self.user y no el
        # usuario creado previamente
        res = self.client.delete(url)
        # comprobamos que la peticion recibe un not_found porque solo
        # el usuario que crea puede eliminar sus recetas
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
        # comprobamos mediante consulta directa que la receta aun existe
        # en la base de datos
        self.assertTrue(Recipe.objects.filter(id=recipe.id).exists())
