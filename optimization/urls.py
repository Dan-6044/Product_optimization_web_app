from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('subscription_payment/', views.subscription_payment, name='subscription_payment'),
    path('dashboard/<int:user_id>/', views.dashboard, name='dashboard'),
    path('upload/', views.upload_excel, name='upload_excel'), 
    path('excel_dashboard/', views.excel_dashboard, name='excel_dashboard'),

   ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)