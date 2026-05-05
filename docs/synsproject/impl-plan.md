# PROJ-001 - Project Sync & Management: Implementation Plan

> Tao: 2026-05-05
> Dua tren: [spec-pack.md](./spec-pack.md)
> Codebase review: 2026-05-05

---

## 1. Tong quan

Module Project Sync & Management chua duoc implement trong codebase hien tai.
 Can bo sung moi toan bo stack de he thong co the:

- sync mot project duy nhat tu Redmine ve DB noi bo
- upsert project theo `redmine_project_id`
- hien thi project dang thuc thi tu DB noi bo
- ghi `project_sync_logs` cho ca success va failed

Module nay phu thuoc truc tiep vao Redmine Connection da duoc implement truoc do:

- shared Redmine connection
- project `identifier` duoc cau hinh trong shared connection
- API key duoc luu dang ma hoa
- auth admin bang `users.is_admin`

Codebase hien tai da co:

- backend FastAPI voi cookie-based auth
- SQLAlchemy async session
- shared Redmine connection route/service
- frontend dashboard co sidebar, settings page, va auth flow

Codebase hien tai chua co:

- model `projects`
- model `project_sync_logs`
- route `/api/projects/sync`
- route `GET /api/projects/current`
- UI `Admin > Settings > Project Sync`
- UI `Dashboard > Current Project`

---

## 2. Ket luan review hien trang

| # | Hang muc | Hien trang | Tac dong |
|---|---|---|---|
| 1 | Redmine connection | Da co shared connection + test flow | Co the tai su dung truc tiep khi sync |
| 2 | Authorization | Da co `require_admin` va `is_admin` | Co the dung cho API sync |
| 3 | Authenticated user | Da co `get_current_user` | Co the dung cho API list project |
| 4 | Database schema | Dang `Base.metadata.create_all`, khong co Alembic | Can bo sung model moi va co startup migration nhe neu can |
| 5 | Redmine HTTP client | Da co `httpx` + URL builder cho account API | Nen mo rong service cho `/projects/{identifier}.json` |
| 6 | Frontend dashboard | Da co settings page cho connection | Co the chen them Project Sync va Current Project vao cung flow |

---

## 3. File map du kien

### Backend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Model project | `backend/app/models/project.py` | Can tao moi |
| 2 | Model sync log | `backend/app/models/project_sync_log.py` | Can tao moi |
| 3 | Schemas project | `backend/app/schemas/project.py` | Can tao moi |
| 4 | Redmine project fetch service | `backend/app/services/redmine_client.py` | Can sua |
| 5 | Route sync/current project | `backend/app/routes/projects.py` | Can tao moi |
| 6 | App router registration | `backend/app/main.py` | Can sua |
| 7 | Optional startup migration nhe | `backend/app/main.py` | Co the can sua |

### Frontend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Project sync admin page | `frontend/src/pages/ProjectSyncPage.jsx` | Can tao moi |
| 2 | Current project page | `frontend/src/pages/ProjectsPage.jsx` hoac `CurrentProjectPage.jsx` | Can tao moi hoac doi ten |
| 3 | Dashboard navigation/state | `frontend/src/pages/DashboardPage.jsx` | Can sua |
| 4 | Styles | `frontend/src/styles.css` | Can sua |

### Docs / Test

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Implementation plan | `docs/synsproject/impl-plan.md` | File nay |
| 2 | Backend automated tests | `backend/tests/...` | Chua thay test harness ro rang trong repo |

---

## 4. Mapping spec -> implementation

| Spec item | Implementation du kien |
|---|---|
| `POST /api/projects/sync` | Route FastAPI yeu cau `require_admin`, lay shared connection + `identifier`, goi Redmine `/projects/{identifier}.json`, upsert DB, ghi sync log |
| `GET /api/projects/current` | Route FastAPI yeu cau user da dang nhap, tra ve project dang thuc thi trong DB |
| Upsert theo `redmine_project_id` | Query theo `(connection_id, redmine_project_id)` truoc khi insert/update |
| `raw_data_json` | Luu raw project object tu Redmine, khong expose ra response |
| `project_sync_logs` | Ghi log cho ca success va failed |
| `is_active` phase nay | Mac dinh `true` cho project duoc sync thanh cong |

---

## 5. Ke hoach trien khai

### Phase 1 - Backend schema

1. Tao model `Project`.
2. Tao model `ProjectSyncLog`.
3. Dang ky model de `create_all()` tao bang.
4. Neu can, them startup migration nhe cho DB dang ton tai.

Expected output:

- DB co bang `projects`
- DB co bang `project_sync_logs`
- schema phu hop voi unique constraints cua spec

### Phase 2 - Backend service va API

1. Mo rong `redmine_client.py` de goi `GET /projects/{identifier}.json`.
2. Tao schema request/response cho sync va current project.
3. Tao `POST /api/projects/sync`.
4. Tao `GET /api/projects/current`.
5. Ghi `project_sync_logs` cho success va failed.
6. Chuan hoa mapping loi:
   - `409 -> REDMINE_CONNECTION_NOT_CONFIGURED`
   - `504 -> REDMINE_TIMEOUT`
   - `502 -> REDMINE_SYNC_FAILED`

Expected output:

- Backend co day du 2 endpoint theo spec
- Sync khong can `connection_id` trong request, dung `identifier` tu connection
- API current project khong tra `raw_data_json`

### Phase 3 - Frontend admin va user screens

1. Tao `ProjectSyncPage` cho `Admin > Settings > Project Sync`.
2. Tao man hinh hien thi current project cho `Dashboard > Projects`.
3. O `ProjectSyncPage` hien:
   - shared connection
   - last sync
   - nut `Sync now`
   - ket qua lan sync gan nhat
