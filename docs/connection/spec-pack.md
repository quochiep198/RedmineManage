# Goi dac ta --- (Redmine Connection)

> Tao: 2026-05-05
> Giai doan: [1] Nguon tham chieu duy nhat cho thay doi nay.
> Khong trien khai bat ky noi dung nao khong duoc viet o day.
> Cac muc chua ro duoc liet ke trong Open Issues.

------------------------------------------------------------------------

## 1. Boi canh / Muc dich

Cho phep admin cau hinh Redmine URL, project `identifier`, va API key de
backend co the goi Redmine REST API cho mot project muc tieu duy nhat.

API key Redmine trong module nay la shared system credential do admin quan ly
de backend cua he thong ket noi toi Redmine. User thuong khong duoc xem,
khong duoc sua, va khong dang nhap vao web bang API key nay.

He thong trong phase nay chi phuc vu mot project dang thuc thi. Khong hien
thi va khong xu ly cac project khac ngoai project co `identifier` da cau hinh.

Man hinh ap dung:

- Admin > Settings > Redmine Connection
- Day la mot man hinh cau hinh rieng danh cho admin.

## 2. Pham vi

### Trong pham vi

- Tao Redmine connection.
- Cap nhat Redmine connection.
- Test connection bang Redmine REST API.
- Cau hinh `identifier` cua project dang thuc thi.
- Ma hoa co the giai ma duoc API key truoc khi luu DB.
- Khong tra API key plain text ve frontend.

### Ngoai pham vi

- Moi user tu quan ly nhieu API key.
- OAuth voi Redmine.
- Rotate API key tu dong.
- Dong bo du lieu issue/project tu Redmine.
- User thuong su dung truc tiep Redmine API key o frontend.
- Hien thi nhieu project cung luc trong phase nay.

## 3. Thuat ngu

| # | Thuat ngu | Dinh nghia |
|---|---|---|
| 1 | Redmine connection | Cau hinh gom `name`, `base_url`, `identifier`, `api_key` de backend ket noi toi mot Redmine server va mot project muc tieu |
| 2 | Connection test | Hanh dong backend goi `GET /my/account.json` voi API key da luu de xac minh ket noi |
| 3 | Reversible encryption | Co che ma hoa cho phep backend giai ma API key khi can goi Redmine API |
| 4 | Shared system credential | Credential dung chung cho backend cua he thong, do admin quan ly, khong cap cho user thuong |
| 5 | Project identifier | Identifier cua project Redmine duoc chon de he thong chi xu ly va hien thi project nay |

## 4. Hien trang / Trang thai muc tieu

| # | Khia canh | Hien trang | Trang thai muc tieu |
|---|---|---|---|
| 1 | Ket noi Redmine | [MISSING] | Backend goi duoc Redmine REST API thong qua connection da luu |
| 2 | Bao mat API key | [MISSING] | API key duoc ma hoa trong DB, khong log, khong tra ve frontend |
| 3 | Kiem tra cau hinh | [MISSING] | Admin co the test connection va nhan ket qua ro rang |

## 5. Chi tiet dac ta

### 5.1 Quyen truy cap

- Chi user co quyen `admin` moi duoc tao, cap nhat, va test Redmine connection.
- Quyen `admin` duoc xac dinh bang truong `is_admin = true` trong bang `users`.
- Neu user khong co quyen `admin`, backend tra `403 FORBIDDEN`.

### 5.2 API tao connection

- Endpoint: `POST /api/redmine/connections`

Request:

```json
{
  "name": "Company Redmine",
  "base_url": "https://redmine.example.com",
  "identifier": "nishimatsuya",
  "api_key": "redmine-api-key"
}
```

Validation:

- `name` bat buoc, do dai 1-100 ky tu sau khi trim.
- `base_url` bat buoc, phai la URL hop le voi scheme `http` hoac `https`.
- `base_url` duoc phep co path prefix, vi du `https://example.com/redmine`.
- `identifier` bat buoc, do dai 1-255 ky tu sau khi trim.
- `api_key` bat buoc khi tao moi.

Response `201 Created`:

```json
{
  "id": 1,
  "name": "Company Redmine",
  "base_url": "https://redmine.example.com",
  "identifier": "nishimatsuya",
  "status": "untested",
  "created_at": "2026-05-05T09:00:00Z",
  "updated_at": "2026-05-05T09:00:00Z",
  "last_tested_at": null
}
```

Rules:

- Backend luu `api_key` duoi dang ma hoa co the giai ma duoc.
- Backend khong tra `api_key` hoac `encrypted_api_key` trong response.
- Trang thai ban dau sau khi tao la `untested`.

### 5.3 API cap nhat connection

- Endpoint: `PATCH /api/redmine/connections/{connection_id}`

Request:

```json
{
  "name": "Company Redmine - Prod",
  "base_url": "https://redmine.example.com",
  "identifier": "nishimatsuya",
  "api_key": "new-redmine-api-key"
}
```

Rules:

