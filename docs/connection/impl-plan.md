# CONN-001 - Redmine Connection: Implementation Plan

> Tao: 2026-05-05
> Dua tren: [spec-pack.md](./spec-pack.md)
> Codebase review: 2026-05-05

---

## 1. Tong quan

Module Redmine Connection chua duoc implement trong codebase hien tai.
Can bo sung moi toan bo stack de admin co the:

- tao Redmine connection
- cap nhat Redmine connection
- test connection toi Redmine REST API
- luu API key o dang ma hoa co the giai ma duoc

Codebase hien tai da co:

- backend FastAPI voi cookie-based auth
- SQLAlchemy async session
- frontend React dashboard co muc `Settings` tren sidebar

Codebase hien tai chua co:

- model `redmine_connections`
- route `/api/redmine/connections`
- co che ma hoa secrets
- man hinh `Admin > Settings > Redmine Connection`
- role `admin` trong user model/dependency

---

## 2. Ket luan review hien trang

| # | Hang muc | Hien trang | Tac dong |
|---|---|---|---|
| 1 | Auth | Da co login bang cookie, co `require_user()` | Co the tai su dung de bao ve API |
| 2 | Authorization | Chua co role `admin` trong `User` model | Chot bo sung `is_admin` vao `users` va dung dependency `require_admin` |
| 3 | Database schema | Dang `Base.metadata.create_all`, chua thay migration framework | Co the them model moi, nhung deployment can can nhac migration sau |
| 4 | HTTP client toi Redmine | Chua co | Phai them service/client de goi `/my/account.json` |
| 5 | Secret encryption | Chua co | Phai them env key va helper ma hoa/giai ma |
| 6 | Frontend settings page | Chua co page rieng | Phai them UI trong dashboard flow |

---

## 3. File map du kien

### Backend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Cau hinh env cho encryption | `backend/app/core/config.py` | Can sua |
| 2 | Model connection | `backend/app/models/redmine_connection.py` | Can tao moi |
| 3 | Dang ky model | `backend/app/models/__init__.py` | Co the can sua |
| 4 | Schema request/response | `backend/app/schemas/redmine_connection.py` | Can tao moi |
| 5 | Helper encryption | `backend/app/core/crypto.py` hoac `backend/app/core/security.py` | Can tao moi |
| 6 | Redmine API client/service | `backend/app/services/redmine_client.py` | Can tao moi |
| 7 | Route create/update/test | `backend/app/routes/redmine_connections.py` | Can tao moi |
| 8 | Authorization helper admin | `backend/app/middleware/auth.py` hoac dependency moi | Can sua |
| 9 | App router registration | `backend/app/main.py` | Can sua |

### Frontend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | API wrapper | `frontend/src/api/client.js` hoac file API moi | Can sua |
| 2 | Page Redmine Connection | `frontend/src/pages/RedmineConnectionPage.jsx` | Can tao moi |
| 3 | Dashboard navigation/state | `frontend/src/pages/DashboardPage.jsx` | Can sua |
| 4 | Styles | `frontend/src/styles.css` | Can sua |

### Docs / Test

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Manual test checklist | `docs/connection/impln-plan.md` | File nay |
| 2 | Backend automated tests | `backend/tests/...` | Chua thay thu muc tests trong repo |

---

## 4. Mapping spec -> implementation

| Spec item | Implementation du kien |
|---|---|
| `POST /api/redmine/connections` | Route FastAPI tao 1 record `redmine_connections`, validate URL, ma hoa `api_key`, tra ve metadata khong kem secret |
| `PATCH /api/redmine/connections/{id}` | Route cap nhat `name`, `base_url`, `api_key`, reset `status` khi doi `base_url` hoac `api_key` |
| `POST /api/redmine/connections/{id}/test` | Route giai ma secret, goi Redmine `GET /my/account.json`, map response sang `status` va error code |
| `status` enum | Luu string trong DB: `untested`, `active`, `failed`, `disabled` |
| Admin only | Dependency auth yeu cau user hop le va co quyen admin |
| API key khong tra frontend | Pydantic response model loai bo truong secret |
| 1 active connection toi da | Check ton tai connection truoc khi create, tra `409 REDMINE_CONNECTION_ALREADY_EXISTS` |

---

## 5. Ke hoach trien khai

### Phase 1 - Backend foundation

1. Bo sung env config cho encryption key va timeout Redmine.
2. Tao helper encryption/giai ma.
3. Tao SQLAlchemy model `RedmineConnection`.
4. Dang ky model de `create_all()` tao bang.

Expected output:

- DB co bang `redmine_connections`
- Backend doc duoc env can thiet
- Co helper secret dung lai duoc trong route/service

### Phase 2 - Authorization va API

1. Bo sung `is_admin` vao `users`.
2. Them dependency `require_admin`.
3. Tao request/response schemas.
4. Tao route create, update, test.
5. Tao Redmine client voi timeout 10 giay.
6. Chuan hoa mapping loi:
   - `401 -> REDMINE_UNAUTHORIZED`
   - `403 -> REDMINE_FORBIDDEN`
   - `504 -> REDMINE_TIMEOUT`

Expected output:

- Backend co day du 3 endpoint theo spec
- Secret khong xuat hien trong response/log
- Route chi cho admin goi

### Phase 3 - Frontend admin screen

