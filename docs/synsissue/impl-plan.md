# ISSUE-001 - Issue Sync & Management: Implementation Plan

> Tao: 2026-05-05
> Dua tren: [spec-pack.md](./spec-pack.md)
> Codebase review: 2026-05-05

---

## 1. Tong quan

Module Issue Sync & Management chua duoc implement trong codebase hien tai.
Can bo sung moi toan bo stack de he thong co the:

- sync tat ca issue cua current project tu Redmine ve DB noi bo
- xu ly Redmine pagination bang `limit` va `offset`
- upsert issue theo `redmine_issue_id`
- hien thi issue list co pagination, filter, search
- mo issue goc tren Redmine
- ghi `issue_sync_logs` cho ca success va failed

Module nay phu thuoc truc tiep vao 2 module da duoc chot/implement truoc do:

- shared Redmine connection
- current project duoc xac dinh bang `redmine_connections.identifier`

Codebase hien tai da co:

- backend FastAPI voi cookie-based auth
- SQLAlchemy async session
- shared Redmine connection route/service
- current project sync route/service
- frontend dashboard co sidebar, auth flow, settings flow

Codebase hien tai chua co:

- model `issues`
- model `issue_sync_logs`
- route `POST /api/issues/sync`
- route `GET /api/issues`
- Redmine client cho `GET /issues.json`
- UI `Admin > Settings > Issue Sync`
- UI `Dashboard > Issues`

---

## 2. Ket luan review hien trang

| # | Hang muc | Hien trang | Tac dong |
|---|---|---|---|
| 1 | Redmine connection | Da co shared connection + decrypt API key | Co the tai su dung truc tiep khi sync issue |
| 2 | Current project | Da co `GET /api/projects/current` va sync theo `identifier` | Issue sync phai phu thuoc vao current project nay |
| 3 | Authorization | Da co `require_admin` va `get_current_user` | Dung cho sync issue va issue list |
| 4 | Database schema | Dang `Base.metadata.create_all`, khong co Alembic | Can bo sung model moi va startup migration nhe neu can |
| 5 | Redmine HTTP client | Da co helper build URL va fetch project/account | Nen mo rong cho `/issues.json` |
| 6 | Frontend dashboard | Da co tab `Issues` nhung chua co implementation | Co the noi UI moi vao luong hien tai |

---

## 3. File map du kien

### Backend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Model issue | `backend/app/models/issue.py` | Can tao moi |
| 2 | Model issue sync log | `backend/app/models/issue_sync_log.py` | Can tao moi |
| 3 | Schema issue | `backend/app/schemas/issue.py` | Can tao moi |
| 4 | Redmine issue fetch service | `backend/app/services/redmine_client.py` | Can sua |
| 5 | Route issue sync/list | `backend/app/routes/issues.py` | Can tao moi |
| 6 | App router registration | `backend/app/main.py` | Can sua |
| 7 | Optional startup migration nhe | `backend/app/main.py` | Co the can sua |

### Frontend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Issue sync admin page | `frontend/src/pages/IssueSyncPage.jsx` | Can tao moi |
| 2 | Issues list page | `frontend/src/pages/IssuesPage.jsx` | Can tao moi |
| 3 | Dashboard navigation/state | `frontend/src/pages/DashboardPage.jsx` | Can sua |
| 4 | Styles | `frontend/src/styles.css` | Can sua |

### Docs / Test

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Implementation plan | `docs/synsissue/impl-plan.md` | File nay |
| 2 | Backend automated tests | `backend/tests/...` | Chua thay test harness ro rang trong repo |

---

## 4. Mapping spec -> implementation

