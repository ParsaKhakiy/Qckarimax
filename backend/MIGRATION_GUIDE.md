# Migration Guide: From Legacy App to Django Backend

This guide explains how the existing payment logic from `/app/` has been preserved and refactored into the Django backend.

## 📋 Mapping Overview

### Models Layer
**Before:** `app/models/transaction.py` (dataclass)
**After:** `backend/payment/models/transaction.py` (Django ORM)

- ✅ All fields preserved (transaction_uuid, order_id, user_id, gateway_id, amount, currency, etc.)
- ✅ Status flags preserved (is_done, is_added_wallet, is_refund)
- ✅ Added TransactionEvent model for audit logging
- ✅ Added proper database indexes and constraints

### Gateways Layer
**Before:** `app/gateways/zarinpal.py`, `app/gateways/stripe.py`, `app/gateways/paypal.py`
**After:** `backend/payment/gateways/zarinpal_gateway.py`, etc.

- ✅ All gateway logic preserved
- ✅ Same API request/response structure
- ✅ Same error handling
- ✅ Configuration moved to Django settings

### Transaction Handlers
**Before:** `app/transacion/handler.py` (RequestZarinpallHandeler)
**After:** `backend/payment/services/transaction_service.py` (TransactionService)

**Key Changes:**
- ✅ Business logic preserved
- ✅ Database operations use Django ORM instead of raw SQL
- ✅ Same transaction flow: create → save → cache → verify
- ✅ Idempotency checks preserved

### Verification Handlers
**Before:** `app/verification/hamdler.py` (VerifyZarinpallHandeler)
**After:** `backend/payment/verification/zarinpal_verifier.py` (ZarinpalVerifier)

- ✅ Verification logic preserved
- ✅ Same gateway verification flow
- ✅ Same status update logic
- ✅ Idempotency validation preserved

### Redis/Caching
**Before:** `app/models/interface.py` (RedisManager, RedisHandler)
**After:** `backend/payment/utils/redis_client.py` (RedisClient)

- ✅ Same caching strategy
- ✅ Same key patterns: `payment:transaction:{uuid}`, `payment:state:{uuid}`
- ✅ Same TTL management
- ✅ Idempotency key caching preserved

### Services
**Before:** `app/services/manager.py` (PaymentManager)
**After:** `backend/payment/services/transaction_service.py` (TransactionService)

- ✅ Gateway selection logic preserved
- ✅ Payment creation flow preserved
- ✅ Enhanced with Django ORM integration

## 🔄 Business Logic Preservation

### Payment Flow (Unchanged)

1. **Initialize Payment**
   - Validate input → Check idempotency → Create gateway request → Save transaction → Cache → Return redirect URL
   - ✅ All steps preserved

2. **Verify Payment**
   - Get transaction → Check if already verified → Verify with gateway → Update status → Remove cache → Log event
   - ✅ All steps preserved

3. **Idempotency**
   - Check Redis cache → Check database → Set in cache
   - ✅ Same logic, now in `IdempotencyManager`

### State Machine (Unchanged)

```
new → created → pending → completed → completed_and_added
                      ↓
                   failed
                      ↓
                  refunded
```

- ✅ All states preserved
- ✅ Status calculation logic preserved

## 🆕 New Features (Django Benefits)

1. **Django ORM**
   - Automatic migrations
   - Better query optimization
   - Built-in admin interface

2. **REST API**
   - Standardized endpoints
   - Request/response validation
   - Swagger documentation

3. **Celery Integration**
   - Async verification tasks
   - Background job processing
   - Retry mechanisms

4. **Settings Management**
   - Environment-based configuration
   - Separate dev/prod settings
   - Better security practices

## 🔧 Configuration Migration

### Database
**Before:** `app/models/interface.py` (DatabaseConfig, PostgresDatabaseManager)
**After:** Django `DATABASES` setting

### Redis
**Before:** `app/models/interface.py` (RedisConfig, RedisManager)
**After:** Django `REDIS_*` settings + `payment.utils.redis_client`

### Gateway Settings
**Before:** Hardcoded in gateway classes
**After:** `PAYMENT_SETTINGS` in Django settings

## 📝 API Endpoints

The new API provides the same functionality as the legacy system:

| Legacy | New API |
|--------|---------|
| Manual gateway calls | `POST /api/v1/payments/initialize/` |
| Manual verification | `POST /api/v1/payments/verify/` |
| Database queries | `GET /api/v1/payments/{id}/status/` |

## ✅ Testing Checklist

- [ ] Payment initialization works
- [ ] Gateway redirect URLs are correct
- [ ] Payment verification works
- [ ] Idempotency prevents duplicates
- [ ] Redis caching works
- [ ] Transaction status updates correctly
- [ ] Event logging works
- [ ] Error handling is proper

## 🚀 Next Steps

1. Run migrations: `python manage.py migrate`
2. Test API endpoints
3. Verify gateway integrations
4. Monitor Redis and database connections
5. Set up Celery workers for async tasks

