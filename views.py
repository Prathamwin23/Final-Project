from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from django.core.paginator import Paginator
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import json
import pandas as pd
import math
from .models import User, Client, Assignment, LocationLog, ImportLog
from .forms import ClientUploadForm, AssignmentForm

# Home page - redirects based on user type
@login_required
def home(request):
    if request.user.user_type == 'manager':
        return redirect('manager_dashboard')
    else:
        return redirect('agent_dashboard')

# Manager Dashboard
@login_required
def manager_dashboard(request):
    if request.user.user_type != 'manager':
        messages.error(request, "Access denied. Managers only.")
        return redirect('agent_dashboard')
    
    # Get statistics
    total_clients = Client.objects.count()
    pending_clients = Client.objects.filter(status='pending').count()
    active_agents = User.objects.filter(user_type='agent', is_active_agent=True).count()
    active_assignments = Assignment.objects.filter(status__in=['assigned', 'accepted', 'in_progress']).count()
    
    # Get recent assignments
    recent_assignments = Assignment.objects.select_related('agent', 'client').order_by('-assigned_at')[:10]
    
    # Get all agents with their current assignments
    agents = User.objects.filter(user_type='agent').prefetch_related('assignments')
    agents_data = []
    for agent in agents:
        current_assignment = agent.assignments.filter(
            status__in=['assigned', 'accepted', 'in_progress']
        ).first()
        agents_data.append({
            'agent': agent,
            'current_assignment': current_assignment,
            'last_update': agent.last_location_update
        })
    
    context = {
        'total_clients': total_clients,
        'pending_clients': pending_clients,
        'active_agents': active_agents,
        'active_assignments': active_assignments,
        'recent_assignments': recent_assignments,
        'agents_data': agents_data,
    }
    
    return render(request, 'operations/manager_dashboard.html', context)

# Agent Dashboard
@login_required
def agent_dashboard(request):
    if request.user.user_type != 'agent':
        messages.error(request, "Access denied. Agents only.")
        return redirect('manager_dashboard')
    
    # Get current assignment
    current_assignment = Assignment.objects.filter(
        agent=request.user,
        status__in=['assigned', 'accepted', 'in_progress']
    ).select_related('client').first()
    
    # Get assignment history
    assignment_history = Assignment.objects.filter(
        agent=request.user
    ).select_related('client').order_by('-assigned_at')[:10]
    
    context = {
        'current_assignment': current_assignment,
        'assignment_history': assignment_history,
    }
    
    return render(request, 'operations/agent_dashboard.html', context)

# Auto-assign clients to agents
@login_required
def auto_assign_clients(request):
    if request.user.user_type != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Get available agents
    available_agents = User.objects.filter(
        user_type='agent',
        is_active_agent=True
    ).exclude(
        assignments__status__in=['assigned', 'accepted', 'in_progress']
    )
    
    # Get pending clients
    pending_clients = Client.objects.filter(status='pending').order_by('-priority')
    
    assignments_created = 0
    
    for client in pending_clients:
        if not available_agents.exists():
            break
        
        # Find closest agent
        best_agent = None
        min_distance = float('inf')
        
        for agent in available_agents:
            if agent.current_latitude and agent.current_longitude:
                distance = client.distance_from(agent.current_latitude, agent.current_longitude)
                if distance < min_distance:
                    min_distance = distance
                    best_agent = agent
        
        # Assign client to best agent
        if best_agent:
            assignment = Assignment.objects.create(
                agent=best_agent,
                client=client,
                status='assigned'
            )
            client.status = 'assigned'
            client.save()
            
            # Remove agent from available list
            available_agents = available_agents.exclude(id=best_agent.id)
            assignments_created += 1
            
            # Send real-time notification
            send_assignment_notification(assignment)
    
    return JsonResponse({
        'success': True,
        'assignments_created': assignments_created,
        'message': f'{assignments_created} assignments created successfully.'
    })

