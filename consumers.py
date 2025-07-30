import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model

User = get_user_model()

class AgentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]
        if self.user.is_anonymous:
            await self.close()
            return
        
        if self.user.user_type == 'agent':
            self.group_name = f'agent_{self.user.id}'
        else:
            self.group_name = 'managers'
        
        # Join group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected as {self.user.username}'
        }))

    async def disconnect(self, close_code):
        # Leave group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'location_update':
                await self.handle_location_update(text_data_json)
            elif message_type == 'status_update':
                await self.handle_status_update(text_data_json)
            elif message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'timestamp': text_data_json.get('timestamp')
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON format'
            }))

    async def handle_location_update(self, data):
        """Handle location update from agent"""
        if self.user.user_type != 'agent':
            return
        
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude and longitude:
            # Update user location in database
            await self.update_user_location(latitude, longitude)
            
            # Broadcast location update to managers
            await self.channel_layer.group_send(
                'managers',
                {
                    'type': 'location_broadcast',
                    'message': {
                        'agent_id': self.user.id,
                        'agent_name': self.user.username,
                        'latitude': latitude,
                        'longitude': longitude,
                        'timestamp': data.get('timestamp')
                    }
                }
            )

    async def handle_status_update(self, data):
        """Handle status update from agent"""
        if self.user.user_type != 'agent':
            return
        
        assignment_id = data.get('assignment_id')
        status = data.get('status')
        
        if assignment_id and status:
            success = await self.update_assignment_status(assignment_id, status)
            
            if success:
                # Broadcast status update to managers
                await self.channel_layer.group_send(
                    'managers',
                    {
                        'type': 'status_broadcast',
                        'message': {
                            'assignment_id': assignment_id,
                            'agent_name': self.user.username,
                            'status': status,
                            'timestamp': data.get('timestamp')
                        }
                    }
                )

    # Group message handlers
    async def assignment_notification(self, event):
        """Handle assignment notifications"""
        await self.send(text_data=json.dumps({
            'type': 'assignment_notification',
            'data': event['message']
        }))

    async def status_update(self, event):
        """Handle status updates"""
        await self.send(text_data=json.dumps({
            'type': 'status_update', 
            'data': event['message']
        }))

    async def location_broadcast(self, event):
        """Handle location broadcasts (for managers)"""
        await self.send(text_data=json.dumps({
            'type': 'location_update',
            'data': event['message']
        }))

    async def status_broadcast(self, event):
        """Handle status broadcasts (for managers)"""
        await self.send(text_data=json.dumps({
            'type': 'status_broadcast',
            'data': event['message']
        }))

    # Database operations
    @database_sync_to_async
    def update_user_location(self, latitude, longitude):
        """Update user location in database"""
        from django.utils import timezone
        from .models import LocationLog
        
        self.user.current_latitude = latitude
        self.user.current_longitude = longitude
        self.user.last_location_update = timezone.now()
        self.user.save()
        
        # Log location
        LocationLog.objects.create(
            agent=self.user,
            latitude=latitude,
            longitude=longitude
        )

    @database_sync_to_async
    def update_assignment_status(self, assignment_id, status):
        """Update assignment status in database"""
        from .models import Assignment
        
        try:
            assignment = Assignment.objects.get(
                id=assignment_id,
                agent=self.user
            )
            
            if status == 'accepted':
                assignment.mark_accepted()
            elif status == 'in_progress':
                assignment.mark_started()
            elif status == 'completed':
                assignment.mark_completed()
            
            return True
        except Assignment.DoesNotExist:
            return False