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
    """Doctor model extending User model"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    profile_picture = models.ImageField(upload_to='doctors/', null=True, blank=True)
    specialization = models.CharField(max_length=100, default='General')
    qualification = models.CharField(max_length=200, default='MBBS')
    experience_years = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    gpay_id = models.CharField(max_length=100, blank=True)
    
    @property
    def full_name(self):
        """Return the doctor's full name"""
        return f"Dr. {self.user.first_name} {self.user.last_name}".strip()
    
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
    image = models.ImageField(upload_to='products/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
    usage_instructions = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.product.name} - {self.dosage}"

class DoctorAvailability(models.Model):
    """Model for doctor's available time slots"""
    DAYS_OF_WEEK = [
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
        ('Sunday', 'Sunday'),
    ]
    
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='availabilities')
    day = models.CharField(max_length=10, choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    
    class Meta:
        ordering = ['day', 'start_time']
        unique_together = ['doctor', 'day', 'start_time', 'end_time']
    
    def __str__(self):
        return f"{self.doctor.full_name} - {self.day} ({self.start_time} - {self.end_time})"

class Payment(models.Model):
    """Payment model for consultation fees"""
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    consultation = models.OneToOneField(Consultation, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    gpay_transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Payment for consultation {self.consultation.id} - {self.status}"

class Feedback(models.Model):
    """Feedback model for user reviews and ratings"""
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.IntegerField(choices=RATING_CHOICES)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    reply = models.TextField(blank=True, null=True)
    replied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='feedback_replies')
    replied_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback by {self.user.get_full_name()} - {self.rating} stars"
