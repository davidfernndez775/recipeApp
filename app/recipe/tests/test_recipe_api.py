'''
Tests for recipe APIs
'''
from decimal import Decimal
import tempfile
import os
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import RecipeSerializer, RecipeDetailSerializer

# *definimos las urls a las que se van a hacer las peticiones
RECIPES_URL = reverse('recipe:recipe-list')


def detail_url(recipe_id):
    '''Create and return a recipe detail URL'''
    # se crea una funcion que devuelva un url para cada elemento en la base de datos
    return reverse('recipe:recipe-detail', args=[recipe_id])


def image_upload_url(recipe_id):
    '''Create and return and image upload URL'''
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_recipe_with_new_tags(self):
        '''Test creating a recipe with new tags'''
        # creamos la informacion para una receta con tags
        payload = {
            'title':'Thai Prawn Curry',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'tags': [{'name':'Thai'}, {'name':'Dinner'}]
        }
        # al hacer la peticion como tenemos un objeto(tag) dentro de otro
        # (recipe) es necesario especificar el formato
        res = self.client.post(RECIPES_URL, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # comprobamos la creacion de la receta en la base de datos
        # hacemos la consulta
        recipes = Recipe.objects.filter(user=self.user)
        # comprobamos que haya una sola receta
        self.assertEqual(recipes.count(), 1)
        # pasamos la informacion a la variable recipe
        recipe = recipes[0]
        # comprobamos que la receta tiene 2 tags
        self.assertEqual(recipe.tags.count(), 2)
        # comprobamos que cada clave del tag en el payload
        # coincide con los valores en la base de datos
        # tanto del usuario como el name
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name = tag['name'],
                user = self.user,
            ).exists()
            # confirmamos que existe la coincidencia
            self.assertTrue(exists)

    def test_create_recipe_with_existing_tags(self):
        '''Test creating a recipe with existing tag'''
        # creamos en la base de datos una tag previa
        tag_indian = Tag.objects.create(user=self.user, name='Indian')
        # creamos una receta que va a tener la tag creada previamente
        # y otra que es nueva
        payload = {
            'title':'Pongal',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'tags': [{'name':'Indian'},{'name':'Breakfast'}],
        }
        # hacemos la peticion
        res = self.client.post(RECIPES_URL, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # hacemos la consulta a la base de datos de las recetas
        recipes = Recipe.objects.filter(user=self.user)
        # comprobamos que se ha creado una sola receta
        self.assertEqual(recipes.count(), 1)
        # asignamos a una variable la receta creada
        recipe = recipes[0]
        # comprobamos la cantidad de tags en la receta
        self.assertEqual(recipe.tags.count(), 2)
        # comprobamos que la etiqueta se encuentre
        self.assertIn(tag_indian, recipe.tags.all())
        # comprobamos los valores dentro de las tags
        for tag in payload['tags']:
            exists = recipe.tags.filter(
                name=tag['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_tag_on_update(self):
        '''Test creating tag when updating a recipe'''
        # creamos una receta
        recipe = create_recipe(user=self.user)
        # creamos el tag a actualizar
        payload = {'tags':[{'name': 'Lunch'}]}
        # definimos la url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # hacemos una consulta a la base de datos para buscar el tag
        new_tag = Tag.objects.get(user=self.user, name='Lunch')
        # comprobamos que la etiqueta existe en la receta que 
        # creamos al principio, notese que no se usa la funcion 
        # refresh_from_db cuando se actualizan campos many to many
        # en su lugar se usa .all()
        self.assertIn(new_tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        '''Test assigning an existing tag when updating a recipe'''
        # creamos una tag
        tag_breakfast = Tag.objects.create(user=self.user, name='Breakfast')
        # creamos una receta
        recipe = create_recipe(user=self.user)
        # agregamos la tag a la receta
        recipe.tags.add(tag_breakfast)
        # creamos una nueva tag
        tag_lunch = Tag.objects.create(user=self.user, name='Lunch')
        # definimos la info para actualizar
        payload = {'tags':[{'name':'Lunch'}]}
        # definimos la url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que tag_lunch sustituyo a tag_breakfast
        self.assertIn(tag_lunch, recipe.tags.all())
        self.assertNotIn(tag_breakfast, recipe.tags.all())


    def test_clear_recipe_tags(self):
        '''Test clearing a recipes tags'''
        # creamos una receta con su tag
        tag = Tag.objects.create(user=self.user, name='Dessert')
        recipe = create_recipe(user=self.user)
        recipe.tags.add(tag)
        # actualizamos borrando las tags de la receta
        payload = {'tags': []}
        # definimos el url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que se borro el tag
        self.assertEqual(recipe.tags.count(), 0)


    def test_create_recipe_with_new_ingredients(self):
        '''Test creating a recipe with new ingredients'''
        # creamos la informacion para una receta con tags
        payload = {
            'title':'Sashimi',
            'time_minutes': 30,
            'price': Decimal('2.50'),
            'ingredients': [{'name':'Fish'}, {'name':'Salt'}]
        }
        # al hacer la peticion como tenemos un objeto(ingredient) dentro de otro
        # (recipe) es necesario especificar el formato
        res = self.client.post(RECIPES_URL, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # comprobamos la creacion de la receta en la base de datos
        # hacemos la consulta
        recipes = Recipe.objects.filter(user=self.user)
        # comprobamos que haya una sola receta
        self.assertEqual(recipes.count(), 1)
        # pasamos la informacion a la variable recipe
        recipe = recipes[0]
        # comprobamos que la receta tiene 2 ingredientes
        self.assertEqual(recipe.ingredients.count(), 2)
        # comprobamos que cada clave del ingredients en el payload
        # coincide con los valores en la base de datos
        # tanto del usuario como el name
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name = ingredient['name'],
                user = self.user,
            ).exists()
            # confirmamos que existe la coincidencia
            self.assertTrue(exists)



    def test_create_recipe_with_existing_ingredients(self):
        '''Test creating a recipe with existing ingredients'''
        # creamos en la base de datos un ingrediente previo
        ingredient_rice = Ingredient.objects.create(user=self.user, name='Rice')
        # creamos una receta que va a tener la tag creada previamente
        # y otra que es nueva
        payload = {
            'title':'Sushi',
            'time_minutes': 60,
            'price': Decimal('4.50'),
            'ingredients': [{'name':'Rice'},{'name':'Fish'}],
        }
        # hacemos la peticion
        res = self.client.post(RECIPES_URL, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        # hacemos la consulta a la base de datos de las recetas
        recipes = Recipe.objects.filter(user=self.user)
        # comprobamos que se ha creado una sola receta
        self.assertEqual(recipes.count(), 1)
        # asignamos a una variable la receta creada
        recipe = recipes[0]
        # comprobamos la cantidad de ingredientes en la receta
        self.assertEqual(recipe.ingredients.count(), 2)
        # comprobamos que la etiqueta se encuentre
        self.assertIn(ingredient_rice, recipe.ingredients.all())
        # comprobamos los valores dentro de los ingredientes
        for ingredient in payload['ingredients']:
            exists = recipe.ingredients.filter(
                name=ingredient['name'],
                user=self.user,
            ).exists()
            self.assertTrue(exists)


    def test_create_ingredient_on_update(self):
        '''Test creating an ingredient when updating a recipe'''
        # creamos una receta
        recipe = create_recipe(user=self.user)
        # creamos el ingrediente a actualizar
        payload = {'ingredients':[{'name': 'Beef'}]}
        # definimos la url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # hacemos una consulta a la base de datos para buscar el ingrediente
        new_ingredient = Ingredient.objects.get(user=self.user, name='Beef')
        # comprobamos que la etiqueta existe en la receta que 
        # creamos al principio, notese que no se usa la funcion 
        # refresh_from_db cuando se actualizan campos many to many
        # en su lugar se usa .all()
        self.assertIn(new_ingredient, recipe.ingredients.all())


    def test_update_recipe_assign_ingredient(self):
        '''Test assigning an existing ingredient when updating a recipe'''
        # creamos un ingrediente
        beef_ingredient = Ingredient.objects.create(user=self.user, name='Beef')
        # creamos una receta
        recipe = create_recipe(user=self.user)
        # agregamos el ingrediente a la receta
        recipe.ingredients.add(beef_ingredient)
        # creamos un nuevo ingrediente
        pork_ingredient = Ingredient.objects.create(user=self.user, name='Pork')
        # definimos la info para actualizar
        payload = {'ingredients':[{'name':'Pork'}]}
        # definimos la url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que tag_lunch sustituyo a tag_breakfast
        self.assertIn(pork_ingredient, recipe.ingredients.all())
        self.assertNotIn(beef_ingredient, recipe.ingredients.all())


    def test_clear_recipe_ingredients(self):
        '''Test clearing recipes ingredients'''
        # creamos una receta con su ingrediente
        ingredient = Ingredient.objects.create(user=self.user, name='Potatoes')
        recipe = create_recipe(user=self.user)
        recipe.ingredients.add(ingredient)
        # actualizamos borrando los ingredientes de la receta
        payload = {'ingredients': []}
        # definimos el url
        url = detail_url(recipe.id)
        # hacemos la peticion
        res = self.client.patch(url, payload, format='json')
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # comprobamos que se borro el ingrediente
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    '''Tests for the image upload API'''


    # creamos un usuario, lo autenticamos y creamos una receta con los 
    # parametros por defecto
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'user@example.com',
            'password123',
        )
        self.client.force_authenticate(self.user)
        self.recipe=create_recipe(user=self.user)

    # el metodo tearDown se ejecuta despues de los tests, el setUp se 
    # ejecuta antes. se pone para asegurarse que la imagen se borra
    # despues de cada test
    def tearDown(self):
        self.recipe.image.delete()

    
    def test_upload_image(self):
        '''Test uploading a image to a recipe'''
        # creamos un url a partir del id de la receta
        url= image_upload_url(self.recipe.id)
        # creamos un archivo temporal, para crear una imagen y hacer el test
        with tempfile.NamedTemporaryFile(suffix='.jpg') as image_file:
            # creamos una imagen de 10 por 10 px
            img=Image.new('RGB', (10,10))
            # guarda la imagen de la memoria a un archivo
            img.save(image_file, format='JPEG')
            # esta linea mueve el puntero en memoria al inicio del archivo
            image_file.seek(0)
            # se crea el payload para la actualizacion
            payload = {'image':image_file}
            # se realiza la peticion, especificando formulario 'multipart'
            # que es la forma recomendada para subir imagenes
            res=self.client.post(url, payload, format='multipart')
        # refrescamos la base de datos
        self.recipe.refresh_from_db()
        # comprobamos la peticion
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # chequeamos que hay un campo 'image' en la respuesta de la peticion
        self.assertIn('image', res.data)
        # chequeamos que hay un atributo 'path' en la consulta a la base de datos
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        '''Test uploading invalid image'''
        url = image_upload_url(self.recipe.id)
        # en este caso no se actualiza con una imagen para provocar el error
        payload = {'image': 'notanimage'}
        res = self.client.post(url, payload, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
