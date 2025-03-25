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
    
    # Prescription URLs
    path('patients/', views.doctor_patients, name='doctor_patients'),
    path('prescriptions/', views.view_prescriptions, name='view_prescriptions'),
    path('prescription/<int:prescription_id>/', views.prescription_detail, name='prescription_detail'),
    path('create-prescription/<int:patient_id>/', views.create_prescription, name='create_prescription'),
    
    # Product Management URLs
    path('manage-products/', views.manage_products, name='manage_products'),
    path('edit-product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('delete-product/<int:product_id>/', views.delete_product, name='delete_product'),
] 