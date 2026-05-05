# Goi dac ta --- (Issue Sync & Management)

> Tao: 2026-05-05
> Giai doan: [1]
> Nguon tham chieu duy nhat cho thay doi nay.
> Khong trien khai bat ky noi dung nao khong duoc viet o day.
> Cac muc chua ro duoc liet ke trong Open Issues.

------------------------------------------------------------------------

## 1. Boi canh / Muc dich

Dong bo issue tu Redmine cho project dang thuc thi ve database noi bo de phuc vu:

- issue list
- dashboard
- thong ke va danh gia hieu suat member

Module nay phu thuoc vao:

- shared Redmine connection da duoc admin cau hinh san
- current project da duoc xac dinh bang `redmine_connections.identifier`

Trong phase nay, he thong chi xu ly issue cua mot project duy nhat dang thuc thi.
User thuong khong truyen API key va khong truy cap truc tiep Redmine.

Man hinh ap dung:

- Admin > Settings > Issue Sync
- Dashboard > Issues

## 2. Pham vi

### Trong pham vi

- Sync issue cua current project tu Redmine.
- Xu ly Redmine pagination bang `limit` va `offset`.
- Upsert issue vao bang `issues`.
- Hien thi issue list tu DB noi bo.
- Filter va search issue trong DB noi bo.
- Mo link issue Redmine goc.
- Ghi sync log cho lan sync thanh cong va that bai.

### Ngoai pham vi

- Tao issue tren Redmine.
- Sua issue tren Redmine.
- Xoa issue tren Redmine.
- Comment issue.
- Sync issue cua nhieu project cung luc.
- User thuong truyen truc tiep `connection_id`, `project_identifier`, hoac API key.

## 3. Thuat ngu

| # | Thuat ngu | Dinh nghia |
|---|---|---|
| 1 | Issue sync | Hanh dong backend goi Redmine API de lay tat ca issue cua current project va upsert vao DB noi bo |
| 2 | Current project | Project duy nhat dang duoc he thong xu ly, duoc xac dinh bang `redmine_connections.identifier` |
| 3 | Redmine issue id | ID goc cua issue ben Redmine, dung lam khoa match chinh khi upsert |
| 4 | `status_id=*` | Tham so Redmine API de lay issue thuoc moi status |
| 5 | Pagination | Co che lap qua nhieu trang Redmine bang `limit` va `offset` |
| 6 | Shared connection | Redmine connection dung chung cho toan he thong, da duoc admin cau hinh san |

## 4. Hien trang / Trang thai muc tieu

| # | Khia canh | Hien trang | Trang thai muc tieu |
|---|---|---|---|
| 1 | Dong bo issue | [MISSING] | Admin co the trigger sync issue cua current project |
| 2 | Redmine pagination | [MISSING] | Backend doc du tat ca trang qua `limit` va `offset` |
| 3 | Luu tru issue | [MISSING] | Issue duoc upsert vao bang `issues` khong tao trung |
| 4 | Hien thi issue | [MISSING] | User xem duoc issue list co pagination, filter, search |
| 5 | Quan sat | [MISSING] | Co sync log cho lan sync thanh cong va that bai |

## 5. Chi tiet dac ta

### 5.1 Quyen truy cap

- Chi user co `users.is_admin = true` moi duoc goi `POST /api/issues/sync`.
- User da dang nhap duoc phep goi `GET /api/issues`.
- Neu user chua dang nhap, backend tra `401 Not authenticated`.
- Neu user khong phai admin ma goi sync, backend tra `403 Forbidden`.

### 5.2 Nguon du lieu Redmine

Backend su dung shared Redmine connection hien hanh da duoc luu trong he thong.

Redmine API duoc su dung:

```text
GET /issues.json?project_id={project_identifier}&status_id=*&limit=100&offset=0
```

Rules:

- `project_identifier` duoc lay tu `redmine_connections.identifier`.
- Phase nay khong cho client truyen `connection_id` hoac `project_identifier` vao API sync.
- Backend phai lap qua nhieu trang cho den khi lay du tat ca issue.
- Backend phai lay issue cua moi status bang `status_id=*`.

### 5.3 API sync issue

- Endpoint: `POST /api/issues/sync`

Request:

```json
{}
```

Behavior:

1. Backend tim shared Redmine connection hien hanh.
2. Backend doc `identifier` tu shared connection.
3. Backend goi Redmine `GET /issues.json` voi:
   - `project_id={identifier}`
   - `status_id=*`
   - `limit=100`
   - `offset=0`, tang dan theo tung trang
4. Backend doc `issues`, `total_count`, `offset`, `limit` tu response.
5. Backend tiep tuc goi cac trang tiep theo cho toi khi tong so issue da lay du bang `total_count`.
6. Moi issue duoc match theo `(connection_id, redmine_issue_id)`.
7. Neu record da ton tai thi update.
8. Neu record chua ton tai thi insert.
9. `raw_data_json` luu raw object issue tu Redmine.
10. `last_synced_at` duoc cap nhat tai thoi diem sync thanh cong.
11. Moi lan sync thanh cong hoac that bai deu phai ghi `issue_sync_logs`.

Response `200 OK`:

```json
{
  "success": true,
  "project_identifier": "nishimatsuya",
  "total_synced": 250,
  "created": 20,
  "updated": 230,
  "synced_at": "2026-05-05T10:30:00Z"
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
  "message": "Timed out while syncing issues from Redmine"
}
```

Response error `502 Bad Gateway`:

```json
{
  "code": "REDMINE_SYNC_FAILED",
  "message": "Failed to sync issues from Redmine"
}
```

### 5.4 API issue list

- Endpoint: `GET /api/issues`

Query params:

| Param | Bat buoc | Mo ta |
|---|---|---|
| `status_id` | Khong | Loc theo Redmine status id; tren UI hien thi dang dropdown list |
| `priority_id` | Khong | Loc theo Redmine priority id; tren UI hien thi dang dropdown list |
| `assignee_id` | Khong | Loc theo assignee id |
| `keyword` | Khong | Tim theo `subject` hoac `description` |
| `due_date_from` | Khong | Loc issue co `due_date >= value` |
| `due_date_to` | Khong | Loc issue co `due_date <= value` |
| `page` | Khong | Mac dinh `1` |
| `page_size` | Khong | Mac dinh `20`, toi da `100` |

Rules:

- API chi tra issue cua current project hien hanh.
- Phase nay khong can query param `project_id` vi he thong chi co 1 current project.
- API phai ho tro pagination.
- API phai cho search theo `keyword`.
- API phai cho filter theo `status_id`, `priority_id`, `assignee_id`, `due_date_from`, `due_date_to`.
- Tren man hinh `Dashboard > Issues`, `status_id` phai duoc render dang dropdown list.
- Tren man hinh `Dashboard > Issues`, `priority_id` phai duoc render dang dropdown list.
- API tra kem `redmine_url` de frontend mo issue goc.
- API khong tra `raw_data_json`.

Response `200 OK`:

```json
{
  "items": [
    {
      "id": 1,
      "connection_id": 1,
      "project_id": 1,
      "redmine_issue_id": 5001,
      "tracker_id": 2,
      "tracker_name": "Bug",
      "status_id": 3,
      "status_name": "In Progress",
      "priority_id": 4,
      "priority_name": "High",
      "author_id": 10,
      "author_name": "Hiep",
      "assignee_id": 12,
      "assignee_name": "An",
      "subject": "Fix login timeout",
      "description": "Issue imported from Redmine",
      "start_date": "2026-05-01",
      "due_date": "2026-05-10",
      "done_ratio": 40,
      "estimated_hours": 8,
      "spent_hours": 3.5,
      "is_closed": false,
      "redmine_url": "https://redmine.example.com/issues/5001",
      "redmine_created_on": "2026-05-01T08:00:00Z",
      "redmine_updated_on": "2026-05-05T10:00:00Z",
      "last_synced_at": "2026-05-05T10:30:00Z",
      "created_at": "2026-05-05T10:30:00Z",
      "updated_at": "2026-05-05T10:30:00Z"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 250
}
```

