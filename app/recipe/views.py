'''
Views for the recipe API
'''
from typing import Any
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers


class RecipeViewSet(viewsets.ModelViewSet):
    '''View for manage recipe API'''
    # definimos el serializador, se pone el RecipeDetailSerializer porque se usa por
    # Create, Update and Delete mientras que el serializador RecipeSerializer solo
    # se usa para listar
    serializer_class = serializers.RecipeDetailSerializer
    # definimos la consulta
    queryset = Recipe.objects.all()
    # establecemos el tipo de autenticacion por tokens
    authentication_classes = [TokenAuthentication]
    # definimos que el usuario debe estar autenticado
    permission_classes = [IsAuthenticated]

    # *configuracion del viewset
    # este metodo hace que cada usuario solo vea sus propias recetas
    def get_queryset(self):
        '''Retrieve recipes for authenticated user'''
        # agregamos un filtro para que cada usuario solo pueda ver sus recetas
        return self.queryset.filter(user=self.request.user).order_by('-id')

    # este metodo cambia el serializer_class en dependencia de la accion
    def get_serializer_class(self):
        '''Return the serializer class for request'''
        if self.action == 'list':
            return serializers.RecipeSerializer
        elif self.action == 'upload_image':
            return serializers.RecipeImageSerializer
        return self.serializer_class

    # metodo para creacion
    def perform_create(self, serializer):
        '''Create a new recipe'''
        # se le pasa el usuario
        serializer.save(user=self.request.user)

    # metodo para la actualizacion de una imagen, adicionamos una accion,
    # se define para el metodo 'POST', para una vista detalle, se define 
    # el url para la accion: 'upload-image'
    @action(methods=['POST'], detail=True, url_path='upload-image')
    def upload_image(self, request, pk=None):
        '''Upload an image to recipe'''
        # se obtiene la receta usando el pk proporcionado
        recipe= self.get_object()
        # pasamos los datos al endpoint
        serializer = self.get_serializer(recipe, data=request.data)
        # chequeamos que el serializador es valido
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # devolvemos el bad_request si no es valido
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class BaseRecipeAttrViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    '''Base viewset for recipes attributes'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter queryset to authenticated user'''
        return self.queryset.filter(user=self.request.user).order_by('-name')


class TagViewSet(BaseRecipeAttrViewSet):
    '''Manage tags in the database'''
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()



class IngredientViewSet(BaseRecipeAttrViewSet):
    '''Manage ingredients in the database'''
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()


