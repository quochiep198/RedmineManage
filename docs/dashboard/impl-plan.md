# DASH-001 - Dashboard: Implementation Plan

> Tao: 2026-05-05
> Dua tren: [spec-pack.md](./spec-pack.md)
> Codebase review: 2026-05-05

---

## 1. Tong quan

Module Dashboard can duoc cap nhat de khop voi spec moi. He thong can:

- hien thi tong so issue cua current project
- hien thi issue open, closed, overdue
- thong ke theo status, priority, assignee
- hien thi trend issue theo `day` hoac `week`
- filter theo date range dua tren `redmine_updated_on`
- cho moi user da dang nhap trigger issue sync ngay tren dashboard
- danh gia suc khoe tong quan cua du an
- thong ke task co kha nang tre
- thong ke task hoan thanh som
- canh bao som cho task uu tien cao `priority_id in {3,4}` neu co dau hieu tre

Module nay phu thuoc vao:

- shared Redmine connection
- current project da duoc sync
- issue data da duoc sync vao bang `issues`
- cau hinh backend `closed_status_ids`

Codebase hien tai da co:

- backend FastAPI voi auth
- bang `projects`, `issues`
- route current project va issue list/sync
- frontend dashboard shell

Codebase hien tai chua co:

- response contract day du cho project health
- config rieng cho `in progress` status neu canh bao som can dung
- dashboard UI hien thi health summary

---

## 2. Ket luan review hien trang

| # | Hang muc | Hien trang | Tac dong |
|---|---|---|---|
| 1 | Current project | Da co `projects` va `GET /api/projects/current` | Dashboard phai rang buoc theo current project |
| 2 | Issue data | Da co bang `issues` voi `status_id`, `priority_id`, `assignee_id`, `redmine_updated_on`, `due_date`, `is_closed` | Du du lieu de aggregate |
| 3 | Auth | Da co `get_current_user` va `require_admin` | Dashboard summary va dashboard sync button chi can authenticated user; route issue sync settings van co the giu admin-only |
| 4 | Closed status mapping | Da co `CLOSED_STATUS_IDS` trong code | Co the tai su dung cho open/closed/overdue |
| 5 | Dashboard UI | Da co summary page co cards + trend | Can mo rong them health section |
| 6 | Project health logic | Chua co trong code | Can them aggregate va warning list |

---

## 3. File map du kien

### Backend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Config closed/in-progress status ids | `backend/app/core/config.py` | Can sua |
| 2 | Dashboard schemas | `backend/app/schemas/dashboard.py` | Can sua |
| 3 | Dashboard route | `backend/app/routes/dashboard.py` | Can sua |
| 4 | Issue sync status mapping | `backend/app/routes/issues.py` | Co the can sua |

### Frontend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Dashboard summary page | `frontend/src/pages/DashboardSummaryPage.jsx` | Can sua |
| 2 | Styles | `frontend/src/styles.css` | Can sua |

### Docs / Test

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Implementation plan | `docs/dashboard/impl-plan.md` | File nay |
| 2 | Backend automated tests | `backend/tests/...` | Chua thay test harness ro rang trong repo |

---

## 4. Mapping spec -> implementation

| Spec item | Implementation du kien |
|---|---|
| `GET /api/dashboard/summary` | Route FastAPI yeu cau authenticated user, aggregate tren bang `issues` cua current project |
| `POST /api/dashboard/sync-issues` | Route FastAPI yeu cau authenticated user, goi chung issue sync core va refresh dashboard sau khi sync |
| Summary cards | `total_issues`, `open_issues`, `closed_issues`, `overdue_issues` |
| `by_status` / `by_priority` / `by_assignee` | Group by SQL hoac aggregate trong Python tren du lieu current project |
| Trend `day/week` | Bucket theo `redmine_updated_on` |
| Date filter | Ap dung inclusive len `redmine_updated_on` |
| Project health | Them `health_status`, `completed_early_count`, `at_risk_task_count`, `high_priority_alert_count`, `health_warnings` |
| High-priority warning | Dung `priority_id in {3,4}` va quy uoc `status_id = 2` la `In Progress` |

---

## 5. Ke hoach trien khai

### Phase 1 - Backend foundation

1. Giu `CLOSED_STATUS_IDS`.
2. Chot `status_id = 2` la `In Progress`.
3. Mo rong dashboard schemas cho project health.

Expected output:

- App doc duoc closed status ids va rule `In Progress`
- Co response model cho project health

### Phase 2 - Backend dashboard API

1. Mo rong `GET /api/dashboard/summary`.
2. Rang buoc current project.
3. Them date filter `from_date`, `to_date`.
4. Giu `group_by=day|week`.
5. Aggregate cards + by status/priority/assignee + trend.
6. Aggregate project health va warning list.
7. Them `POST /api/dashboard/sync-issues` cho moi user da dang nhap.
8. Tai su dung issue sync core thay vi duplicate logic.

Expected output:

- Backend tra du lieu dashboard dung theo spec
- Dashboard khong goi Redmine truc tiep
- Dashboard co them du lieu project health
- Dashboard co shortcut sync issue cho user da dang nhap

### Phase 3 - Frontend dashboard screen

1. Mo rong `DashboardSummaryPage`.
2. Giu date filter va toggle `Day / Week`.
3. Them nut `Sync Issues` cho moi user da dang nhap.
4. Hien cards va chart-style sections.
5. Sau khi sync thanh cong, tai lai dashboard summary.
6. Them health section:
   - health badge
   - completed early count
   - at-risk task count
   - high-priority alert count
   - warning list

Expected output:

