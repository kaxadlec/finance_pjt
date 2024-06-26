from django.urls import path
from . import views

app_name = 'saving'
urlpatterns = [
    path('api/', views.get_saving_products),
    path('fixed/products/', views.fixed_product_list),
    path('free/products/', views.free_product_list),
    path('like_fixed/<int:product_id>/', views.like_fixed_saving_product),
    path('like_free/<int:product_id>/', views.like_free_saving_product),
    path('like_fixed/check/<int:product_id>/', views.check_like_fixed_saving_product),
    path('like_free/check/<int:product_id>/', views.check_like_free_saving_product),
]
