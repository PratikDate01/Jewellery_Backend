# 💎 Jewellery Backend

A robust Django REST Framework backend API for a jewellery e-commerce platform with MongoDB integration, featuring secure authentication, image management with Cloudinary, and comprehensive filtering capabilities.

## 📋 Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Getting Started](#getting-started)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## ✨ Features

- **Django REST Framework** - Powerful RESTful API framework
- **MongoDB Integration** - NoSQL database with django-mongodb-backend
- **JWT Authentication** - Secure token-based authentication
- **CORS Support** - Cross-Origin Resource Sharing enabled
- **Image Management** - Cloudinary integration for image upload and storage
- **Advanced Filtering** - Django filter for flexible API queries
- **Database Migrations** - Alembic support for database versioning
- **Production Ready** - Gunicorn, WhiteNoise for static files
- **HTTPS Security** - Environment-based configuration

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.8+ | Language |
| Django | Latest | Web framework |
| Django REST Framework | Latest | API framework |
| MongoDB | 4.0+ | Database |
| Pymongo | Latest | MongoDB driver |
| Cloudinary | Latest | Image storage |
| djangorestframework-simplejwt | Latest | JWT authentication |
| Gunicorn | Latest | WSGI server |
| WhiteNoise | Latest | Static file serving |

## 📦 Prerequisites

- **Python** (3.8 or higher) - [Download](https://www.python.org/downloads/)
- **MongoDB** (4.0 or higher) - [Download](https://www.mongodb.com/try/download/community) or [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
- **pip** (Python package manager)
- **Git** - [Download](https://git-scm.com/)

## 🔧 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/PratikDate01/Jewellery_Backend.git
   cd Jewellery_Backend
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create environment variables**
   ```bash
   cp .env.example .env
   ```

5. **Configure your .env file** with:
   - MongoDB connection string
   - Cloudinary credentials
   - Django secret key
   - CORS settings

## 🚀 Getting Started

### Development Mode

Start the development server:

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

### Create Database Tables

```bash
python manage.py migrate
```

### Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

### Running Tests

```bash
python manage.py test
```

## 📚 API Documentation

### Base URL
```
http://localhost:8000/api
```

### Authentication
Include JWT token in the Authorization header:

```
Authorization: Bearer <your_jwt_token>
```

### Key Endpoints

#### Authentication
- `POST /auth/register/` - Register new user
- `POST /auth/login/` - Login and get JWT token
- `POST /auth/refresh/` - Refresh JWT token

#### Products
- `GET /products/` - List all products
- `GET /products/<id>/` - Get product details
- `POST /products/` - Create new product (admin only)
- `PUT /products/<id>/` - Update product (admin only)
- `DELETE /products/<id>/` - Delete product (admin only)

#### Orders
- `GET /orders/` - List user orders
- `POST /orders/` - Create new order
- `GET /orders/<id>/` - Get order details

#### Filters
- `/products/?category=jewelry` - Filter by category
- `/products/?price_min=100&price_max=1000` - Filter by price range
- `/products/?search=diamond` - Search products

## 📁 Project Structure

```
Jewellery_Backend/
├── app/
│   ├── models.py            # Database models
│   ├── views.py             # API views
│   ├── serializers.py       # Serializers
│   ├── urls.py              # URL routing
│   └── filters.py           # Custom filters
├── config/
│   ├── settings.py          # Django settings
│   ├── urls.py              # Project URLs
│   └── wsgi.py              # WSGI configuration
├── .env.example             # Environment variables template
├── manage.py                # Django management
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```env
# Django Configuration
SECRET_KEY=your_secret_key_here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database_name
MONGO_DB_NAME=jewellery_db

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# JWT
JWT_SECRET=your_jwt_secret_key

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com

# Email (Optional)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
```

## 🚀 Deployment

### Deploy to Heroku

1. **Install Heroku CLI**
   ```bash
   # Download from https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Login and create app**
   ```bash
   heroku login
   heroku create your-app-name
   ```

3. **Set environment variables**
   ```bash
   heroku config:set SECRET_KEY=your_secret_key
   heroku config:set MONGODB_URI=your_mongo_uri
   # ... set other variables
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

### Deploy with Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🤝 Contributing

We welcome contributions! Follow these steps:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/amazing-feature`)
3. **Commit your changes** (`git commit -m 'Add amazing feature'`)
4. **Push to the branch** (`git push origin feature/amazing-feature`)
5. **Open a Pull Request**

## 📄 License

This project is licensed under the ISC License.

## 🆘 Support

- **Issues** - [GitHub Issues](https://github.com/PratikDate01/Jewellery_Backend/issues)
- **Documentation** - Check the docs folder

## 🔗 Related Projects

- [Jewellery Frontend](https://github.com/PratikDate01/Jwellery_Frontend)

---

Made with ❤️ by the Jewellery Team
