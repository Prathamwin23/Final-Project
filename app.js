// Field Operations Management System - JavaScript
class FieldOperationsApp {
    constructor() {
        this.currentUser = null;
        this.managerMap = null;
        this.agentMap = null;
        this.websocketConnected = true;
        this.currentAssignment = null;
        
        // Sample Data
        this.users = [
            {id: 1, username: "manager1", user_type: "manager", email: "manager@company.com"},
            {id: 2, username: "agent1", user_type: "agent", phone: "9876543210", current_lat: 12.9716, current_lng: 77.5946},
            {id: 3, username: "agent2", user_type: "agent", phone: "9876543211", current_lat: 12.9758, current_lng: 77.6070}
        ];
        
        this.clients = [
            {id: 1, name: "John Doe", phone: "9876543210", address: "123 Main St, Bangalore", latitude: 12.9716, longitude: 77.5946, priority: 3, status: "pending"},
            {id: 2, name: "Jane Smith", phone: "9876543211", address: "456 MG Road, Bangalore", latitude: 12.9758, longitude: 77.6070, priority: 2, status: "assigned"},
            {id: 3, name: "Bob Wilson", phone: "9876543212", address: "789 Brigade Road, Bangalore", latitude: 12.9698, longitude: 77.6205, priority: 1, status: "completed"},
            {id: 4, name: "Alice Johnson", phone: "9876543213", address: "321 Commercial St, Bangalore", latitude: 12.9833, longitude: 77.5833, priority: 2, status: "pending"},
            {id: 5, name: "Charlie Brown", phone: "9876543214", address: "654 Residency Road, Bangalore", latitude: 12.9667, longitude: 77.6000, priority: 1, status: "pending"}
        ];
        
        this.assignments = [
            {id: 1, agent_id: 2, client_id: 2, status: "in_progress", assigned_at: "2025-07-29T10:30:00Z", client_name: "Jane Smith"},
            {id: 2, agent_id: 3, client_id: 3, status: "completed", assigned_at: "2025-07-29T09:00:00Z", completed_at: "2025-07-29T11:30:00Z", client_name: "Bob Wilson"}
        ];
        
        this.statistics = {
            total_clients: 15,
            pending_clients: 8,
            active_agents: 12,
            active_assignments: 5
        };
        
        this.init();
    }
    
    init() {
        this.setupEventListeners();
        this.simulateRealTimeUpdates();
        this.updateConnectionStatus();
    }
    
