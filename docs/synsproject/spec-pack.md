# Goi dac ta --- (Project Sync & Management)

> Tao: 2026-05-05
> Giai doan: [1]
> Nguon tham chieu duy nhat cho thay doi nay.
> Khong trien khai bat ky noi dung nao khong duoc viet o day.
> Cac muc chua ro duoc liet ke trong Open Issues.

------------------------------------------------------------------------

## 1. Boi canh / Muc dich

 Dong bo project dang thuc thi tu Redmine ve database noi bo de phuc vu:

- dashboard
- project list
- issue list
- member performance

 Module nay su dung shared Redmine connection da duoc admin cau hinh san
 trong module Redmine Connection, bao gom `identifier` cua project muc tieu.
 User thuong khong truyen API key va khong truy cap truc tiep Redmine.

Man hinh ap dung:

- Admin > Settings > Project Sync
- Dashboard > Projects

## 2. Pham vi

### Trong pham vi

- Sync mot project duy nhat tu Redmine ve DB noi bo.
- Luu project vao bang `projects`.
- Upsert project theo `redmine_project_id`.
- Hien thi project dang thuc thi tu DB noi bo.
- Luu thong tin sync gan nhat cho tung project.
- Ghi sync log khi sync loi.

### Ngoai pham vi

- Tao/sua/xoa project tren Redmine.
- Phan quyen project chi tiet theo user noi bo.
- User thuong truyen truc tiep API key hoac connection config.
- Scheduled sync tu dong.
- Hien thi danh sach nhieu project trong phase nay.

## 3. Thuat ngu

| # | Thuat ngu | Dinh nghia |
|---|---|---|
| 1 | Project sync | Hanh dong backend goi Redmine API, lay project theo `identifier` da cau hinh, va upsert vao DB noi bo |
| 2 | Redmine project id | ID goc cua project ben Redmine, dung lam khoa match chinh khi upsert |
| 3 | Identifier | Gia tri string duy nhat cua project tren Redmine, vi du `nishimatsuya` |
| 4 | Shared connection | Redmine connection dung chung cho toan he thong, da duoc admin cau hinh san |

## 4. Hien trang / Trang thai muc tieu

| # | Khia canh | Hien trang | Trang thai muc tieu |
|---|---|---|---|
| 1 | Dong bo project | [MISSING] | Admin co the trigger sync project muc tieu tu Redmine |
| 2 | Luu tru | [MISSING] | Project duoc luu trong bang `projects` |
| 3 | Cap nhat du lieu | [MISSING] | Upsert theo `redmine_project_id`, khong tao trung |
| 4 | Truy van | [MISSING] | Co API lay project dang thuc thi tu DB noi bo |
| 5 | Quan sat | [MISSING] | Co sync log khi xay ra loi |

## 5. Chi tiet dac ta

### 5.1 Quyen truy cap

- Chi user co `users.is_admin = true` moi duoc goi `POST /api/projects/sync`.
- User da dang nhap duoc phep goi `GET /api/projects`.
- Neu user chua dang nhap, backend tra `401 Not authenticated`.
- Neu user khong phai admin ma goi sync, backend tra `403 Forbidden`.

### 5.2 Nguon du lieu Redmine

Backend su dung shared Redmine connection hien hanh da duoc luu trong he thong.

Redmine API duoc su dung:

- `GET /projects/{identifier}.json`

Ghi chu:

- `identifier` duoc lay tu module Redmine Connection.
- Phase nay khong goi `GET /projects.json` de lay danh sach nhieu project.
- Toan bo du lieu project can thiet cho phase nay phai duoc lay tu `GET /projects/{identifier}.json`.

### 5.3 API sync project

- Endpoint: `POST /api/projects/sync`

Request:

```json
{}
```

Rules:

- Backend tu tim shared Redmine connection hien hanh.
- Neu chua co Redmine connection, backend tra `409` voi code `REDMINE_CONNECTION_NOT_CONFIGURED`.
- Neu Redmine connection ton tai nhung test chua thanh cong truoc do, backend van duoc phep thu sync.

Behavior:

1. Backend doc `identifier` tu shared Redmine connection hien hanh.
2. Backend goi Redmine `GET /projects/{identifier}.json`.
3. Backend doc object project tu response.
4. Project duoc match theo `(connection_id, redmine_project_id)`.
5. Neu record da ton tai thi update.
6. Neu record chua ton tai thi insert.
7. Khong xoa project local neu project hien tai sync that bai.
8. `raw_data_json` luu raw object project tu Redmine.
9. `last_synced_at` duoc cap nhat tai thoi diem sync thanh cong.

Response `200 OK`:

```json
{
  "success": true,
  "total_synced": 1,
  "created": 0,
  "updated": 1,
  "connection_id": 1,
  "identifier": "nishimatsuya",
  "synced_at": "2026-05-05T10:00:00Z"
}
```

