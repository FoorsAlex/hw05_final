from django.urls import path

from . import views

app_name = 'about'

urlpatterns = [
    path('author/', views.AboutAuth.as_view(), name='author'),
    path('tech/', views.AboutTech.as_view(), name='tech'),
]