    setupEventListeners() {
        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });
        
        // Global key listener for demo shortcuts
        document.addEventListener('keydown', (e) => {
            if (e.ctrlKey && e.key === 'r') {
                e.preventDefault();
                this.refreshData();
            }
        });
    }
    
    handleLogin() {
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        
        if (!username || !password) {
            this.showNotification('Please enter username and password', 'error');
            return;
        }
        
        const user = this.users.find(u => u.username === username);
        if (user) {
            this.currentUser = user;
            document.getElementById('currentUser').textContent = `Welcome, ${user.username}`;
            this.showDashboard(user.user_type);
            this.showNotification(`Logged in successfully as ${user.user_type}`, 'success');
        } else {
            this.showNotification('Invalid credentials', 'error');
        }
    }
    
    showDashboard(userType) {
        document.getElementById('loginPage').style.display = 'none';
        
        if (userType === 'manager') {
            document.getElementById('managerDashboard').style.display = 'block';
            document.getElementById('agentDashboard').style.display = 'none';
            this.initManagerDashboard();
        } else {
            document.getElementById('agentDashboard').style.display = 'block';
            document.getElementById('managerDashboard').style.display = 'none';
            this.initAgentDashboard();
        }
    }
    
    initManagerDashboard() {
        this.updateStatistics();
        this.updateAgentStatus();
        this.updateAssignmentsTable();
        this.initManagerMap();
        this.populateAssignmentDropdowns();
    }
    
    initAgentDashboard() {
        this.updateCurrentAssignment();
        this.updateAgentHistory();
        this.initAgentMap();
    }
    
    updateStatistics() {
        document.getElementById('totalClients').textContent = this.statistics.total_clients;
        document.getElementById('pendingClients').textContent = this.statistics.pending_clients;
        document.getElementById('activeAgents').textContent = this.statistics.active_agents;
        document.getElementById('activeAssignments').textContent = this.statistics.active_assignments;
    }
    
    updateAgentStatus() {
        const agentStatusContainer = document.getElementById('agentStatus');
        const agents = this.users.filter(u => u.user_type === 'agent');
        
        agentStatusContainer.innerHTML = agents.map(agent => {
            const assignment = this.assignments.find(a => a.agent_id === agent.id && a.status !== 'completed');
            const status = assignment ? 'busy' : 'available';
            const statusClass = status === 'busy' ? 'warning' : 'success';
            
            return `
                <div class="agent-card card mb-2">
                    <div class="card-body p-3">
                        <div class="d-flex align-items-center">
                            <div class="agent-avatar">
                                ${agent.username.charAt(0).toUpperCase()}
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="mb-1">${agent.username}</h6>
                                <p class="mb-0 text-muted">${agent.phone}</p>
                            </div>
                            <div>
                                <span class="badge bg-${statusClass}">${status}</span>
                            </div>
                        </div>
                        ${assignment ? `<div class="mt-2"><small class="text-muted">Assigned to: ${assignment.client_name}</small></div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
    }
    
    updateAssignmentsTable() {
        const tableBody = document.getElementById('assignmentsTable');
        
        tableBody.innerHTML = this.assignments.map(assignment => {
            const agent = this.users.find(u => u.id === assignment.agent_id);
            const client = this.clients.find(c => c.id === assignment.client_id);
            const statusClass = this.getStatusClass(assignment.status);
            const timeAgo = this.timeAgo(new Date(assignment.assigned_at));
            
            return `
                <tr>
                    <td>${agent ? agent.username : 'Unknown'}</td>
                    <td>${client ? client.name : 'Unknown'}</td>
                    <td><span class="status-badge ${statusClass}">${assignment.status}</span></td>
                    <td>${timeAgo}</td>
                </tr>
            `;
        }).join('');
    }
    
    initManagerMap() {
        if (this.managerMap) {
            this.managerMap.remove();
        }
        
        this.managerMap = L.map('managerMap').setView([12.9716, 77.5946], 12);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.managerMap);
        
        // Add agent markers
        this.users.filter(u => u.user_type === 'agent').forEach(agent => {
            const marker = L.marker([agent.current_lat, agent.current_lng])
                .addTo(this.managerMap)
                .bindPopup(`
                    <div>
                        <h6>${agent.username}</h6>
                        <p>Phone: ${agent.phone}</p>
                        <p>Status: Available</p>
                    </div>
                `);
        });
        
        // Add client markers
        this.clients.forEach(client => {
            const color = client.status === 'pending' ? 'red' : 
                         client.status === 'assigned' ? 'orange' : 'green';
            
            const marker = L.marker([client.latitude, client.longitude])
                .addTo(this.managerMap)
                .bindPopup(`
                    <div>
                        <h6>${client.name}</h6>
                        <p>${client.address}</p>
                        <p>Phone: ${client.phone}</p>
                        <p>Priority: ${this.getPriorityText(client.priority)}</p>
                        <p>Status: <span class="status-badge ${this.getStatusClass(client.status)}">${client.status}</span></p>
                    </div>
                `);
        });
    }
    
    initAgentMap() {
        if (this.agentMap) {
            this.agentMap.remove();
        }
        
        const agent = this.currentUser;
        this.agentMap = L.map('agentMap').setView([agent.current_lat, agent.current_lng], 13);
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors'
        }).addTo(this.agentMap);
        
        // Add agent location
        L.marker([agent.current_lat, agent.current_lng])
            .addTo(this.agentMap)
            .bindPopup(`<div><h6>Your Location</h6><p>${agent.username}</p></div>`)
            .openPopup();
        
        // Add current assignment location if exists
        const assignment = this.assignments.find(a => a.agent_id === agent.id && a.status !== 'completed');
        if (assignment) {
            const client = this.clients.find(c => c.id === assignment.client_id);
            if (client) {
                L.marker([client.latitude, client.longitude])
                    .addTo(this.agentMap)
                    .bindPopup(`
                        <div>
                            <h6>${client.name}</h6>
                            <p>${client.address}</p>
                            <p>Phone: ${client.phone}</p>
                        </div>
                    `);
                
                // Draw route line
                L.polyline([
                    [agent.current_lat, agent.current_lng],
                    [client.latitude, client.longitude]
                ], {color: 'blue', weight: 3}).addTo(this.agentMap);
            }
        }
    }
    
    updateCurrentAssignment() {
        const agent = this.currentUser;
        const assignment = this.assignments.find(a => a.agent_id === agent.id && a.status !== 'completed');
        const assignmentContainer = document.getElementById('currentAssignment');
        
        if (assignment) {
            const client = this.clients.find(c => c.id === assignment.client_id);
            this.currentAssignment = assignment;
            
            assignmentContainer.innerHTML = `
                <div class="assignment-detail">
                    <h6>Client: ${client.name}</h6>
                    <p class="text-muted mb-2">${client.address}</p>
                    <p class="mb-2"><strong>Phone:</strong> ${client.phone}</p>
                    <p class="mb-2"><strong>Priority:</strong> <span class="priority-${this.getPriorityClass(client.priority)}">${this.getPriorityText(client.priority)}</span></p>
                    <p class="mb-0"><strong>Status:</strong> <span class="status-badge ${this.getStatusClass(assignment.status)}">${assignment.status}</span></p>
                </div>
            `;
        } else {
            assignmentContainer.innerHTML = '<p class="text-muted">No active assignment</p>';
            this.currentAssignment = null;
        }
    }
    
    updateAgentHistory() {
        const agent = this.currentUser;
        const agentAssignments = this.assignments.filter(a => a.agent_id === agent.id);
        const historyTableBody = document.getElementById('agentHistory');
        
        historyTableBody.innerHTML = agentAssignments.map(assignment => {
            const client = this.clients.find(c => c.id === assignment.client_id);
            return `
                <tr>
                    <td>${client ? client.name : 'Unknown'}</td>
                    <td>${client ? client.address : 'Unknown'}</td>
                    <td><span class="status-badge ${this.getStatusClass(assignment.status)}">${assignment.status}</span></td>
                    <td>${this.formatDate(assignment.assigned_at)}</td>
                    <td>${assignment.completed_at ? this.formatDate(assignment.completed_at) : '-'}</td>
                </tr>
            `;        
        }).join('');
    }
    
    populateAssignmentDropdowns() {
        const agentSelect = document.getElementById('selectAgent');
        const clientSelect = document.getElementById('selectClient');
        
        // Populate agents
        const availableAgents = this.users.filter(u => u.user_type === 'agent');
        agentSelect.innerHTML = availableAgents.map(agent => 
            `<option value="${agent.id}">${agent.username}</option>`
        ).join('');
        
        // Populate pending clients
        const pendingClients = this.clients.filter(c => c.status === 'pending');
        clientSelect.innerHTML = pendingClients.map(client => 
            `<option value="${client.id}">${client.name} - ${client.address}</option>`
        ).join('');
    }
    
    // Action Functions
    autoAssign() {
        this.showNotification('Auto-assigning clients to available agents...', 'info');
        
        setTimeout(() => {
            const pendingClients = this.clients.filter(c => c.status === 'pending');
            const availableAgents = this.users.filter(u => u.user_type === 'agent' && 
                !this.assignments.some(a => a.agent_id === u.id && a.status !== 'completed'));
            
            if (pendingClients.length === 0) {
                this.showNotification('No pending clients to assign', 'warning');
                return;
            }
            
            if (availableAgents.length === 0) {
                this.showNotification('No available agents for assignment', 'warning');
                return;
            }
            
            // Simple auto-assignment logic
            const client = pendingClients[0];
            const agent = availableAgents[0];
            
            this.createAssignment(agent.id, client.id);
            this.showNotification(`Assigned ${client.name} to ${agent.username}`, 'success');
        }, 1000);
    }
    
    showManualAssign() {
        const modal = new bootstrap.Modal(document.getElementById('manualAssignModal'));
        modal.show();
    }
    
    confirmManualAssign() {
        const agentId = parseInt(document.getElementById('selectAgent').value);
        const clientId = parseInt(document.getElementById('selectClient').value);
        
        if (agentId && clientId) {
            this.createAssignment(agentId, clientId);
            
            const agent = this.users.find(u => u.id === agentId);
            const client = this.clients.find(c => c.id === clientId);
            
            this.showNotification(`Manually assigned ${client.name} to ${agent.username}`, 'success');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('manualAssignModal'));
            modal.hide();
        }
    }
    
    createAssignment(agentId, clientId) {
        const newAssignment = {
            id: this.assignments.length + 1,
            agent_id: agentId,
            client_id: clientId,
            status: 'assigned',
            assigned_at: new Date().toISOString(),
            client_name: this.clients.find(c => c.id === clientId).name
        };
        
        this.assignments.push(newAssignment);
        
        // Update client status
        const client = this.clients.find(c => c.id === clientId);
        if (client) client.status = 'assigned';
        
        // Update statistics
        this.statistics.pending_clients--;
        this.statistics.active_assignments++;
        
        this.refreshDashboard();
    }
    
    showUploadClients() {
        const modal = new bootstrap.Modal(document.getElementById('uploadClientsModal'));
        modal.show();
    }
    
    uploadClients() {
        const fileInput = document.getElementById('clientFile');
        
        if (!fileInput.files[0]) {
            this.showNotification('Please select a file to upload', 'error');
            return;
        }
        
        this.showNotification('Uploading client data...', 'info');
        
        setTimeout(() => {
            // Simulate file processing
            const newClients = [
                {id: this.clients.length + 1, name: "New Client 1", phone: "9876543215", address: "New Address 1, Bangalore", latitude: 12.9700, longitude: 77.5800, priority: 2, status: "pending"},
                {id: this.clients.length + 2, name: "New Client 2", phone: "9876543216", address: "New Address 2, Bangalore", latitude: 12.9800, longitude: 77.5900, priority: 1, status: "pending"}
            ];
            
            this.clients.push(...newClients);
            this.statistics.total_clients += newClients.length;
            this.statistics.pending_clients += newClients.length;
            
            this.showNotification(`Successfully uploaded ${newClients.length} new clients`, 'success');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('uploadClientsModal'));
            modal.hide();
            
            this.refreshDashboard();
        }, 2000);
    }
    
    // Agent Actions
    acceptAssignment() {
        if (!this.currentAssignment) {
            this.showNotification('No assignment to accept', 'warning');
            return;
        }
        
        this.currentAssignment.status = 'accepted';
        this.showNotification('Assignment accepted successfully', 'success');
        this.updateCurrentAssignment();
    }
    
    startAssignment() {
        if (!this.currentAssignment) {
            this.showNotification('No assignment to start', 'warning');
            return;
        }
        
        this.currentAssignment.status = 'in_progress';
        this.showNotification('Assignment started', 'success');
        this.updateCurrentAssignment();
    }
    
    completeAssignment() {
        if (!this.currentAssignment) {
            this.showNotification('No assignment to complete', 'warning');
            return;
        }
        
        this.currentAssignment.status = 'completed';
        this.currentAssignment.completed_at = new Date().toISOString();
        
        // Update client status
        const client = this.clients.find(c => c.id === this.currentAssignment.client_id);
        if (client) client.status = 'completed';
        
        this.statistics.active_assignments--;
        
        this.showNotification('Assignment completed successfully!', 'success');
        this.updateCurrentAssignment();
        this.updateAgentHistory();
    }
    
    shareLocation() {
        this.showNotification('Location shared with manager', 'info');
        
        // Simulate location update
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition((position) => {
                this.currentUser.current_lat = position.coords.latitude;
                this.currentUser.current_lng = position.coords.longitude;
                this.showNotification('Location updated successfully', 'success');
                this.initAgentMap();
            }, () => {
                this.showNotification('Location sharing enabled (simulated)', 'info');
            });
        } else {
            this.showNotification('Location sharing enabled (simulated)', 'info');
        }
    }
    
    refreshData() {
        this.showNotification('Refreshing data...', 'info');
        
        setTimeout(() => {
            this.refreshDashboard();
            this.showNotification('Data refreshed successfully', 'success');
        }, 1000);
    }
    
    refreshDashboard() {
        if (this.currentUser.user_type === 'manager') {
            this.updateStatistics();
            this.updateAgentStatus();
            this.updateAssignmentsTable();
            this.initManagerMap();
        } else {
            this.updateCurrentAssignment();
            this.updateAgentHistory();
            this.initAgentMap();
        }
    }
    
    logout() {
        this.currentUser = null;
        document.getElementById('loginPage').style.display = 'block';
        document.getElementById('managerDashboard').style.display = 'none';
        document.getElementById('agentDashboard').style.display = 'none';
        document.getElementById('currentUser').textContent = 'Welcome, Guest';
        document.getElementById('username').value = '';
        document.getElementById('password').value = '';
        this.showNotification('Logged out successfully', 'info');
    }
    
    // Utility Functions
    showNotification(message, type = 'info') {
        const notificationsContainer = document.getElementById('notifications');
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show notification ${type}`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        notificationsContainer.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }
    
    getStatusClass(status) {
        const statusClasses = {
            'pending': 'status-pending',
            'assigned': 'status-assigned',
            'accepted': 'status-assigned',
            'in_progress': 'status-in-progress',
            'completed': 'status-completed'
        };
        return statusClasses[status] || 'status-pending';
    }
    
    getPriorityClass(priority) {
        return priority === 1 ? 'high' : priority === 2 ? 'medium' : 'low';
    }
    
    getPriorityText(priority) {
        return priority === 1 ? 'High' : priority === 2 ? 'Medium' : 'Low';        
    }
    
    timeAgo(date) {
        const now = new Date();
        const diff = now - date;
        const minutes = Math.floor(diff / 60000);
        const hours = Math.floor(minutes / 60);
        
        if (hours > 0) return `${hours}h ago`;
        return `${minutes}m ago`;
    }
    
    formatDate(dateString) {
        return new Date(dateString).toLocaleString();
    }
    
    simulateRealTimeUpdates() {
        setInterval(() => {
            // Simulate random updates
            if (Math.random() > 0.95) {
                const messages = [
                    'New client request received',
                    'Agent location updated',
                    'Assignment status changed',
                    'Client contacted successfully'
                ];
                const randomMessage = messages[Math.floor(Math.random() * messages.length)];
                // Only show if user is logged in
                if (this.currentUser) {
                    this.showNotification(randomMessage, 'info');
                }
            }
        }, 10000);
    }
    
    updateConnectionStatus() {
        const statusElement = document.getElementById('connectionStatus');
        
        setInterval(() => {
            // Simulate connection status
            this.websocketConnected = Math.random() > 0.1; // 90% uptime
            
            if (this.websocketConnected) {
                statusElement.innerHTML = '<span class="badge bg-success"><i class="fas fa-wifi me-1"></i>Connected</span>';
            } else {
                statusElement.innerHTML = '<span class="badge bg-danger"><i class="fas fa-wifi me-1"></i>Disconnected</span>';
            }
        }, 5000);
    }
}

// Global Functions (for onclick handlers)
let app;

function logout() {
    if (app) app.logout();
}

function autoAssign() {
    if (app) app.autoAssign();
}

function showManualAssign() {
    if (app) app.showManualAssign();
}

function confirmManualAssign() {
    if (app) app.confirmManualAssign();
}

function showUploadClients() {
    if (app) app.showUploadClients();
}

function uploadClients() {
    if (app) app.uploadClients();
}

function refreshData() {
    if (app) app.refreshData();
}

function acceptAssignment() {
    if (app) app.acceptAssignment();
}

function startAssignment() {
    if (app) app.startAssignment();
}

function completeAssignment() {
    if (app) app.completeAssignment();
}

function shareLocation() {
    if (app) app.shareLocation();
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    app = new FieldOperationsApp();
    
    // Add some demo keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        if (e.altKey) {
            switch(e.key) {
                case '1':
                    e.preventDefault();
                    document.getElementById('username').value = 'manager1';
                    document.getElementById('password').value = 'password';
                    break;
                case '2':
                    e.preventDefault();
                    document.getElementById('username').value = 'agent1';
                    document.getElementById('password').value = 'password';
                    break;
                case '3':
                    e.preventDefault();
                    document.getElementById('username').value = 'agent2';
                    document.getElementById('password').value = 'password';    
                    break;
            }
        }
    });
    
    // Show initial help message
    setTimeout(() => {
        if (!app.currentUser) {
            app.showNotification('Demo shortcuts: Alt+1 (Manager), Alt+2 (Agent1), Alt+3 (Agent2)', 'info');
        }
    }, 2000);
});