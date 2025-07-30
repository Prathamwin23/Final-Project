from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import math

# Custom User Model
class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('manager', 'Manager'),
        ('agent', 'Field Agent'),
    ]
    
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='agent')
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_active_agent = models.BooleanField(default=True)
    current_latitude = models.FloatField(null=True, blank=True)
    current_longitude = models.FloatField(null=True, blank=True)
    last_location_update = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"

# Client Model
class Client(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    name = models.CharField(max_length=200)
    phone = models.CharField(max_length=15)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    latitude = models.FloatField()
    longitude = models.FloatField()
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', 'created_at']
    
    def __str__(self):
        return f"{self.name} - {self.get_priority_display()}"
    
    def distance_from(self, latitude, longitude):
        """Calculate distance from given coordinates using Haversine formula"""
        if not all([self.latitude, self.longitude, latitude, longitude]):
            return float('inf')
        
        # Convert latitude and longitude from degrees to radians
        lat1, lon1, lat2, lon2 = map(math.radians, [latitude, longitude, self.latitude, self.longitude])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        return c * r

# Assignment Model
class Assignment(models.Model):
    STATUS_CHOICES = [
        ('assigned', 'Assigned'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assignments')
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='assignments')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    assigned_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    estimated_duration = models.IntegerField(null=True, blank=True, help_text="Estimated duration in minutes")
    
    class Meta:
        ordering = ['-assigned_at']
        unique_together = ['agent', 'client', 'status']
    
    def __str__(self):
        return f"{self.agent.username} -> {self.client.name} ({self.status})"
    
    def mark_accepted(self):
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
    
    def mark_started(self):
        self.status = 'in_progress'
        self.started_at = timezone.now()
        self.save()
    
    def mark_completed(self):
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.client.status = 'completed'
        self.client.save()
        self.save()

# Location Log Model (for tracking agent movements)
class LocationLog(models.Model):
    agent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='location_logs')
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    accuracy = models.FloatField(null=True, blank=True, help_text="GPS accuracy in meters")
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.agent.username} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

# Excel Import Log Model
class ImportLog(models.Model):
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file_name = models.CharField(max_length=200)
    upload_time = models.DateTimeField(auto_now_add=True)
    total_rows = models.IntegerField(default=0)
    successful_imports = models.IntegerField(default=0)
    failed_imports = models.IntegerField(default=0)
    error_details = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return f"Import {self.file_name} by {self.uploaded_by.username}"