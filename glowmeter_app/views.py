from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import User, Doctor, RegularUser, Consultation, Message, Product, Prescription, PrescriptionItem
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
        doctors = Doctor.objects.all()
        users_count = User.objects.filter(is_doctor=False, is_admin=False).count()
        consultations_count = Consultation.objects.count()
        context = {
            'doctors': doctors,
            'users_count': users_count,
            'consultations_count': consultations_count,
            'products_count': 0  # Add actual products count when implemented
        }
        return render(request, 'admin_dashboard.html', context)
    elif user.is_doctor:
        return render(request, 'doctor_dashboard.html')
    else:
        available_doctors = Doctor.objects.filter(is_available=True)
        return render(request, 'user_dashboard.html', {'doctors': available_doctors})

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

class AdminProfileEditForm(forms.ModelForm):
    """Form for editing admin profile information"""
    profile_picture = forms.ImageField(required=False, widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'profile_picture')
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

@login_required
def edit_profile(request):
    """Edit profile view for users, doctors and admins"""
    user = request.user
    
    if request.method == 'POST':
        if user.is_admin:
            user_form = AdminProfileEditForm(request.POST, request.FILES, instance=user)
            profile_form = None
        elif user.is_doctor:
            user_form = UserProfileEditForm(request.POST, instance=user)
            profile_form = DoctorProfileEditForm(
                request.POST, 
                request.FILES, 
                instance=user.doctor_profile
            )
        else:
            user_form = UserProfileEditForm(request.POST, instance=user)
            profile_form = RegularUserProfileEditForm(
                request.POST, 
                request.FILES, 
                instance=user.user_profile
            )
        
        if user_form.is_valid() and (profile_form is None or profile_form.is_valid()):
            user = user_form.save(commit=False)
            if user.is_admin and 'profile_picture' in request.FILES:
                user.profile_picture = request.FILES['profile_picture']
            user.save()
            if profile_form:
                profile_form.save()
            messages.success(request, "Your profile was successfully updated!")
            return redirect('dashboard')
    else:
        if user.is_admin:
            user_form = AdminProfileEditForm(instance=user)
            profile_form = None
        elif user.is_doctor:
            user_form = UserProfileEditForm(instance=user)
            profile_form = DoctorProfileEditForm(instance=user.doctor_profile)
        else:
            user_form = UserProfileEditForm(instance=user)
            profile_form = RegularUserProfileEditForm(instance=user.user_profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'is_doctor': user.is_doctor,
        'is_admin': user.is_admin,
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

class PrescriptionForm(forms.ModelForm):
    """Form for creating prescriptions"""
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False)
    
    class Meta:
        model = Prescription
        fields = ('notes',)

class PrescriptionItemForm(forms.ModelForm):
    """Form for prescription items"""
    product = forms.ModelChoiceField(
        queryset=Product.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    dosage = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    duration = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = PrescriptionItem
        fields = ('product', 'dosage', 'duration')

@login_required
def doctor_patients(request):
    """View for doctors to see their patients"""
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can access this page.")
        return redirect('dashboard')
    
    # Get all consultations for this doctor
    consultations = Consultation.objects.filter(
        doctor=request.user.doctor_profile,
        is_active=True
    ).select_related('user')
    
    # Get unique patients
    patients = User.objects.filter(
        user_consultations__doctor=request.user.doctor_profile,
        user_consultations__is_active=True
    ).distinct()
    
    return render(request, 'doctor_patients.html', {'patients': patients})

@login_required
def create_prescription(request, patient_id):
    """Create a new prescription for a patient"""
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can create prescriptions.")
        return redirect('dashboard')
    
    patient = get_object_or_404(User, id=patient_id)
    products = Product.objects.all()
    
    if request.method == 'POST':
        prescription_form = PrescriptionForm(request.POST)
        item_forms = []
        
        # Get the number of items from the form
        num_items = int(request.POST.get('num_items', 0))
        
        if prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.doctor = request.user.doctor_profile
            prescription.patient = patient
            prescription.save()
            
            # Process each prescription item
            for i in range(num_items):
                product_id = request.POST.get(f'item-{i}-product')
                dosage = request.POST.get(f'item-{i}-dosage')
                duration = request.POST.get(f'item-{i}-duration')
                
                if product_id and dosage and duration:
                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        product_id=product_id,
                        dosage=dosage,
                        duration=duration
                    )
            
            messages.success(request, "Prescription created successfully!")
            return redirect('doctor_patients')
    else:
        prescription_form = PrescriptionForm()
        item_form = PrescriptionItemForm()
    
    return render(request, 'create_prescription.html', {
        'prescription_form': prescription_form,
        'item_form': item_form,
        'patient': patient,
        'products': products
    })

@login_required
def view_prescriptions(request):
    """View prescriptions for the current user"""
    user = request.user
    
    if user.is_doctor:
        prescriptions = Prescription.objects.filter(doctor=user.doctor_profile)
        template = 'doctor_prescriptions.html'
    else:
        prescriptions = Prescription.objects.filter(patient=user)
        template = 'user_prescriptions.html'
    
    return render(request, template, {'prescriptions': prescriptions})

@login_required
def prescription_detail(request, prescription_id):
    """View details of a specific prescription"""
    prescription = get_object_or_404(Prescription, id=prescription_id)
    user = request.user
    
    # Check if user has permission to view this prescription
    if user != prescription.patient and (not user.is_doctor or user.doctor_profile != prescription.doctor):
        messages.error(request, "You don't have permission to view this prescription.")
        return redirect('dashboard')
    
    items = PrescriptionItem.objects.filter(prescription=prescription).select_related('product')
    
    return render(request, 'prescription_detail.html', {
        'prescription': prescription,
        'items': items
    })

class ProductForm(forms.ModelForm):
    """Form for adding/editing products"""
    class Meta:
        model = Product
        fields = ('name', 'description')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

@login_required
def manage_products(request):
    """View for admins to manage products"""
    if not request.user.is_admin:
        messages.error(request, "Only administrators can manage products.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Product added successfully!")
            return redirect('manage_products')
    else:
        form = ProductForm()
    
    products = Product.objects.all().order_by('name')
    return render(request, 'manage_products.html', {
        'form': form,
        'products': products
    })

@login_required
def edit_product(request, product_id):
    """View for editing existing products"""
    if not request.user.is_admin:
        messages.error(request, "Only administrators can edit products.")
        return redirect('dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form.save()
            messages.success(request, "Product updated successfully!")
            return redirect('manage_products')
    else:
        form = ProductForm(instance=product)
    
    return render(request, 'edit_product.html', {
        'form': form,
        'product': product
    })

@login_required
def delete_product(request, product_id):
    """View for deleting products"""
    if not request.user.is_admin:
        messages.error(request, "Only administrators can delete products.")
        return redirect('dashboard')
    
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == 'POST':
        product.delete()
        messages.success(request, "Product deleted successfully!")
        return redirect('manage_products')
    
    return render(request, 'delete_product.html', {
        'product': product
    })
