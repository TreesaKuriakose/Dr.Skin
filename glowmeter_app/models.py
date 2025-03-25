from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    def _create_user(self, email, password=None, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_admin', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """Custom User model with email as the unique identifier."""
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    profile_picture = models.ImageField(upload_to='admins/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_doctor = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Doctor(models.Model):
    """Doctor model linked to User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    full_name = models.CharField(max_length=100)
    specialty = models.CharField(max_length=100)
    bio = models.TextField()
    profile_picture = models.ImageField(upload_to='doctors/', null=True, blank=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return self.full_name

class RegularUser(models.Model):
    """Regular user model linked to User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='user_profile')
    full_name = models.CharField(max_length=100)
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    
    def __str__(self):
        return self.full_name

class Consultation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_consultations')
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='doctor_consultations')
    started_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Consultation between {self.user.email} and Dr. {self.doctor.full_name}"

class Message(models.Model):
    consultation = models.ForeignKey(Consultation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Message from {self.sender.email} at {self.timestamp}"

class Product(models.Model):
    """Product model for prescriptions"""
    name = models.CharField(max_length=200)
    description = models.TextField()
    usage_instructions = models.TextField()
    
    def __str__(self):
        return self.name

class Prescription(models.Model):
    """Prescription model for doctor's prescriptions"""
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='prescriptions')
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='prescriptions')
    products = models.ManyToManyField(Product, through='PrescriptionItem')
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"Prescription by Dr. {self.doctor.full_name} for {self.patient.email}"

class PrescriptionItem(models.Model):
    """Individual items in a prescription"""
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.product.name} - {self.dosage}"
