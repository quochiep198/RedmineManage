# Redmine Simple Starter

Source đơn giản để bắt đầu phát triển web quản lý Redmine.

## Có sẵn

- Backend: FastAPI
- Database: MySQL
- ORM: SQLAlchemy async
- Frontend: React + Vite
- Layout login đơn giản
- API login demo
- API health check database
- Docker Compose

## Cấu trúc

```text
AIPROJECT/
  backend/
    app/
      main.py
      core/
      db/
      models/
      routes/
  frontend/
    src/
      App.jsx
      pages/LoginPage.jsx
      api/client.js
  docker-compose.yml
```

## Chạy bằng Docker

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## URL

Frontend:

```text
http://localhost:3000
```

Backend Swagger:

```text
http://localhost:8000/docs
```

## Tài khoản demo

```text
username: admin
password: admin
```

## API test DB

```text
GET http://localhost:8000/api/health/db
```

## Ghi chú

Đây là starter đơn giản. Login hiện tại là demo hardcode để bạn dễ nhìn flow. Khi phát triển thật, hãy thay bằng user table + password hash.



cd backend
pip install -r requirements.txt   # cài dependencies
uvicorn app.main:app --reload --port 8000


cd frontend
npm install           # cài node_modules lần đầu
npm run dev -- --port 3000