# Manual assignment
@login_required
def manual_assign(request):
    if request.user.user_type != 'manager':
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    if request.method == 'POST':
        agent_id = request.POST.get('agent_id')
        client_id = request.POST.get('client_id')
        
        try:
            agent = User.objects.get(id=agent_id, user_type='agent')
            client = Client.objects.get(id=client_id, status='pending')
            
            # Check if agent is available
            existing_assignment = Assignment.objects.filter(
                agent=agent,
                status__in=['assigned', 'accepted', 'in_progress']
            ).exists()
            
            if existing_assignment:
                return JsonResponse({'error': 'Agent is already assigned to another client'}, status=400)
            
            assignment = Assignment.objects.create(
                agent=agent,
                client=client,
                status='assigned'
            )
            client.status = 'assigned'
            client.save()
            
            # Send real-time notification
            send_assignment_notification(assignment)
            
            return JsonResponse({
                'success': True,
                'message': f'Client {client.name} assigned to {agent.username}'
            })
            
        except (User.DoesNotExist, Client.DoesNotExist) as e:
            return JsonResponse({'error': 'Invalid agent or client'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Upload clients from Excel
@login_required
def upload_clients(request):
    if request.user.user_type != 'manager':
        messages.error(request, "Access denied. Managers only.")
        return redirect('home')
    
    if request.method == 'POST':
        form = ClientUploadForm(request.POST, request.FILES)
        if form.is_valid():
            excel_file = request.FILES['file']
            
            try:
                # Read Excel file
                df = pd.read_excel(excel_file)
                
                # Expected columns: name, phone, email, address, latitude, longitude, priority
                required_columns = ['name', 'phone', 'address', 'latitude', 'longitude']
                
                if not all(col in df.columns for col in required_columns):
                    messages.error(request, f"Excel file must contain columns: {', '.join(required_columns)}")
                    return redirect('upload_clients')
                
                successful_imports = 0
                failed_imports = 0
                error_details = []
                
                for index, row in df.iterrows():
                    try:
                        # Clean and validate data
                        name = str(row['name']).strip()
                        phone = str(row['phone']).strip()
                        address = str(row['address']).strip()
                        latitude = float(row['latitude'])
                        longitude = float(row['longitude'])
                        
                        # Optional fields
                        email = str(row.get('email', '')).strip() if pd.notna(row.get('email')) else ''
                        priority = int(row.get('priority', 2)) if pd.notna(row.get('priority')) else 2
                        
                        # Validate priority
                        if priority not in [1, 2, 3, 4]:
                            priority = 2
                        
                        # Create client
                        Client.objects.create(
                            name=name,
                            phone=phone,
                            email=email if email else None,
                            address=address,
                            latitude=latitude,
                            longitude=longitude,
                            priority=priority
                        )
                        successful_imports += 1
                        
                    except Exception as e:
                        failed_imports += 1
                        error_details.append(f"Row {index + 2}: {str(e)}")
                
                # Log the import
                ImportLog.objects.create(
                    uploaded_by=request.user,
                    file_name=excel_file.name,
                    total_rows=len(df),
                    successful_imports=successful_imports,
                    failed_imports=failed_imports,
                    error_details='\n'.join(error_details) if error_details else None
                )
                
                if successful_imports > 0:
                    messages.success(request, f"Successfully imported {successful_imports} clients.")
                if failed_imports > 0:
                    messages.warning(request, f"{failed_imports} rows failed to import. Check import logs for details.")
                
                return redirect('manager_dashboard')
                
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
                return redirect('upload_clients')
    else:
        form = ClientUploadForm()
    
    return render(request, 'operations/upload_clients.html', {'form': form})

# Update agent location (AJAX)
@csrf_exempt
@login_required
def update_location(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            latitude = float(data.get('latitude'))
            longitude = float(data.get('longitude'))
            accuracy = data.get('accuracy')
            
            # Update user location
            request.user.current_latitude = latitude
            request.user.current_longitude = longitude
            request.user.last_location_update = timezone.now()
            request.user.save()
            
            # Log location
            LocationLog.objects.create(
                agent=request.user,
                latitude=latitude,
                longitude=longitude,
                accuracy=accuracy
            )
            
            return JsonResponse({'success': True})
            
        except (ValueError, KeyError) as e:
            return JsonResponse({'error': 'Invalid location data'}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Update assignment status (AJAX)
@csrf_exempt
@login_required
def update_assignment_status(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            assignment_id = data.get('assignment_id')
            new_status = data.get('status')
            notes = data.get('notes', '')
            
            assignment = get_object_or_404(Assignment, id=assignment_id, agent=request.user)
            
            if new_status == 'accepted':
                assignment.mark_accepted()
            elif new_status == 'in_progress':
                assignment.mark_started()
            elif new_status == 'completed':
                assignment.mark_completed()
                assignment.notes = notes
                assignment.save()
            
            # Send real-time update
            send_status_update(assignment)
            
            return JsonResponse({'success': True, 'message': 'Status updated successfully'})
            
        except Assignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Get route data (AJAX)
@login_required
def get_route(request):
    if request.method == 'GET':
        start_lat = request.GET.get('start_lat')
        start_lng = request.GET.get('start_lng')
        end_lat = request.GET.get('end_lat')
        end_lng = request.GET.get('end_lng')
        
        # For now, return a simple direct route
        # In production, you would use OpenRouteService API here
        route_data = {
            'coordinates': [
                [float(start_lng), float(start_lat)],
                [float(end_lng), float(end_lat)]
            ],
            'distance': calculate_distance(float(start_lat), float(start_lng), float(end_lat), float(end_lng)),
            'duration': 0  # Calculate based on distance and speed
        }
        
        return JsonResponse(route_data)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

# Helper functions
def send_assignment_notification(assignment):
    """Send real-time notification about new assignment"""
    channel_layer = get_channel_layer()
    
    # Send to specific agent
    async_to_sync(channel_layer.group_send)(
        f'agent_{assignment.agent.id}',
        {
            'type': 'assignment_notification',
            'message': {
                'type': 'new_assignment',
                'assignment_id': assignment.id,
                'client_name': assignment.client.name,
                'client_address': assignment.client.address,
                'client_phone': assignment.client.phone,
                'client_lat': assignment.client.latitude,
                'client_lng': assignment.client.longitude,
                'priority': assignment.client.get_priority_display(),
            }
        }
    )
    
    # Send to managers
    async_to_sync(channel_layer.group_send)(
        'managers',
        {
            'type': 'assignment_notification',
            'message': {
                'type': 'assignment_created',
                'agent_name': assignment.agent.username,
                'client_name': assignment.client.name,
                'assignment_id': assignment.id,
            }
        }
    )

def send_status_update(assignment):
    """Send real-time status update"""
    channel_layer = get_channel_layer()
    
    async_to_sync(channel_layer.group_send)(
        'managers',
        {
            'type': 'status_update',
            'message': {
                'type': 'status_changed',
                'assignment_id': assignment.id,
                'agent_name': assignment.agent.username,
                'client_name': assignment.client.name,
                'new_status': assignment.status,
            }
        }
    )

def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two points using Haversine formula"""
    # Convert latitude and longitude from degrees to radians
    lat1, lng1, lat2, lng2 = map(math.radians, [lat1, lng1, lat2, lng2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    return c * r