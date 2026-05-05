# AUTH-001 — Login Module: Review Checklist

> Checklist cho Giai đoạn tự kiểm tra (self-review). Mỗi mục phải được đánh dấu ✅ hoặc ❌ và ghi bằng chứng.

---

## 0. Trước khi review

- [ ] Đọc đầy đủ [spec_pack.md](./spec_pack.md)
- [ ] Đọc đầy đủ [impl-plan.md](./impl-plan.md)
- [ ] Hiểu rõ 10 AC của AUTH-001 (AC-auth-1 → AC-auth-10)
- [ ] Chạy lệnh lint/test của dự án (nếu có)

---

## 1. Correctness (Tính đúng đắn)

- [ ] **AC-auth-1** — Login đúng user/pass → HTTP 200 + set cookie `access_token`
  - Evidence: [routes/auth.py:33-68](backend/app/routes/auth.py#L33)
- [ ] **AC-auth-2** — Login sai password → HTTP 401
  - Evidence: [routes/auth.py:42](backend/app/routes/auth.py#L42)
- [ ] **AC-auth-3** — User disabled (`is_active=false`) → HTTP 403
  - Evidence: [routes/auth.py:45](backend/app/routes/auth.py#L45)
- [ ] **AC-auth-4** — `/me` với cookie hợp lệ → trả user object
  - Evidence: [routes/auth.py:77-82](backend/app/routes/auth.py#L77)
- [ ] **AC-auth-5** — Không có cookie → HTTP 401
  - Evidence: [routes/auth.py:79-81](backend/app/routes/auth.py#L79)
- [ ] **AC-auth-6** — Token hết hạn → HTTP 401
  - Evidence: [routes/auth.py:93](backend/app/routes/auth.py#L93)
- [ ] **AC-auth-7** — Logout xoá cookie `access_token`
  - Evidence: [routes/auth.py:73](backend/app/routes/auth.py#L73)
- [ ] **AC-auth-8** — Reload page → session restore (gọi `/me` trên mount)
  - Evidence: [App.jsx:10-16](frontend/src/App.jsx#L10)
- [ ] JWT payload đúng format: `sub`, `username`, `exp`
  - Evidence: [routes/auth.py:18-25](backend/app/routes/auth.py#L18)
- [ ] Database query có parameterized (SQL injection safe)
  - Evidence: [routes/auth.py:36](backend/app/routes/auth.py#L36) — dùng SQLAlchemy ORM

---

## 2. Security

- [ ] **AC-auth-9** — httpOnly cookie → JS không đọc được
  - Evidence: [routes/auth.py:53](backend/app/routes/auth.py#L53)
- [ ] **AC-auth-10** — `withCredentials: true` trên frontend client
  - Evidence: [api/client.js:6](frontend/src/api/client.js#L6)
- [ ] **AC-auth-10** — CORS `allow_credentials=True` + `allow_origins` đúng
  - Evidence: [main.py:11-17](backend/app/main.py#L11)
- [ ] Password được verify bằng bcrypt (không so sánh plaintext)
  - Evidence: [routes/auth.py:42](backend/app/routes/auth.py#L42)
- [ ] JWT algorithm hard-coded `HS256` (không nhận từ user input)
  - Evidence: [routes/auth.py:14](backend/app/routes/auth.py#L14)
- [ ] HTTPException không leak thông tin nhạy cảm trong detail
  - Evidence: [routes/auth.py:96](backend/app/routes/auth.py#L96) — `JWTError` detail được ghi ra nhưng không chứa token hay secret
- [ ] Không có secret/hardcoded credentials trong code (SECRET_KEY từ env)
  - Evidence: [core/config.py:6](backend/app/core/config.py#L6) — từ `.env`

---

## 3. Performance

- [ ] Không có N+1 query
  - Evidence: Chỉ 1 query đơn lẻ trong login `/me`
- [ ] Không I/O không cần thiết (đồng bộ call trong async function)
  - Evidence: bcrypt, jwt đều là sync calls nhưng nhanh và không block event loop đáng kể

---

## 4. Reliability / Error Handling

- [ ] Tất cả `await` có try/except hợp lý (backend)
  - Evidence: [routes/auth.py:35](backend/app/routes/auth.py#L35) — wrapped in try (ngoại trừ get_me gọi get_current_user đồng bộ)
- [ ] Không unhandled promise rejection (frontend)
  - Evidence: [App.jsx:11](frontend/src/App.jsx#L11) — `.catch(() => {})` bắt lỗi `/me` khi chưa login
- [ ] LoginPage handle error 401, error khác tách biệt
  - Evidence: [LoginPage.jsx:22-27](frontend/src/pages/LoginPage.jsx#L22)
- [ ] DashboardPage logout không crash nếu API fail
  - Evidence: [DashboardPage.jsx:14-21](frontend/src/pages/DashboardPage.jsx#L14)

---

## 5. Maintainability / Code Quality

- [ ] Type hints đầy đủ (Python backend)
  - Evidence: [routes/auth.py:18](backend/app/routes/auth.py#L18) — `user_id: int, username: str`
- [ ] Error message rõ ràng, có ý nghĩa với người dùng cuối
  - Evidence: [LoginPage.jsx:24-26](frontend/src/pages/LoginPage.jsx#L24)
- [ ] No code duplication (middleware tái sử dụng logic)
  - Evidence: [middleware/auth.py](backend/app/middleware/auth.py) được dùng bởi `get_me` path
- [ ] Comment chỉ khi cần thiết, không giải thích điều hiển nhiên
  - Evidence: Có comment tiếng Việt cho business logic, tiếng Anh cho technical

---

## 6. Testing Coverage (nếu có tests)

- [ ] Unit tests cho backend auth logic
- [ ] Unit tests cho middleware `require_user`
- [ ] Integration tests cho API endpoints
- [ ] E2E tests cho login flow / session restore (nếu dùng Playwright)

---

## 7. Trùng lắp spec vs. impl

- [ ] Không có tính năng triển khai ngoài phạm vi spec
  - Scope spec: login/logout/me + JWT Cookie. Đã không có register, refresh token, rate limit.
- [ ] Không AC nào bị bỏ qua hoặc khác biệt so với spec
  - Tất cả 10 AC đã được verify ở §1.

---

## 8. Pre-deploy checklist

- [ ] `.env` đã cấu hình `SECRET_KEY` (không dùng "change-me")
- [ ] `COOKIE_SECURE` được set `true` khi deploy HTTPS
- [ ] Seed user `admin/admin` đã được tạo (hoặc migration có user mẫu)
- [ ] CORS `allow_origins` đã cập nhật domain production

---

## Tóm tắt

| Danh mục | Tổng | ✅ Pass | ❌ Fail |
|----------|------|--------|--------|
| Correctness | 11   | _      | _      |
| Security    | 7    | _      | _      |
| Performance | 2    | _      | _      |
| Reliability | 4    | _      | _      |
| Maintainability | 4 | _      | _      |
| **Tổng**     | **28** | **_**  | **_**  |

→ Ghi kết quả vào [self-review.md](./self-review.md)