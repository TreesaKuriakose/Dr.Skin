from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import User, Doctor, RegularUser, Consultation, Message, Product, Prescription, PrescriptionItem, DoctorAvailability, Payment
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django import forms
import time

class UserRegistrationForm(forms.ModelForm):
    """Form for user registration"""
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}))
    
    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
        }
    
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
    """Form for doctor registration"""
    class Meta:
        model = Doctor
        fields = ('profile_picture', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'gpay_id', 'is_available')
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Specialization'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Qualification'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Years of Experience'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01', 'placeholder': 'Consultation Fee'}),
            'gpay_id': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'GPay ID'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean_experience_years(self):
        years = self.cleaned_data.get('experience_years')
        if years is not None and years < 0:
            raise forms.ValidationError("Experience years cannot be negative")
        return years

    def clean_consultation_fee(self):
        fee = self.cleaned_data.get('consultation_fee')
        if fee is not None and fee < 0:
            raise forms.ValidationError("Consultation fee cannot be negative")
        return fee

class CustomLoginForm(AuthenticationForm):
    """Custom login form that uses email instead of username"""
    username = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

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
            
            # Log in user with specified backend
            login(request, user, backend='glowmeter_app.backends.EmailBackend')
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
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to access this page.")
        return redirect('home')
    
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        doctor_form = DoctorForm(request.POST)
        
        if user_form.is_valid() and doctor_form.is_valid():
            # Create user with email as username
            user = user_form.save(commit=False)
            user.is_doctor = True
            user.save()
            
            # Create doctor profile
            doctor = doctor_form.save(commit=False)
            doctor.user = user
            doctor.save()
            
            messages.success(request, f"Doctor registration successful! Email: {user.email}")
            return redirect('dashboard')
        else:
            # Print detailed form errors
            if not user_form.is_valid():
                for field, errors in user_form.errors.items():
                    for error in errors:
                        messages.error(request, f"User Form - {field}: {error}")
            if not doctor_form.is_valid():
                for field, errors in doctor_form.errors.items():
                    for error in errors:
                        messages.error(request, f"Doctor Form - {field}: {error}")
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
        form = CustomLoginForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')  # AuthenticationForm uses username field for email
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            
            if user is not None:
                login(request, user, backend='glowmeter_app.backends.EmailBackend')
                messages.success(request, f"Welcome back, {user.email}!")
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = CustomLoginForm()
    
    return render(request, 'login.html', {'form': form})

