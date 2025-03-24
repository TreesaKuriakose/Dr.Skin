from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Doctor, RegularUser, Consultation, Message
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
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

class UserProfileEditForm(forms.ModelForm):
    """Form for editing user account information"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email')

class RegularUserProfileEditForm(forms.ModelForm):
    """Form for editing regular user profile information"""
    class Meta:
        model = RegularUser
        fields = ('full_name', 'profile_picture')
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

class DoctorProfileEditForm(forms.ModelForm):
    """Form for editing doctor profile information"""
    class Meta:
        model = Doctor
        fields = ('full_name', 'specialty', 'bio', 'profile_picture', 'is_available')
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows': 5}),
        }

@login_required
def edit_profile(request):
    """Edit profile view for both users and doctors"""
    user = request.user
    
    if request.method == 'POST':
        user_form = UserProfileEditForm(request.POST, instance=user)
        
        if user.is_doctor:
            profile_form = DoctorProfileEditForm(
                request.POST, 
                request.FILES, 
                instance=user.doctor_profile
            )
        else:
            profile_form = RegularUserProfileEditForm(
                request.POST, 
                request.FILES, 
                instance=user.user_profile
            )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Your profile was successfully updated!")
            return redirect('dashboard')
    else:
        user_form = UserProfileEditForm(instance=user)
        
        if user.is_doctor:
            profile_form = DoctorProfileEditForm(instance=user.doctor_profile)
        else:
            profile_form = RegularUserProfileEditForm(instance=user.user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'is_doctor': user.is_doctor,
    }
    
    return render(request, 'edit_profile.html', context)

@login_required
def change_password(request):
    """Change password view"""
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            # Keep the user logged in
            update_session_auth_hash(request, user)
            messages.success(request, "Your password was successfully updated!")
            return redirect('dashboard')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = PasswordChangeForm(request.user)
    
    return render(request, 'change_password.html', {'form': form})

@login_required
def start_consultation(request, doctor_id):
    """Start a new consultation with a doctor"""
    doctor = Doctor.objects.get(id=doctor_id)
    user = request.user
    
    # Check if there's already an active consultation between the user and the doctor
    existing_consultation = Consultation.objects.filter(
        user=user, 
        doctor=doctor, 
        is_active=True
    ).first()
    
    if existing_consultation:
        consultation = existing_consultation
    else:
        consultation = Consultation.objects.create(
            user=user,
            doctor=doctor
        )
        # Create first message to start the conversation
        Message.objects.create(
            consultation=consultation,
            sender=user,
            content=f"Hello Dr. {doctor.full_name}, I would like to start a consultation with you."
        )
    
    return redirect('consultation', consultation_id=consultation.id)

@login_required
def consultation_view(request, consultation_id):
    """View a specific consultation"""
    consultation = Consultation.objects.get(id=consultation_id)
    user = request.user
    
    # Security check: only the user or the doctor involved can view the consultation
    if user != consultation.user and user != consultation.doctor.user:
        messages.error(request, "You don't have permission to view this consultation.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            Message.objects.create(
                consultation=consultation,
                sender=user,
                content=message_content
            )
            return redirect('consultation', consultation_id=consultation.id)
    
    # Mark all unread messages as read if the viewer is not the sender
    unread_messages = Message.objects.filter(
        consultation=consultation,
        is_read=False
    ).exclude(sender=user)
    
    unread_messages.update(is_read=True)
    
    messages_list = Message.objects.filter(consultation=consultation).order_by('timestamp')
    
    context = {
        'consultation': consultation,
        'messages': messages_list,
        'is_doctor': user.is_doctor
    }
    
    return render(request, 'consultation.html', context)

@login_required
def my_consultations(request):
    """View all consultations for the current user"""
    user = request.user
    
    if user.is_doctor:
        consultations = Consultation.objects.filter(doctor=user.doctor_profile)
    else:
        consultations = Consultation.objects.filter(user=user)
    
    # Count unread messages for each consultation
    for consultation in consultations:
        consultation.unread_count = Message.objects.filter(
            consultation=consultation,
            is_read=False
        ).exclude(sender=user).count()
    
    context = {
        'consultations': consultations,
        'is_doctor': user.is_doctor
    }
    
    return render(request, 'my_consultations.html', context)
