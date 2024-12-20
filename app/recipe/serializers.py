'''
Serializers for recipe API
'''

from rest_framework import serializers
from core.models import Recipe, Tag, Ingredient


# *SE DEFINEN PRIMERO LOS SERIALIZADORES QUE NO CONTIENEN OTROS

class IngredientSerializer(serializers.ModelSerializer):
    '''Serializer for ingredients'''

    class Meta:
        model = Ingredient
        fields = ['name', 'id']
        read_only_fields = ['id']


class TagSerializer(serializers.ModelSerializer):
    '''Serializer for tags'''

    class Meta:
        model = Tag
        fields = ['id', 'name']
        read_only_fields =['id']


# *SE DEFINEN LOS SERIALIZADORES QUE DEPENDEN DE OTROS DEFINIDOS PREVIAMENTE

class RecipeSerializer(serializers.ModelSerializer):
    '''Serializer for recipes'''
    # definimos el nested serializer
    tags = TagSerializer(many=True, required=False)
    ingredients = IngredientSerializer(many=True, required=False)

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags', 'ingredients']
        read_only_fields = ['id']

    # este metodo va a ser usado por los metodos create y update cuando sean 
    # modificados para los campos many to many 
    def _get_or_create_tags(self, tags, recipe):
        '''Handle getting or creating tags as needed'''
        # obtenemos el usuario autenticado, como estamos en el serializador y no
        # en la vista tenemos que usar este metodo
        auth_user = self.context['request'].user
        # creamos cada tag y la adicionamos a la receta
        for tag in tags:
            # se usa el metodo get_or_create porque si existe el tag previamente
            # no lo duplica
            tag_obj, created = Tag.objects.get_or_create(
                user=auth_user,
                **tag,
            )
            # adicionamos el tag a la receta
            recipe.tags.add(tag_obj)


    def _get_or_create_ingredients(self, ingredients, recipe):
        '''Handle getting or create ingredients as needed'''
        auth_user = self.context['request'].user
        for ingredient in ingredients:
            ingredient_obj, created = Ingredient.objects.get_or_create(
                user=auth_user,
                **ingredient,
            )
            recipe.ingredients.add(ingredient_obj)


    # los nested serializer son por defecto campos read-only para cambiar eso
    # es necesario modificar la funcion
    def create(self, validated_data):
        '''Create a recipe'''
        # borramos el tag del validated_data y si no existe obtenemos un array vacio
        tags = validated_data.pop('tags', [])
        ingredients = validated_data.pop('ingredients', [])
        # procedemos a crear la receta sin los tags
        recipe = Recipe.objects.create(**validated_data)
        # obtenemos el usuario autenticado, como estamos en el serializador y no
        self._get_or_create_tags(tags, recipe)
        self._get_or_create_ingredients(ingredients, recipe)
        # devolvemos la receta
        return recipe


    # hay que modificar el metodo update para que admita los nested serializer
    def update(self, instance, validated_data):
        '''Update recipe'''
        # tomamos las tags y las borramos de validated_data
        tags = validated_data.pop('tags', None)
        ingredients = validated_data.pop('ingredients', None)
        # chequeamos si los tags y los ingredients existen
        if tags is not None:
            instance.tags.clear()
            # creamos las tags
            self._get_or_create_tags(tags, instance)
        if ingredients is not None:
            instance.ingredients.clear()
            # creamos los ingredients
            self._get_or_create_ingredients(ingredients, instance)
        # creamos el resto del objeto recipe
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # guardamos el objeto
        instance.save()
        
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    '''Serializer for recipe detail view'''

    class Meta(RecipeSerializer.Meta):
        # se pone image solo si existiera ese campo
        fields = RecipeSerializer.Meta.fields + ['description', 'image']


# se crea un serializador aparte porque es una buena practica solamente
# actualizar un tipo de datos en un API, en este caso usamos un API 
# para las imagenes
class RecipeImageSerializer(serializers.ModelSerializer):
    '''Serializer for uploading images to recipes'''

    class Meta:
        model = Recipe
        fields = ['id', 'image']
        read_only_fields = ['id']
        # se pone required porque si no hay una imagen no tiene sentido usar el
        # serializador
        extra_kwargs = {'image': {'required': 'True'}}