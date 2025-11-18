# Captive Portal System

A comprehensive captive portal solution integrating Django backend, Vue.js frontend, and Mikrotik RouterOS.

## Architecture

This project consists of three main components:

- **Backend** (Django + DRF): REST API for user management, authentication, and RADIUS integration
- **Frontend** (Vue 3 + TypeScript): User-facing captive portal interface
- **Mikrotik Agent** (Node.js + Express): Mikrotik RouterOS API integration service

## Features

- User authentication with JWT
- Mikrotik Hotspot integration via RouterOS API
- RADIUS authentication and accounting
- Voucher-based guest access
- Session management and tracking
- Device tracking and management
- Real-time monitoring of active connections
- Admin dashboard for user and session management

## Prerequisites

- Python 3.10+
- Node.js 20+
- PostgreSQL (or SQLite for development)
- Mikrotik RouterOS device with API enabled

## Installation

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd frontend/portail-captif

# Install dependencies
npm install

# Configure environment (if needed)
cp .env.example .env

# Start development server
npm run dev
```

### 3. Mikrotik Agent Setup

```bash
cd mikrotik-agent

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your Mikrotik credentials

# Start the agent
npm start

# Or for development with auto-reload
npm run dev
```

## Configuration

### Backend (.env)

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=captive_portal
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# Mikrotik
MIKROTIK_HOST=192.168.88.1
MIKROTIK_PORT=8728
MIKROTIK_USERNAME=admin
MIKROTIK_PASSWORD=your-password

# RADIUS
RADIUS_SERVER=127.0.0.1
RADIUS_SECRET=testing123
```

### Mikrotik Agent (.env)

```env
PORT=3001
MIKROTIK_HOST=192.168.88.1
MIKROTIK_PORT=8728
MIKROTIK_USERNAME=admin
MIKROTIK_PASSWORD=your-password
```

## API Documentation

### Backend API Endpoints

- `POST /api/auth/login/` - User authentication
- `POST /api/auth/register/` - User registration
- `GET /api/users/` - List users
- `GET /api/sessions/` - List active sessions
- `GET /api/devices/` - List registered devices
- `POST /api/vouchers/` - Create voucher
- `GET /api/vouchers/validate/{code}` - Validate voucher

### Mikrotik Agent API Endpoints

- `GET /api/mikrotik/test` - Test connection
- `GET /api/mikrotik/hotspot/users` - List hotspot users
- `POST /api/mikrotik/hotspot/users` - Add hotspot user
- `PUT /api/mikrotik/hotspot/users/:username` - Update user
- `DELETE /api/mikrotik/hotspot/users/:username` - Remove user
- `GET /api/mikrotik/hotspot/active` - List active sessions
- `DELETE /api/mikrotik/hotspot/active/:id` - Disconnect session

## Database Models

### Core Models

- **User**: Extended Django user model with MAC address, phone, etc.
- **Device**: Connected device information
- **Session**: User session tracking with data usage
- **Voucher**: Guest access voucher codes

### Mikrotik Models

- **MikrotikRouter**: Router configuration
- **MikrotikHotspotUser**: Hotspot user accounts
- **MikrotikActiveConnection**: Active connection tracking
- **MikrotikLog**: Operation logs

### RADIUS Models

- **RadiusServer**: RADIUS server configuration
- **RadiusAuthLog**: Authentication logs
- **RadiusAccounting**: Accounting records
- **RadiusClient**: NAS client configuration

## Development

### Running Tests

```bash
# Backend tests
cd backend
python manage.py test

# Frontend tests
cd frontend/portail-captif
npm run test:unit
```

### Code Formatting

```bash
# Backend (using black)
cd backend
black .

# Frontend (using prettier)
cd frontend/portail-captif
npm run format
```

## Production Deployment

(TODO: Add Docker configuration and deployment instructions)

## Mikrotik Configuration

Enable API on your Mikrotik router:

```
/ip service
set api address=0.0.0.0/0 disabled=no port=8728
```

Create API user:

```
/user add name=api-user group=full password=your-password
```

## License

ISC

## Contributing

(TODO: Add contribution guidelines)

## Support

For issues and questions, please open an issue on GitHub.