### 5.5 Data model

Table: `issues`

| Field | Type | Ghi chu |
|---|---|---|
| `id` | bigint | Khoa chinh |
| `connection_id` | bigint | FK toi `redmine_connections.id` |
| `project_id` | bigint | FK toi `projects.id` cua current project local |
| `redmine_issue_id` | bigint | ID goc cua issue ben Redmine |
| `tracker_id` | int, nullable | ID tracker ben Redmine |
| `tracker_name` | varchar(100), nullable | Ten tracker |
| `status_id` | int, nullable | ID status ben Redmine |
| `status_name` | varchar(100), nullable | Ten status |
| `priority_id` | int, nullable | ID priority ben Redmine |
| `priority_name` | varchar(100), nullable | Ten priority |
| `author_id` | int, nullable | ID author ben Redmine |
| `author_name` | varchar(255), nullable | Ten author |
| `assignee_id` | int, nullable | ID assignee ben Redmine |
| `assignee_name` | varchar(255), nullable | Ten assignee |
| `subject` | varchar(255) | Tieu de issue |
| `description` | text, nullable | Mo ta issue |
| `start_date` | date, nullable | Ngay bat dau |
| `due_date` | date, nullable | Han xu ly |
| `done_ratio` | int, nullable | Tien do phan tram |
| `estimated_hours` | decimal(10,2), nullable | So gio uoc tinh |
| `spent_hours` | decimal(10,2), nullable | So gio da dung |
| `is_closed` | boolean | Trang thai dong/mo theo mapping local |
| `redmine_created_on` | datetime, nullable | Thoi diem tao ben Redmine |
| `redmine_updated_on` | datetime, nullable | Thoi diem cap nhat ben Redmine |
| `raw_data_json` | json | Raw object issue tu Redmine |
| `last_synced_at` | datetime | Lan sync thanh cong gan nhat |
| `created_at` | datetime | Thoi diem tao local |
| `updated_at` | datetime | Thoi diem cap nhat local |

Unique constraints:

- `(connection_id, redmine_issue_id)`

Table: `issue_sync_logs`

| Field | Type | Ghi chu |
|---|---|---|
| `id` | bigint | Khoa chinh |
| `connection_id` | bigint | FK toi `redmine_connections.id` |
| `project_id` | bigint, nullable | FK toi `projects.id` neu xac dinh duoc project local |
| `status` | varchar(20) | `success` hoac `failed` |
| `error_code` | varchar(100), nullable | Vi du `REDMINE_TIMEOUT` |
| `error_message` | text, nullable | Noi dung loi tom tat |
| `total_synced` | int, nullable | Tong so issue xu ly |
| `created_count` | int, nullable | So issue tao moi |
| `updated_count` | int, nullable | So issue cap nhat |
| `started_at` | datetime | Thoi diem bat dau sync |
| `finished_at` | datetime | Thoi diem ket thuc sync |

### 5.6 Business rules

