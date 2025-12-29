# Zellpay Django Backend

Enterprise-level Django payment gateway backend with clean architecture.

## 🏗️ Architecture

```
backend/
 ├── manage.py
 ├── backend/                 # Django project settings
 │    ├── settings/
 │    │    ├── base.py       # Base settings
 │    │    ├── dev.py        # Development settings
 │    │    └── prod.py       # Production settings
 │    ├── urls.py
 │    └── wsgi.py
 ├── payment/                 # Payment Django app
 │    ├── models/            # Django ORM Models
 │    ├── gateways/          # Payment gateway adapters
 │    ├── services/          # Business logic layer
 │    ├── verification/      # Payment verification handlers
 │    ├── api/               # REST API (Views, Serializers, URLs)
 │    ├── tasks/             # Celery async tasks
 │    └── utils/             # Utilities (Redis, hashing)
 └── requirements.txt
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
cd backend
cp .env.example .env
# Edit .env with your configuration
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Database Setup

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Development Server

```bash
python manage.py runserver
```

### 5. Using Docker Compose

```bash
docker-compose up -d
```

## 📡 API Endpoints

### Initialize Payment
```
POST /api/v1/payments/initialize/
```

**Request:**
```json
{
  "amount": 150000,
  "currency": "IRR",
  "gateway": 1,
  "order_id": "1234-567",
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "description": "Payment for order"
}
```

**Response:**
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "redirect_url": "https://gateway.com/payment/...",
  "authority_code": "A00000000000000000000000000000000000000"
}
```

### Verify Payment
```
POST /api/v1/payments/verify/
```

**Request:**
```json
{
  "payment_id": "550e8400-e29b-41d4-a716-446655440000",
  "callback_data": {
    "Authority": "A00000000000000000000000000000000000000",
    "Status": "OK"
  }
}
```

### Get Payment Status
```
GET /api/v1/payments/{payment_id}/status/
```

## 📚 API Documentation

- Swagger UI: http://localhost:8000/swagger/
- ReDoc: http://localhost:8000/redoc/

## 🔧 Configuration

All configuration is done via environment variables in `.env` file:

- Database settings (PostgreSQL)
- Redis settings
- Payment gateway credentials
- Cache TTL settings

## 🧪 Testing

```bash
python manage.py test payment
```

## 📦 Features

- ✅ Django ORM Models for transactions
- ✅ REST API with DRF
- ✅ Redis-based caching and idempotency
- ✅ Payment state machine
- ✅ Gateway adapters (Zarinpal, Stripe, PayPal)
- ✅ Async verification with Celery
- ✅ Swagger/OpenAPI documentation
- ✅ Docker Compose setup
- ✅ Production-ready settings

## 🔐 Security

- Idempotency key validation
- Double-spending prevention
- Transaction state machine
- Webhook signature verification (to be implemented)

## 📝 License

Proprietary