4. O man hinh current project hien:
   - `name`
   - `identifier`
   - `last_synced_at`
   - `status`
5. Noi navigation vao `DashboardPage`.

Expected output:

- Admin trigger sync duoc tren UI
- User da dang nhap xem duoc project dang thuc thi
- UI khong bao gio hien `raw_data_json`

### Phase 4 - Verification

1. Test sync khi chua co Redmine connection.
2. Test sync success theo `identifier`.
3. Test sync update record cu, khong tao trung.
4. Test sync timeout.
5. Test sync log success va failed.
6. Test API current project.
7. Test user thuong bi chan khoi sync.

---

## 6. Chi tiet ky thuat de xuat

### 6.1 Model `projects`

De xuat field:

- `id`
- `connection_id`
- `redmine_project_id`
- `identifier`
- `name`
- `description`
- `is_active`
- `raw_data_json`
- `last_synced_at`
- `created_at`
- `updated_at`

Rang buoc de xuat:

- unique `(connection_id, redmine_project_id)`
- unique `(connection_id, identifier)`
- index cho `identifier`
- index cho `is_active`

### 6.2 Model `project_sync_logs`

De xuat field:

- `id`
- `connection_id`
- `status`
- `error_code`
- `error_message`
- `total_synced`
- `created_count`
- `updated_count`
- `started_at`
- `finished_at`

Ghi chu:

- `status` chi nhan `success` hoac `failed`
- success van phai ghi log theo spec da chot

### 6.3 Redmine sync flow

Pseudo-flow:

```text
require_admin
load current shared connection
read identifier from connection
decrypt api key
GET {base_url}/projects/{identifier}.json
parse payload.project
match by (connection_id, redmine_project_id)
update or insert
set is_active=true
set raw_data_json
set last_synced_at=now
commit
write project_sync_logs(status=success)
return counts for one project
```

Failure flow:

```text
require_admin
load current shared connection
if no connection or no identifier -> 409
call Redmine
if timeout/http failure:
  write project_sync_logs(status=failed, error_code, error_message)
  return mapped error response
```

### 6.4 Query API current project

De xuat:

- tim project local theo `connection_id` va `identifier` da cau hinh
- neu khong tim thay project local, tra `404`

Response shape:

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

### 6.5 UI integration

Navigation de xuat:

- `Dashboard`
- `Projects`
- `Issues`
- `Members`
- `Settings` (chi admin)

Trong `Settings`, de xuat tach it nhat 2 khu:

- `Redmine Connection`
- `Project Sync`

Neu chua muon tao nested navigation phuc tap, co the dung state tab trong `DashboardPage`.

---

## 7. Gap va quyet dinh can chot truoc khi code

| ID | Van de | De xuat |
|---|---|---|
| GAP-PROJ-1 | Chua co `impl-plan.md` trong repo | Tao file nay truoc, sau do code |
| GAP-PROJ-2 | Chua co migration framework | Tam thoi dung `create_all()` theo style hien tai |
| GAP-PROJ-3 | `identifier` nam trong connection, khong nam trong project sync request | Sync route phai phu thuoc chac chan vao connection config |
| GAP-PROJ-4 | `is_active` chua map chi tiet tu Redmine | Phase nay mac dinh `true` |
| GAP-PROJ-5 | Scheduled sync nam o phase sau | Chua implement cron/background job trong phase nay |

---

## 8. Acceptance Criteria -> test cases

| AC | Test case | Ket qua mong doi |
|---|---|---|
| PROJ-AC-001 | Admin goi sync voi connection hop le + co `identifier` | `200`, co `total_synced=1`, `created` hoac `updated` |
| PROJ-AC-002 | Sync 2 lan cung project | Khong duplicate, record cu duoc update |
| PROJ-AC-003 | User mo `GET /api/projects/current` | Nhan du `name`, `identifier`, `last_synced_at` |
| PROJ-AC-004 | He thong chi tra project theo `identifier` da cau hinh | Khong co project khac trong response/UI |
| PROJ-AC-005 | Redmine sync loi | Co 1 record `project_sync_logs` voi `status=failed` |
| PROJ-AC-006 | User khong phai admin goi sync | `403 Forbidden` |
| PROJ-AC-007 | Goi current project | Response khong co `raw_data_json` |

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
# 4. Mo Settings > Project Sync
# 5. Bam Sync now
# 6. Mo Projects va kiem tra project dang thuc thi
# 7. Xac nhan khong co project khac duoc hien thi
# 8. Login bang user thuong va thu goi sync
```

Checklist:

- Sync thanh cong tao/updated project dung so luong
- Sync log success duoc ghi
- Loi sync duoc ghi `project_sync_logs`
- `Projects` page khong hien `raw_data_json`
- User thuong xem duoc project dang thuc thi nhung khong trigger sync duoc
- Khong co project khac ngoai `identifier` da cau hinh duoc hien thi

---

## 10. Thu tu thuc hien de xuat

1. Tao model `Project` va `ProjectSyncLog`.
2. Mo rong Redmine client cho `/projects/{identifier}.json`.
3. Implement backend routes `POST /api/projects/sync` va `GET /api/projects/current`.
4. Ghi sync logs success/failed.
5. Implement `ProjectSyncPage`.
6. Implement man hinh current project.
7. Noi navigation vao dashboard.
8. Test manual va verify response shape.

---

## 11. Ket luan

Feature nay nen duoc implement backend truoc, frontend sau.
Rui ro lon nhat nam o 3 diem:

- sync sai project khi connection config `identifier` sai
- khong ghi sync log day du cho failure/success
- expose thua du lieu project hoac `raw_data_json`

Neu 3 diem nay duoc giu dung theo spec, implementation se thang va it rui ro hon.
