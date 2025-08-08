from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views  
from tracker import views  



urlpatterns = [
    path('admin/', admin.site.urls),
      path('accounts/', include('django.contrib.auth.urls')),
    path('', include('tracker.urls')),
    path('', views.dashboard, name='dashboard'),
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='tracker/logout.html'), name='logout'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='tracker/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='tracker/logout.html'), name='logout'),
   

]
