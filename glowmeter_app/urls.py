from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', auth_views.LogoutView.as_view(
        template_name='registration/logged_out.html',
        next_page='home'
    ), name='logout'),
    path('register/', views.register_user, name='register'),
    path('register-doctor/', views.register_doctor, name='register_doctor'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('change-password/', views.change_password, name='change_password'),
    
    # Consultation URLs
    path('start-consultation/<int:doctor_id>/', views.start_consultation, name='start_consultation'),
    path('consultation/<int:consultation_id>/', views.consultation_view, name='consultation'),
    path('my-consultations/', views.my_consultations, name='my_consultations'),
] 