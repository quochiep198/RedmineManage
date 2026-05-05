# Goi dac ta --- (Dashboard)

> Tao: 2026-05-05
> Giai doan: [1]
> Nguon tham chieu duy nhat cho thay doi nay.
> Khong trien khai bat ky noi dung nao khong duoc viet o day.
> Cac muc chua ro duoc liet ke trong Open Issues.

------------------------------------------------------------------------

## 1. Boi canh / Muc dich

Hien thi tong quan tinh trang project va issue tu du lieu da duoc sync vao DB noi bo de phuc vu:

- theo doi tong quan current project
- theo doi so luong issue open/closed/overdue
- xem phan bo issue theo status, priority, assignee
- danh gia suc khoe tong quan cua du an

Module nay phu thuoc vao:

- current project da duoc xac dinh bang `redmine_connections.identifier`
- du lieu `projects` da duoc sync tu module Project Sync
- du lieu `issues` da duoc sync tu module Issue Sync

Trong phase nay, dashboard chi phuc vu mot current project duy nhat.
Dashboard khong goi Redmine truc tiep khi mo man hinh. Tuy nhien user da dang nhap duoc phep chu dong trigger lai issue sync bang nut `Sync Issues` ngay tren dashboard.

Man hinh ap dung:

- Dashboard

## 2. Pham vi

### Trong pham vi

- Hien thi tong so issue cua current project.
- Hien thi so issue open.
- Hien thi so issue closed.
- Hien thi so issue overdue.
- Thong ke theo status.
- Thong ke theo priority.
- Thong ke theo assignee.
- Thong ke trend issue theo ngay/tuan.
- Filter theo date range.
- Trigger issue sync ngay tren dashboard.
- Thong ke cac task co kha nang tre.
- Thong ke task hoan thanh som.
- Tong quan suc khoe cua du an.
- Canh bao som cho task uu tien cao `priority_id in {3,4}` neu bi tre:
  - chua chuyen qua `In Progress`
  - hoac da `In Progress` nhung van chua hoan thanh

### Ngoai pham vi

- Dashboard realtime.
- Export dashboard.
- Drill-down nang cao.
- Filter theo nhieu project.
- Trigger project sync tu dashboard trong phase nay.

## 3. Thuat ngu

| # | Thuat ngu | Dinh nghia |
|---|---|---|
| 1 | Dashboard summary | Tap hop metric tong quan cua current project |
| 2 | Current project | Project duy nhat dang duoc he thong xu ly, duoc xac dinh bang `redmine_connections.identifier` |
| 3 | Overdue issue | Issue co `due_date < today` va khong thuoc nhom closed |
| 4 | Date range | Khoang loc du lieu dashboard, trong MVP dua tren `redmine_updated_on` |
| 5 | Closed status | Tap `status_id` duoc cau hinh trong backend bang `closed_status_ids` de phuc vu tinh `closed_issues` va `overdue_issues` |
| 6 | Trend bucket | Don vi nhom du lieu trend, ho tro `day` hoac `week` |
| 7 | Project health | Danh gia tong quan suc khoe cua du an dua tren issue tre, issue hoan thanh som, va canh bao task uu tien cao |

## 4. Hien trang / Trang thai muc tieu

| # | Khia canh | Hien trang | Trang thai muc tieu |
|---|---|---|---|
| 1 | Tong quan issue | [MISSING] | User xem duoc tong so issue cua current project |
| 2 | Metric open/closed/overdue | [MISSING] | Dashboard tinh duoc issue open, closed, overdue tu DB noi bo |
| 3 | Bieu do tong hop | [MISSING] | Dashboard hien thi duoc phan bo issue theo status, priority, assignee |
| 4 | Trend chart | [MISSING] | Dashboard hien thi duoc trend issue theo ngay/tuan |
| 5 | Project health | [MISSING] | Dashboard hien thi duoc tong quan suc khoe cua project va canh bao som |
| 6 | Filter date | [MISSING] | User loc duoc dashboard theo date range |
| 7 | Hieu nang va on dinh | [MISSING] | Dashboard khong goi Redmine truc tiep va khong lam cham UI dang ke |

