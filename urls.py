from django.urls import path
from . import views

app_name = 'operations'

urlpatterns = [
    # Dashboard URLs
    path('', views.home, name='home'),
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    path('agent/', views.agent_dashboard, name='agent_dashboard'),
    
    # Assignment URLs
    path('auto-assign/', views.auto_assign_clients, name='auto_assign_clients'),
    path('manual-assign/', views.manual_assign, name='manual_assign'),
    path('upload-clients/', views.upload_clients, name='upload_clients'),
    
    # AJAX URLs
    path('update-location/', views.update_location, name='update_location'),
    path('update-assignment-status/', views.update_assignment_status, name='update_assignment_status'),
    path('get-route/', views.get_route, name='get_route'),
]