Response error `409 Conflict`:

```json
{
  "code": "REDMINE_CONNECTION_NOT_CONFIGURED",
  "message": "Redmine connection is not configured"
}
```

Response error `504 Gateway Timeout`:

```json
{
  "code": "REDMINE_TIMEOUT",
  "message": "Timed out while syncing projects from Redmine"
}
```

Response error `502 Bad Gateway`:

```json
{
  "code": "REDMINE_SYNC_FAILED",
  "message": "Failed to sync projects from Redmine"
}
```

### 5.4 API lay project dang thuc thi

- Endpoint: `GET /api/projects/current`

Query params:

- Khong co query params trong phase nay.

Response `200 OK`:

```json
{
  "id": 1,
  "connection_id": 1,
  "redmine_project_id": 101,
  "identifier": "nishimatsuya",
  "name": "Nishimatsuya",
  "description": "Project imported from Redmine",
  "is_active": true,
  "last_synced_at": "2026-05-05T10:00:00Z",
  "created_at": "2026-05-05T10:00:00Z",
  "updated_at": "2026-05-05T10:00:00Z"
}
```

Rules:

- API tra ve duy nhat project co `identifier` da duoc cau hinh trong shared Redmine connection.
- API khong tra `raw_data_json`.

### 5.5 Data model

Table: `projects`

| Field | Type | Ghi chu |
|---|---|---|
| `id` | bigint | Khoa chinh |
| `connection_id` | bigint | FK toi `redmine_connections.id` |
| `redmine_project_id` | bigint | ID goc cua project ben Redmine |
| `identifier` | varchar(255) | Identifier cua project |
| `name` | varchar(255) | Ten project |
| `description` | text, nullable | Mo ta project |
| `is_active` | boolean | Trang thai local cua project |
| `raw_data_json` | json | Raw object tu Redmine |
| `last_synced_at` | datetime | Lan sync thanh cong gan nhat |
| `created_at` | datetime | Thoi diem tao |
| `updated_at` | datetime | Thoi diem cap nhat cuoi |

Unique constraints:

- `(connection_id, redmine_project_id)`
- `(connection_id, identifier)`

Table: `project_sync_logs`

| Field | Type | Ghi chu |
|---|---|---|
| `id` | bigint | Khoa chinh |
| `connection_id` | bigint | FK toi `redmine_connections.id` |
| `status` | varchar(20) | `success` hoac `failed` |
| `error_code` | varchar(100), nullable | Vi du `REDMINE_TIMEOUT` |
| `error_message` | text, nullable | Noi dung loi tom tat |
| `total_synced` | int, nullable | Tong so record xu ly |
| `created_count` | int, nullable | So record tao moi |
| `updated_count` | int, nullable | So record cap nhat |
| `started_at` | datetime | Thoi diem bat dau sync |
| `finished_at` | datetime | Thoi diem ket thuc sync |

### 5.6 Business rules

- Sync project chi duoc chay bang shared Redmine connection.
- Shared Redmine connection bat buoc phai co `identifier`.
- Match upsert theo `redmine_project_id`, khong match chinh theo `identifier`.
- Neu `identifier` thay doi tren Redmine, record local hien co van duoc update cung record do.
- `is_active` cua project duoc map tu field `status` hoac `is_public` cua Redmine neu API tra du lieu phu hop; neu khong co field ro rang, backend mac dinh giu `true`.
- Phase nay tam thoi mac dinh `is_active = true` cho project duoc sync thanh cong.
- He thong chi duoc xu ly va hien thi project co `identifier` da cau hinh.
- Cac project khac tren Redmine khong duoc dua vao DB/UI cua phase nay.
- Project local khong bi xoa khi sync.
- `raw_data_json` chi luu de debug va doi soat, khong tra truc tiep ve frontend.
- Moi lan sync loi phai ghi 1 dong vao `project_sync_logs`.
- Moi lan sync thanh cong cung phai ghi 1 dong vao `project_sync_logs` voi `status = "success"`.

## 6. Yeu cau phi chuc nang

| # | Danh muc | Yeu cau |
|---|---|---|
| 1 | Hieu nang | Sync phai timeout sau toi da 30 giay |
| 2 | Bao mat | Khong log API key; user thuong khong duoc trigger sync |
| 3 | Tinh san sang | Sync loi khong duoc lam crash service |
| 4 | Kha nang quan sat | Ghi sync log voi `connection_id`, `status`, `started_at`, `finished_at`, `error_code` |

## 7. Tieu chi chap nhan

