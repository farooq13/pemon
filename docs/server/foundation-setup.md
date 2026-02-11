# Pemon

A comprehensive fintech platform offering digital wallet services, P2P transfers, bill payments, merchant payment acceptance, agent networks, savings plans, and more.

##  Features

- **Digital Wallet** - Secure wallet management with virtual account numbers
- **P2P Transfers** - Instant money transfers between users
- **Bill Payments** - Airtime, data, electricity, cable TV payments
- **Merchant Services** - Payment links, QR codes, business analytics
- **Agent Network** - Cash-in/cash-out services with POS integration
- **Savings Plans** - Fixed, target, and group savings with interest
- **KYC Verification** - Multi-tier verification system
- **Transaction Ledger** - Double-entry accounting system
- **Security** - JWT authentication, encryption, fraud detection
- **API Documentation** - Swagger/OpenAPI documentation

## Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.11+** - [Download Python](https://www.python.org/downloads/)
- **Node.js 18+** - [Download Node.js](https://nodejs.org/)
- **PostgreSQL 14+** - [Download PostgreSQL](https://www.postgresql.org/download/)
- **Redis 6+** - [Download Redis](https://redis.io/download/)
- **Git** - [Download Git](https://git-scm.com/downloads/)

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/farooq13/pemon.git
cd pemon
```

### 2. Backend Setup (Django)

```bash
# Create virtual environment
python3 -m venv env

# Activate virtual environment
# On macOS/Linux:
source env/bin/activate
# On Windows:
env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables template
cp .env.example .env

# Edit .env file with your configuration
nano .env  # or use your preferred editor
```

### 3. Database Setup

```bash
# Create PostgreSQL database
createdb pemon_db

# Or using psql:
psql -U postgres
CREATE DATABASE pemon_db;
\q

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 4. Redis Setup

```bash
# Start Redis server
# On macOS (with Homebrew):
brew services start redis

# On Ubuntu/Debian:
sudo systemctl start redis

# On Windows:
# Run redis-server.exe from your Redis installation directory

# Verify Redis is running:
redis-cli ping
# Should return: PONG
```

### 5. Frontend Setup (React)

```bash
# Navigate to client directory
cd client

# Install dependencies
npm install

# Copy environment variables template
cp .env.example .env.development

# Edit .env.development with your configuration
nano .env.development
```

## Running the Application

### Development Mode

You'll need **4 terminal windows** to run all services:

#### Terminal 1: Django Development Server

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Run Django development server
python manage.py runserver
```

Server will be available at: http://127.0.0.1:8000/

#### Terminal 2: Celery Worker

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Start Celery worker
celery -A pemon worker --loglevel=info
```

#### Terminal 3: Celery Beat (Scheduled Tasks)

```bash
# Make sure virtual environment is activated
source env/bin/activate

# Start Celery beat scheduler
celery -A pemon beat --loglevel=info
```

#### Terminal 4: React Development Server

```bash
# Navigate to client directory
cd client

# Start React dev server
npm run dev
```


##  Environment Variables

### Backend (.env)

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
DJANGO_SETTINGS_MODULE=pemon.settings.development

# Database
DATABASE_NAME=pemon_db
DATABASE_USER=postgres
DATABASE_PASSWORD=your-password
DATABASE_HOST=localhost
DATABASE_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Security
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173

# JWT
JWT_ACCESS_TOKEN_LIFETIME_MINUTES=60
JWT_REFRESH_TOKEN_LIFETIME_DAYS=7

# Email (Development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### Frontend (.env.development)

```env
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
VITE_API_TIMEOUT=30000
```



## Security
- JWT token-based authentication
- Encrypted sensitive fields (BVN, NIN)
- Rate limiting on API endpoints
- CSRF protection
- SQL injection prevention (Django ORM)
- XSS protection
- Input validation and sanitization
- Audit logging for critical operations

## Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in production settings
- [ ] Configure production database
- [ ] Set up environment variables securely
- [ ] Configure static file serving (WhiteNoise or CDN)
- [ ] Set up HTTPS/SSL certificates
- [ ] Configure email service (SendGrid, etc.)
- [ ] Set up SMS provider (Termii, Twilio)
- [ ] Configure Sentry for error monitoring
- [ ] Set up backup and disaster recovery
- [ ] Run security audit
- [ ] Load test the application
- [ ] Set up CI/CD pipeline

## License

This project is proprietary software. All rights reserved.



## Support

For support and questions:
- Email: fidbyte@gmail.com


## Roadmap

- [x] Sprint 0: Foundation Setup
- [ ] Sprint 1: User Authentication & Registration
- [ ] Sprint 2: KYC Tier 1 (Basic)
- [ ] Sprint 3: Wallet Creation & Balance
- [ ] Sprint 4: Transaction Ledger Foundation
- [ ] Sprint 5: Internal P2P Transfers
- [ ] Sprint 6: Transaction History UI
- [ ] Sprint 7: Airtime & Data Purchase
- [ ] Sprint 8: Utility Bill Payments
- [ ] Sprint 9: Merchant Account Setup
- [ ] Sprint 10: Payment Links & QR Codes

---

**Built with ❤️ by Faruk**