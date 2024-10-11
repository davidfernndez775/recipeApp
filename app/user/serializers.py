'''
Serializers for the user API View
'''
from django.contrib.auth import get_user_model
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    '''Serializer for the user object'''

    class Meta:
        model = get_user_model()
        # se especifican los campos que pueden ser modificados por el usuario
        fields = ['email', 'password', 'name']
        # la clave write_only se agrega para evitar que el password sea regresado
        # en el response al usuario, es una medida de seguridad
        extra_kwargs = {'password': {'write_only': True, 'min_length': 5}}

    def create(self, validated_data):
        '''Create and return a user with encryted password'''
        return get_user_model().objects.create_user(**validated_data)
