from django.urls import path

from . import views

app_name = 'rango'

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('about/', views.AboutView.as_view(), name='about'),
    path('category/<slug:category_name_slug>/',
         views.CategoryView.as_view(), name='show_category'),
    path('add_category/', views.AddCategoryView.as_view(), name='add_category'),
    path('category/<slug:category_name_slug>/add_page/',
         views.AddPageView.as_view(), name='add_page'),
    path('restricted/', views.restricted, name='restricted'),
    path('search/', views.search, name='search'),
    path('goto/<int:page_id>/', views.goto_url, name='goto'),
    path('register_profile/',
         views.register_profile,
         name='register_profile'),
    path('profile/<username>',
         views.ProfileView.as_view(),
         name='profile'),
    path('profiles/', views.list_profiles, name='list_profiles'),
    path('category/<slug:category_name_slug>/like/',
         views.like_category, name='like_category'),
    path('suggest/', views.suggest_category, name='suggest_category'),
    path('category/<slug:category_name_slug>/add/', views.auto_add_page, name='auto_add_page'),
]
