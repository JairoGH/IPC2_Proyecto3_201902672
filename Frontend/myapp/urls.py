from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name="index"),
    path('index/', views.index, name='index'),
    path('upload_m/', views.upload_m, name="upload_m"),
    path('upload_c/', views.upload_c, name="upload_c"),
    path('limpiar_datos/', views.limpiar_datos, name='limpiar_datos'),
    path('get_hashtags/', views.get_hashtags, name='get_hashtags'),
    path('get_menciones/', views.get_menciones, name='get_menciones'),
    path('stats_hashtags/', views.stats_hashtags, name='stats_hashtags'),
    path('info_estudiante/', views.info_estudiante, name='info_estudiante'),
]