@login_required
def dashboard(request):
    """Dashboard view - redirects based on user type"""
    user = request.user
    
    if user.is_admin:
        # Get counts for statistics
        users_count = User.objects.filter(is_doctor=False, is_admin=False).count()
        doctors = Doctor.objects.all().select_related('user')  # Get all doctors with their user info
        doctors_count = doctors.count()
        consultations_count = Consultation.objects.count()
        products_count = Product.objects.count()
        
        # Get recent activities (last 10)
        recent_activities = []
        
        # Recent user registrations
        recent_users = User.objects.filter(is_doctor=False, is_admin=False).order_by('-date_joined')[:5]
        for user in recent_users:
            recent_activities.append({
                'type': 'registration',
                'user': user,
                'timestamp': user.date_joined,
                'message': f"New user registered: {user.first_name} {user.last_name}"
            })
        
        # Recent consultations
        recent_consultations = Consultation.objects.order_by('-started_at')[:5]
        for consultation in recent_consultations:
            recent_activities.append({
                'type': 'consultation',
                'user': consultation.user,
                'timestamp': consultation.started_at,
                'message': f"New consultation: {consultation.user.first_name} with Dr. {consultation.doctor.full_name}"
            })
        
        # Recent doctor registrations
        recent_doctors = Doctor.objects.order_by('-user__date_joined')[:5]
        for doctor in recent_doctors:
            recent_activities.append({
                'type': 'doctor',
                'user': doctor.user,
                'timestamp': doctor.user.date_joined,
                'message': f"New doctor registered: Dr. {doctor.full_name}"
            })
            
        # Sort all activities by timestamp, most recent first
        recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
        recent_activities = recent_activities[:10]  # Get only the 10 most recent activities
        
        context = {
            'users_count': users_count,
            'doctors': doctors,
            'doctors_count': doctors_count,
            'consultations_count': consultations_count,
            'products_count': products_count,
            'recent_activities': recent_activities,
        }
        return render(request, 'admin_dashboard.html', context)
    elif user.is_doctor:
        # Get active consultations for the doctor
        active_consultations = Consultation.objects.filter(
            doctor=user.doctor_profile,
            is_active=True
        ).select_related('user').order_by('-started_at')

        # Get recent consultations
        recent_consultations = Consultation.objects.filter(
            doctor=user.doctor_profile
        ).select_related('user').order_by('-started_at')[:5]

        # Get recent prescriptions
        recent_prescriptions = Prescription.objects.filter(
            doctor=user.doctor_profile
        ).select_related('patient').order_by('-created_at')[:5]

        # Count unread messages
        for consultation in active_consultations:
            consultation.unread_count = Message.objects.filter(
                consultation=consultation,
                is_read=False
            ).exclude(sender=user).count()

        context = {
            'active_consultations': active_consultations,
            'recent_consultations': recent_consultations,
            'recent_prescriptions': recent_prescriptions
        }
        return render(request, 'doctor_dashboard.html', context)
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
    """Form for editing doctor profile"""
    class Meta:
        model = Doctor
        fields = ('profile_picture', 'specialization', 'qualification', 'experience_years', 'consultation_fee', 'gpay_id', 'is_available')
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'step': '0.01'}),
            'gpay_id': forms.TextInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'})
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
    
    # Check if there's already an active consultation
    existing_consultation = Consultation.objects.filter(
        user=user, 
        doctor=doctor, 
        is_active=True
    ).first()
    
    if existing_consultation:
        # If there's an active consultation, check if payment is completed
        if hasattr(existing_consultation, 'payment') and existing_consultation.payment.status == 'completed':
            return redirect('consultation', consultation_id=existing_consultation.id)
        else:
            # If payment is pending, redirect to payment
            return redirect('payment', doctor_id=doctor_id)
    else:
        # Redirect to payment page for new consultation
        return redirect('payment', doctor_id=doctor_id)

