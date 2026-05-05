# Gói đặc tả — AUTH-001 (Login Module - JWT Cookie Auth)

> Tạo: 2026-05-04 · Giai đoạn: 1  
> **Nguồn tham chiếu duy nhất cho thay đổi này.**  
> Không triển khai bất kỳ nội dung nào không được viết ở đây. Các điểm chưa rõ → Open Issues.

---

## 1. Bối cảnh / Mục đích

Xây dựng module xác thực người dùng (login/logout) sử dụng JWT lưu trong httpOnly cookie nhằm:
- Tăng bảo mật (chống XSS)
- Đơn giản hóa session management phía frontend
- Cho phép frontend tự động restore session khi reload

---

## 2. Phạm vi

### Trong phạm vi
- API login/logout/me
- JWT authentication (HS256)
- Cookie-based auth
- CORS config (credentials)
- Frontend auth flow

### Ngoài phạm vi
- Refresh token
- Register / Forgot password
- Rate limiting
- HTTPS bắt buộc

---

## 3. Thuật ngữ

| # | Thuật ngữ | Định nghĩa |
|---|----------|-----------|
| 1 | JWT | Token xác thực |
| 2 | httpOnly Cookie | Cookie không truy cập bằng JS |
| 3 | Session | Trạng thái đăng nhập |
| 4 | Access Token | Token dùng xác thực request |

---

## 4. Hiện trạng / Trạng thái mục tiêu

| # | Khía cạnh | Hiện trạng | Mục tiêu |
|---|----------|-----------|----------|
| 1 | Auth | Không có | JWT Cookie |
| 2 | Storage | Local | Cookie |
| 3 | Security | Thấp | XSS-safe |
| 4 | UX | Không auto login | Auto restore |

---

## 5. Chi tiết đặc tả

### 5.1 API

#### POST /api/auth/login
- Validate username/password
- Tạo JWT
- Set cookie

#### GET /api/auth/me
- Đọc cookie
- Verify token
- Trả user

#### POST /api/auth/logout
- Clear cookie

---

### 5.2 JWT

- Algorithm: HS256
- Expiry: 60 phút
- Payload:
```json
{
  "sub": "user_id",
  "username": "string",
  "exp": "timestamp"
}
```

---

### 5.3 Database

```sql
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE,
    password VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE
);
```

---

## 6. Yêu cầu phi chức năng

| # | Danh mục | Yêu cầu |
|---|----------|--------|
| 1 | Hiệu năng | < 200ms |
| 2 | Bảo mật | bcrypt + httpOnly |
| 3 | Availability | 99% |
| 4 | Logging | log auth events |

---

## 7. Tiêu chí chấp nhận (AC)

| # | ID | Mô tả | Input | Expected Output | Test |
|---|----|------|-------|----------------|------|
| 1 | AC-auth-1 | Login success | đúng user/pass | 200 + cookie | IT |
| 2 | AC-auth-2 | Login fail | sai password | 401 | UT |
| 3 | AC-auth-3 | User disabled | is_active=false | 403 | UT |
| 4 | AC-auth-4 | Get current user | có cookie hợp lệ | trả user | IT |
| 5 | AC-auth-5 | No token | không cookie | 401 | IT |
| 6 | AC-auth-6 | Expired token | token hết hạn | 401 | E2E |
| 7 | AC-auth-7 | Logout | call logout | cookie bị xoá | IT |
| 8 | AC-auth-8 | Session restore | reload page | vẫn login | E2E |
| 9 | AC-auth-9 | Cookie security | inspect JS | không đọc được | Security |
| 10 | AC-auth-10 | CORS credentials | cross origin | cookie gửi kèm | IT |

---

## 8. Ví dụ

### Normal flow
1. Login → dashboard
2. Reload → vẫn login

### Error flow
1. Sai password → 401
2. Token hết hạn → login lại

### Edge cases
1. Cookie bị xoá
2. User bị disable

---

## 9. Wireframe

## 9.1. Layout Overview

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

---

## 9.2. Left Panel (Desktop Only)

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

---

## 9.3. Right Panel (Login Form)

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

## 10. Open Issues

| ID | Question |
|----|----------|
| OI-1 | Có cần refresh token? |
| OI-2 | Có cần HTTPS? |

---

## 11. Risks

| # | Risk | Mitigation |
|---|------|-----------|
| 1 | Token leak | httpOnly |
| 2 | Brute force | future rate limit |
| 3 | CORS sai | test |

---

## Traceability

| AC | API |
|----|-----|
| AC-auth-1 | /login |
| AC-auth-4 | /me |
| AC-auth-7 | /logout |
