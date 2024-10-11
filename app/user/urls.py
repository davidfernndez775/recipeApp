'''
URL Mappings for the user API
'''
from django.urls import path
from user import views

# definimos el nombre de la app en el enrutamiento general
app_name = 'user'

urlpatterns = [
    path('create/', views.CreateUserView.as_view(), name='create'),
]