- Cho phep cap nhat `name`, `base_url`, `identifier`, `api_key`.
- Neu request khong gui `api_key`, backend giu nguyen API key hien tai.
- Neu request co gui `api_key`, backend ma hoa lai gia tri moi truoc khi luu.
- Sau khi cap nhat `base_url` hoac `api_key`, backend dat `status = "untested"` va `last_tested_at = null`.
- Neu chi cap nhat `name`, backend khong thay doi `status`.

Response `200 OK`:

```json
{
  "id": 1,
  "name": "Company Redmine - Prod",
  "base_url": "https://redmine.example.com",
  "identifier": "nishimatsuya",
  "status": "untested",
  "created_at": "2026-05-05T09:00:00Z",
  "updated_at": "2026-05-05T09:30:00Z",
  "last_tested_at": null
}
```

### 5.4 API test connection

- Endpoint: `POST /api/redmine/connections/{connection_id}/test`

Logic:

```text
GET {base_url}/my/account.json
Header: X-Redmine-API-Key: {API_KEY_GIAI_MA}
```

URL handling:

- Backend phai normalize `base_url` de tranh loi double slash.
- Neu `base_url` co path prefix, backend phai giu nguyen path prefix khi noi `/my/account.json`.

Response success `200 OK`:

```json
{
  "success": true,
  "message": "Connection successful",
  "status": "active",
  "redmine_user": {
    "id": 10,
    "login": "hiep",
    "firstname": "Hiep"
  },
  "last_tested_at": "2026-05-05T09:35:00Z"
}
```

Response error `401 Unauthorized`:

```json
{
  "code": "REDMINE_UNAUTHORIZED",
  "message": "Invalid Redmine API key"
}
```

Response error `403 Forbidden`:

```json
{
  "code": "REDMINE_FORBIDDEN",
  "message": "Redmine user does not have permission"
}
```

Response error `504 Gateway Timeout`:

```json
{
  "code": "REDMINE_TIMEOUT",
  "message": "Timed out while connecting to Redmine"
}
```

Rules:

- Neu Redmine tra `200`, backend cap nhat `status = "active"` va `last_tested_at` bang thoi diem test.
- Neu Redmine tra `401`, backend cap nhat `status = "failed"` va `last_tested_at` bang thoi diem test.
- Neu Redmine tra `403`, backend cap nhat `status = "failed"` va `last_tested_at` bang thoi diem test.
- Neu timeout, backend cap nhat `status = "failed"` va `last_tested_at` bang thoi diem test.
- Backend khong duoc dua API key vao request log, application log, hay error response.

### 5.5 Data model

Table: `redmine_connections`

| Field | Type | Ghi chu |
|---|---|---|
| `id` | bigint | Khoa chinh |
| `name` | varchar(100) | Ten connection hien thi |
| `base_url` | varchar(255) | URL goc cua Redmine |
| `identifier` | varchar(255) | Identifier cua project dang thuc thi tren Redmine |
| `encrypted_api_key` | text | API key da ma hoa, backend giai ma khi goi Redmine |
| `status` | varchar(20) | Gia tri hop le: `untested`, `active`, `failed`, `disabled` |
| `created_by` | bigint | ID user admin tao ban ghi |
| `created_at` | datetime | Thoi diem tao |
| `updated_at` | datetime | Thoi diem cap nhat cuoi |
| `last_tested_at` | datetime, nullable | Thoi diem test gan nhat |

Bang `users`:

| Field | Type | Ghi chu |
|---|---|---|
| `is_admin` | boolean | Xac dinh user co quyen quan tri hay khong; chi user co `is_admin = true` duoc quan ly Redmine Connection |

### 5.6 Business rules

- `base_url` bat buoc va phai la URL hop le.
- `identifier` bat buoc va xac dinh project duy nhat he thong duoc phep xu ly/hien thi.
- `api_key` bat buoc khi tao moi.
- `api_key` khong bat buoc khi cap nhat.
- API key phai duoc ma hoa theo co che reversible encryption truoc khi luu DB.
- API key khong duoc hash mot chieu vi backend can dung lai gia tri goc de goi Redmine.
- API key khong duoc log.
- API key khong duoc tra ve frontend.
- Chi user co `users.is_admin = true` moi duoc goi cac API trong module nay.
- User thuong su dung cac tinh nang Redmine thong qua backend va shared connection da duoc admin cau hinh san.
- API key nay khong duoc dung lam credential dang nhap cho user vao ung dung nay.
- Trong phase nay, he thong chi duoc hien thi va xu ly project co `identifier` da cau hinh.
- Cac project khac tren Redmine khong duoc dua vao UI cua he thong.
- Mac dinh moi he thong chi co 1 Redmine connection hoat dong tai mot thoi diem.
- Neu tao them connection moi khi da ton tai connection khac, backend tra `409 CONFLICT` voi code `REDMINE_CONNECTION_ALREADY_EXISTS`.

## 6. Yeu cau phi chuc nang

