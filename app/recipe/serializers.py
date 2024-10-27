'''
Serializers for recipe API
'''

from rest_framework import serializers
from core.models import Recipe, Tag


# *SE DEFINEN PRIMERO LOS SERIALIZADORES QUE NO CONTIENEN OTROS

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

    class Meta:
        model = Recipe
        fields = ['id', 'title', 'time_minutes', 'price', 'link', 'tags']
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


    # los nested serializer son por defecto campos read-only para cambiar eso
    # es necesario modificar la funcion
    def create(self, validated_data):
        '''Create a recipe'''
        # borramos el tag del validated_data y si no existe obtenemos un array vacio
        tags = validated_data.pop('tags', [])
        # procedemos a crear la receta sin los tags
        recipe = Recipe.objects.create(**validated_data)
        # obtenemos el usuario autenticado, como estamos en el serializador y no
        self._get_or_create_tags(tags, recipe)
        # devolvemos la receta
        return recipe


    # hay que modificar el metodo update para que admita los nested serializer
    def update(self, instance, validated_data):
        '''Update recipe'''
        # tomamos las tags y las borramos de validated_data
        tags = validated_data.pop('tags', None)
        if tags is not None:
            instance.tags.clear()
            # creamos las tags
            self._get_or_create_tags(tags, instance)
        # creamos el resto del objeto recipe
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        # guardamos el objeto
        instance.save()
        
        return instance

class RecipeDetailSerializer(RecipeSerializer):
    '''Serializer for recipe detail view'''

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ['description']