@login_required
def payment_view(request, doctor_id):
    """Handle consultation payment"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    user = request.user
    
    if request.method == 'POST':
        gpay_id = request.POST.get('gpay_id')
        
        # Create new consultation
        consultation = Consultation.objects.create(
            user=user,
            doctor=doctor
        )
        
        # Create payment record
        payment = Payment.objects.create(
            consultation=consultation,
            amount=doctor.consultation_fee,
            status='pending'
        )
        
        # Simulate payment processing (in real app, integrate with GPay API)
        payment.status = 'completed'
        payment.gpay_transaction_id = f"GPAY_{int(time.time())}"
        payment.save()
        
        # Create first message
        Message.objects.create(
            consultation=consultation,
            sender=user,
            content=f"Hello Dr. {doctor.full_name}, I would like to start a consultation with you."
        )
        
        messages.success(request, "Payment successful! Starting consultation...")
        return redirect('consultation', consultation_id=consultation.id)
    
    return render(request, 'payment.html', {'doctor': doctor})

@login_required
def consultation_view(request, consultation_id):
    """View a specific consultation"""
    consultation = get_object_or_404(Consultation, id=consultation_id)
    user = request.user
    
    # Security check: only the user or the doctor involved can view the consultation
    if user != consultation.user and (not user.is_doctor or user.doctor_profile != consultation.doctor):
        messages.error(request, "You don't have permission to view this consultation.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        message_content = request.POST.get('message')
        if message_content:
            Message.objects.create(
                consultation=consultation,
                sender=user,
                content=message_content,
                is_read=False
            )
            return redirect('consultation', consultation_id=consultation.id)
    
    # Mark all unread messages as read for the current user
    Message.objects.filter(
        consultation=consultation,
        is_read=False
    ).exclude(sender=user).update(is_read=True)
    
    chat_messages = Message.objects.filter(consultation=consultation).order_by('timestamp')
    
    context = {
        'consultation': consultation,
        'chat_messages': chat_messages,
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
        
        if prescription_form.is_valid():
            prescription = prescription_form.save(commit=False)
            prescription.doctor = request.user.doctor_profile
            prescription.patient = patient
            prescription.save()
            
            # Get the number of items from the form
            num_items = int(request.POST.get('num_items', 0))
            
            # Process each prescription item
            for i in range(num_items):
                product_id = request.POST.get(f'item-{i}-product')
                dosage = request.POST.get(f'item-{i}-dosage')
                duration = request.POST.get(f'item-{i}-duration')
                instructions = request.POST.get(f'item-{i}-instructions', '')
                
                if product_id and dosage and duration:
                    PrescriptionItem.objects.create(
                        prescription=prescription,
                        product_id=product_id,
                        dosage=dosage,
                        duration=duration,
                        usage_instructions=instructions
                    )
            
            messages.success(request, "Prescription created successfully!")
            return redirect('doctor_patients')
    else:
        prescription_form = PrescriptionForm()
    
    return render(request, 'create_prescription.html', {
        'prescription_form': prescription_form,
        'patient': patient,
        'products': products
    })

@login_required
def view_prescriptions(request):
    """View prescriptions for the current user"""
    user = request.user
    
    if user.is_doctor:
        prescriptions = Prescription.objects.filter(doctor=user.doctor_profile).select_related('doctor', 'patient').prefetch_related('prescriptionitem_set', 'prescriptionitem_set__product')
        template = 'doctor_prescriptions.html'
    else:
        prescriptions = Prescription.objects.filter(patient=user).select_related('doctor').prefetch_related('prescriptionitem_set', 'prescriptionitem_set__product')
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
        fields = ('name', 'description', 'image')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

@login_required
def manage_products(request):
    """View for admins to manage products"""
    if not request.user.is_admin:
        messages.error(request, "Only administrators can manage products.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
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
        form = ProductForm(request.POST, request.FILES, instance=product)
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

@login_required
def view_doctor(request, doctor_id):
    """View doctor details - admin only"""
    if not request.user.is_admin:
        messages.error(request, "Only administrators can view doctor details.")
        return redirect('dashboard')
    
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Get doctor's statistics
    patients_count = User.objects.filter(
        user_consultations__doctor=doctor,
        user_consultations__is_active=True
    ).distinct().count()
    
    consultations_count = Consultation.objects.filter(doctor=doctor).count()
    active_consultations = Consultation.objects.filter(doctor=doctor, is_active=True).count()
    
    context = {
        'doctor': doctor,
        'patients_count': patients_count,
        'consultations_count': consultations_count,
        'active_consultations': active_consultations
    }
    
    return render(request, 'view_doctor.html', context)

@login_required
def edit_doctor(request, doctor_id):
    """Edit doctor profile"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Only allow the doctor to edit their own profile or admin to edit any profile
    if not (request.user.is_admin or request.user == doctor.user):
        messages.error(request, "You don't have permission to edit this profile.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=doctor.user)
        doctor_form = DoctorForm(request.POST, request.FILES, instance=doctor)
        
        if user_form.is_valid() and doctor_form.is_valid():
            user = user_form.save()
            doctor = doctor_form.save(commit=False)
            doctor.user = user
            doctor.save()
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('view_doctor', doctor_id=doctor.id)
    else:
        user_form = UserForm(instance=doctor.user)
        doctor_form = DoctorForm(instance=doctor)
    
    return render(request, 'edit_doctor.html', {
        'user_form': user_form,
        'doctor_form': doctor_form,
        'doctor': doctor
    })

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

@login_required
@user_passes_test(lambda u: u.is_superuser)
def manage_users(request):
    """View for admins to manage users"""
    regular_users = User.objects.filter(is_doctor=False, is_admin=False)
    
    context = {
        'users': regular_users,
    }
    return render(request, 'manage_users.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def view_user(request, user_id):
    """View user details - admin only"""
    user = get_object_or_404(User, id=user_id)
    
    # Get user's statistics
    consultations_count = Consultation.objects.filter(user=user).count()
    active_consultations = Consultation.objects.filter(user=user, is_active=True).count()
    prescriptions_count = Prescription.objects.filter(patient=user).count()
    
    context = {
        'viewed_user': user,
        'consultations_count': consultations_count,
        'active_consultations': active_consultations,
        'prescriptions_count': prescriptions_count,
    }
    
    return render(request, 'view_user.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    """Edit user details - admin only"""
    user = get_object_or_404(User, id=user_id)
    regular_user = RegularUser.objects.get(user=user)
    
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=user)
        profile_form = RegularUserForm(request.POST, request.FILES, instance=regular_user)
        
        if user_form.is_valid() and profile_form.is_valid():
            user = user_form.save()
            profile = profile_form.save(commit=False)
            profile.user = user
            profile.save()
            
            messages.success(request, 'User profile updated successfully.')
            return redirect('view_user', user_id=user.id)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserForm(instance=user)
        profile_form = RegularUserForm(instance=regular_user)

    return render(request, 'edit_user.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'viewed_user': user
    })

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    """Delete user - admin only"""
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.delete()
        messages.success(request, 'User deleted successfully.')
        return redirect('manage_users')
        
    return render(request, 'delete_user.html', {'user': user})

@login_required
def patient_history(request, patient_id):
    """View patient history - prescriptions and consultations"""
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can view patient history.")
        return redirect('dashboard')
    
    patient = get_object_or_404(User, id=patient_id)
    
    # Get all prescriptions for this patient by the current doctor
    prescriptions = Prescription.objects.filter(
        doctor=request.user.doctor_profile,
        patient=patient
    ).order_by('-created_at')
    
    # Get all consultations between this patient and the doctor
    consultations = Consultation.objects.filter(
        doctor=request.user.doctor_profile,
        user=patient
    ).order_by('-started_at')
    
    context = {
        'patient': patient,
        'prescriptions': prescriptions,
        'consultations': consultations
    }
    
    return render(request, 'patient_history.html', context)

@login_required
def manage_availability(request):
    """View for doctors to manage their availability"""
    if not request.user.is_doctor:
        messages.error(request, "Only doctors can manage their availability.")
        return redirect('dashboard')
    
    doctor = request.user.doctor_profile
    availabilities = DoctorAvailability.objects.filter(doctor=doctor).order_by('day', 'start_time')
    
    if request.method == 'POST':
        # Delete existing availabilities
        if request.POST.get('action') == 'delete':
            availability_id = request.POST.get('availability_id')
            DoctorAvailability.objects.filter(id=availability_id, doctor=doctor).delete()
            messages.success(request, "Time slot removed successfully!")
            return redirect('manage_availability')
        
        # Add new availability
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        
        if day and start_time and end_time:
            try:
                DoctorAvailability.objects.create(
                    doctor=doctor,
                    day=day,
                    start_time=start_time,
                    end_time=end_time
                )
                messages.success(request, "Time slot added successfully!")
            except Exception as e:
                messages.error(request, "Failed to add time slot. Please check your input.")
        else:
            messages.error(request, "Please fill in all fields.")
        
        return redirect('manage_availability')
    
    context = {
        'availabilities': availabilities,
        'days_of_week': DoctorAvailability.DAYS_OF_WEEK
    }
    return render(request, 'manage_availability.html', context)

@login_required
def view_doctor_availability(request, doctor_id):
    """View for patients to see doctor's availability schedule"""
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Get all availability slots for this doctor
    availabilities = DoctorAvailability.objects.filter(
        doctor=doctor
    ).order_by('day', 'start_time')
    
    context = {
        'doctor': doctor,
        'availabilities': availabilities
    }
    
    return render(request, 'doctor_availability.html', context)