## 5. Chi tiet dac ta

### 5.1 Quyen truy cap

- User da dang nhap duoc phep xem dashboard.
- Neu user chua dang nhap, backend tra `401 Not authenticated`.
- Dashboard khong yeu cau quyen admin de xem.
- Hanh dong dong bo issue tren dashboard duoc phep voi moi user da dang nhap.

### 5.2 Nguon du lieu

- Dashboard chi doc du lieu tu DB noi bo.
- Dashboard khong duoc goi Redmine REST API truc tiep khi mo man hinh.
- Dashboard chi thong ke issue cua current project hien hanh.
- Current project duoc xac dinh bang shared Redmine connection da cau hinh.

### 5.3 API dashboard summary

- Endpoint: `GET /api/dashboard/summary`

Query params:

| Param | Bat buoc | Mo ta |
|---|---|---|
| `from_date` | Khong | Ngay bat dau loc theo `redmine_updated_on`, dinh dang `YYYY-MM-DD` |
| `to_date` | Khong | Ngay ket thuc loc theo `redmine_updated_on`, dinh dang `YYYY-MM-DD` |
| `group_by` | Khong | Don vi trend chart, nhan `day` hoac `week`, mac dinh `day` |

Rules:

- Phase nay khong co query param `project_id` vi he thong chi co 1 current project.
- Date range trong MVP dua tren `redmine_updated_on`.
- `from_date` va `to_date` la inclusive.
- `group_by` chi ap dung cho du lieu trend, khong thay doi logic cua summary cards.
- Neu khong gui date range, dashboard thong ke tren toan bo issue cua current project trong DB.
- Neu chua co current project hoac chua co issue nao, API tra metric bang `0` va cac mang chart rong.

Response `200 OK`:

```json
{
  "project": {
    "id": 1,
    "identifier": "nishimatsuya",
    "name": "Nishimatsuya"
  },
  "date_range": {
    "from_date": "2026-05-01",
    "to_date": "2026-05-31",
    "field": "redmine_updated_on"
  },
  "total_issues": 250,
  "open_issues": 180,
  "closed_issues": 70,
  "overdue_issues": 15,
  "project_health": {
    "health_status": "warning",
    "completed_early_count": 8,
    "at_risk_task_count": 6,
    "high_priority_alert_count": 2,
    "health_warnings": [
      {
        "redmine_issue_id": 5001,
        "subject": "Fix login timeout",
        "priority_id": 4,
        "priority_name": "High",
        "status_id": 1,
        "status_name": "New",
        "due_date": "2026-05-03",
        "warning_type": "high_priority_late"
      }
    ]
  },
  "by_status": [
    {
      "status_id": 1,
      "status_name": "New",
      "count": 50
    }
  ],
  "by_priority": [
    {
      "priority_id": 4,
      "priority_name": "High",
      "count": 20
    }
  ],
  "by_assignee": [
    {
      "assignee_id": 12,
      "assignee_name": "Nguyen Van A",
      "count": 12
    }
  ],
  "trend": [
    {
      "bucket": "2026-05-01",
      "label": "2026-05-01",
      "total_issues": 18,
      "open_issues": 12,
      "closed_issues": 6
    }
  ]
}
```

Sorting rules:

- `by_status`: sap xep theo `count desc`, sau do `status_name asc`
- `by_priority`: sap xep theo `count desc`, sau do `priority_name asc`
- `by_assignee`: sap xep theo `count desc`, sau do `assignee_name asc`
- `trend`: sap xep tang dan theo thoi gian cua `bucket`

Trend rules:

- Neu `group_by=day`, moi diem trend dai dien cho 1 ngay.
- Neu `group_by=week`, moi diem trend dai dien cho 1 tuan ISO.
- Trend duoc tinh dua tren `redmine_updated_on`.
- `bucket` la gia tri ky thuat on dinh de frontend ve chart.
- `label` la chuoi hien thi cho frontend.

Project health rules:

- `health_status` nhan 1 trong 3 gia tri:
  - `healthy`
  - `warning`
  - `critical`
- `completed_early_count`:
  - issue thuoc nhom closed
  - va co `due_date`
  - va `redmine_updated_on.date() < due_date`
- `at_risk_task_count`:
  - issue chua closed
  - va da qua han hoac co dau hieu tre theo rule canh bao som
- `high_priority_alert_count`:
  - issue co `priority_id in {3,4}`
  - va (
    - chua chuyen qua trang thai `In Progress`, hoac
    - da `In Progress` nhung qua han va chua closed
    )
- `health_warnings`:
  - danh sach rut gon cac issue canh bao
  - `warning_type` la gia tri ky thuat de frontend hien thi theo nhom canh bao

### 5.4 API dong bo issue tu dashboard

- Endpoint: `POST /api/dashboard/sync-issues`

Request:

```json
{}
```

Rules:

- API nay la dashboard shortcut de trigger lai issue sync cho current project.
- Backend khong nhan `project_id`, `connection_id`, hay `identifier` tu frontend.
- Backend tai su dung cung logic voi `POST /api/issues/sync`.
- Moi user da dang nhap deu co the goi API nay.
- Neu user chua dang nhap, backend tra `401 Not authenticated`.

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

Response error:

- Giong contract cua `POST /api/issues/sync`
- `409 REDMINE_CONNECTION_NOT_CONFIGURED`
- `504 REDMINE_TIMEOUT`
- `502 REDMINE_SYNC_FAILED`

### 5.5 UI dashboard

Dashboard Page:

```text
+--------------------------------------------------------------------+
| Redmine Management Web                                             |
+--------------------------------------------------------------------+
| Current Project: Nishimatsuya         Date: [ From ] [ To ]        |
|                                           [ Apply ] [ Sync Issues ] |
+--------------------------------------------------------------------+
| Total Issues | Open Issues | Closed Issues | Overdue Issues         |
| Project Health: Healthy / Warning / Critical                       |
| Completed Early | At Risk | High Priority Alerts                   |
+--------------------------------------------------------------------+
| Warning List                                                       |
| - #5001 Fix login timeout                                          |
+--------------------------------------------------------------------+
| Issue by Status Chart                                              |
| Issue by Priority Chart                                            |
| Issue by Assignee Chart                                            |
| Issue Trend Chart (Day / Week)                                     |
+--------------------------------------------------------------------+
```

Rules:

- UI phai hien thi ro current project dang duoc thong ke.
- UI khong co project dropdown trong phase nay.
- UI duoc phep co date filter va nut `Apply`.
- UI phai co toggle hoac selector `Day / Week` cho trend chart.
- UI phai co khu vuc `Project Health`.
- UI phai hien thi danh sach canh bao ngan cho task co nguy co tre.
- UI co nut `Sync Issues` tren dashboard cho moi user da dang nhap.
- Nut `Sync Issues` duoc enable voi moi user da dang nhap.
- Sau khi sync thanh cong, frontend phai tai lai dashboard summary.

### 5.6 Business rules

- Dashboard chi doc du lieu tu DB noi bo.
- Dashboard khong goi Redmine truc tiep khi mo man hinh, ngoai tru khi user da dang nhap chu dong bam `Sync Issues`.
- Dashboard chi thong ke issue cua current project hien hanh.
- `open_issues` = tong issue khong thuoc nhom closed.
- `closed_issues` = tong issue thuoc nhom closed.
- `overdue_issues` = issue co `due_date < today` va khong thuoc nhom closed.
- Danh sach closed status duoc cau hinh trong backend bang `closed_status_ids`.
- Backend khong duoc suy luan closed status theo `status_name`.
- Date range trong MVP dua tren `redmine_updated_on`.
- Trend chart trong MVP cung dua tren `redmine_updated_on`.
- Neu issue khong co `assignee_id`, dashboard co the group vao `Unassigned`.
- `priority_id in {3,4}` duoc xem la nhom uu tien cao cho phan canh bao som trong phase nay.
- Trong phase nay, `status_id = 2` duoc xem la trang thai `In Progress`.
- Backend khong duoc suy luan `In Progress` bang `status_name`; phai dung mapping `status_id = 2`.

## 6. Data dependencies

Bang `projects`:

- `id`
- `identifier`
- `name`

Bang `issues`:

- `project_id`
- `status_id`
- `status_name`
- `priority_id`
- `priority_name`
- `assignee_id`
- `assignee_name`
- `due_date`
- `is_closed`
- `redmine_updated_on`

## 7. Yeu cau phi chuc nang

| # | Danh muc | Yeu cau |
|---|---|---|
| 1 | Hieu nang | API dashboard summary phai phan hoi trong muc hop ly voi du lieu issue da sync; khong goi Redmine truc tiep khi chi xem dashboard |
| 2 | Bao mat | Chi user da dang nhap moi xem duoc dashboard; dashboard khong tra `raw_data_json` |
| 3 | Tinh san sang | Dashboard khong duoc crash neu chua co project hoac chua co issue |
| 4 | Kha nang quan sat | Backend log thoi gian xu ly dashboard API va so record tong hop; khong log du lieu nhay cam |

## 8. Tieu chi chap nhan

| # | ID | Mo ta | Loai kiem thu |
|---|---|---|---|
| 1 | DASH-AC-001 | Dashboard hien thi duoc tong so issue cua current project | API integration + UI |
| 2 | DASH-AC-002 | Dashboard hien thi duoc open, closed, overdue | API integration + UI |
| 3 | DASH-AC-003 | Dashboard thong ke duoc theo status | API integration + UI |
| 4 | DASH-AC-004 | Dashboard thong ke duoc theo priority | API integration + UI |
| 5 | DASH-AC-005 | Dashboard thong ke duoc theo assignee | API integration + UI |
| 6 | DASH-AC-006 | Filter date range hoat dong dung theo `redmine_updated_on` | API integration + UI |
| 7 | DASH-AC-007 | Dashboard hien thi duoc trend issue theo `day` va `week` | API integration + UI |
| 8 | DASH-AC-008 | Dashboard hien thi duoc project health, task at risk, completed early, va high priority alerts | API integration + UI |
| 9 | DASH-AC-009 | Moi user da dang nhap co the bam `Sync Issues` ngay tren dashboard va dashboard duoc refresh lai so lieu | API integration + UI |
| 10 | DASH-AC-010 | User chua dang nhap khong trigger duoc sync tu dashboard | Authorization |
| 11 | DASH-AC-011 | Dashboard khong goi Redmine truc tiep khi mo man hinh neu user khong bam sync | Code review / integration |
| 12 | DASH-AC-012 | User chua dang nhap khong xem duoc dashboard | Authorization |

## 9. Vi du

### Cac luong binh thuong

1. User mo dashboard, backend tra summary tu du lieu issue cua current project.
2. User chon `from_date` va `to_date`, backend loc lai metric theo `redmine_updated_on`.
3. User xem chart theo status, priority, assignee ma khong can goi Redmine.
4. User chuyen trend chart giua `Day` va `Week`, backend tra du lieu trend theo `group_by`.
5. User xem khu vuc `Project Health` de nhan biet task co nguy co tre va task uu tien cao dang can xu ly som.
6. User da dang nhap bam `Sync Issues` tren dashboard, backend trigger issue sync va frontend tai lai so lieu dashboard.

### Cac luong loi

1. User chua dang nhap goi API dashboard, backend tra `401 Not authenticated`.
2. Chua co current project hoac chua co issue, backend van tra `200` voi so lieu bang `0`.
3. User chua dang nhap bam sync issue tu dashboard, backend tra `401 Not authenticated`.

### Cac truong hop bien

1. Issue khong co assignee duoc group vao `Unassigned`.
2. Danh sach closed status duoc xac dinh bang `closed_status_ids`.
3. Date range rong hoac khong gui thi dashboard tinh tren toan bo current project.
4. `group_by` khong hop le, backend tra validation error `422`.
5. Neu chua co mapping ro cho `In Progress`, phan canh bao som can duoc xac nhan theo cau hinh backend.

## 10. Cac van de mo

| # | Cau hoi | Nguoi phu trach | Han chot |
|---|---|---|---|
| OI-1 | Da chot dung `closed_status_ids` trong backend de xac dinh closed issue; khong hardcode theo `status_name` | Product + Backend | Da chot |
| OI-2 | Da chot bo sung chart trend theo `day/week` ngay trong phase nay, query bang `group_by` | Product | Da chot |
| OI-3 | Co can cho phep user click chart de drill-down sang danh sach issue da loc san khong | Product + Frontend | [MISSING] |
| OI-4 | Da chot `status_id = 2` la `In Progress` de phuc vu canh bao som task uu tien cao | Product + Backend | Da chot |

## 11. Rui ro

| # | Rui ro | Kha nang xay ra | Muc do anh huong | Bien phap giam thieu |
|---|---|---|---|---|
| 1 | Cau hinh `closed_status_ids` sai lam sai metric open/closed/overdue | Trung binh | Cao | Review cau hinh backend va test voi bo status thuc te |
| 2 | Query aggregate khong rang buoc current project lam sai so lieu | Trung binh | Cao | Bat buoc query theo current project local |
| 3 | Date filter va trend bucket khong thong nhat field loc lam user hieu sai so lieu | Trung binh | Trung binh | Chot ro `redmine_updated_on` trong MVP |
| 4 | Mapping `In Progress` sai lam sai canh bao som task uu tien cao | Trung binh | Cao | Dung co dinh `status_id = 2` trong phase nay va them test voi rule nay |
| 5 | Admin sync tren dashboard nhieu lan lien tiep co the gay tai lai du lieu khong can thiet | Trung binh | Trung binh | Disable nut khi dang sync va hien thi trang thai dang dong bo |

------------------------------------------------------------------------

## Bang truy vet

| # | AC | Man hinh/API | DB | Logs | Quyen | Loai kiem thu |
|---|---|---|---|---|---|---|
| 1 | DASH-AC-001 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 2 | DASH-AC-002 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 3 | DASH-AC-003 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 4 | DASH-AC-004 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 5 | DASH-AC-005 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 6 | DASH-AC-006 | `GET /api/dashboard/summary` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 7 | DASH-AC-007 | `GET /api/dashboard/summary?group_by=day|week` + Dashboard | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 8 | DASH-AC-008 | `GET /api/dashboard/summary` + Dashboard health section | `issues` | Dashboard summary log | Authenticated user | API integration + UI |
| 9 | DASH-AC-009 | `POST /api/dashboard/sync-issues` + Dashboard | `issues`, `issue_sync_logs` | Issue sync log | Authenticated user | API integration + UI |
| 10 | DASH-AC-010 | `POST /api/dashboard/sync-issues` | `issue_sync_logs` | Authorization failure log | Unauthenticated user | Authorization |
| 11 | DASH-AC-011 | Dashboard + backend aggregate query | `issues` | Dashboard summary log | Authenticated user | Code review / integration |
| 12 | DASH-AC-012 | `GET /api/dashboard/summary` | N/A | Authorization failure log | Authenticated user | Authorization |