- Issue sync chi duoc chay bang shared Redmine connection hien hanh.
- Shared Redmine connection bat buoc phai co `identifier`.
- He thong chi xu ly issue cua current project co `identifier` da cau hinh.
- Backend phai sync tat ca issue qua nhieu trang cho toi khi du `total_count`.
- Upsert issue theo `redmine_issue_id`, khong upsert theo `subject`.
- `project_id` trong bang `issues` la local `projects.id`, khong phai Redmine project id.
- `status_id`, `priority_id`, `assignee_id` duoc luu de phuc vu filter on dinh.
- `status_name`, `priority_name`, `assignee_name` duoc luu de hien thi UI.
- UI filter `status_id` su dung dropdown list, label hien thi bang `status_name`, gia tri submit la `status_id`.
- UI filter `priority_id` su dung dropdown list, label hien thi bang `priority_name`, gia tri submit la `priority_id`.
- Phase nay map `is_closed` bang danh sach `closed_status_ids` duoc cau hinh trong backend.
- Backend khong duoc suy luan `is_closed` theo `status_name`.
- `raw_data_json` chi luu de debug va doi soat, khong tra truc tiep ve frontend.
- `redmine_url` cua issue duoc tao theo format `{base_url}/issues/{redmine_issue_id}` va phai giu nguyen path prefix neu `base_url` co path.
- Moi lan sync thanh cong phai ghi 1 dong vao `issue_sync_logs` voi `status = "success"`.
- Moi lan sync that bai phai ghi 1 dong vao `issue_sync_logs` voi `status = "failed"`.

## 6. Yeu cau phi chuc nang

| # | Danh muc | Yeu cau |
|---|---|---|
| 1 | Hieu nang | Moi request Redmine timeout sau toi da 30 giay; page size sync Redmine mac dinh 100 |
| 2 | Bao mat | Khong log API key; user thuong khong duoc trigger sync; API list khong tra `raw_data_json` |
| 3 | Tinh san sang | Sync loi khong duoc lam crash service; du lieu issue local cu khong bi xoa khi sync that bai |
| 4 | Kha nang quan sat | Ghi `issue_sync_logs` voi `connection_id`, `project_id`, `status`, `started_at`, `finished_at`, `error_code` |

## 7. Tieu chi chap nhan

| # | ID | Mo ta | Loai kiem thu |
|---|---|---|---|
| 1 | ISSUE-AC-001 | Admin sync duoc issue cua current project theo `identifier` da cau hinh | API integration |
| 2 | ISSUE-AC-002 | Sync lay du issue qua nhieu trang Redmine | API integration |
| 3 | ISSUE-AC-003 | Issue da ton tai thi update, khong tao trung | API integration |
| 4 | ISSUE-AC-004 | User xem duoc issue list co pagination | API integration |
| 5 | ISSUE-AC-005 | User filter duoc theo `status_id`, `priority_id`, `assignee_id`, `due_date`; `status_id` va `priority_id` hien thi dang dropdown list | API integration + E2E |
| 6 | ISSUE-AC-006 | User search duoc theo `keyword` | API integration |
| 7 | ISSUE-AC-007 | Click issue mo duoc Redmine issue goc qua `redmine_url` | E2E |
| 8 | ISSUE-AC-008 | User khong phai admin khong duoc trigger sync | Authorization |
| 9 | ISSUE-AC-009 | Sync loi phai ghi `issue_sync_logs` | API integration |

## 8. Vi du

### Cac luong binh thuong

1. Admin goi `POST /api/issues/sync`, he thong sync thanh cong tat ca issue cua current project.
2. User goi `GET /api/issues?page=1&page_size=20`, he thong tra issue list tu DB noi bo.
3. User loc issue theo `status_id=3` hoac `assignee_id=12`.
4. User search issue theo `keyword=login`.
5. User click `redmine_url` de mo issue goc tren Redmine.

### Cac luong loi

1. Chua cau hinh Redmine connection hoac thieu `identifier`, sync tra `409 REDMINE_CONNECTION_NOT_CONFIGURED`.
2. Redmine timeout khi sync, backend tra `504 REDMINE_TIMEOUT`.
3. Redmine tra loi khac, backend tra `502 REDMINE_SYNC_FAILED`.
4. User thuong goi API sync, backend tra `403 Forbidden`.

### Cac truong hop bien

1. Issue da ton tai thi update, khong tao trung.
2. Sync phai lap qua nhieu trang bang `limit` va `offset`.
3. `is_closed` phu thuoc vao cau hinh `closed_status_ids` trong backend.
4. `base_url` co path prefix thi `redmine_url` van phai dung, vi du `https://example.com/redmine/issues/5001`.