| # | Danh muc | Yeu cau |
|---|---|---|
| 1 | Hieu nang | API test connection phai timeout sau toi da 10 giay |
| 2 | Bao mat | API key phai duoc ma hoa truoc khi luu DB; khong log; khong tra ve frontend |
| 3 | Tinh san sang | Loi test connection khong duoc lam crash service |
| 4 | Kha nang quan sat | Log phai ghi nhan `connection_id`, HTTP status, thoi gian xu ly; khong ghi API key |

## 7. Tieu chi chap nhan

| # | ID | Mo ta | Loai kiem thu |
|---|---|---|---|
| 1 | CONN-AC-001 | Admin tao duoc Redmine connection | API integration |
| 2 | CONN-AC-002 | Admin test duoc API key hop le | API integration |
| 3 | CONN-AC-003 | API key khong xuat hien trong response create, update, get, test | API integration |
| 4 | CONN-AC-004 | API key sai tra `401` voi code `REDMINE_UNAUTHORIZED` | API integration |
| 5 | CONN-AC-005 | Redmine timeout tra `504` voi code `REDMINE_TIMEOUT` | API integration |
| 6 | CONN-AC-006 | Cap nhat `base_url` hoac `api_key` se reset `status` ve `untested` | API integration |
| 7 | CONN-AC-007 | User khong phai admin khong tao, cap nhat, test duoc connection | Authorization |

## 8. Vi du

### Cac luong binh thuong

1. Tao connection voi `base_url`, `identifier`, va `api_key` hop le, backend tao thanh cong va tra `status = "untested"`.
2. Test connection voi API key hop le, backend tra `success = true`, `status = "active"`.
3. Cap nhat `name` ma khong doi `api_key`, backend giu nguyen API key da luu.

### Cac luong loi

1. API key sai, backend tra `401 REDMINE_UNAUTHORIZED`.
2. Redmine tra `403`, backend tra `403 REDMINE_FORBIDDEN`.
3. Timeout khi goi Redmine, backend tra `504 REDMINE_TIMEOUT`.
4. User khong phai admin goi API, backend tra `403 FORBIDDEN`.
5. Tao connection thu hai khi da ton tai connection, backend tra `409 REDMINE_CONNECTION_ALREADY_EXISTS`.

### Cac truong hop bien

1. `base_url` khong hop le, backend tra validation error `422`.
2. Thieu `api_key` khi tao moi, backend tra validation error `422`.
3. `base_url` co dang `https://example.com/redmine/`, backend van tao URL test dung den `/redmine/my/account.json`.
4. `identifier` khong ton tai tren Redmine se duoc module downstream xu ly nhu project khong tim thay.

## 9. Wireframe ASCII (Tuy chon)

```text
Navigation: Admin > Settings > Redmine Connection

+------------------------------------------------------+
| Redmine Connection                                   |
+------------------------------------------------------+
| Name        [ Company Redmine                      ] |
| Base URL    [ https://redmine.example.com         ] |
| Identifier  [ nishimatsuya                        ] |
| API Key     [ ************************            ] |
|                                                    |
| [ Save ]                         [ Test connection ] |
|                                                    |
| Status: Untested / Active / Failed                 |
| Last tested: 2026-05-05 09:35 UTC                  |
+------------------------------------------------------+
```

## 10. Cac van de mo

| # | Cau hoi | Nguoi phu trach | Han chot |
|---|---|---|---|
| OI-1 | Co can endpoint `GET /api/redmine/connections/current` cho frontend tai lai cau hinh hien tai khong | Product + Backend | [MISSING] |
| OI-2 | `disabled` co duoc su dung ngay trong phase nay khong, hay de phase sau | Product + Backend | [MISSING] |
| OI-3 | Co can luu them `last_error_code` va `last_error_message` de hien thi lich su test gan nhat khong | Product + Backend | [MISSING] |

## 11. Rui ro

| # | Rui ro | Kha nang xay ra | Muc do anh huong | Bien phap giam thieu |
|---|---|---|---|---|
| 1 | Dung hash mot chieu cho API key khien backend khong goi duoc Redmine | Trung binh | Cao | Chot ro reversible encryption trong spec va review implementation |
| 2 | Xu ly sai `base_url` co path prefix lam test sai endpoint | Trung binh | Trung binh | Them test cho URL co va khong co path prefix |
| 3 | Log lo API key trong exception hoac debug log | Thap | Cao | Review logging, redact secrets, test negative paths |

------------------------------------------------------------------------

## Bang truy vet

| # | AC | Man hinh/API | DB | Logs | Quyen | Loai kiem thu |
|---|---|---|---|---|---|---|
| 1 | CONN-AC-001 | `POST /api/redmine/connections` | `redmine_connections` | Create audit log khong chua API key | Admin | API integration |
| 2 | CONN-AC-002 | `POST /api/redmine/connections/{id}/test` | `redmine_connections` | Test log co `connection_id`, status, duration | Admin | API integration |
| 3 | CONN-AC-003 | Create/Update/Test responses | `encrypted_api_key` | Secret redaction | Admin | API integration |
| 4 | CONN-AC-007 | Create/Update/Test APIs | N/A | Authorization failure log | Admin only | Authorization |
