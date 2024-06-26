from django.urls import path
from . import views

urlpatterns = [
    path('',views.index,name='index'),
    path('login',views.login,name='login'),
    path('signup',views.signup,name='signup'),
    path('logout',views.logout,name='logout'),
    path('music/<str:id>',views.music,name="music"),
    path('profile/<str:id>',views.profile,name='profile'),
    path('callback',views.callback,name='callback'),
    path('search',views.search,name='search')
]