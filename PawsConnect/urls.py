"""
URL configuration for PawsConnect project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from UserManagement.views import user_login, home, register, landing_page

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('landing_page/', landing_page, name='landing_page'),  # Set the landing page as the root URL
      # Move the home page to a separate URL
    path('register/', register, name='register'),
    path('login/', user_login, name='login'),
]
