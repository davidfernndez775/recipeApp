'''
Views for the recipe API
'''
from typing import Any
from drf_spectacular.utils import extend_schema_view, extend_schema, OpenApiParameter, OpenApiTypes
from rest_framework import viewsets, mixins, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Recipe, Tag, Ingredient
from recipe import serializers

# usando el decorador @extend_schema_view podemos extender la funcionalidad de la documentacion
# de drf_spectacular para agregar el filtrado, esto es solo para la documentacion, la aplicacion
# puede funcionar sin esto pero es una forma de probar su funcionamiento


@extend_schema_view(
    # se especifica que queremos extender el esquema para el endpoint list
    list=extend_schema(
        # definimos los parametros de filtrado que agregamos a la peticion
        parameters=[
            OpenApiParameter(
                'tags',
                OpenApiTypes.STR,
                description='Comma separated list of tags IDs to filter',
            ),
            OpenApiParameter(
                'ingredients',
                OpenApiTypes.STR,
                description='Comma separated list of ingredients IDs to filter',
            ),
        ]
    )
)
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
    # recibe una cadena de texto que contiene numeros separados por comas
    # y lo vuelve una lista de enteros
    def _params_to_ints(self, qs):
        '''Convert a list of strings to integers'''
        return [int(str_id) for str_id in qs.split(',')]

    # este metodo hace que cada usuario solo vea sus propias recetas
    def get_queryset(self):
        '''Retrieve recipes for authenticated user'''
        # tomamos los parametros de la peticion
        tags = self.request.query_params.get('tags')
        ingredients = self.request.query_params.get('ingredients')
        # redefinimos la queryset
        queryset = self.queryset
        # chequeamos si hay filtros en la peticion
        if tags:
            # obtenemos los id de las tags
            tags_ids = self._params_to_ints(tags)
            # usamos el orm de Django para hacer la consulta a la base de datos, en el orm se explica la
            # sintaxis para el filtrado de campos relacionados tags__id__in en este caso
            queryset = queryset.filter(tags__id__in=tags_ids)
        if ingredients:
            ingredient_ids = self._params_to_ints(ingredients)
            queryset = queryset.filter(ingredients__id__in=ingredient_ids)
        # notese que no se pone self.queryset sino solo queryset para que tome la propiedad modificada
        # por nosotros, agregamos un filtro para que cada usuario solo pueda ver sus recetas. Se agrega distinct
        # porque puedes tener resultados duplicados si una receta comparte el tag y el ingrediente que se busca
        return queryset.filter(user=self.request.user).order_by('-id').distinct()

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
        recipe = self.get_object()
        # pasamos los datos al endpoint
        serializer = self.get_serializer(recipe, data=request.data)
        # chequeamos que el serializador es valido
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        # devolvemos el bad_request si no es valido
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema_view(
    # se especifica que queremos extender el esquema para el endpoint
    list=extend_schema(
        # definimos los parametros de filtrado que agregamos a la peticion
        parameters=[
            OpenApiParameter(
                'assigned_only',
                OpenApiTypes.INT,
                description='Filter by items assigned to recipes',
            ),
        ]
    )
)
class BaseRecipeAttrViewSet(mixins.ListModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    '''Base viewset for recipes attributes'''
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        '''Filter queryset to authenticated user'''
        # usamos esta variable para comprobar si se envian parametros de filtrado
        # convierte el 0 o el 1 de la peticion en un booleano
        assigned_only = bool(
            # por defecto se pone en 0 o sea no hay filtros
            int(self.request.query_params.get('assigned_only', 0))
        )
        # creamos una variable para nuestra queryset modificada
        queryset = self.queryset
        # si assigned_only es true, o sea recibe 1
        if assigned_only:
            queryset = queryset.filter(recipe__isnull=False)
        # agregamos distinct para garantizar no tener resultados duplicados
        return queryset.filter(user=self.request.user).order_by('-name').distinct()


class TagViewSet(BaseRecipeAttrViewSet):
    '''Manage tags in the database'''
    serializer_class = serializers.TagSerializer
    queryset = Tag.objects.all()


class IngredientViewSet(BaseRecipeAttrViewSet):
    '''Manage ingredients in the database'''
    serializer_class = serializers.IngredientSerializer
    queryset = Ingredient.objects.all()
