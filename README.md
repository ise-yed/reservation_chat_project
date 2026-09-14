# Reservation API

A full-featured backend system for appointment booking, service providers, availability management, notifications, reminders, mock payments, transaction logs, and audit logs.

The project is built with Django and Django REST Framework. It uses JWT authentication, PostgreSQL as the main database, Celery and Redis for background jobs, django-celery-beat for scheduled tasks, and drf-spectacular for Swagger and Redoc API documentation.

This backend can be used for appointment-based businesses such as clinics, doctors, consultants, coaches, salons, training centers, or any organization that needs provider-based scheduling and reservation management.

---

## Table of Contents

- [Main Features](#main-features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Applications](#applications)
- [User Roles](#user-roles)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [PostgreSQL Setup](#postgresql-setup)
- [Migrations](#migrations)
- [Running the Server](#running-the-server)
- [Celery and Reminders](#celery-and-reminders)
- [Running Tests](#running-tests)
- [API Documentation](#api-documentation)
- [Main System Flow](#main-system-flow)
- [API Endpoints](#api-endpoints)
- [Main Database Models](#main-database-models)
- [Business Rules](#business-rules)
- [Notifications and Reminders](#notifications-and-reminders)
- [Payments](#payments)
- [Audit Logs](#audit-logs)
- [Error Handling](#error-handling)
- [Pagination, Search, and Ordering](#pagination-search-and-ordering)
- [Security Notes](#security-notes)
- [Manual Test Scenarios](#manual-test-scenarios)
- [Useful Commands](#useful-commands)
- [Final Presentation Notes](#final-presentation-notes)

---

## Main Features

- User registration and login with JWT authentication
- Custom user model with role-based access control
- User roles: `customer`, `provider`, `staff`, `org_admin`, and `super_admin`
- Organization and branch management
- Provider profile management inside organizations
- Offering/service management for providers
- Provider working hours, time off, organization holidays, and available slot generation
- Appointment creation, cancellation, detail view, and status updates
- Prevention of duplicate reservations in the same time range
- Support for buffer time before and after each offering
- Event-driven notification system with support for in-app, email, SMS, and push channels
- Email reminder system for upcoming appointments
- Internal mock payment system with payment status updates and refund support
- Payment transaction logging
- Audit logging for important system operations
- Swagger UI and Redoc API documentation
- Unit and API tests with pytest

---

## Tech Stack

```text
Language: Python
Framework: Django 5.2
API Framework: Django REST Framework
Authentication: JWT / SimpleJWT
Database: PostgreSQL
Async Tasks: Celery
Broker: Redis
Scheduled Tasks: django-celery-beat
API Documentation: drf-spectacular, Swagger UI, Redoc
Testing: pytest, pytest-django
Configuration: python-decouple
```

---

## Project Structure

```text
reservation_project/
├── apps/
│   ├── common/
│   ├── users/
│   ├── authentication/
│   ├── organizations/
│   ├── providers/
│   ├── offerings/
│   ├── availability/
│   ├── appointments/
│   ├── notifications/
│   ├── payments/
│   └── audit/
│
├── config/
│   ├── settings/
│   │   ├── base.py
│   │   ├── dev.py
│   │   ├── test.py
│   │   └── prod.py
│   ├── urls.py
│   ├── celery.py
│   ├── asgi.py
│   └── wsgi.py
│
├── requirements/
│   ├── base.txt
│   ├── dev.txt
│   ├── test.txt
│   └── prod.txt
│
├── manage.py
├── pytest.ini
├── .env.example
└── README.md
```

---

## Applications

| App | Responsibility |
| --- | --- |
| `common` | Shared base models, pagination, and custom exception handling |
| `users` | Custom user model and user roles |
| `authentication` | Register, login, refresh token, password change, and password reset |
| `organizations` | Organization and branch management |
| `providers` | Provider profiles inside organizations |
| `offerings` | Bookable services for providers |
| `availability` | Working hours, time off, holidays, and available slot generation |
| `appointments` | Appointment booking, cancellation, view, and status changes |
| `notifications` | Event-driven in-app and email notifications |
| `payments` | Mock payments, payment transactions, refunds, and payment notifications |
| `audit` | Audit logs for important system events |

---

## User Roles

Roles are defined in `apps/users/enums.py`:

```text
customer
provider
staff
org_admin
super_admin
```

Public registration only allows:

```text
customer
provider
```

| Role | Description |
| --- | --- |
| `customer` | A normal user who can book appointments and make payments |
| `provider` | A service provider who can have a provider profile |
| `staff` | Internal staff user |
| `org_admin` | Organization administrator |
| `super_admin` | High-level system administrator |
| `is_superuser` | Full Django admin-level permission |

---

## Installation

### 1. Open the project directory

```bash
cd path/to/reservation_project
```

### 2. Create and activate a virtual environment

Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

Linux or macOS:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

For development:

```bash
pip install -r requirements/dev.txt
```

For tests:

```bash
pip install -r requirements/test.txt
```

For production:

```bash
pip install -r requirements/prod.txt
```

---

## Environment Variables

Copy `.env.example` to `.env`:

Windows:

```bash
copy .env.example .env
```

Linux or macOS:

```bash
cp .env.example .env
```

Example development configuration:

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=reservation_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1

FRONTEND_PASSWORD_RESET_URL=http://localhost:3000/reset-password
```

For production email delivery, configure these variables:

```env
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=noreply@example.com
```

In development, emails are printed to the console if the development email backend is enabled.

Important: never commit the real `.env` file.

---

## PostgreSQL Setup

Create the PostgreSQL database:

```sql
CREATE DATABASE reservation_db;
```

Example database configuration:

```env
DB_NAME=reservation_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432
```

Tests use:

```text
config/settings/test.py
```

The pytest configuration points to the test settings module:

```ini
DJANGO_SETTINGS_MODULE = config.settings.test
```

---

## Migrations

Create and apply migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create a superuser:

```bash
python manage.py createsuperuser
```

---

## Running the Server

For local development:

```bash
python manage.py runserver
```

Base API URL:

```text
http://127.0.0.1:8000/api/v1/
```

---

## Celery and Reminders

This project uses Celery for background jobs such as notification delivery and appointment reminders.

Start Redis first, then run the Celery worker:

```bash
celery -A config worker -l info
```

Run Celery Beat for scheduled tasks:

```bash
celery -A config beat -l info
```

If needed, run the worker and beat in separate terminal windows.

### Appointment Reminder Task

The task responsible for 24-hour appointment reminders is:

```text
apps.appointments.tasks.send_due_appointment_24h_reminders_task
```

This task finds appointments that start within the next 24 hours and have not received a reminder yet.

Recommended setup through Django Admin:

```text
Django Admin → Periodic Tasks → Add periodic task
```

Suggested configuration:

```text
Name: Send appointment 24h reminders
Task: apps.appointments.tasks.send_due_appointment_24h_reminders_task
Interval: Every 5 minutes
```

---

## Running Tests

Run all tests:

```bash
pytest -v
```

Run tests for a specific app:

```bash
pytest apps/appointments/tests -v
pytest apps/payments/tests -v
pytest apps/audit/tests -v
```

Pytest configuration file:

```text
pytest.ini
```

Main pytest settings:

```ini
DJANGO_SETTINGS_MODULE = config.settings.test
python_files = test_*.py *_tests.py
```

In the test environment:

- Emails use `locmem.EmailBackend`
- Celery runs with `CELERY_TASK_ALWAYS_EAGER=True`
- A faster password hasher is enabled for tests

---

## API Documentation

Swagger UI:

```text
/api/schema/swagger-ui/
```

Redoc:

```text
/api/schema/redoc/
```

OpenAPI schema:

```text
/api/schema/
```

In Swagger, authenticate with the access token using this format:

```text
Bearer <access_token>
```

---

## Main System Flow

A normal system workflow is:

```text
1. Register a customer or provider
2. Login and receive access and refresh tokens
3. Create an organization by a provider
4. Create a branch for the organization
5. Create a ProviderProfile for the provider user
6. Create an Offering for the provider
7. Define WorkingHour records for the provider
8. Define TimeOff or Holiday records if needed
9. Fetch available slots from the availability API
10. Create an Appointment by a customer
11. Send appointment-created notifications
12. Create a Payment for the appointment
13. Mark the payment as paid or failed
14. Register important actions in AuditLog
15. Send email reminders for upcoming appointments
```

---

## API Endpoints

All API endpoints are under this prefix:

```text
/api/v1/
```

### Authentication

| Method | Endpoint | Description | Access |
| --- | --- | --- | --- |
| `POST` | `/api/v1/auth/register/` | Register a new user | Public |
| `POST` | `/api/v1/auth/login/` | Login and receive JWT tokens | Public |
| `POST` | `/api/v1/auth/refresh/` | Refresh access token | Public |
| `GET` | `/api/v1/auth/me/` | Get current user profile | Authenticated |
| `PATCH` | `/api/v1/auth/me/` | Update current user profile | Authenticated |
| `POST` | `/api/v1/auth/change-password/` | Change password | Authenticated |
| `POST` | `/api/v1/auth/password-reset/` | Request password reset | Public |
| `POST` | `/api/v1/auth/password-reset/confirm/` | Confirm password reset | Public |

Example register payload:

```json
{
  "email": "customer@example.com",
  "first_name": "Ali",
  "last_name": "Ahmadi",
  "phone_number": "09120000000",
  "role": "customer",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

Example login payload:

```json
{
  "email": "customer@example.com",
  "password": "StrongPass123!"
}
```

---

### Organizations

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/organizations/` | List active organizations |
| `POST` | `/api/v1/organizations/` | Create an organization |
| `GET` | `/api/v1/organizations/my/` | List organizations owned by the current user |
| `GET` | `/api/v1/organizations/<organization_id>/` | Retrieve organization details |
| `PATCH` | `/api/v1/organizations/<organization_id>/` | Update organization |
| `GET` | `/api/v1/organizations/<organization_id>/branches/` | List organization branches |
| `POST` | `/api/v1/organizations/<organization_id>/branches/` | Create a branch |
| `GET` | `/api/v1/organizations/branches/<branch_id>/` | Retrieve branch details |
| `PATCH` | `/api/v1/organizations/branches/<branch_id>/` | Update branch |

Example organization payload:

```json
{
  "name": "Tehran Clinic",
  "slug": "tehran-clinic",
  "description": "Medical appointment center",
  "phone_number": "02112345678",
  "email": "info@example.com",
  "website": "https://example.com",
  "timezone": "Asia/Tehran",
  "is_active": true
}
```

Example branch payload:

```json
{
  "name": "Main Branch",
  "address": "Tehran, Example Street",
  "phone_number": "02112345678",
  "latitude": "35.689200",
  "longitude": "51.389000",
  "is_active": true
}
```

---

### Providers

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/providers/` | List active providers |
| `POST` | `/api/v1/providers/` | Create a ProviderProfile |
| `GET` | `/api/v1/providers/my/` | List current user's provider profiles |
| `GET` | `/api/v1/providers/organizations/<organization_id>/` | List providers of an organization |
| `GET` | `/api/v1/providers/<provider_profile_id>/` | Retrieve provider details |
| `PATCH` | `/api/v1/providers/<provider_profile_id>/` | Update provider |

Example ProviderProfile payload:

```json
{
  "user_id": "USER_UUID",
  "organization_id": "ORGANIZATION_UUID",
  "branch_id": "BRANCH_UUID",
  "title": "Dr.",
  "specialty": "General Medicine",
  "bio": "General practitioner",
  "default_slot_duration_minutes": 30,
  "is_active": true
}
```

---

### Offerings

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/offerings/` | List active offerings |
| `POST` | `/api/v1/offerings/` | Create an offering for a provider |
| `GET` | `/api/v1/offerings/my/` | List offerings of the current provider |
| `GET` | `/api/v1/offerings/organizations/<organization_id>/` | List offerings of an organization |
| `GET` | `/api/v1/offerings/providers/<provider_id>/` | List offerings of a provider |
| `GET` | `/api/v1/offerings/<offering_id>/` | Retrieve offering details |
| `PATCH` | `/api/v1/offerings/<offering_id>/` | Update offering |

Example offering payload:

```json
{
  "organization_id": "ORGANIZATION_UUID",
  "provider_id": "PROVIDER_UUID",
  "title": "General Visit",
  "description": "General medical visit",
  "duration_minutes": 30,
  "buffer_before_minutes": 0,
  "buffer_after_minutes": 10,
  "price": "100000.00",
  "requires_approval": false,
  "is_active": true
}
```

---

### Availability

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/availability/working-hours/` | List active working hours |
| `POST` | `/api/v1/availability/working-hours/` | Create provider working hour |
| `GET` | `/api/v1/availability/working-hours/<id>/` | Retrieve working hour |
| `PATCH` | `/api/v1/availability/working-hours/<id>/` | Update working hour |
| `GET` | `/api/v1/availability/providers/<provider_id>/working-hours/` | List provider working hours |
| `GET` | `/api/v1/availability/time-offs/` | List time off records |
| `POST` | `/api/v1/availability/time-offs/` | Create provider time off |
| `GET` | `/api/v1/availability/providers/<provider_id>/time-offs/` | List provider time off records |
| `GET` | `/api/v1/availability/holidays/` | List holidays |
| `POST` | `/api/v1/availability/holidays/` | Create organization holiday |
| `GET` | `/api/v1/availability/organizations/<organization_id>/holidays/` | List organization holidays |
| `GET` | `/api/v1/availability/slots/` | Get available slots |

Weekday values:

```text
0 = Monday
1 = Tuesday
2 = Wednesday
3 = Thursday
4 = Friday
5 = Saturday
6 = Sunday
```

Example working hour payload:

```json
{
  "provider_id": "PROVIDER_UUID",
  "weekday": 0,
  "start_time": "09:00:00",
  "end_time": "13:00:00",
  "is_active": true
}
```

Example time off payload:

```json
{
  "provider_id": "PROVIDER_UUID",
  "start_at": "2026-06-20T10:00:00+03:30",
  "end_at": "2026-06-20T12:00:00+03:30",
  "reason": "Personal time off",
  "is_active": true
}
```

Example available slots request:

```text
GET /api/v1/availability/slots/?provider_id=PROVIDER_UUID&offering_id=OFFERING_UUID&date=2026-06-20
```

---

### Appointments

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/appointments/` | List visible appointments |
| `POST` | `/api/v1/appointments/` | Create a new appointment |
| `GET` | `/api/v1/appointments/my/` | List current user's appointments |
| `GET` | `/api/v1/appointments/providers/<provider_id>/` | List provider appointments |
| `GET` | `/api/v1/appointments/organizations/<organization_id>/` | List organization appointments |
| `GET` | `/api/v1/appointments/<appointment_id>/` | Retrieve appointment details |
| `POST` | `/api/v1/appointments/<appointment_id>/cancel/` | Cancel appointment |
| `PATCH` | `/api/v1/appointments/<appointment_id>/status/` | Update appointment status |

Example appointment payload:

```json
{
  "provider_id": "PROVIDER_UUID",
  "offering_id": "OFFERING_UUID",
  "start_at": "2026-06-20T09:00:00+03:30",
  "notes": "First appointment"
}
```

Appointment statuses:

```text
pending
confirmed
cancelled_by_customer
cancelled_by_provider
completed
no_show
```

Example cancel payload:

```json
{
  "cancel_reason": "Changed plan"
}
```

Example status update payload:

```json
{
  "status": "completed"
}
```

---

### Notifications

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/notifications/` | List current user's notifications |
| `GET` | `/api/v1/notifications/<notification_id>/` | Retrieve notification details |
| `POST` | `/api/v1/notifications/<notification_id>/mark-read/` | Mark a notification as read |
| `POST` | `/api/v1/notifications/mark-all-read/` | Mark all notifications as read |

Notification types:

```text
password_changed
password_reset_requested
appointment_created
appointment_confirmed
appointment_cancelled
appointment_reminder
appointment_completed
appointment_no_show
payment_success
payment_failed
refund_success
```

Supported channels:

```text
in_app
email
sms
push
```

Currently, email and in-app notifications are implemented. Appointment reminders use email only.

---

### Payments

| Method | Endpoint | Description |
| --- | --- | --- |
| `POST` | `/api/v1/payments/appointments/` | Create payment for an appointment |
| `GET` | `/api/v1/payments/my/` | List current user's payments |
| `GET` | `/api/v1/payments/organizations/<organization_id>/` | List organization payments |
| `GET` | `/api/v1/payments/<payment_id>/` | Retrieve payment details |
| `POST` | `/api/v1/payments/<payment_id>/mark-paid/` | Mark payment as paid |
| `POST` | `/api/v1/payments/<payment_id>/mark-failed/` | Mark payment as failed |
| `POST` | `/api/v1/payments/<payment_id>/cancel/` | Cancel a pending payment |
| `POST` | `/api/v1/payments/<payment_id>/refund/` | Refund a paid payment |

Payment statuses:

```text
pending
paid
failed
cancelled
refunded
```

Payment methods:

```text
mock
cash
card
online_gateway
```

Example create payment payload:

```json
{
  "appointment_id": "APPOINTMENT_UUID",
  "method": "mock"
}
```

Example mark paid payload:

```json
{
  "gateway_reference": "ref-123",
  "raw_response": {
    "status": "ok"
  }
}
```

Example mark failed payload:

```json
{
  "failure_reason": "Gateway rejected payment",
  "gateway_reference": "ref-failed-123",
  "raw_response": {
    "status": "failed"
  }
}
```

Example refund payload:

```json
{
  "refund_reason": "Customer requested refund"
}
```

---

### Audit

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/v1/audit/` | List visible audit logs |
| `GET` | `/api/v1/audit/my/` | List current user's audit logs |
| `GET` | `/api/v1/audit/organizations/<organization_id>/` | List organization audit logs |
| `GET` | `/api/v1/audit/<audit_log_id>/` | Retrieve audit log details |

Audit logs are created by the system. There is no direct create endpoint for users.

Important audit actions:

```text
appointment_created
appointment_cancelled
appointment_status_changed
payment_initiated
payment_paid
payment_failed
payment_cancelled
payment_refunded
working_hour_created
working_hour_updated
time_off_created
time_off_updated
holiday_created
holiday_updated
```

---

## Main Database Models

### User

A custom user model that uses email as `USERNAME_FIELD`.

Important fields:

```text
email
first_name
last_name
phone_number
role
is_active
is_staff
is_verified
```

### Organization

Represents a business or organization.

Important fields:

```text
owner
name
slug
description
phone_number
email
website
timezone
is_active
```

### Branch

Represents branches of an organization.

Important fields:

```text
organization
name
address
phone_number
latitude
longitude
is_active
```

### ProviderProfile

Represents a provider inside an organization.

Important fields:

```text
user
organization
branch
title
specialty
bio
default_slot_duration_minutes
is_active
```

### Offering

Represents a bookable service provided by a provider.

Important fields:

```text
organization
provider
title
description
duration_minutes
buffer_before_minutes
buffer_after_minutes
price
requires_approval
is_active
```

### WorkingHour

Represents provider working hours for weekdays.

Important fields:

```text
provider
weekday
start_time
end_time
is_active
```

### TimeOff

Represents provider absence or time off.

Important fields:

```text
provider
start_at
end_at
reason
is_active
```

### Holiday

Represents an organization holiday.

Important fields:

```text
organization
date
title
is_active
```

### Appointment

Represents a booked appointment.

Important fields:

```text
organization
branch
customer
provider
offering
start_at
end_at
blocked_start_at
blocked_end_at
status
price
notes
cancel_reason
cancelled_by
cancelled_at
created_by
```

`blocked_start_at` and `blocked_end_at` are used to handle buffer time before and after appointments.

### AppointmentReminder

Prevents duplicate reminder delivery.

Important fields:

```text
appointment
reminder_type
channel
sent_at
```

### Notification

Represents a user notification.

Important fields:

```text
user
type
title
message
is_read
read_at
related_object_type
related_object_id
data
```

### NotificationDelivery

Represents delivery status for each notification channel.

Important fields:

```text
notification
user
channel
type
recipient
subject
body
status
error_message
sent_at
data
```

### Payment

Represents an appointment payment.

Important fields:

```text
appointment
organization
payer
amount
currency
status
method
gateway_reference
idempotency_key
paid_at
failed_at
cancelled_at
refunded_at
failure_reason
refund_reason
created_by
data
```

### PaymentTransaction

Represents payment transaction logs.

Important fields:

```text
payment
transaction_type
amount
status
gateway_reference
message
raw_response
```

### AuditLog

Represents important system events.

Important fields:

```text
actor
organization
action
status
target_object_type
target_object_id
target_object_repr
ip_address
user_agent
metadata
error_message
```

---

## Business Rules

### Organization and Branch

- Each organization has one owner.
- Only the owner or a superuser can manage the organization.
- Branch names must be unique inside each organization.

### Provider

- A provider user can have ProviderProfile records.
- Each user can have only one ProviderProfile per organization.
- A provider may be assigned to a branch, but branch is optional.

### Offering

- Each offering belongs to a provider and an organization.
- The provider must belong to the same organization as the offering.
- Offering title must be unique per provider.
- Duration must be greater than zero.
- Price cannot be negative.

### Availability

- End time must be after start time.
- Active working hours for the same provider must not overlap.
- Time off records must have a valid start and end datetime.
- Each organization can have only one holiday for the same date.

### Appointment

- Appointments can only be created for available slots.
- `start_at` must be in the future.
- Appointments cannot be created for inactive offerings or inactive providers.
- Booked time ranges are controlled with `blocked_start_at` and `blocked_end_at`.
- Two active appointments for the same provider must not overlap.
- If `requires_approval=True`, the initial status is `pending`.
- If `requires_approval=False`, the initial status is `confirmed`.
- Only `pending` and `confirmed` appointments can be cancelled.
- Final statuses include cancelled, completed, and no-show states.

### Payment

- Payments can only be created for payable appointments.
- A duplicate pending or paid payment cannot be created for the same appointment.
- Payment amount is copied from `appointment.price`.
- Only pending payments can be marked as paid, failed, or cancelled.
- Only paid payments can be refunded.
- Each payment operation creates a PaymentTransaction record.

### Notification

- Notifications are published through events.
- Notification creation happens after database commit.
- Appointment reminders currently use email only.

### Audit

- Audit logs are not created directly by users.
- Important appointment and payment operations are logged.
- Audit logging failure must not break the main business operation.

---

## Notifications and Reminders

The notification system is event-driven.

Main files:

```text
apps/notifications/events/event_types.py
apps/notifications/events/registry.py
apps/notifications/events/dispatcher.py
apps/notifications/events/handlers.py
apps/notifications/services.py
apps/notifications/tasks.py
```

Each event in the registry defines:

```text
notification_type
channels
title
message
email_subject
email_body
```

Appointment reminder task:

```text
apps.appointments.tasks.send_due_appointment_24h_reminders_task
```

This task:

- Finds active appointments that start within the next 24 hours
- Checks that a reminder has not already been sent
- Creates an `AppointmentReminder` record
- Publishes the `appointment_reminder` event
- Sends email only

---

## Payments

The current payment implementation is internal and mock-based. It does not connect to a real banking gateway, but the structure is ready for future gateway integration.

Payment flow:

```text
1. Customer creates a payment for an appointment
2. Payment is created with status=pending
3. A PaymentTransaction with type=initiated is recorded
4. Provider or organization manager can mark the payment as paid or failed
5. On success, payment_success notification is sent
6. On failure, payment_failed notification is sent
7. Paid payments can be refunded
8. refund_success notification is sent
9. Important payment operations are saved in audit logs
```

---

## Audit Logs

Audit logs are used to track important operations in the system.

Examples:

```text
appointment_created
appointment_cancelled
appointment_status_changed
payment_initiated
payment_paid
payment_failed
payment_cancelled
payment_refunded
```

Audit logs are useful for:

- Tracking who performed an action
- Reviewing important appointment and payment changes
- Debugging and support
- Improving backend accountability and project quality

---

## Error Handling

The project uses a custom exception handler:

```text
apps.common.exception_handler.custom_exception_handler
```

General error response format:

```json
{
  "message": "Invalid input provided.",
  "error_code": "validation_error",
  "errors": {
    "field_name": [
      "Error message"
    ]
  }
}
```

When `DEBUG=True`, the response may also include `status_code`.

Common status codes:

| Status Code | Meaning |
| --- | --- |
| `400` | Invalid data or validation error |
| `401` | Authentication required |
| `403` | Permission denied |
| `404` | Record not found |
| `409` | Integrity or conflict error |
| `500` | Internal server error |

---

## Pagination, Search, and Ordering

Default pagination class:

```text
apps.common.pagination.StandardResultsSetPagination
```

Settings:

```text
page_size = 20
page_size_query_param = page_size
max_page_size = 100
```

Example:

```text
GET /api/v1/appointments/my/?page=1&page_size=10
```

Many list endpoints support search and ordering.

Example:

```text
GET /api/v1/offerings/?search=visit&ordering=price
```

---

## Security Notes

Implemented security-related features:

- JWT authentication
- Django password validation
- Password hashing
- Public registration limited to customer and provider roles
- Object-level permissions for organizations, providers, appointments, payments, and audit logs
- Users cannot access other users' appointments or payments unless they have the correct role or ownership
- Separate production settings in `config/settings/prod.py`
- `select_for_update(of=("self",))` is used in sensitive operations to reduce race conditions

Production checklist:

```env
DEBUG=False
SECRET_KEY=strong-production-secret
ALLOWED_HOSTS=your-domain.com
```

Also make sure the real `.env` file is never committed to Git.

---

## Manual Test Scenarios

### Scenario 1: Registration and Login

1. Register a customer
2. Register a provider
3. Login both users
4. Store access tokens

### Scenario 2: Organization and Provider Setup

1. Provider creates an organization
2. Provider creates a branch for the organization
3. Provider creates a ProviderProfile

### Scenario 3: Offering and Availability

1. Create an offering for the provider
2. Create provider working hours
3. Create holiday or time off if needed
4. Test the available slots endpoint

### Scenario 4: Appointment Booking

1. Customer fetches available slots
2. Customer creates an appointment
3. Try to book the same time again and expect an error
4. Cancel the appointment

### Scenario 5: Payment

1. Create a payment for an appointment
2. Provider marks it as paid
3. Check payment_success notification
4. Refund the payment
5. Check audit logs

### Scenario 6: Reminder

1. Create an appointment close to the next 24 hours
2. Run the reminder task
3. Check reminder email delivery
4. Run the task again and verify that duplicate reminders are not sent

---

## Useful Commands

Run server:

```bash
python manage.py runserver
```

Create migrations:

```bash
python manage.py makemigrations
```

Apply migrations:

```bash
python manage.py migrate
```

Create superuser:

```bash
python manage.py createsuperuser
```

Run tests:

```bash
pytest -v
```

Open shell:

```bash
python manage.py shell
```

Run Celery worker:

```bash
celery -A config worker -l info
```

Run Celery beat:

```bash
celery -A config beat -l info
```

Run Django checks:

```bash
python manage.py check
```

Check for missing migrations:

```bash
python manage.py makemigrations --check --dry-run
```

---

## Final Presentation Notes

The following points can be used when presenting or defending the project:

- The project is a complete REST API for appointment booking.
- The architecture is app-based and uses a service layer.
- Business logic is placed inside services, while views remain lightweight.
- Authentication is handled with JWT.
- Roles and permissions are checked at both endpoint and object level.
- PostgreSQL is used as the main database.
- Celery is used for notifications and reminders.
- Appointment booking uses row-level locking to reduce race conditions.
- Available slots are calculated using working hours, time off, holidays, active appointments, and offering buffers.
- The payment system is mock-based but structured for future gateway integration.
- Notifications are event-driven.
- Audit logs are created for important operations.
- Swagger and Redoc are available for API documentation and testing.
- Unit and API tests are included for the main applications.

---

## Final Project Status

Implemented core applications:

```text
users
authentication
organizations
providers
offerings
availability
appointments
notifications
payments
audit
```

Main backend capabilities:

```text
Authentication
Authorization
Organization Management
Provider Management
Service Management
Availability Management
Appointment Booking
Notification System
Email Reminder
Mock Payment
Transaction Log
Audit Log
API Documentation
Automated Tests
```