## 9. Wireframe ASCII (Tuy chon)

```text
Admin > Settings > Issue Sync

+------------------------------------------------------------+
| Issue Sync                                                 |
+------------------------------------------------------------+
| Shared Connection: Company Redmine                         |
| Current Project: nishimatsuya                              |
| Last sync: 2026-05-05 10:30 UTC                            |
|                                                            |
| [ Sync now ]                                               |
|                                                            |
| Last result: 250 synced / 20 created / 230 updated         |
+------------------------------------------------------------+

Dashboard > Issues

+--------------------------------------------------------------------------------------------------+
| Issues                                                                                           |
+--------------------------------------------------------------------------------------------------+
| Search: [ login                    ] [ Reset filters ]                                           |
| Status ID:   [ In Progress v ]    Priority ID: [ High v ]                                       |
| Assignee ID: [ 12               ]  Due Date:    [ from ] [ to ]                                 |
|--------------------------------------------------------------------------------------------------|
| ID   | Subject            | Status        | Priority | Assignee | Due Date   | Redmine           |
| 5001 | Fix login timeout  | In Progress   | High     | An       | 2026-05-10 | [ Open ]          |
+--------------------------------------------------------------------------------------------------+
| Page 1 / N                                                                                       |
+--------------------------------------------------------------------------------------------------+
```

## 10. Cac van de mo

| # | Cau hoi | Nguoi phu trach | Han chot |
|---|---|---|---|
| OI-1 | Da chot dung `closed_status_ids` trong backend de map `is_closed`; khong hardcode theo `status_name` | Product + Backend | Da chot |
| OI-2 | Co can bo sung them filter theo `author_id` trong phase nay khong | Product + Frontend | [MISSING] |
| OI-3 | Co can hien thi sync status gan nhat tren man hinh Issues hay chi o man hinh admin | Product + Frontend | [MISSING] |

## 11. Rui ro

| # | Rui ro | Kha nang xay ra | Muc do anh huong | Bien phap giam thieu |
|---|---|---|---|---|
| 1 | Sai logic pagination khien sync thieu issue | Trung binh | Cao | Doc `total_count`, `offset`, `limit` va viet test nhieu trang |
| 2 | Chi luu ten ma khong luu ID status/priority/assignee khien filter khong on dinh | Trung binh | Cao | Luu ca id va name trong bang `issues` |
| 3 | Cau hinh `closed_status_ids` sai lam sai dashboard va thong ke | Trung binh | Trung binh | Review cau hinh backend va test metric phu thuoc |

------------------------------------------------------------------------

## Bang truy vet

| # | AC | Man hinh/API | DB | Logs | Quyen | Loai kiem thu |
|---|---|---|---|---|---|---|
| 1 | ISSUE-AC-001 | `POST /api/issues/sync` | `issues` | `issue_sync_logs` | Admin | API integration |
| 2 | ISSUE-AC-002 | Redmine API `GET /issues.json` + `POST /api/issues/sync` | `issues` | `issue_sync_logs` | Admin | API integration |
| 3 | ISSUE-AC-003 | `POST /api/issues/sync` | `issues` | `issue_sync_logs` | Admin | API integration |
| 4 | ISSUE-AC-004 | `GET /api/issues` | `issues` | N/A | Authenticated user | API integration |
| 5 | ISSUE-AC-005 | `GET /api/issues` | `issues` | N/A | Authenticated user | API integration |
| 6 | ISSUE-AC-006 | `GET /api/issues` | `issues` | N/A | Authenticated user | API integration |
| 7 | ISSUE-AC-007 | `GET /api/issues` | `issues` | N/A | Authenticated user | E2E |
| 8 | ISSUE-AC-008 | `POST /api/issues/sync` | N/A | Authorization failure log | Admin only | Authorization |
| 9 | ISSUE-AC-009 | `POST /api/issues/sync` | `issue_sync_logs` | `issue_sync_logs` | Admin | API integration |
