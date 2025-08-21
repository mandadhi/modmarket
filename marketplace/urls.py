from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import StyledAuthenticationForm

urlpatterns = [
    # Public pages
    path('', views.home, name='home'),
    path('products/', views.product_list, name='product_list'),
    path('products/<str:pk>/', views.product_detail, name='product_detail'),
    path('products/<str:pk>/download/', views.download_product, name='download_product'),
    path('products/<str:pk>/review/', views.add_review, name='add_review'),
    path("thumbnail/<str:file_id>/", views.serve_thumbnail, name="serve_thumbnail"),
    path("avatar/<str:file_id>/", views.serve_avatar, name="serve_avatar"),
    path('serve_file/<str:file_id>/', views.serve_file, name='serve_file'),
    path('file/<str:file_id>/<str:bucket>/download/', views.download_product_file, name='download_file'),
    path('developer/<str:pk>/',views.developer_profile,name="developer_profile"),
    
    # Authentication
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(authentication_form=StyledAuthenticationForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Developer area
    path('dashboard/', views.developer_dashboard, name='developer_dashboard'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('upload/', views.upload_product, name='upload_product'),
    
    # Moderation (staff only)
    path('moderation/', views.moderation_queue, name='moderation_queue'),
    path('moderation/<str:pk>/', views.moderate_product, name='moderate_product'),

    # ------------------------------
    # Custom PyMongo Admin Routes
    # ------------------------------
    # Category management
    path('manage/',views.manage,name="manage"),
    path('manage/categories/', views.admin_category_list, name='admin_category_list'),
    path('manage/categories/add/', views.admin_category_add, name='admin_category_add'),
    path('manage/categories/<str:pk>/edit/', views.admin_category_edit, name='admin_category_edit'),
    path('manage/categories/<str:pk>/delete/', views.admin_category_delete, name='admin_category_delete'),

    # Product management
    path('manage/products/', views.admin_product_list, name='admin_product_list'),
    path('manage/products/<str:pk>/delete/', views.admin_product_delete, name='admin_product_delete'),

    # Developer management
    path('manage/developers/', views.admin_developer_list, name='admin_developer_list'),
    path('manage/developers/<str:pk>/delete/', views.admin_developer_delete, name='admin_developer_delete'),
    path('manage/deveopers/<str:pk>/view/',views.admin_developer_view,name="admin_developer_view"),
]
