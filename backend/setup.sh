""" Pemon - Setup Script
    This script automates the initial setup of the Pemon
    Run this script after cloning the repository
"""

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored messages
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "================================================================================"
echo "           Pemon - Automated Setup"
echo "================================================================================"
echo ""

# Step 1: Check Prerequisites

print_message "Checking prerequisites..."

# Check Python
if ! command_exists python3; then
    print_error "Python 3 is not installed. Please install Python 3.x"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
print_message "Python version: $PYTHON_VERSION ✓"

# Check pip
if ! command_exists pip3; then
    print_error "pip is not installed. Please install pip"
    exit 1
fi
print_message "pip is installed ✓"

# Check PostgreSQL
if ! command_exists psql; then
    print_warning "PostgreSQL command-line tools not found. Make sure PostgreSQL is installed."
else
    print_message "PostgreSQL is installed ✓"
fi

# Check Redis
if ! command_exists redis-cli; then
    print_warning "Redis command-line tools not found. Make sure Redis is installed."
else
    print_message "Redis is installed ✓"
fi

# Check Node.js (optional for backend-only setup)
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_message "Node.js version: $NODE_VERSION ✓"
else
    print_warning "Node.js not found. Frontend setup will be skipped."
fi

echo ""

# Step 2: Create Virtual Environment

print_message "Creating Python virtual environment..."

if [ -d "env" ]; then
    print_warning "Virtual environment already exists. Skipping creation."
else
    python3 -m venv env
    print_message "Virtual environment created ✓"
fi

# Activate virtual environment
print_message "Activating virtual environment..."
source env/bin/activate
print_message "Virtual environment activated ✓"

echo ""

# Step 3: Install Python Dependencies

print_message "Installing Python dependencies..."

if [ -f "requirements.txt" ]; then
    pip install --upgrade pip
    pip install -r requirements.txt
    print_message "Python dependencies installed ✓"
else
    print_error "requirements.txt not found!"
    exit 1
fi

echo ""

# Step 4: Setup Environment Variables

print_message "Setting up environment variables..."

if [ -f ".env" ]; then
    print_warning ".env file already exists. Skipping creation."
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_message ".env file created from template ✓"
        print_warning "Please edit .env file with your configuration before proceeding!"
    else
        print_error ".env.example not found!"
        exit 1
    fi
fi

echo ""

# Step 5: Create Required Directories

print_message "Creating required directories..."

mkdir -p logs
mkdir -p media
mkdir -p staticfiles
mkdir -p static

print_message "Directories created ✓"

echo ""

# Step 6: Database Setup

print_message "Setting up database..."

# Check if .env has been configured
if grep -q "your-password" .env; then
    print_warning "Please configure your .env file before running database migrations!"
    print_warning "Skipping database setup."
else
    # Run migrations
    print_message "Running database migrations..."
    python manage.py migrate
    print_message "Database migrations completed ✓"
fi

echo ""

# Step 7: Create Superuser (Optional)

read -p "Do you want to create a superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_message "Creating superuser..."
    python manage.py createsuperuser
fi

echo ""

# Step 8: Frontend Setup (Optional)

if command_exists npm; then
    read -p "Do you want to setup the frontend? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [ -d "pemon-frontend" ]; then
            print_message "Setting up frontend..."
            cd pemon-frontend
            
            # Install dependencies
            npm install
            print_message "Frontend dependencies installed ✓"
            
            # Setup environment file
            if [ ! -f ".env.development" ]; then
                if [ -f ".env.example" ]; then
                    cp .env.example .env.development
                    print_message "Frontend .env.development created ✓"
                fi
            fi
            
            cd ..
        else
            print_warning "Frontend directory not found. Skipping frontend setup."
        fi
    fi
fi

echo ""

# Step 9: Test Redis Connection

if command_exists redis-cli; then
    print_message "Testing Redis connection..."
    if redis-cli ping > /dev/null 2>&1; then
        print_message "Redis is running ✓"
    else
        print_warning "Redis is not running. Please start Redis server:"
        print_warning "  macOS: brew services start redis"
        print_warning "  Linux: sudo systemctl start redis"
        print_warning "  Windows: Run redis-server.exe"
    fi
fi

echo ""

# Setup Complete

echo "================================================================================"
echo "                    Setup Complete! "
echo "================================================================================"
echo ""
echo "Next steps:"
echo ""
echo "1. Edit .env file with your configuration"
echo "2. Start Redis server (if not running)"
echo "3. Run the development server:"
echo "   $ source env/bin/activate"
echo "   $ python manage.py runserver"
echo ""
echo "4. In a new terminal, start Celery worker:"
echo "   $ source env/bin/activate"
echo "   $ celery -A pemon worker --loglevel=info"
echo ""
echo "5. In another terminal, start Celery beat:"
echo "   $ source env/bin/activate"
echo "   $ celery -A pemon beat --loglevel=info"
echo ""

if [ -d "client" ]; then
    echo "6. Start the frontend (in a new terminal):"
    echo "   $ cd pemon-frontend"
    echo "   $ npm run dev"
    echo ""
fi

echo "Access the application:"
echo "  - Backend API: http://127.0.0.1:8000/"
echo "  - Admin Panel: http://127.0.0.1:8000/admin/"
echo "  - API Docs: http://127.0.0.1:8000/api/docs/"
if [ -d "pemon-frontend" ]; then
    echo "  - Frontend: http://localhost:5173/"
fi
echo ""
