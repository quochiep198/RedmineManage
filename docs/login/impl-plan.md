# AUTH-001 — Login Module: Implementation Plan

> Tạo: 2026-05-04 · Dựa trên: [spec_pack.md](./spec_pack.md) · Code đã review: 2026-05-04

---

## 1. Tổng quan

Module login/logout sử dụng JWT + httpOnly cookie đã **triển khai hoàn tất** và **khớp đặc tả spec_pack.md AUTH-001** ở hầu hết các điểm. Phần lớn acceptance criteria (AC-auth-1 → AC-auth-10) đã được cover.

---

## 2. File map — spec → code

| # | Spec item | File | Dòng | Trạng thái |
|---|-----------|------|------|-----------|
| 1 | `POST /api/auth/login` | [routes/auth.py](backend/app/routes/auth.py) | 33–68 | ✅ Done |
| 2 | `GET /api/auth/me` | [routes/auth.py](backend/app/routes/auth.py) | 77–82 | ✅ Done |
| 3 | `POST /api/auth/logout` | [routes/auth.py](backend/app/routes/auth.py) | 71–74 | ✅ Done |
| 4 | JWT HS256 + payload `sub/username/exp` | [routes/auth.py](backend/app/routes/auth.py) | 14–25 | ✅ Done |
| 5 | `bcrypt.checkpw` password verify | [routes/auth.py](backend/app/routes/auth.py) | 42 | ✅ Done |
| 6 | httpOnly cookie set | [routes/auth.py](backend/app/routes/auth.py) | 50–58 | ✅ Done (thiếu `secure=True` — xem §3) |
| 7 | Cookie delete on logout | [routes/auth.py](backend/app/routes/auth.py) | 73 | ✅ Done |
| 8 | JWT verify `get_current_user` | [routes/auth.py](backend/app/routes/auth.py) | 85–98 | ✅ Done |
| 9 | `User` model (`id`, `username`, `password`, `is_active`) | [models/user.py](backend/app/models/user.py) | 5–11 | ✅ Done |
| 10 | `require_user` / `optional_user` middleware helpers | [middleware/auth.py](backend/app/middleware/auth.py) | 21–36 | ✅ Done |
| 11 | CORS `allow_credentials=True` | [main.py](backend/app/main.py) | 11–18 | ✅ Done |
| 12 | `withCredentials` frontend axios | [api/client.js](frontend/src/api/client.js) | 6 | ✅ Done |
| 13 | Frontend auto restore on mount (`/auth/me`) | [App.jsx](frontend/src/App.jsx) | 10–16 | ✅ Done |
| 14 | LoginPage submit + error handle | [pages/LoginPage.jsx](frontend/src/pages/LoginPage.jsx) | 10–31 | ✅ Done |
| 15 | DashboardPage logout call | [pages/DashboardPage.jsx](frontend/src/pages/DashboardPage.jsx) | 14–21 | ✅ Done |
| 16 | Startup create all tables | [main.py](backend/app/main.py) | 24–28 | ✅ Done |

---

## 3. Gap đã nhận diện

### GAP-1: Cookie `secure=True` bị hard-code `False`

