# Sprint 1 Frontend Setup Guide

## ✅ Stories 1.3, 1.4, 1.5: React Frontend - COMPLETE!

### Files Created:
1. ✅ `src/services/api.js` - Axios configuration with interceptors
2. ✅ `src/services/authService.js` - Authentication API calls
3. ✅ `src/context/AuthContext.jsx` - Global auth state management
4. ✅ `src/components/PrivateRoute.jsx` - Protected route wrapper
5. ✅ `src/pages/Register.jsx` - Beautiful registration page
6. ✅ `src/pages/Login.jsx` - Clean login page
7. ✅ `src/pages/Dashboard.jsx` - Placeholder dashboard
8. ✅ `src/App.jsx` - Main app with routing
9. ✅ `.env.development` - Environment variables

---

##  Frontend Setup Instructions

### Step 1: Create React App (If Not Done)

```bash
# From project root
npm create vite@latest client -- --template react
cd client
```

### Step 2: Install Dependencies

```bash
# Core dependencies
npm install

# Router
npm install react-router-dom

# HTTP client
npm install axios

# Install Tailwind CSS (if not installed)
npm install tailwindcss @tailwindcss/vite
```

### Step 3: Configure Tailwind CSS

Update `vite.config.js`:
```javaScript
import { defineConfig } from 'vite'
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [
    tailwindcss(),
  ],
})
```

Import Tailwind CSS
Add an `@import` to your CSS file that imports Tailwind CSS.
```javaScript

@import "tailwindcss";
```

Update `tailwind.config.js`:

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#E8F5FF',
          100: '#B8DDFF',
          500: '#0066FF',
          600: '#0052CC',
          900: '#003D99',
        },
        secondary: {
          50: '#E6F9F0',
          500: '#00D68F',
          600: '#00B377',
        },
      },
    },
  },
  plugins: [],
}
```

Update `src/index.css`:

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

/* Custom scrollbar */
::-webkit-scrollbar {
  width: 8px;
}

::-webkit-scrollbar-track {
  background: #f1f1f1;
}

::-webkit-scrollbar-thumb {
  background: #888;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #555;
}
```

### Step 4: Create Project Structure

```bash
# Create all necessary directories
mkdir -p src/components
mkdir -p src/pages
mkdir -p src/services
mkdir -p src/context
mkdir -p src/utils
mkdir -p src/hooks
mkdir -p src/assets
```

### Step 5: Copy All Files

Copy all the artifacts I created into their respective locations:

```
src/
├── services/
│   ├── api.js
│   └── authService.js
├── context/
│   └── AuthContext.jsx
├── components/
│   └── PrivateRoute.jsx
├── pages/
│   ├── Register.jsx
│   ├── Login.jsx
│   └── Dashboard.jsx
├── App.jsx
└── main.jsx
```

### Step 6: Update main.jsx

Make sure `src/main.jsx` looks like this:

```javascript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### Step 7: Create Environment File

```bash
# Copy environment template
cp .env.development .env

# Edit if needed (should work as-is for local development)
```

### Step 8: Start Development Server

```bash
npm run dev
```

The app will be available at: **http://localhost:5173/**

---

##  Testing the Frontend

### 1. Test Registration Flow

1. Navigate to: http://localhost:5173/register
2. Fill in the registration form:
   - First Name: Faruk
   - Last Name: Idris
   - Email: faruk@example.com
   - Phone: +2348012345678
   - Password: SecurePass123!
   - Confirm Password: SecurePass123!
3. Click "Create Account"
4. Should redirect to Dashboard with success message

### 2. Test Login Flow

1. Navigate to: http://localhost:5173/login
2. Enter credentials:
   - Email: you@example.com
   - Password: SecurePass123!
3. Click "Sign In"
4. Should redirect to Dashboard

### 3. Test Protected Routes

1. Try accessing: http://localhost:5173/dashboard (without logging in)
2. Should redirect to Login page
3. After login, should access Dashboard successfully

### 4. Test Logout

1. On Dashboard, click "Logout" button
2. Should be logged out and redirected to Login page
3. Try accessing Dashboard again - should redirect to Login

---

##  UI Features Implemented

### Registration Page:
- ✅ Beautiful gradient background
- ✅ Real-time password strength indicator
- ✅ Phone number auto-formatting
- ✅ Show/hide password toggles
- ✅ Inline validation errors
- ✅ Loading states with spinner
- ✅ Responsive design (mobile-first)
- ✅ Smooth animations and transitions

### Login Page:
- ✅ Clean, modern design
- ✅ Show/hide password toggle
- ✅ Remember me checkbox
- ✅ Forgot password link (placeholder)
- ✅ Social login buttons (placeholders)
- ✅ Error handling with clear messages
- ✅ Loading states
- ✅ Responsive design

### Protected Routes:
- ✅ Authentication check before rendering
- ✅ Automatic token refresh
- ✅ Redirect to login if not authenticated
- ✅ Remember intended destination
- ✅ Loading state while checking auth

---

## 📱 Responsive Design

The app is fully responsive and works on:

- **Mobile**: 375px - 428px ✅
- **Tablet**: 768px - 1024px ✅
- **Desktop**: 1280px+ ✅

Test by resizing your browser or using device emulation in DevTools.

---

##  Security Features

1. **JWT Token Management**:
   - Tokens stored in localStorage
   - Automatic token refresh when expired
   - Token sent with every authenticated request

2. **Protected Routes**:
   - Routes require authentication
   - Automatic redirect to login
   - State preserved across redirects

3. **Password Security**:
   - Client-side validation
   - Password strength indicator
   - Minimum requirements enforced

4. **Error Handling**:
   - User-friendly error messages
   - Field-specific validation errors
   - Network error handling

---

##  Troubleshooting

### Issue: "Failed to fetch" or Network Error
**Solution**: Make sure Django backend is running on http://127.0.0.1:8000/

```bash
# In backend directory
python manage.py runserver
```

### Issue: CORS Error
**Solution**: Check that `CORS_ALLOWED_ORIGINS` in Django settings includes `http://localhost:5173`

### Issue: 404 on API calls
**Solution**: Verify `VITE_API_BASE_URL` in `.env` is correct:
```
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### Issue: Token not working
**Solution**: Clear localStorage and try logging in again:
```javascript
// In browser console:
localStorage.clear()
```

### Issue: Page not found
**Solution**: Make sure React Router is properly configured and you're using `BrowserRouter`

---

##  Acceptance Criteria Check

### Story 1.3: Registration Page
| Criteria | Status |
|----------|--------|
| Registration form with all required fields | ✅ |
| Client-side validation for email, password | ✅ |
| Password strength indicator | ✅ |
| Error messages displayed clearly | ✅ |
| Success redirect to dashboard | ✅ |
| Responsive design (mobile-friendly) | ✅ |

### Story 1.4: Login Page
| Criteria | Status |
|----------|--------|
| Login form with email and password | ✅ |
| Form validation | ✅ |
| Error handling for invalid credentials | ✅ |
| Success redirect to dashboard | ✅ |
| Remember me checkbox | ✅ |
| Responsive design | ✅ |

### Story 1.5: Protected Routes
| Criteria | Status |
|----------|--------|
| Private route component created | ✅ |
| Redirects to login if not authenticated | ✅ |
| Token refresh logic implemented | ✅ |
| Auth context/provider setup | ✅ |
| Works seamlessly with React Router | ✅ |

---
