'''
Serializers for the user API View
'''
from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
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

    def update(self, instance, validated_data):
        '''Update and return user'''
        # primero tomamos el password del validated_data y lo guardamos en una variable
        # y lo borramos del validated_data
        password = validated_data.pop('password', None)
        # invocamos el metodo update de Django para que haga el trabajo
        user = super().update(instance, validated_data)
        # chequeamos si hay un password
        if password:
            # si el usuario envio el password, lo actualizamos
            user.set_password(password)
            user.save()
        # retornamos el usuario actualizado
        return user


class AuthTokenSerializer(serializers.Serializer):
    '''Serializer for the user auth token'''
    # definimos un serializador con email y password
    email = serializers.EmailField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )
    # validacion del usuario

    def validate(self, attrs):
        '''Validate and authenticate the user'''
        # una vez que la funcion llega al serializador se llama a la funcion validate
        # de manera automatica
        # se toman los valores de los argumentos
        email = attrs.get('email')
        password = attrs.get('password')
        # se invoca la funcion autheticate de Django, en este caso al campo por defecto
        # username le corresponde el valor del email. El request se pasa por ser requerido
        # en realidad no se va a usar
        user = authenticate(
            request=self.context.get('request'),
            username=email,
            password=password
        )
        # si no existe el usuario
        if not user:
            msg = _('Unable to autheticate with provided credentials')
            # cuando elevamos un error se ejecuta un 400_BAD_REQUEST
            raise serializers.ValidationError(msg, code='authorization')
        # si existe el usuario
        attrs['user'] = user
        return attrs