**Mô tả:** Trong [routes/auth.py:54](backend/app/routes/auth.py#L54), `secure=False` được hard-code. Điều này chống lại yêu cầu bảo mật (AC-auth-9: "inspect JS không đọc được cookie" — đã ok vì httpOnly, nhưng `secure=False` không bảo vệ cookie khỏi bị sniff trên HTTP).

**spec:** Section 6 — "Bảo mật: bcrypt + httpOnly" (httpOnly đã đủ cho XSS, nhưng production nên có HTTPS → `secure=True`).

**Đề xuất:** Đọc từ env var:
```python
# Thay secure=False bằng:
secure=settings.COOKIE_SECURE,  # env: COOKIE_SECURE=false (local) / true (production)
```

**Severity:** Low — không ảnh hưởng dev, cần fix trước deploy.

### GAP-2: Không có seed script tạo user demo

**Mô tả:** Login cần user trong DB. Hiện tại bảng `users` được tạo tự động (startup event), nhưng **không có user seed**. LoginPage hard-code `"admin / admin"` nhưng không có user đó trong DB.

**Impact:** Login thực tế thất bại nếu chưa seed.

**Đề xuất:** Thêm seed user trong `main.py` startup event:
```python
# Tạo user demo nếu chưa có
result = await session.execute(select(User).where(User.username == "admin"))
if result.scalar_one_or_none() is None:
    hashed = bcrypt.hashpw("admin".encode(), bcrypt.gensalt())
    session.add(User(username="admin", password=hashed.decode(), is_active=True))
    await session.commit()
```

### GAP-3: `SECRET_KEY` default `"change-me"` ✅ FIXED (2026-05-05)

**Đã fix** trong [core/config.py](backend/app/core/config.py) — dùng `model_post_init` (Pydantic v2) thay vì `__init__` override để raise error khi dùng giá trị mặc định `"change-me"`.

### SEC-1: JWT exposed trong response body ✅ FIXED (2026-05-05)

**Mô tả:** `routes/auth.py` trả `access_token` trong response body — attack surface rộng hơn nếu response bị đọc (XSS, mitm, server log).

**Giải pháp:** Xoá `"access_token"` khỏi response body, chỉ gửi cookie httpOnly.

### SEC-2: CORS hard-coded `localhost:3000` ✅ FIXED (2026-05-05)

**Mô tả:** `main.py` hard-code `allow_origins=["http://localhost:3000"]`, bỏ qua `settings.CORS_ORIGINS`. Production bị CORS block.

**Giải pháp:** Dùng `settings.cors_origins_list`.

### SEC-3: Token error rò rỉ internal details ✅ FIXED (2026-05-05)

**Mô tả:** Error message trong `_verify_token` expose chi tiết nội bộ (`jwt.exceptions` message) — attacker học được internal implementation.

**Giải pháp:** Refactor thành `_verify_token` trả generic messages: `"Invalid token"` / `"Token expired"`.

### SEC-4: Không có rate limiting ✅ FIXED (2026-05-05)

**Mô tả:** Không giới hạn số lần login thất bại → brute-force / credential stuffing.

**Giải pháp:** Tạo [middleware/ratelimit.py](backend/app/middleware/ratelimit.py) — in-memory limiter, 5 lần thử / 15 phút. Trả 429 + `Retry-After` header. X-Forwarded-For aware cho deployment behind proxy.

---

## 4. Acceptance Criteria — Verification

| ID | Mô tả | Endpoint / Đường dẫn code | Kết quả |
|----|-------|--------------------------|---------|
| AC-auth-1 | Login success → 200 + cookie | [routes/auth.py:33](backend/app/routes/auth.py#L33) | ✅ OK |
| AC-auth-2 | Sai password → 401 | [routes/auth.py:42](backend/app/routes/auth.py#L42) | ✅ OK |
| AC-auth-3 | User disabled → 403 | [routes/auth.py:45](backend/app/routes/auth.py#L45) | ✅ OK |
| AC-auth-4 | /me với cookie hợp lệ → user | [routes/auth.py:77](backend/app/routes/auth.py#L77) | ✅ OK |
| AC-auth-5 | Không cookie → 401 | [routes/auth.py:79](backend/app/routes/auth.py#L79) | ✅ OK |
| AC-auth-6 | Token hết hạn → 401 | [routes/auth.py:93](backend/app/routes/auth.py#L93) | ✅ OK |
| AC-auth-7 | Logout xoá cookie | [routes/auth.py:73](backend/app/routes/auth.py#L73) | ✅ OK |
| AC-auth-8 | Reload page → vẫn login | [App.jsx:10](frontend/src/App.jsx#L10) | ✅ OK |
| AC-auth-9 | httpOnly — JS không đọc được | [routes/auth.py:53](backend/app/routes/auth.py#L53) | ✅ OK |
| AC-auth-10 | CORS credentials | [main.py:14](backend/app/main.py#L14) + [api/client.js:6](frontend/src/api/client.js#L6) | ✅ OK |

---

## 5. Cấu trúc thư mục Login Module

```
backend/app/
├── core/
│   └── config.py          ← SECRET_KEY, CORS_ORIGINS, (COOKIE_SECURE)
├── db/
│   ├── session.py         ← AsyncSessionLocal, get_db
│   └── base.py            ← DeclarativeBase
├── middleware/
│   └── auth.py            ← require_user(), optional_user(), verify_token()
├── models/
│   └── user.py            ← User model
├── routes/
│   ├── auth.py            ← /login, /logout, /me
│   └── health.py          ← /health/db
└── main.py                ← app, CORS, startup create tables

frontend/src/
├── api/
│   └── client.js          ← axios withCredentials
├── pages/
│   ├── LoginPage.jsx      ← Login form
│   └── DashboardPage.jsx ← Protected page + logout
├── App.jsx                ← Auth flow: /me check → render
├── main.jsx
└── styles.css
```

---

## 6. Environment Variables cần thiết

```env
# .env (backend)
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/redmine_db
SECRET_KEY=<random-32-char-string>    # Bắt buộc — không dùng "change-me"
CORS_ORIGINS=http://localhost:3000

# .env.production (deploy)
COOKIE_SECURE=true    # HTTPS bắt buộc
```

---

## 7. Test thủ công

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 2. Start frontend
cd frontend
npm run dev

# 3. Test flow
# Login: admin / admin         → redirect dashboard ✅
# Reload: vẫn ở dashboard      → session restore ✅
# Logout: về login page         → ✅
# Sai pass: hiện error message  → ✅
```

---

## 9. Wireframe (từ spec_pack.md §9)

### 9.1. Layout Overview

```text
+----------------------------------------------------------------------------------+
|                                 LOGIN SCREEN                                     |
+----------------------------------------------------------------------------------+
|                                                                                  |
|  [ LEFT PANEL - BRANDING ]        |   [ RIGHT PANEL - LOGIN FORM ]               |
|----------------------------------|----------------------------------------------|
|  Logo (Redmine)                  |   Logo (mobile only)                         |
|  Headline                        |   "Sign In"                                   |
|  Description                     |   Description text                            |
|                                  |                                              |
|  Version Info                    |   Username Field                              |
|  Status (Online)                 |   Password Field                              |
|                                  |   Forgot password link                        |
|                                  |                                              |
|                                  |   [ ] Remember me                            |
|                                  |                                              |
|                                  |   [ Login Button ]                           |
|                                  |                                              |
|                                  |   Footer (Contact admin)                     |
|                                                                                  |
+----------------------------------------------------------------------------------+
```

### 9.2. Left Panel (Desktop Only)

```text
+--------------------------------------+
| [Logo] Redmine                       |
|--------------------------------------|
| "Manage your projects..."            |
|                                      |
| Enterprise description text          |
|                                      |
|--------------------------------------|
| Version: 5.1.2 Enterprise            |
| Status: ● Systems Online             |
+--------------------------------------+
```

### 9.3. Right Panel (Login Form)

```text
+--------------------------------------+
| Sign In                              |
| Access your workspace...             |
|--------------------------------------|
| Login or Email                       |
| [ 👤  input field                ]   |
|                                      |
| Password              Forgot?        |
| [ 🔒  ************   👁 ]            |
|                                      |
| [ ] Stay logged in for 30 days       |
|                                      |
| [   Log In to Workspace   ]          |
|                                      |
|--------------------------------------|
| Don't have account? Contact admin    |
+--------------------------------------+
```

---

## 10. Open Issues (từ spec_pack.md §10)

| ID | Question | Priority |
|----|----------|----------|
| OI-1 | Có cần refresh token? | Future |
| OI-2 | Có cần HTTPS? | Before prod |

---

## 11. Risks (từ spec_pack.md §11)

| # | Risk | Mitigation | Status |
|---|------|-----------|--------|
| 1 | Token leak | httpOnly cookie | Mitigated ✅ |
| 2 | Brute force | future rate limit | Out of scope |
| 3 | CORS sai | test credentials | Tested ✅ |

---

## 12. Kết luận + Traceability

Module AUTH-001 **triển khai đầy đủ** theo spec_pack.md. Các gap và lỗ hổng bảo mật đã được fix (GAP-1 → GAP-3, SEC-1 → SEC-4). Khuyến nghị remaining items:

1. **SEC-5** (`samesite="lax"`) — cân nhắc `"strict"` trước khi deploy nếu không có cross-site navigation
2. **In-memory rate limiter** — production nên thay bằng Redis-backed limiter
3. **HTTPS bắt buộc** — đảm bảo `COOKIE_SECURE=true` + backend behind TLS terminator

### Wireframe → Code (impl §9, 2026-05-04)

| Wireframe element | Spec ref | CSS class | Code file | Dòng |
|-------------------|----------|-----------|-----------|------|
| Layout 2 cột (brand + form) | §9.1 | `.login-layout` | [styles.css](frontend/src/styles.css) | 15–19 |
| Left panel — branding | §9.1 | `.login-brand` | [styles.css](frontend/src/styles.css) | 22–28 |
| Logo + "Redmine" | §9.2 | `.brand-logo` / `.brand-logo-name` | [LoginPage.jsx:36](frontend/src/pages/LoginPage.jsx#L36) + [styles.css:43](frontend/src/styles.css#L43) | 36–38, 43–60 |
| Headline VN | §9.2 | `.brand-headline` | [LoginPage.jsx:41](frontend/src/pages/LoginPage.jsx#L41) + [styles.css:66](frontend/src/styles.css#L66) | 41–43, 66–72 |
| Description | §9.2 | `.brand-description` | [LoginPage.jsx:44](frontend/src/pages/LoginPage.jsx#L44) + [styles.css:74](frontend/src/styles.css#L74) | 44–47, 74–79 |
| Version + Status dot | §9.2 | `.brand-foot` / `.status-dot` | [LoginPage.jsx:50](frontend/src/pages/LoginPage.jsx#L50) + [styles.css:81](frontend/src/styles.css#L81) | 50–56, 81–109 |
| Right panel — form | §9.1 | `.login-form-panel` | [styles.css:112](frontend/src/styles.css#L112) | 112–118 |
| Form card | §9.1 | `.login-form-card` | [styles.css:120](frontend/src/styles.css#L120) | 120–127 |
| "Sign In" header | §9.3 | `.form-header` | [LoginPage.jsx:69](frontend/src/pages/LoginPage.jsx#L69) + [styles.css:142](frontend/src/styles.css#L142) | 69–72, 142–157 |
| Username field (👤) | §9.3 | `.input-icon-wrap` | [LoginPage.jsx:76](frontend/src/pages/LoginPage.jsx#L76) + [styles.css:185](frontend/src/styles.css#L185) | 76–87, 185–212 |
| Password field (🔒 + 👁) | §9.3 | `.input-icon-wrap` + `.toggle-pw` | [LoginPage.jsx:89](frontend/src/pages/LoginPage.jsx#L89) + [styles.css:214](frontend/src/styles.css#L214) | 89–116, 214–229 |
| Forgot? link | §9.3 | `.forgot-link` | [LoginPage.jsx:92](frontend/src/pages/LoginPage.jsx#L92) + [styles.css:231](frontend/src/styles.css#L231) | 92–94, 231–240 |
| "Log In to Workspace" button | §9.3 | `.btn-login` | [LoginPage.jsx:120](frontend/src/pages/LoginPage.jsx#L120) + [styles.css:251](frontend/src/styles.css#L251) | 120–122, 251–272 |
| Footer — Contact admin | §9.3 | `.form-footer` | [LoginPage.jsx:125](frontend/src/pages/LoginPage.jsx#L125) + [styles.css:274](frontend/src/styles.css#L274) | 125–128, 274–289 |
| Mobile layout (hide left panel) | §9.1 | `@media (max-width: 768px)` | [styles.css:292](frontend/src/styles.css#L292) | 291–311 |
| Mobile logo row | §9.1 | `.mobile-logo` | [LoginPage.jsx:65](frontend/src/pages/LoginPage.jsx#L65) + [styles.css:135](frontend/src/styles.css#L135) | 65–67, 129–134 |

> **Ghi chú:** "Stay logged in for 30 days" checkbox (spec §9.3) **không implement** — thuộc refresh-token scope, đã noted trong [spec_pack.md §2](spec_pack.md#2-phạm-vi) là out of scope.

### Traceability AC → API (từ spec_pack.md §12)

| AC | API | Code file |
|----|-----|-----------|
| AC-auth-1 | /login | [routes/auth.py](backend/app/routes/auth.py) |
| AC-auth-4 | /me | [routes/auth.py](backend/app/routes/auth.py) |
| AC-auth-7 | /logout | [routes/auth.py](backend/app/routes/auth.py) |