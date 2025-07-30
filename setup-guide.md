# Field Operations Management System - Complete Setup Guide

## Step 1: Initial Setup

### 1.1 Navigate to your working directory
```bash
cd C:\Users\HP\dj23
```

### 1.2 Activate your environment
```bash
pushpa\Scripts\activate
```

### 1.3 Install required packages
```bash
pip install -r requirements.txt
```

### 1.4 Install Redis (for Django Channels)
Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
- Download Redis-x64-3.0.504.msi
- Install with default settings
- Redis will run on localhost:6379

### 1.5 Create Django Project
```bash
django-admin startproject field_ops_system
cd field_ops_system
python manage.py startapp operations
```

## Step 2: Project Structure
After running the commands above, your structure should look like:

```
C:\Users\HP\dj23\field_ops_system\
├── field_ops_system\
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── operations\
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── tests.py
│   └── views.py
├── templates\
├── static\
├── media\
└── manage.py
```

## Step 3: Create Required Directories
```bash
mkdir templates
mkdir static
mkdir static\css
mkdir static\js
mkdir media
mkdir operations\templates
mkdir operations\templates\operations
```

## Step 4: Database Setup
Your PostgreSQL database details:
- Database: btrdj24
- User: postgres
- Password: root
- Host: localhost
- Port: 5432

Make sure PostgreSQL is running on your system.

## Step 5: Apply the configuration files
Copy all the configuration files provided in the following steps to their respective locations.

## Step 6: Run migrations and start server
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Step 7: Start Redis Server
Open a new command prompt and run:
```bash
redis-server
```

## Step 8: Access the application
- Admin Panel: http://127.0.0.1:8000/admin/
- Agent Interface: http://127.0.0.1:8000/agent/
- Manager Dashboard: http://127.0.0.1:8000/

## Important Notes:
1. Make sure PostgreSQL service is running
2. Make sure Redis server is running
3. Create a superuser account for admin access
4. Import client data through admin panel using Excel files