1. Them trang `RedmineConnectionPage`.
2. Dat man hinh nay trong `Admin > Settings > Redmine Connection`.
3. Form gom:
   - `name`
   - `base_url`
   - `api_key`
   - `save`
   - `test connection`
   - `status`
   - `last tested`
4. Hien thi loi theo error code backend.
5. Khong preload API key cu.

Expected output:

- Admin thao tac duoc create/update/test tren UI
- UI khong hien secret da luu

### Phase 4 - Verification

1. Test create connection.
2. Test update name khong doi status.
3. Test update `base_url` hoac `api_key` reset `status`.
4. Test connection success/fail/timeout.
5. Test non-admin bi chan.
6. Test khong response nao lo `api_key`.

---

## 6. Chi tiet ky thuat de xuat

### 6.1 Model DB

Bang `redmine_connections`:

- `id`
- `name`
- `base_url`
- `encrypted_api_key`
- `status`
- `created_by`
- `created_at`
- `updated_at`
- `last_tested_at`

Rang buoc de xuat:

- `name`: `String(100)`, not null
- `base_url`: `String(255)`, not null
- `status`: `String(20)`, not null, default `untested`
- index cho `created_by`

### 6.2 Encryption

De xuat them env:

```env
REDMINE_SECRET_KEY=<32-byte-base64-or-fernet-key>
REDMINE_TIMEOUT_SECONDS=10
```

Huong ky thuat:

- Dung reversible encryption, khong dung bcrypt/hash mot chieu.
- Neu chon `cryptography.fernet.Fernet`, key phai duoc cap qua env.
- Toan bo log/error phai redact secret.

### 6.3 Redmine client

De xuat:

- Dung `httpx.AsyncClient`
- timeout = `REDMINE_TIMEOUT_SECONDS`
- helper build URL an toan cho `base_url` co hoac khong co trailing slash / path prefix

Pseudo-flow:

```text
decrypt api_key
normalize base_url
GET {base_url}/my/account.json
Header: X-Redmine-API-Key
map status code
update DB status + last_tested_at
return response model
```

### 6.4 Authorization

Codebase hien tai chua co `is_admin`, va quyet dinh duoc chot la bo sung truong nay vao `users`.

Huong implement:

1. Bo sung `is_admin: bool` vao model `User`
2. Dat default `False` cho user thuong
3. Seed `admin` user voi `is_admin=True`
4. Tao dependency `require_admin()`
5. Toan bo API Redmine Connection bat buoc di qua `require_admin()`

---

## 7. Gap va quyet dinh can chot truoc khi code

| ID | Van de | De xuat |
|---|---|---|
| GAP-CONN-1 | Chua co role admin trong DB | Se implement bang truong `is_admin` trong `users`; khong dung fallback theo `username` |
| GAP-CONN-2 | Chua co migration framework | Tam thoi dung `create_all()` theo style hien tai; sau do xem xet Alembic |
| GAP-CONN-3 | Spec nhac `GET current` trong open issue | Chua implement neu product chua chot |
| GAP-CONN-4 | `disabled` da co trong enum nhung chua co use case UI | Giu trong enum, chua them action disable |
| GAP-CONN-5 | Chi 1 connection trong he thong | Enforce o backend bang query ton tai truoc khi create |

---

## 8. Acceptance Criteria -> test cases

| AC | Test case | Ket qua mong doi |
|---|---|---|
| CONN-AC-001 | Admin create voi payload hop le | `201`, response co `id`, `status=untested`, khong co `api_key` |
| CONN-AC-002 | Admin test voi API key hop le | `200`, `success=true`, `status=active` |
| CONN-AC-003 | Kiem tra response create/update/test | Khong co `api_key`, khong co `encrypted_api_key` |
| CONN-AC-004 | Test voi API key sai | `401`, code `REDMINE_UNAUTHORIZED`, DB status `failed` |
| CONN-AC-005 | Test timeout | `504`, code `REDMINE_TIMEOUT`, DB status `failed` |
| CONN-AC-006 | Update `base_url` hoac `api_key` | `status=untested`, `last_tested_at=null` |
| CONN-AC-007 | User khong phai admin goi API | `403 FORBIDDEN` |

---

## 9. Manual test checklist

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 2. Start frontend
cd frontend
npm run dev

# 3. Login as admin
# 4. Mo Admin > Settings > Redmine Connection
# 5. Tao connection moi
# 6. Bam Test connection
# 7. Thu API key sai
# 8. Thu sua base_url hoac api_key va xac nhan status reset
```

Checklist:

- UI hien trang thai `untested` sau create
- UI hien `active` sau test thanh cong
- UI hien thong bao loi ro rang khi `401`, `403`, `504`
- Reload trang van hien metadata connection, nhung khong bao gio hien API key da luu

---

## 10. Thu tu thuc hien de xuat

1. Bo sung `is_admin` vao `users` va cap nhat auth dependency.
2. Them config encryption + timeout.
3. Tao model + bang `redmine_connections`.
4. Tao helper encryption + Redmine client.
5. Implement backend routes.
6. Implement frontend page.
7. Test manual va bo sung automated tests neu repo bat dau co test harness.

---

## 11. Ket luan

Feature nay nen duoc implement theo thu tu backend truoc, frontend sau.
Rui ro lon nhat khong nam o UI ma o 3 diem:

- chon sai co che luu API key
- can cap nhat schema auth de them `is_admin`
- xu ly sai `base_url` co path prefix

Neu 3 diem nay duoc chot dung ngay tu dau, phan con lai la implementation tuong doi thang.