| Spec item | Implementation du kien |
|---|---|
| `POST /api/issues/sync` | Route FastAPI yeu cau `require_admin`, lay shared connection + current project, goi Redmine `/issues.json`, lap pagination, upsert DB, ghi sync log |
| `GET /api/issues` | Route FastAPI yeu cau user da dang nhap, tra issue list trong DB co pagination, filter, search |
| Upsert theo `redmine_issue_id` | Query theo `(connection_id, redmine_issue_id)` truoc khi insert/update |
| Chi xu ly current project | Route list va sync deu rang buoc theo project co `identifier` dang cau hinh |
| `redmine_url` | Build tu `base_url` cua shared connection va `redmine_issue_id` |
| `issue_sync_logs` | Ghi log cho ca success va failed |
| `raw_data_json` | Luu raw issue object, khong expose ra frontend |

---

## 5. Ke hoach trien khai

### Phase 1 - Backend schema

1. Tao model `Issue`.
2. Tao model `IssueSyncLog`.
3. Dang ky model de `create_all()` tao bang.
4. Neu can, them startup migration nhe cho DB dang ton tai.

Expected output:

- DB co bang `issues`
- DB co bang `issue_sync_logs`
- schema phu hop voi unique constraints cua spec

### Phase 2 - Backend service va API

1. Mo rong `redmine_client.py` de goi `GET /issues.json`.
2. Tao helper fetch nhieu trang Redmine issue.
3. Tao schema response cho sync va issue list.
4. Tao `POST /api/issues/sync`.
5. Tao `GET /api/issues`.
6. Ghi `issue_sync_logs` cho success va failed.
7. Chuan hoa mapping loi:
   - `409 -> REDMINE_CONNECTION_NOT_CONFIGURED`
   - `504 -> REDMINE_TIMEOUT`
   - `502 -> REDMINE_SYNC_FAILED`

Expected output:

- Backend co day du 2 endpoint theo spec
- Sync khong can `connection_id` hoac `project_identifier` trong request
- API list khong tra `raw_data_json`

### Phase 3 - Frontend admin va user screens

1. Tao `IssueSyncPage` cho `Admin > Settings > Issue Sync`.
2. Tao man hinh `IssuesPage` cho `Dashboard > Issues`.
3. O `IssueSyncPage` hien:
   - shared connection
   - current project identifier
   - last sync
   - nut `Sync now`
   - ket qua lan sync gan nhat
4. O `IssuesPage` hien:
   - issue list
   - search box
   - filter co ban
   - `Status ID` dang dropdown list
   - `Priority ID` dang dropdown list
   - pagination
   - nut/link mo Redmine
5. Noi navigation vao `DashboardPage`.

Expected output:

- Admin trigger sync duoc tren UI
- User da dang nhap xem duoc issue list
- UI khong bao gio hien `raw_data_json`

### Phase 4 - Verification

1. Test sync khi chua co Redmine connection.
2. Test sync nhieu trang issue.
3. Test sync update record cu, khong tao trung.
4. Test sync timeout.
5. Test issue sync log success va failed.
6. Test API list issue voi pagination.
7. Test search va filter.
8. Test user thuong bi chan khoi sync.

---

## 6. Chi tiet ky thuat de xuat

### 6.1 Model `issues`

De xuat field:

- `id`
- `connection_id`
- `project_id`
- `redmine_issue_id`
- `tracker_id`
- `tracker_name`
- `status_id`
- `status_name`
- `priority_id`
- `priority_name`
- `author_id`
- `author_name`
- `assignee_id`
- `assignee_name`
- `subject`
- `description`
- `start_date`
- `due_date`
- `done_ratio`
- `estimated_hours`
- `spent_hours`
- `is_closed`
- `redmine_created_on`
- `redmine_updated_on`
- `raw_data_json`
- `last_synced_at`
- `created_at`
- `updated_at`

Rang buoc de xuat:

- unique `(connection_id, redmine_issue_id)`
- index cho `project_id`
- index cho `status_id`
- index cho `priority_id`
- index cho `assignee_id`
- index cho `due_date`

### 6.2 Model `issue_sync_logs`

De xuat field:

- `id`
- `connection_id`
- `project_id`
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
load local current project
decrypt api key
loop:
  GET {base_url}/issues.json?project_id={identifier}&status_id=*&limit=100&offset={offset}
  parse payload.issues, total_count, offset, limit
  upsert issues by (connection_id, redmine_issue_id)
  offset += limit
until fetched_count >= total_count
commit
write issue_sync_logs(status=success)
return counts
```

Failure flow:

```text
require_admin
load current shared connection
if no connection or no identifier -> 409
call Redmine
if timeout/http failure:
  write issue_sync_logs(status=failed, error_code, error_message)
  return mapped error response
```

### 6.4 Mapping Redmine issue fields

De xuat map:

- `issue.id -> redmine_issue_id`
- `issue.project.id -> project_id` chi de doi soat tam, con `project_id` local van la FK toi bang `projects`
- `issue.tracker.id/name -> tracker_id/tracker_name`
- `issue.status.id/name -> status_id/status_name`
- `issue.priority.id/name -> priority_id/priority_name`
- `issue.author.id/name -> author_id/author_name`
- `issue.assigned_to.id/name -> assignee_id/assignee_name`
- `issue.subject -> subject`
- `issue.description -> description`
- `issue.start_date -> start_date`
- `issue.due_date -> due_date`
- `issue.done_ratio -> done_ratio`
- `issue.estimated_hours -> estimated_hours`
- `issue.spent_hours -> spent_hours`
- `issue.created_on -> redmine_created_on`
- `issue.updated_on -> redmine_updated_on`
- `issue.status.id` duoc doi chieu voi cau hinh `closed_status_ids` de set `is_closed`

### 6.4a Closed status mapping

De xuat:

- them config backend `CLOSED_STATUS_IDS=5,6`
- parse thanh tap `set[int]` khi app startup
- khi sync issue:
  - `is_closed = status_id in CLOSED_STATUS_IDS`
- khong suy luan theo `status_name` vi ten status co the thay doi theo ngon ngu va quy trinh Redmine

### 6.5 `GET /api/issues` query handling

De xuat:

- mac dinh `page=1`, `page_size=20`
- gioi han `page_size <= 100`
- keyword search tren `subject` va `description`
- filter theo:
  - `status_id`
  - `priority_id`
  - `assignee_id`
  - `due_date_from`
  - `due_date_to`
- `status_id` tren UI duoc render bang dropdown list:
  - label hien thi: `status_name`
  - value gui len API: `status_id`
- `priority_id` tren UI duoc render bang dropdown list:
  - label hien thi: `priority_name`
  - value gui len API: `priority_id`
- Nguon option dropdown trong phase nay co the lay tu distinct value trong bang `issues`
- sort mac dinh theo `redmine_updated_on desc`, fallback `id desc`

Response shape:

```json
{
  "items": [],
  "page": 1,
  "page_size": 20,
  "total": 0
}
```

### 6.6 Redmine URL builder

De xuat:

- them helper build issue URL tu `base_url` va `redmine_issue_id`
- phai giu nguyen path prefix neu `base_url` co dang `https://example.com/redmine`

Vi du:

```text
https://example.com/redmine/issues/5001
```

### 6.7 UI integration

Navigation de xuat:

- `Dashboard`
- `Current Project`
- `Issues`
- `Members`
- `Settings` (chi admin)

Trong `Settings`, de xuat co them:

- `Redmine Connection`
- `Project Sync`
- `Issue Sync`

Neu chua muon tao nested navigation phuc tap, co the dung state tab trong `DashboardPage`.

Cho filter issue, de xuat UI:

- `Status ID`: dropdown list
- `Priority ID`: dropdown list
- `Assignee ID`: input text hoac dropdown phase sau neu can
- `Keyword`: text input
- `Due date from/to`: date input

---

## 7. Gap va quyet dinh can chot truoc khi code

