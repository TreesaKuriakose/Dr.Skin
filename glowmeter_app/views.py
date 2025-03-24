from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Doctor, RegularUser
from django.contrib.auth.forms import AuthenticationForm
from django import forms

class UserRegistrationForm(forms.ModelForm):
    """Form for user registration"""
    password = forms.CharField(widget=forms.PasswordInput)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
    
    def clean_confirm_password(self):
        password = self.cleaned_data.get('password')
        confirm_password = self.cleaned_data.get('confirm_password')
        if password and confirm_password and password != confirm_password:
            raise forms.ValidationError("Passwords don't match")
        return confirm_password
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user

class RegularUserForm(forms.ModelForm):
    """Form for regular user additional details"""
    class Meta:
        model = RegularUser
        fields = ('full_name',)

class DoctorForm(forms.ModelForm):
    """Form for doctor additional details"""
    class Meta:
        model = Doctor
        fields = ('full_name', 'specialty', 'bio')

def home(request):
    """Home page view"""
    return render(request, 'home.html')

def register_user(request):
    """User registration view"""
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = RegularUserForm(request.POST)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            # Create user profile
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            # Log in user
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        user_form = UserRegistrationForm()
        profile_form = RegularUserForm()
    
    return render(request, 'register.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'user_type': 'user'
    })

def register_doctor(request):
    """Doctor registration view - only accessible to admin"""
    if not request.user.is_admin:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        doctor_form = DoctorForm(request.POST)
        
        if user_form.is_valid() and doctor_form.is_valid():
            user = user_form.save(commit=False)
            user.is_doctor = True
            user.save()
            
            # Create doctor profile
            doctor = doctor_form.save(commit=False)
            doctor.user = user
            doctor.save()
            
            messages.success(request, "Doctor registration successful!")
            return redirect('dashboard')
        else:
            messages.error(request, "Registration failed. Please correct the errors.")
    else:
        user_form = UserRegistrationForm()
        doctor_form = DoctorForm()
    
    return render(request, 'register.html', {
        'user_form': user_form,
        'profile_form': doctor_form,
        'user_type': 'doctor'
    })

def login_view(request):
    """Login view for both users and doctors"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.email}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = AuthenticationForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def dashboard(request):
    """Dashboard view - redirects based on user type"""
    user = request.user
    
    if user.is_admin:
        return render(request, 'admin_dashboard.html')
    elif user.is_doctor:
        return render(request, 'doctor_dashboard.html')
    else:
        doctors = Doctor.objects.filter(is_available=True)
        return render(request, 'user_dashboard.html', {'doctors': doctors})
