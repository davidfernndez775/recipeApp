'''
Test for models
'''
# primero se importan las librerias externas
from unittest.mock import patch
from decimal import Decimal

from django.test import TestCase
# para importar el modelo user se usa el metodo get_user_model
from django.contrib.auth import get_user_model
# el resto de los modelos se importa normalmente
from core import models

# metodo para crear un usuario


def create_user(email='user@example.com', password='testpass123'):
    '''Create and return a new user'''
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    '''Test models'''

    def test_create_user_with_email_successful(self):
        '''Test creating a user with an email is successful'''
        # se recomienda usar @example.com para evitar mandar un email real durante un test
        email = 'test@example.com'
        password = 'testpass123'
        user = get_user_model().objects.create_user(
            email=email,
            password=password,
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        '''Test email is normalized for new users'''

        # Este test es para chequear el algoritmo que verifica el uso de mayusculas en los email
        # se usan varios ejemplos de prueba, cada ejemplo es una lista que tiene en la primera
        # posicion el email recibido y en la segunda como debe ser
        sample_emails = [['test1@EXAMPLE.com', 'test1@example.com'],
                         ['Test2@Example.com', 'Test2@example.com'],
                         ['TEST3@EXAMPLE.COM', 'TEST3@example.com'],
                         ['test4@example.COM', 'test4@example.com'],]

        for email, expected in sample_emails:
            # con cada email creamos un usuario, pasando ademas el password 'sample123'
            user = get_user_model().objects.create_user(email, 'sample123')
            # chequeamos que este correctamente normalizado
            self.assertEqual(user.email, expected)

    def test_new_user_without_email_raises_error(self):
        '''Test that creating a user without an email raises a ValueError'''
        # este test chequea que si el usuario pasa un email vacio, se devuelva un ValueError
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('', 'test123')

    def test_create_superuser(self):
        '''Test creating a superuser'''
        user = get_user_model().objects.create_superuser(
            'test@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):
        '''Test creating a recipe is successful'''
        # creamos el usuario que va a crear la receta
        user = get_user_model().objects.create_user(
            'test@example.com',
            'testpass123',
        )
        # creamos la receta
        recipe = models.Recipe.objects.create(
            user=user,
            title='Sample recipe name',
            time_minutes=5,
            price=Decimal('5.50'),
            description='Sample recipe description'
        )
        # chequea que el nombre de la receta coincida
        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        '''Test creating a tag is successful'''
        # creamos el usuario
        user = create_user()
        # creamos la tag
        tag = models.Tag.objects.create(user=user, name='Tag1')
        # comprobamos que el valor de la base de datos coincide con el
        # argumento que pasamos
        self.assertEqual(str(tag), tag.name)

    def test_create_ingredient(self):
        '''Test creating and ingredient is successful'''
        user = create_user()
        ingredient = models.Ingredient.objects.create(
            user=user,
            name='Ingredient1'
        )

        # el primer parametro es lo que recibe de la consulta y el segundo es el valor
        # de la variable que creamos
        self.assertEqual(str(ingredient), ingredient.name)


    # uuid es una libreria que genera un string aleatorio que funciona como un
    # identificador unico
    @patch('core.models.uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        '''Test generating image path'''
        # se le hace un mocking a uuid para hacer el test, al final no queremos que 
        # la funcion genere el string sino que use "test-uuid" para poderlo comprobar
        uuid = 'test-uuid'
        mock_uuid.return_value=uuid
        # se llama a la funcion que asigna el path
        file_path = models.recipe_image_file_path(None, 'example.jpg')
        # chequeamos que reemplaza el nombre "example.jpg" por "test-uuid.jpg"
        self.assertEqual(file_path, f'uploads/recipe/{uuid}.jpg')