| ID | Van de | De xuat |
|---|---|---|
| GAP-ISSUE-1 | Chua co migration framework | Tam thoi dung `create_all()` theo style hien tai |
| GAP-ISSUE-2 | `is_closed` phu thuoc mapping closed status | Da chot dung `closed_status_ids` trong backend; khong suy luan theo `status_name` |
| GAP-ISSUE-3 | Chua co issue sync log model | Tao moi `issue_sync_logs` theo spec |
| GAP-ISSUE-4 | Route list issue phai chi hien issue cua current project | Query bat buoc rang buoc theo connection hien hanh + project local hien hanh |
| GAP-ISSUE-5 | Dashboard/metrics sau nay co the can issue status chuan hoa | Luu ca `status_id` va `status_name` ngay tu phase nay |
| GAP-ISSUE-6 | Dropdown option cho `status_id` va `priority_id` chua co endpoint rieng | Phase nay co the suy ra tu distinct data trong `issues`; neu can on dinh hon thi them endpoint metadata o phase sau |

---

## 8. Acceptance Criteria -> test cases

| AC | Test case | Ket qua mong doi |
|---|---|---|
| ISSUE-AC-001 | Admin goi sync voi connection hop le + co `identifier` | `200`, co `total_synced`, `created`, `updated` |
| ISSUE-AC-002 | Redmine co nhieu trang issue | Sync lay du tat ca issue |
| ISSUE-AC-003 | Sync 2 lan cung issue | Khong duplicate, record cu duoc update |
| ISSUE-AC-004 | User goi `GET /api/issues` | Nhan duoc list co `items`, `page`, `page_size`, `total` |
| ISSUE-AC-005 | User loc theo `status_id`, `priority_id`, `assignee_id`, `due_date`; `status_id` va `priority_id` hien thi dang dropdown list | Ket qua duoc loc dung, UI render dung control |
| ISSUE-AC-006 | User search theo `keyword` | Ket qua chi gom issue phu hop |
| ISSUE-AC-007 | User mo `redmine_url` | URL dung format issue goc |
| ISSUE-AC-008 | User khong phai admin goi sync | `403 Forbidden` |
| ISSUE-AC-009 | Redmine sync loi | Co 1 record `issue_sync_logs` voi `status=failed` |

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
# 4. Mo Settings > Issue Sync
# 5. Bam Sync now
# 6. Mo Issues va kiem tra list
# 7. Thu search / filter / pagination
# 8. Login bang user thuong va thu goi sync
```

Checklist:

- Sync thanh cong tao/updated issue dung so luong
- Sync log success duoc ghi
- Loi sync duoc ghi `issue_sync_logs`
- `GET /api/issues` khong hien `raw_data_json`
- User thuong xem duoc issue list nhung khong trigger sync duoc
- `redmine_url` mo dung issue goc
- Issue list chi chua issue cua current project
- `Status ID` filter hien thi dang dropdown list
- `Priority ID` filter hien thi dang dropdown list

---

## 10. Thu tu thuc hien de xuat

1. Tao model `Issue` va `IssueSyncLog`.
2. Mo rong Redmine client cho `/issues.json`.
3. Implement backend route `POST /api/issues/sync`.
4. Implement backend route `GET /api/issues`.
5. Ghi sync logs success/failed.
6. Implement `IssueSyncPage`.
7. Implement `IssuesPage`.
8. Noi navigation vao dashboard.
9. Test manual va verify response shape.

---

## 11. Ket luan

Feature nay nen duoc implement backend truoc, frontend sau.
Rui ro lon nhat nam o 4 diem:

- sync thieu issue do sai logic pagination
- khong luu cac ID can thiet khien filter khong on dinh
- query list khong rang buoc current project
- mapping `is_closed` khong duoc chot ro truoc khi dashboard phu thuoc vao no

Neu 4 diem nay duoc giu dung theo spec, implementation se thang va it rui ro hon.
