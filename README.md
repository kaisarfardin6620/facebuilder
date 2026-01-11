# FaceBuilder (FaceSculpt AI) Backend 🏋️

![Django](https://img.shields.io/badge/Django-5.2-092E20?logo=django)
![DRF](https://img.shields.io/badge/DRF-3.16-red)
![Channels](https://img.shields.io/badge/Channels-WebSockets-blue)
![Celery](https://img.shields.io/badge/Celery-Async-green)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?logo=docker)

FaceBuilder is a high-performance backend system for a facial fitness application ("FaceSculpt AI"). It utilizes Computer Vision (MediaPipe) to analyze facial landmarks, provides AI-generated workout plans, tracks user progress, and features a real-time AI Coach using OpenAI.

The system is built to scale using Django Channels (ASGI), Celery for background processing, and Redis, all containerized with Docker.

---

## 🚀 Key Features

- **Advanced Facial Analysis:** Uses MediaPipe and OpenCV to calculate Jawline Angle, Symmetry Score, and Puffiness Index from uploaded photos
- **AI Workout Coach:** Real-time Chat via WebSockets powered by OpenAI (GPT-4o), context-aware of the user's scan data and goals
- **Dynamic Workout Plans:** Algorithmically generates daily facial exercise routines based on scan results and user goals (Jawline, Symmetry, etc.)
- **Authentication:** Secure Phone Number login with Twilio OTP verification and JWT (JSON Web Tokens)
- **Subscription Management:** Integrated with RevenueCat to handle Premium/Free tiers (gating Chat and detailed Stats)
- **Gamification:** Streak tracking, leaderboards, and progress badges
- **Admin Dashboard:** Custom metrics for tracking user growth, earnings, and scan throughput

---

## 🛠 Tech Stack

- **Framework:** Django 5.2, Django REST Framework
- **Async/Real-time:** Django Channels, Daphne, Redis
- **Task Queue:** Celery, Celery Beat
- **Database:** PostgreSQL (Production), SQLite (Dev)
- **AI/ML:** Google MediaPipe, OpenCV, OpenAI API
- **Third-Party Services:** Twilio (SMS), RevenueCat (Payments)
- **Infrastructure:** Docker, Nginx

---

## ⚙️ Installation & Setup

### Prerequisites

- Docker & Docker Compose
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/kaisarfardin6620/facebuilder.git
cd facebuilder
```

### 2. Configure Environment Variables

Create a `.env` file in the root directory. You can use the provided template below:

```env
# General
DEBUG=True
SECRET_KEY=your_super_secret_key_here
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
SERVER_BASE_URL=http://127.0.0.1:8000

# Database & Redis
DATABASE_URL=postgres://user:password@db:5432/facebuilder_db
REDIS_URL=redis://redis:6379/0

# AI Services
OPENAI_API_KEY=sk-your-openai-key

# Twilio (OTP)
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token
TWILIO_VERIFY_SERVICE_SID=your_service_sid
# Optional for testing:
# TEST_PHONE_NUMBER=+1234567890
# TEST_OTP_CODE=123456

# RevenueCat (Subscriptions)
REVENUECAT_API_KEY=your_rc_api_key
REVENUECAT_WEBHOOK_SECRET=your_rc_webhook_secret
REVENUECAT_ENTITLEMENT_IDS=monthly,sixmonthly,yearly
```

### 3. Build and Run via Docker

This project is containerized. Run the following command to start the Web Server (Daphne), Worker, Beat, Redis, and Nginx.

```bash
docker-compose up --build
```

The API will be available at:
- **Via Nginx:** `http://localhost:8050`
- **Direct:** `http://localhost:8000`

### 4. Database Migrations & Seeding

Once the containers are running, execute migrations and seed the database with exercises:

```bash
# Run Migrations
docker-compose exec web python manage.py migrate

# Create Superuser
docker-compose exec web python manage.py createsuperuser

# Seed Initial Exercises (AI Generated)
docker-compose exec web python manage.py seed_exercises
```

---

## 📖 API Documentation

The API uses JWT Authentication. Include the token in the header:

```
Authorization: Bearer <your_access_token>
```

### 🔐 Authentication (`/api/auth/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/signup/` | Register a new user. Returns 201 and sends OTP |
| POST | `/verify-otp/` | Verify phone number. Returns JWT tokens |
| POST | `/login/` | Log in with password. Checks if active |
| POST | `/token/refresh/` | Refresh expired access token |
| POST | `/forgot-password/` | Trigger OTP for password reset |
| POST | `/reset-password/` | Set new password using OTP |

**Example Signup Payload:**

```json
{
  "phone_number": "+12345678901",
  "name": "John Doe",
  "password": "StrongPassword123"
}
```

### 📸 Face Scans (`/api/scans/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/analyze/` | Upload an image for immediate analysis |
| GET | `/analyze/` | Get the latest scan data |
| POST | `/set-goals/` | Set fitness targets (Jawline, Symmetry, etc.) |

**Analyze Response (Success):**

```json
{
  "message": "Scan complete.",
  "scan_data": {
    "jawline_angle": 125.5,
    "symmetry_score": 88.2,
    "puffiness_index": 1.15,
    "status": "COMPLETED"
  }
}
```

### 🏋️ Workouts (`/api/workouts/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/my-plan/` | Get the current active workout plan (Premium only) |
| POST | `/complete/` | Mark today's session as complete. Updates streak |
| GET | `/dashboard/` | Get user stats, streak, graph data, and leaderboard |

**Dashboard Response Example:**

```json
{
  "streak_days": 5,
  "consistency_text": "Momentum is building!",
  "progress_summary": {
    "overall_progress": 45,
    "jawline_status": "125° (Goal 118°)"
  },
  "leaderboard": { ... }
}
```

### 💬 AI Coach & Chat (`/api/chat/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| WS | `/ws/chat/?token=...` | WebSocket. Real-time chat with FaceCoach |
| GET | `/ask/` | Retrieve chat history |
| POST | `/ask/` | REST fallback for sending a message |

**WebSocket Protocol:**

1. Connect to `ws://localhost:8050/ws/chat/?token=<ACCESS_TOKEN>`
2. Send JSON: `{"message": "How do I improve my jawline?"}`
3. Receive JSON: `{"sender": "AI", "message": "Based on your scan, your jawline angle is..."}`

**Note:** Chat is a Premium feature.

### 💳 Payments (`/api/payments/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/sync/` | Manually sync subscription status with RevenueCat |
| POST | `/webhook/` | Endpoint for RevenueCat webhooks (server-to-server) |

---

## 🧩 Architecture Details

### 1. Face Analysis Pipeline

When a user uploads an image to `/scans/analyze/`:

1. OpenCV converts the image to grayscale and checks for brightness/blur
2. MediaPipe Face Mesh extracts 468 3D facial landmarks
3. Algorithms calculate geometric angles (jaw), bilateral variance (symmetry), and facial width ratios (puffiness)
4. Results are stored in PostgreSQL and used to generate/update User Goals

### 2. Dynamic Workout Generation

Workouts are not static. The `generate_workout_plan` utility:

1. Checks the user's specific goals (e.g., "Sharper Jawline")
2. Selects exercises from the database tagged with relevant metrics
3. Adds a mandatory "Lymphatic Drainage" finisher
4. As users complete sessions, the Difficulty Level increases, adjusting reps and duration automatically

### 3. Real-Time Chat (WebSocket)

The `ChatConsumer`:

1. Authenticates the user via JWT in the query string
2. Checks Subscription Status (Premium gate)
3. Pulls the latest FaceScan and UserGoal data
4. Injects this data into the OpenAI System Prompt so the AI acts as a personalized coach ("FaceCoach") adhering to a strict Knowledge Base

---

## 🛡️ Admin & Analytics

Access the Django Admin panel at `/admin/`.

Dashboard App (`/api/dashboard/stats/`) provides high-level metrics for administrators:

- Total Active Users
- Total Scans Processed
- Total Earnings (Aggregated from Payment History)
- Monthly Revenue Graphs

---

## 🔗 Repository

**GitHub:** [facebuilder](https://github.com/kaisarfardin6620/facebuilder.git)

---

## 📜 License

This project is proprietary software. All rights reserved.

**Developed by:** Kaisar Fardin