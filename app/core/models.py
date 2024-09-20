'''
Database models
'''

from django.db import models
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin
)


class UserManager(BaseUserManager):
    '''Manager for users'''

    # el metodo contiene la informacion minima necesaria para crear un usuario
    # se usa un valor por defecto para el password por si queremos usar
    # usuarios de prueba. Todas las modificaciones que hagamos en la clase User
    # van a pasar a traves de **extra_fields sin tener que modificar el UserManager
    def create_user(self, email, password=None, **extra_fields):
        '''Create, save and return a new user'''
        # se chequea que el email exista
        if not email:
            raise ValueError('User most have an email address')
        # se crea el usuario, notese que se normaliza el email, por si tiene mayusculas despues
        # de la @. normalize_email es un metodo de la clase BaseUserManager
        user = self.model(email=self.normalize_email(email), **extra_fields)
        # el password se agrega despues de encriptado
        user.set_password(password)
        # se guarda en la base de datos
        user.save(using=self._db)

        return user

    def create_superuser(self, email, password):
        '''Create and return a new superuser'''
        user = self.create_user(email, password)
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)

        return user


class User(AbstractBaseUser, PermissionsMixin):
    '''User in the system'''
    email = models.EmailField(max_length=255, unique=True)
    # 255 es la maxima longitud de un CharField
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    # is_staff define si puede acceder al Django Admin
    is_staff = models.BooleanField(default=False)

    # asignamos el UserManager a la clase User
    objects = UserManager()

    # reemplazamos el campo por defecto para autenticacion username por el email
    USERNAME_FIELD = 'email'