| # | ID | Mo ta | Loai kiem thu |
|---|---|---|---|
| 1 | PROJ-AC-001 | Admin sync duoc project theo `identifier` da cau hinh tu Redmine | API integration |
| 2 | PROJ-AC-002 | Project da ton tai thi update, khong tao trung | API integration |
| 3 | PROJ-AC-003 | Man hinh Project chi hien thi `name`, `identifier`, `last_synced_at` cua project dang thuc thi | E2E |
| 4 | PROJ-AC-004 | He thong khong hien thi cac project khac ngoai project theo `identifier` da cau hinh | E2E |
| 5 | PROJ-AC-005 | Sync loi thi ghi `project_sync_logs` | API integration |
| 6 | PROJ-AC-006 | User khong phai admin khong duoc trigger sync | Authorization |
| 7 | PROJ-AC-007 | API `GET /api/projects/current` khong tra `raw_data_json` | API integration |

## 8. Vi du

### Cac luong binh thuong

1. Admin goi `POST /api/projects/sync`, he thong sync thanh cong project `nishimatsuya`.
2. User goi `GET /api/projects/current`, he thong tra thong tin project dang thuc thi.
3. Project da ton tai trong DB duoc update `name` va `description` khi sync lan sau.

### Cac luong loi

1. Chua cau hinh Redmine connection hoac thieu `identifier`, sync tra `409 REDMINE_CONNECTION_NOT_CONFIGURED`.
2. Redmine timeout khi sync, backend tra `504 REDMINE_TIMEOUT`.
3. User thuong goi API sync, backend tra `403 Forbidden`.

### Cac truong hop bien

1. Project da ton tai va Redmine doi `identifier`, backend update record cu theo `redmine_project_id`.
2. `identifier` cau hinh khong ton tai tren Redmine, sync tra loi va ghi `project_sync_logs`.
3. Chua co project local nao duoc sync, `GET /api/projects/current` tra `404` hoac response rong theo implementation duoc chot.

## 9. Wireframe ASCII (Tuy chon)

```text
Admin > Settings > Project Sync

+------------------------------------------------------------+
| Project Sync                                               |
+------------------------------------------------------------+
| Shared Connection: Company Redmine                         |
| Project Identifier: nishimatsuya                           |
| Last sync: 2026-05-05 10:00 UTC                            |
|                                                            |
| [ Sync now ]                                               |
|                                                            |
| Last result: 12 synced / 2 created / 10 updated            |
+------------------------------------------------------------+

Dashboard > Projects

+--------------------------------------------------------------------------------+
| Current Project                                                                |
+--------------------------------------------------------------------------------+
| Name            | Identifier     | Last Synced            | Status             |
| Nishimatsuya    | nishimatsuya   | 2026-05-05 10:00 UTC   | Active             |
+--------------------------------------------------------------------------------+
```

## 10. Cac van de mo

| # | Cau hoi | Nguoi phu trach | Han chot |
|---|---|---|---|
| OI-1 | Scheduled sync khong nam trong phase nay, nhung se duoc dua vao phase tiep theo | Product + Backend | Phase sau |
| OI-2 | Tam thoi bo qua mapping chi tiet cho `is_active`; phase nay mac dinh `true` khi sync thanh cong | Product + Backend | Da chot cho phase nay |
| OI-3 | Da chot moi lan sync thanh cong phai ghi `project_sync_logs` voi `status=success`; sync loi ghi `status=failed` | Product + Backend | Da chot |

## 11. Rui ro

| # | Rui ro | Kha nang xay ra | Muc do anh huong | Bien phap giam thieu |
|---|---|---|---|---|
| 1 | Dung `identifier` lam khoa match chinh gay duplicate khi identifier doi | Trung binh | Cao | Match theo `redmine_project_id` |
| 2 | `identifier` cau hinh sai lam sync luon that bai | Trung binh | Trung binh | Validate ro trong connection va ghi sync log |
| 3 | Sync loi nhung khong co log de truy vet | Thap | Cao | Bat buoc ghi `project_sync_logs` |

------------------------------------------------------------------------

## Bang truy vet

| # | AC | Man hinh/API | DB | Logs | Quyen | Loai kiem thu |
|---|---|---|---|---|---|---|
| 1 | PROJ-AC-001 | `POST /api/projects/sync` | `projects` | `project_sync_logs` | Admin | API integration |
| 2 | PROJ-AC-002 | `POST /api/projects/sync` | `projects` | N/A | Admin | API integration |
| 3 | PROJ-AC-003 | `GET /api/projects/current` | `projects` | N/A | Authenticated user | E2E |
| 4 | PROJ-AC-004 | `GET /api/projects/current` | `projects` | N/A | Authenticated user | E2E |
| 5 | PROJ-AC-005 | `POST /api/projects/sync` | `project_sync_logs` | `project_sync_logs` | Admin | API integration |
| 6 | PROJ-AC-006 | `POST /api/projects/sync` | N/A | Authorization failure log | Admin only | Authorization |
| 7 | PROJ-AC-007 | `GET /api/projects/current` | `projects` | N/A | Authenticated user | API integration |
