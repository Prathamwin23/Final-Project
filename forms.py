from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Client, Assignment

class ClientUploadForm(forms.Form):
    file = forms.FileField(
        label='Excel File',
        help_text='Upload Excel file with columns: name, phone, address, latitude, longitude, priority (optional), email (optional)',
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.xlsx,.xls'
        })
    )

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['agent', 'client', 'notes']
        widgets = {
            'agent': forms.Select(attrs={'class': 'form-control'}),
            'client': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show available agents and pending clients
        self.fields['agent'].queryset = User.objects.filter(
            user_type='agent',
            is_active_agent=True
        ).exclude(
            assignments__status__in=['assigned', 'accepted', 'in_progress']
        )
        self.fields['client'].queryset = Client.objects.filter(status='pending')

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=15, required=False)
    user_type = forms.ChoiceField(choices=User.USER_TYPE_CHOICES, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone_number', 'user_type']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'user_type': forms.Select(attrs={'class': 'form-control'}),
        }

class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'phone', 'email', 'address', 'latitude', 'longitude', 'priority', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': 'any'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }