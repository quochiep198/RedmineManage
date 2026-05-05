# DASH-HEALTH-001 - Project Health Dashboard: Implementation Plan

> Tao: 2026-05-05
> Dua tren: [spec-pack-healthy.md](./spec-pack-healthy.md)
> Codebase review: 2026-05-05

---

## 1. Tong quan

Feature `Project Health` khong can build moi tu dau. Codebase hien tai da co:

- bang `issues` da duoc sync tu Redmine vao DB local
- route `GET /api/dashboard/summary`
- route `POST /api/dashboard/sync-issues`
- dashboard UI co summary cards, trend, issue distribution va health badge heuristic

Nhung implementation hien tai chua khop spec `spec-pack-healthy.md`:

- health hien tai la heuristic `healthy / warning / critical`, khong phai score `0..12`
- chua co 6 metric scoring theo spec
- chua co health snapshot history
- chua co root cause analysis, early warning rules, suggested actions theo risk driver
- chua co drill-down theo risk metric
- chua co scoring config theo closed status / bug tracker / threshold / weight

MVP nay da duoc chot:

- pham vi `single-project dashboard`
- du lieu nguon la DB local da sync tu Redmine
- closed status mac dinh la `status_id in {3,5}`
- bug tracker mac dinh la `Tracker = Bug` hoac `Tracker = Defect`
- metric khong du du lieu hop le thi `score = 0`
- weight mac dinh cua 6 metric deu bang `1`
- score cuoi luon duoc chuan hoa ve thang `12`

Muc tieu cua impl plan nay la nang cap dashboard hien tai thanh dashboard health dung spec, khong lam sai lech pham vi MVP.

---

## 2. Ket luan review hien trang

| # | Hang muc | Hien trang | Tac dong |
|---|---|---|---|
| 1 | Issue source | Da co bang `issues` voi `status_id`, `done_ratio`, `due_date`, `estimated_hours`, `spent_hours`, `assignee_name`, `tracker_name`, `redmine_updated_on` | Du du lieu de tinh 6 metric health |
| 2 | Current project | Da co co che current project dua tren connection identifier | Health dashboard phai tiep tuc rang buoc current project |
| 3 | Dashboard API | `GET /api/dashboard/summary` dang tra cards + warning heuristic | Can thay contract va logic aggregate |
| 4 | Dashboard schema | `backend/app/schemas/dashboard.py` dang model health theo heuristic cu | Can refactor schema theo score, metric detail, trend, risk driver, suggestion |
| 5 | Dashboard UI | `DashboardSummaryPage.jsx` dang hien badge healthy/warning/critical, warning list va trend issue | Can redesign de hien score `X/12`, metric breakdown, trend score, main risks, suggested actions |
| 6 | Closed status config | `backend/app/core/config.py` dang de `CLOSED_STATUS_IDS=1,2,3,4,5` | Sai voi spec moi, can doi default ve `3,5` |
| 7 | Snapshot history | Chua co model/table health snapshot | Can them de support trend, warning theo ky, history |
| 8 | Scoring config | Chua co model/table config health | Can them cau hinh global cho MVP va de mo rong sau |
| 9 | Issue drill-down | Da co `IssuesPage` va `GET /api/issues` | Co the tai su dung de mo issue list, nhung van can route/filter cho risk drill-down |

---

## 3. File map du kien

### Backend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Default config closed status / health config | `backend/app/core/config.py` | Can sua |
| 2 | Health config model | `backend/app/models/dashboard_health_config.py` | Can tao moi |
| 3 | Health snapshot model | `backend/app/models/dashboard_health_snapshot.py` | Can tao moi |
| 4 | Model registry | `backend/app/models/__init__.py` | Can sua |
| 5 | Health calculation schema | `backend/app/schemas/dashboard.py` | Can sua lon |
| 6 | Dashboard aggregate route | `backend/app/routes/dashboard.py` | Can sua lon |
| 7 | Optional helper/service tach logic scoring | `backend/app/services/dashboard_health.py` | Nen tao moi |
| 8 | Issue list route cho risk drill-down | `backend/app/routes/issues.py` | Co the can sua |

### Frontend

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Project health dashboard screen | `frontend/src/pages/DashboardSummaryPage.jsx` | Can sua lon |
| 2 | Dashboard navigation/state | `frontend/src/pages/DashboardPage.jsx` | Co the can sua nhe |
| 3 | Shared API client calls | `frontend/src/api/client.js` | Co the khong can sua |
| 4 | Styles cho health dashboard | `frontend/src/styles.css` | Can sua lon |

### Docs / Test

| # | Muc dich | File du kien | Trang thai |
|---|---|---|---|
| 1 | Health spec | `docs/dashboard/spec-pack-healthy.md` | Da co |
| 2 | Implementation plan | `docs/dashboard/impl-plan-healthy.md` | File nay |
| 3 | Backend automated tests | `backend/tests/...` | Chua xac minh test harness day du |

---

## 4. Mapping spec -> implementation

| Spec item | Implementation du kien |
|---|---|
| Single-project dashboard | Tiep tuc rang buoc current project trong `GET /api/dashboard/summary` |
| 6 metric health | Tinh trong backend tu bang `issues` cua current project |
| Score toi da `12` | Backend tra tong score da chuan hoa theo thang `12` |
| Green / Yellow / Red | Backend derive tu score `10-12`, `7-9`, `0-6` |
| Closed status mac dinh `3,5` | Doi default `CLOSED_STATUS_IDS` va config health default |
| Bug tracker mac dinh `Bug/Defect` | Match theo `tracker_name` trong scoring config |
| Trend theo ngay/tuan | Dashboard trend khong con la trend issue count; se them health snapshot trend |
| Main risk drivers | Backend phan tich issue risk theo assignee, tracker, subject, overdue, effort, stale, bug |
| Early warning | Backend evaluate rules tren current snapshot + previous snapshots |
| Suggested actions | Backend map action theo risk driver va warning type |
| Configurable scoring | Luu global config trong DB; chua can per-project o MVP |
| Drill-down | Them filter risk vao issue list hoac them route health drill-down tra issue lien quan |

---

## 5. Ke hoach trien khai

### Phase 1 - Data foundation va config

1. Sua default `CLOSED_STATUS_IDS` trong config sang `3,5`.
2. Tao model `DashboardHealthConfig` luu:
   - closed status ids
   - bug tracker names
   - stale threshold days
   - overdue thresholds
   - effort thresholds
   - metric weights
   - health status thresholds
3. Tao model `DashboardHealthSnapshot` luu:
   - project id
   - snapshot date
   - score
   - status
   - metric scores
   - metric values
   - main risk drivers
   - warnings
   - suggested actions
4. Dang ky model moi de DB tao bang.
5. Seed mot ban ghi config global mac dinh neu chua ton tai.

Expected output:

- he thong co config global cho health scoring
- he thong co noi luu history health theo snapshot
- default config khop spec moi

### Phase 2 - Health scoring engine

1. Tao helper/service `dashboard_health.py`.
2. Implement 6 metric tinh toan:
   - progress score
   - closed rate score
   - overdue score
   - bug score
   - effort score
   - stale score
3. Implement handling edge cases:
   - metric khong du du lieu hop le -> `score = 0`
   - planned progress gioi han `0..100`
   - tranh chia cho `0`
4. Implement weighted raw score va normalized score thang `12`.
5. Implement health status derive `Green / Yellow / Red`.
6. Implement root cause analysis va top risk drivers.
7. Implement early warning rules dua tren current snapshot va previous snapshot.
8. Implement suggested actions mapping theo risk driver.

Expected output:

- co scoring engine doc lap, test duoc
- logic khop spec va khong con phu thuoc heuristic cu

### Phase 3 - Dashboard API refactor

1. Refactor `backend/app/schemas/dashboard.py` theo response moi.
2. Refactor `GET /api/dashboard/summary`:
   - load current project
   - load issues tu DB local
   - tinh health summary
   - load snapshot trend theo `day/week`
   - tra metric detail, main risks, warnings, suggested actions
3. Giu `POST /api/dashboard/sync-issues`, nhung sau sync thanh cong phai:
   - recalculate current health
   - persist snapshot moi
4. De xuat them `GET /api/dashboard/health/drilldown` voi params:
   - `risk_type`
   - `assignee`
   - `tracker`
   - `subject_group`
   - `priority`
5. Neu muon giam surface area API, co the reuse `GET /api/issues` bang query params risk filter; quyet dinh nay co the chot trong luc code.

Expected output:

- dashboard API tra dung contract health moi
- snapshot duoc tao sau moi lan sync thanh cong
- co du lieu cho drill-down UI

### Phase 4 - Frontend dashboard rewrite

1. Refactor `DashboardSummaryPage.jsx`.
2. Thay health panel hien tai bang layout dung spec:
   - project name
   - health status
   - score `X / 12`
   - trend `+/-/0`
   - 6 metric cards/rows co gia tri + score
   - main risk drivers
   - suggested actions
   - early warnings
3. Them section health trend theo snapshot.
4. Them click target cho drill-down:
   - overdue
   - bug rate
   - effort ratio
   - stale rate
   - assignee
   - target version neu co du lieu
5. Tai su dung `IssuesPage` cho issue list neu co the; neu khong thi them panel/list rieng trong dashboard.
6. Cap nhat CSS cho layout single-project health screen.

Expected output:

- UI khop wireframe va noi dung spec health
- user nhin thay score, trend, risk driver, action tren mot man hinh

### Phase 5 - Verification

1. Verify khong co current project.
2. Verify khong co issue.
3. Verify metric `score = 0` khi thieu du lieu.
4. Verify closed status mac dinh `3,5`.
5. Verify bug tracker mac dinh `Bug/Defect`.
6. Verify normalized score thang `12` khi doi weight.
7. Verify snapshot trend sau 2 lan sync.
8. Verify early warning theo score change.
9. Verify drill-down tra dung issue risk.

---

## 6. Chi tiet ky thuat de xuat

### 6.1 Health config default

De xuat luu trong DB va fallback tu code:

```text
closed_status_ids = [3, 5]
bug_tracker_names = ["Bug", "Defect"]
stale_threshold_days = 7

progress_weight = 1
closed_rate_weight = 1
overdue_weight = 1
bug_weight = 1
effort_weight = 1
stale_weight = 1

status_green_min = 10
status_yellow_min = 7
status_red_max = 6
```

Nguong metric mac dinh:

```text
progress: 2 if actual >= planned; 1 if lag <= 10%; 0 otherwise
closed_rate: 2 if >= 80%; 1 if >= 50%; 0 otherwise
overdue_rate: 2 if = 0%; 1 if <= 10%; 0 otherwise
open_bug_rate: 2 if <= 10%; 1 if <= 25%; 0 otherwise
effort_ratio: 2 if <= 100%; 1 if <= 120%; 0 otherwise
stale_rate: 2 if <= 5%; 1 if <= 15%; 0 otherwise
```

### 6.2 Snapshot model

De xuat field:

- `id`
- `connection_id`
- `project_id`
- `snapshot_at`
- `snapshot_granularity`
- `health_score`
- `health_status`
- `metric_scores_json`
- `metric_values_json`
- `main_risk_drivers_json`
- `warnings_json`
- `suggested_actions_json`
- `created_at`

Ly do dung JSON thay vi normalize sau:

- MVP can giao nhanh
- payload snapshot co cau truc nested
- trend chi can `score`, `status`, `snapshot_at`
- main risk drivers / warnings / actions khong can query join phuc tap o phase nay

### 6.3 Health calculation flow

Pseudo-flow:

```text
load current project
load health config
load all issues of current project

calculate planned progress
calculate actual progress
derive progress score

calculate closed rate
derive closed score

calculate overdue rate
derive overdue score

calculate open bug rate
derive bug score

calculate effort ratio
derive effort score

calculate stale rate
derive stale score

weighted_raw_score = sum(metric_score * metric_weight)
max_weighted_raw_score = 2 * sum(weights)
normalized_score = (weighted_raw_score / max_weighted_raw_score) * 12
rounded_score = round(normalized_score) hoac quy tac lam tron can chot luc code

derive Green / Yellow / Red
analyze risk drivers
load previous snapshot
evaluate early warnings
generate suggested actions
return payload
```

Luu y can chot trong code:

- score nen dung `round half up` hoac `floor`
- khuyen nghi dung `round()` nhung phai viet test ro rang

### 6.4 Planned progress

De xuat aggregate theo project:

- `project_start_date = min(issue.start_date)` cua issue co `start_date`
- `project_due_date = max(issue.due_date)` cua issue co `due_date`
- neu thieu mot trong hai -> progress metric `score = 0`
- neu `project_start_date == project_due_date`:
  - neu today < start -> planned `0`
  - nguoc lai -> planned `100`
- neu today > due -> planned `100`
- neu today < start -> planned `0`

Ly do:

- spec chi noi dung input tu issue, khong dua vao bang project
- can mot quy uoc on dinh de tinh planned progress cho dashboard

### 6.5 Root cause analysis

De xuat output schema:

```text
[
  {
    "risk_type": "overdue",
    "label": "40% overdue issues belong to assignee A",
    "issue_count": 4,
    "issue_ratio": 40.0,
    "dimension": "assignee",
    "dimension_value": "A"
  }
]
```

Quy tac:

- uu tien metric co score thap nhat
- trong metric do, lay nhom issue co ty trong cao nhat
- toi da top `3..5`, MVP nen co dinh `3`

### 6.6 Early warnings

De xuat can previous snapshot:

- `progress_not_changed_5_working_days`
- `overdue_rate_up_2_periods`
- `bug_rate_up_over_20_percent`
- `effort_ratio_over_120_percent`
- `score_green_to_yellow`
- `score_yellow_to_red`
- `stale_rate_over_15_percent`
- `high_or_critical_issue_overdue`

Neu chua co previous snapshot:

- bo qua rule can comparison
- tra `No previous snapshot` o trend/warning context neu can

### 6.7 Suggested actions

De xuat khong generate bang AI. Dung rule-based mapping:

- `overdue` -> review overdue high/critical issues
- `bug` -> focus tracker/subject group co nhieu bug nhat
- `effort` -> review estimate va scope issue vuot effort
- `stale` -> yeu cau assignee update stale issue
- `progress` -> re-plan hoac split issue lon
- `assignee_overloaded` -> review workload va support/reassign

### 6.8 API contract de xuat

De xuat `GET /api/dashboard/summary` tra:

```text
project
last_updated
health_summary:
  score
  max_score
  status
  trend_value
  trend_direction
metrics:
  progress
  closed_rate
  overdue
  bug
  effort
  stale
main_risk_drivers[]
suggested_actions[]
early_warnings[]
health_trend[]
drilldown_links or drilldown_filters
```

Khong nen tiep tuc dung schema `completed_early_count`, `at_risk_task_count`, `high_priority_alert_count` lam contract chinh, vi no khong con khop spec.

---

## 7. Gap va quyet dinh can chot truoc khi code

| ID | Van de | De xuat |
|---|---|---|
| GAP-HEALTH-1 | Existing dashboard schema khac xa spec moi | Chap nhan breaking change ben trong module dashboard |
| GAP-HEALTH-2 | Chua co rule lam tron score thang 12 | Chot trong code va viet test ro rang |
| GAP-HEALTH-3 | "Module" hien duoc quy uoc bang `Subject` | MVP chap nhan, ve sau nen doi sang field phan loai thuc su |
| GAP-HEALTH-4 | Chua co bang config va snapshot | Tao bang moi thay vi co gang nhoi vao bang khac |
| GAP-HEALTH-5 | Drill-down nen la route moi hay tai su dung `GET /api/issues` | Uu tien reuse `GET /api/issues` neu query params du, neu khong thi them route rieng |

---

## 8. Acceptance Criteria -> test cases

| AC | Test case | Ket qua mong doi |
|---|---|---|
| HEALTH-AC-001/v1 | Dataset co start/due/done ratio hop le | Planned Progress, Actual Progress, Schedule Gap tinh dung |
| HEALTH-AC-002/v1 | Actual vs planned theo 3 nguong | Progress score = 2/1/0 dung |
| HEALTH-AC-003/v1 | Closed issue dua tren `status_id in {3,5}` | Closed Rate va score dung |
| HEALTH-AC-004/v1 | Issue overdue va issue open | Overdue Rate va score dung |
| HEALTH-AC-005/v1 | Tracker `Bug`/`Defect` | Open Bug Rate va score dung |
| HEALTH-AC-006/v1 | Estimated/Spent hours | Effort Ratio va score dung |
| HEALTH-AC-007/v1 | Stale threshold 7 ngay | Stale Rate va score dung |
| HEALTH-AC-008/v1 | 6 metric score + weight = 1 | Tong score toi da 12, normalized dung |
| HEALTH-AC-009/v1 | Score = 11, 8, 5 | Status = Green, Yellow, Red |
| HEALTH-AC-011/v1 | Sau moi lan sync thanh cong | Snapshot moi duoc luu |
| HEALTH-AC-012/v1 | Co previous snapshot | Trend value tang/giam/khong doi dung |
| HEALTH-AC-013/v1 | Dataset co overdue / bug / effort concentration | Top risk drivers dung metric va dimension |
| HEALTH-AC-014/v1 | Dataset kich hoat early warning rules | Warning list dung |
| HEALTH-AC-015/v1 | Co risk driver tuong ung | Suggested actions mapping dung |
| HEALTH-AC-016/v1 | Sua global weight/threshold config | Ket qua scoring thay doi va van chuan hoa thang 12 |
| HEALTH-AC-017/v1 | Mo dashboard current project | UI hien health summary dung cho 1 project |
| HEALTH-AC-018/v1 | Click metric risk | Issue list/drill-down hien dung tap issue lien quan |

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
# 4. Sync current project issues
# 5. Mo Dashboard
# 6. Kiem tra score / status / trend / metric breakdown
# 7. Kiem tra risk drivers / suggested actions / early warnings
# 8. Thu click drill-down
# 9. Sync lai de tao them snapshot va kiem tra trend
```

Checklist:

- current project duoc hien dung
- health score dung tren thang `12`
- Green / Yellow / Red khop score
- metric khong du du lieu thi `score = 0`
- trend dung sau khi co >= 2 snapshots
- suggested actions khop risk drivers
- early warnings chi hien khi dung rule
- drill-down mo dung issue risk cua current project

---

## 10. Thu tu thuc hien de xuat

1. Sua default config `CLOSED_STATUS_IDS`.
2. Tao model `DashboardHealthConfig` va `DashboardHealthSnapshot`.
3. Tao `dashboard_health.py` cho scoring engine.
4. Refactor `schemas/dashboard.py`.
5. Refactor `routes/dashboard.py`.
6. Neu can, mo rong `routes/issues.py` cho risk drill-down.
7. Refactor `DashboardSummaryPage.jsx`.
8. Cap nhat `styles.css`.
9. Chay verify manual + automated tests co the thuc hien.

---

## 11. Ket luan

Project Health khong phai la mot widget nho tren dashboard hien tai. Day la mot lan refactor co chu dich:

- doi health heuristic cu thanh scoring engine theo spec
- bo sung storage cho config va snapshots
- doi trend issue count thanh trend health score
- bo sung risk drivers, early warnings, suggested actions, drill-down

Rui ro lon nhat nam o 4 diem:

- score edge cases khong duoc chot ro trong code va test
- dashboard route moi khong giu current project constraint
- snapshot bi ghi trung moi lan user refresh page
- contract frontend/backend doi nhieu nhung khong doi dong bo

Neu giai quyet dung 4 diem nay, feature se khop spec hien tai va co duong mo rong ro rang cho phase sau.