- User mo dashboard thay duoc so lieu that
- UI filter hoat dong voi API
- UI co the trigger sync issue truc tiep tu dashboard
- UI co tong quan suc khoe cua du an

### Phase 4 - Verification

1. Test khi khong co current project.
2. Test khi khong co issue.
3. Test date filter.
4. Test trend `day` va `week`.
5. Test closed/open/overdue voi `CLOSED_STATUS_IDS`.
6. Test project health va high-priority warning.

---

## 6. Chi tiet ky thuat de xuat

### 6.1 Config status ids

De xuat env:

```env
CLOSED_STATUS_IDS=5,6
```

Huong xu ly:

- parse thanh `list[int]`
- `CLOSED_STATUS_IDS` dung cho `is_closed`, open/closed/overdue
- `status_id = 2` duoc co dinh la `In Progress` trong phase nay

### 6.2 Dashboard aggregate flow

Pseudo-flow:

```text
require authenticated user
load current connection
load current project
build base issue set for current project
apply from_date/to_date on redmine_updated_on
compute:
  total_issues
  closed_issues
  open_issues
  overdue_issues
  completed_early_count
  at_risk_task_count
  high_priority_alert_count
group:
  by_status
  by_priority
  by_assignee
trend by day/week
build health_warnings
derive health_status
return response
```

### 6.3 Project health heuristics

De xuat phase nay:

- `completed_early_count`
  - issue thuoc nhom closed
  - va co `due_date`
  - va `redmine_updated_on.date() < due_date`
- `at_risk_task_count`
  - issue chua closed
  - va (`due_date < today` hoac sap den han theo nguong canh bao som)
- `high_priority_alert_count`
  - `priority_id in {3,4}`
  - va (
    - `status_id != 2`, hoac
    - `status_id = 2` nhung qua han va chua closed
    )
- `health_status`
  - `critical` neu `high_priority_alert_count > 0`
  - `warning` neu `at_risk_task_count > 0`
  - `healthy` neu khong co canh bao

### 6.4 Frontend rendering

De xuat:

- cards cho 4 metric chinh
- toolbar co `Apply` + `Sync Issues`
- 3 section dang horizontal bars cho status/priority/assignee
- trend section dang list/bars
- health section gom:
  - health badge
  - completed early count
  - at-risk task count
  - high-priority alert count
  - warning list ngan

---

## 7. Gap va quyet dinh can chot truoc khi code

| ID | Van de | De xuat |
|---|---|---|
| GAP-DASH-1 | Spec health chua co response schema chi tiet | Impl plan de xuat them `health_status`, `completed_early_count`, `at_risk_task_count`, `high_priority_alert_count`, `health_warnings` |
| GAP-DASH-2 | Mapping `In Progress` da duoc chot | Dung co dinh `status_id = 2` trong phase nay |
| GAP-DASH-3 | "Sap den han" chua co nguong ro | Tam thoi coi qua han la canh bao chinh; neu can mo rong se them config sau |
| GAP-DASH-4 | Chua co chart library | Phase nay dung CSS bars thay vi them dependency moi |

---

## 8. Acceptance Criteria -> test cases

| AC | Test case | Ket qua mong doi |
|---|---|---|
| DASH-AC-001 | Goi summary voi issue ton tai | Nhan duoc `total_issues` dung |
| DASH-AC-002 | Closed status ids duoc cau hinh | `open/closed/overdue` dung |
| DASH-AC-003 | Group by status | Nhan mang `by_status` sort dung |
| DASH-AC-004 | Group by priority | Nhan mang `by_priority` sort dung |
| DASH-AC-005 | Group by assignee | Nhan mang `by_assignee` sort dung |
| DASH-AC-006 | Date filter | Ket qua doi theo `redmine_updated_on` |
| DASH-AC-007 | `group_by=day|week` | Trend doi bucket dung |
| Health | Co issue priority cao bi tre | Health summary va warning list phan anh dung |
| DASH-AC-009 | User da dang nhap bam `Sync Issues` | Sync thanh cong va dashboard duoc refresh |
| DASH-AC-010 | User khong dang nhap goi `POST /api/dashboard/sync-issues` | `401` |

---

## 9. Manual test checklist

```bash
# 1. Start backend
cd backend
uvicorn app.main:app --reload --port 8000

# 2. Start frontend
cd frontend
npm run dev

# 3. Login
# 4. Mo Dashboard
# 5. Thu date filter
# 6. Thu toggle Day / Week
# 7. Kiem tra health section va warning list
# 8. Thu nut Sync Issues tren dashboard
```

Checklist:

- Dashboard hien du current project
- Cards hien so lieu dung
- Trend thay doi khi doi `group_by`
- Khong co call Redmine khi mo dashboard
- Sync Issues co the bam ngay tren dashboard va xong thi so lieu duoc tai lai
- Health badge doi dung theo du lieu issue
- Task priority cao co dau hieu tre duoc dua vao warning list

---

## 10. Thu tu thuc hien de xuat

1. Mo rong dashboard schemas + route.
2. Them health aggregate vao API.
3. Mo rong dashboard UI.
4. Test compile/import/manual.

---

## 11. Ket luan

Feature nay nen implement backend aggregate truoc, frontend sau.
Rui ro lon nhat nam o 4 diem:

- closed status ids cau hinh sai
- query aggregate khong rang buoc current project
- trend bucket khong nhat quan giua day/week
- mapping `status_id = 2` khac voi workflow Redmine thuc te lam warning cua task priority cao bi sai

Neu 4 diem nay duoc giu dung, dashboard se khop voi spec va kien truc hien tai.
