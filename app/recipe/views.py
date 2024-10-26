'''
Views for the recipe API
'''
from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag
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
        return self.serializer_class

    # metodo para creacion
    def perform_create(self, serializer):
        '''Create a new recipe'''
        # se le pasa el usuario
        serializer.save(user=self.request.user)


class TagViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin,mixins.DestroyModelMixin, viewsets.GenericViewSet):
    '''Manage tags in the database'''
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter queryset to authenticated user'''
        return self.queryset.filter(user = self.request.user).order_by('-name')