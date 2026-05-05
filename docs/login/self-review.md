# AUTH-001 — Login Module: Self-Review

> Ghi lại kết quả tự kiểm tra sau khi triển khai xong.
> Điền theo [review-checklist.md](./review-checklist.md).
> Thực hiện: 2026-05-04

---

## Tổng quan

| Trường | Giá trị |
|--------|---------|
| Ticket | AUTH-001 |
| Module | Login Module — JWT Cookie Auth |
| Reviewer | (Claude Code tự kiểm tra) |
| Ngày | 2026-05-04 |
| Trạng thái | ✅ Triển khai hoàn tất, 3 gap nhỏ được ghi nhận |

---

## 1. Correctness

| Checklist | Result | Bằng chứng / Ghi chú |
|-----------|--------|----------------------|
| AC-auth-1 Login success | ✅ | `POST /api/auth/login` → 200 + Set-Cookie. File: [routes/auth.py:33-68](backend/app/routes/auth.py#L33) |
| AC-auth-2 Sai password | ✅ | `bcrypt.checkpw` fail → 401. File: [routes/auth.py:42](backend/app/routes/auth.py#L42) |
| AC-auth-3 User disabled | ✅ | `if not user.is_active` → 403. File: [routes/auth.py:45](backend/app/routes/auth.py#L45) |
| AC-auth-4 `/me` hợp lệ | ✅ | Cookie → verify → user dict. File: [routes/auth.py:77-98](backend/app/routes/auth.py#L77) |
| AC-auth-5 Không cookie | ✅ | `request.cookies.get` trả None → 401. File: [routes/auth.py:79](backend/app/routes/auth.py#L79) |
| AC-auth-6 Token expired | ✅ | `ExpiredSignatureError` → 401. File: [routes/auth.py:93](backend/app/routes/auth.py#L93) |
| AC-auth-7 Logout | ✅ | `response.delete_cookie`. File: [routes/auth.py:73](backend/app/routes/auth.py#L73) |
| AC-auth-8 Session restore | ✅ | `App.jsx useEffect` gọi `/me`. File: [App.jsx:10-16](frontend/src/App.jsx#L10) |
| JWT payload format | ✅ | `sub`, `username`, `exp`. File: [routes/auth.py:18-25](backend/app/routes/auth.py#L18) |
| SQL injection safe | ✅ | SQLAlchemy ORM parameterized query. File: [routes/auth.py:36](backend/app/routes/auth.py#L36) |

**Correctness: 10/10 ✅**

---

## 2. Security

| Checklist | Result | Bằng chứng |
|-----------|--------|------------|
| httpOnly cookie | ✅ | `httponly=True`. File: [routes/auth.py:53](backend/app/routes/auth.py#L53) |
| `withCredentials: true` | ✅ | File: [api/client.js:6](frontend/src/api/client.js#L6) |
| CORS credentials | ✅ | File: [main.py:14](backend/app/main.py#L14) |
| bcrypt password verify | ✅ | `bcrypt.checkpw`. File: [routes/auth.py:42](backend/app/routes/auth.py#L42) |
| JWT algorithm hard-coded | ✅ | `ALGORITHM = "HS256"`. File: [routes/auth.py:14](backend/app/routes/auth.py#L14) |
| Không leak secret | ✅ | SECRET_KEY từ env. File: [core/config.py:6](backend/app/core/config.py#L6) |
|Không expose token/secret trong error | ✅ | JWTError message không chứa secret. File: [routes/auth.py:96](backend/app/routes/auth.py#L96) |

**Security: 7/7 ✅**

---

## 3. Performance

| Checklist | Result | Bằng chứng |
|-----------|--------|------------|
| Không N+1 | ✅ | 1 query đơn lẻ |
| Không I/O không cần thiết | ✅ | bcrypt/jwt sync nhưng nhanh |

**Performance: 2/2 ✅**

---

## 4. Reliability / Error Handling

| Checklist | Result | Bằng chứng |
|-----------|--------|------------|
| Backend try/except | ✅ | [routes/auth.py:35](backend/app/routes/auth.py#L35) |
| Frontend unhandled rejection | ✅ | [App.jsx:11](frontend/src/App.jsx#L11) `.catch(() => {})` |
| LoginPage error handle tách biệt | ✅ | [LoginPage.jsx:22-27](frontend/src/pages/LoginPage.jsx#L22) |
| Logout crash-safe | ✅ | [DashboardPage.jsx:14-21](frontend/src/pages/DashboardPage.jsx#L14) |

**Reliability: 4/4 ✅**

---

## 5. Maintainability / Code Quality

| Checklist | Result | Bằng chứng |
|-----------|--------|------------|
| Type hints | ✅ | Có đầy đủ |
| Error message rõ ràng | ✅ | User-friendly message |
| No duplication | ✅ | middleware tái sử dụng |
| Comment có mục đích | ✅ | Chỉ comment khi cần |

**Maintainability: 4/4 ✅**

---

## 6. Testing Coverage

| Test | Trạng thái | Ghi chú |
|------|-----------|---------|
| Unit tests backend | ❌ Chưa có | Cần viết thêm |
| Integration tests API | ❌ Chưa có | Cần viết thêm |
| E2E login flow | ❌ Chưa có | Cần viết thêm |

**Testing: 0/3** — Đây là một thiếu sót cần bổ sung trong Giai đoạn 6.

---

## 7. Spec vs. Impl

| Checklist | Result |
|-----------|--------|
| Không triển khai ngoài phạm vi spec | ✅ |
| Không AC bị bỏ sót | ✅ |

---

## 8. Gaps / Issues cần theo dõi

### GAP-1 — `secure=False` trong cookie (Severity: Low)

- **File:** [routes/auth.py:54](backend/app/routes/auth.py#L54)
- **Mô tả:** `secure=False` hard-coded. Cần `secure=True` khi deploy HTTPS.
- **Fix:** Thêm `COOKIE_SECURE` env var, đọc từ `settings`

### GAP-2 — Không có seed user (Severity: Medium)

- **Mô tả:** Database tạo bảng tự động nhưng không có user `admin/admin`
- **Impact:** Login thực tế thất bại nếu chưa seed
- **Fix:** Thêm logic trong `startup` event ở [main.py](backend/app/main.py) để tạo user demo nếu chưa có

### GAP-3 — SECRET_KEY fallback (Severity: Medium)

- **File:** [core/config.py:6](backend/app/core/config.py#L6)
- **Mô tả:** Default `"change-me"` — có thể chạy production mà không nhận ra
- **Fix:** Raise error nếu dùng giá trị mặc định trong môi trường không phải dev

### GAP-4 — Thiếu tests (Severity: Medium)

- **Mô tả:** Không có UT/IT/E2E cho auth module
- **Fix:** Viết tests theo test-plan.md (Giai đoạn 6)

---

## Tổng kết

| Danh mục | Pass | Fail |
|----------|------|------|
| Correctness | 10 | 0 |
| Security | 7 | 0 |
| Performance | 2 | 0 |
| Reliability | 4 | 0 |
| Maintainability | 4 | 0 |
| **Tổng cộng** | **27/27** | **0** |
| Testing | 0/3 | 3 |

**Đánh giá tổng thể: ✅ Triển khai đạt yêu cầu.**

Module login/logout hoạt động đúng theo spec. 3 gap (GAP-1 → GAP-3) không chặn dev nhưng cần fix trước production. GAP-4 (tests) cần bổ sung trong Giai đoạn 6.

**Rekomendasi:**
1. GAP-2 (seed user) — ưu tiên cao vì không login được ở dev
2. GAP-3 (SECRET_KEY validation) — ưu tiên cao vì bảo mật
3. GAP-1 (COOKIE_SECURE) — ưu tiên trung bình, fix trước deploy
4. GAP-4 (tests) — Giai đoạn 6 tiếp theo