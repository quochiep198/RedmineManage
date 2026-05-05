# Goi dac ta --- (Member Performance Evaluation)

> Tao: 2026-05-05
> Giai doan: [1]
> Nguon tham chieu duy nhat cho thay doi nay.
> Khong trien khai bat ky noi dung nao khong duoc viet o day.
> Cac muc chua ro duoc liet ke trong Open Issues.

------------------------------------------------------------------------

## 1. Boi canh / Muc dich

Bo sung chuc nang thong ke va danh gia hieu suat member dua tren du lieu issue da duoc sync vao DB noi bo de phuc vu:

- theo doi workload cua tung member
- nhan dien member co nguy co tre han
- nhan dien member co nhieu issue uu tien cao chua xu ly xong
- ho tro team leader/admin trong theo doi van hanh project

Module nay phu thuoc vao:

- current project da duoc xac dinh bang `redmine_connections.identifier`
- du lieu `projects` da duoc sync tu module Project Sync
- du lieu `issues` da duoc sync tu module Issue Sync

Trong phase nay, he thong chi danh gia member cua mot current project duy nhat.
Chuc nang nay chi su dung du lieu DB noi bo, khong goi Redmine truc tiep khi user mo man hinh.

Man hinh ap dung:

- Dashboard > Member Performance

## 2. Pham vi

### Trong pham vi

- Thong ke issue theo member trong current project.
- Tinh `assigned_issues`, `open_issues`, `closed_issues`, `overdue_issues`.
- Tinh `in_progress_issues`.
- Tinh `completion_rate`.
- Tinh `overdue_rate`.
- Tinh `avg_done_ratio`.
- Tinh `high_priority_open`.
- Tinh `performance_score`.
- Phan loai `risk_level`.
- Danh dau `INSUFFICIENT_DATA` neu so issue qua it.
- Filter theo date range, risk level, sort.
- Xem chi tiet issue cua tung member.
- Gom issue khong co assignee vao nhom `Unassigned`.

### Ngoai pham vi

- Danh gia nhan su chinh thuc cho HR.
- Danh gia bang AI.
- Sync time entry.
- Danh gia effort thuc te neu chua co time entry.
- So sanh da project trong cung mot man hinh.
- Notification tu dong.
- Cấu hình cong thuc score tren UI trong phase nay.

## 3. Thuat ngu

| # | Thuat ngu | Dinh nghia |
|---|---|---|
| 1 | Member | Nguoi duoc xac dinh chu yeu bang `assignee_id`; neu issue khong co `assignee_id` thi duoc gom vao nhom `Unassigned` |
| 2 | assigned_issues | Tong issue duoc assign cho member |
| 3 | open_issues | Tong issue khong thuoc nhom closed |
| 4 | closed_issues | Tong issue thuoc nhom closed |
| 5 | overdue_issues | Issue co `due_date < today` va khong thuoc nhom closed |
| 6 | in_progress_issues | Issue co `status_id = 2` va khong thuoc nhom closed |
| 7 | completion_rate | `closed_issues / assigned_issues * 100` |
| 8 | overdue_rate | `overdue_issues / assigned_issues * 100` |
| 9 | avg_done_ratio | Trung binh `done_ratio` cua issue cua member |
| 10 | high_priority_open | So issue co `priority_id in {3,4}` va chua closed |
| 11 | performance_score | Chi so tham khao trong khoang 0-100 |
| 12 | risk_level | `LOW`, `MEDIUM`, `HIGH`, hoac `INSUFFICIENT_DATA` |
| 13 | Current project | Project duy nhat dang duoc he thong xu ly, xac dinh bang `redmine_connections.identifier` |

## 4. Hien trang / Trang thai muc tieu

| # | Khia canh | Hien trang | Trang thai muc tieu |
|---|---|---|---|
| 1 | Thong ke member | [MISSING] | User xem duoc tong quan hieu suat cua tung member trong current project |
| 2 | Theo doi workload | [MISSING] | Team leader/admin nhin duoc member nao dang co nhieu issue, issue tre, issue uu tien cao |
| 3 | Danh gia rui ro | [MISSING] | He thong phan loai `LOW/MEDIUM/HIGH/INSUFFICIENT_DATA` de uu tien theo doi |
| 4 | Chi tiet issue | [MISSING] | User mo duoc danh sach issue cua tung member |

## 5. Chi tiet dac ta

### 5.1 Quyen truy cap

- User da dang nhap duoc phep xem member performance.
- Neu user chua dang nhap, backend tra `401 Not authenticated`.
- Phase nay khong yeu cau quyen admin de xem thong ke member.

### 5.2 Nguon du lieu

- Module chi doc du lieu tu DB noi bo.
- Khong goi Redmine truc tiep khi user mo man hinh.
- Chi thong ke issue cua current project hien hanh.
- Date range trong MVP dua tren `redmine_updated_on`.

### 5.3 Metric co ban

| Metric | Cong thuc / y nghia |
|---|---|
| `assigned_issues` | Tong issue cua member trong current project va trong khoang loc |
| `open_issues` | Tong issue khong thuoc nhom closed |
| `closed_issues` | Tong issue thuoc nhom closed |
| `overdue_issues` | Tong issue co `due_date < today` va khong closed |
| `in_progress_issues` | Tong issue co `status_id = 2` va khong closed |
| `completion_rate` | `closed_issues / assigned_issues * 100` |
| `overdue_rate` | `overdue_issues / assigned_issues * 100` |
| `avg_done_ratio` | Trung binh `done_ratio` |
| `high_priority_open` | Tong issue co `priority_id in {3,4}` va khong closed |
| `workload_score` | Gia tri tham khao bang `assigned_issues` trong MVP; khong co cong thuc tach rieng phuc tap trong phase nay |

Rules:

- Neu `assigned_issues = 0`, `completion_rate` va `overdue_rate` duoc tinh bang `0`.
- Neu khong co `done_ratio`, `avg_done_ratio` bo qua record do; neu khong co record hop le thi gia tri bang `0`.
- `closed` duoc xac dinh bang `issues.is_closed`, khong suy luan lai theo `status_name`.

### 5.4 Performance score MVP

```text
performance_score =
  completion_rate * 0.5
  + avg_done_ratio * 0.3
  + (100 - overdue_rate) * 0.2
```

Rules:

- Gia tri duoc gioi han trong khoang `0` den `100`.
- Day la chi so tham khao cho van hanh project, khong phai ket luan danh gia nang luc nhan su.

### 5.5 Risk level

Rules:

1. Neu `assigned_issues < MIN_MEMBER_ISSUES`, `risk_level = INSUFFICIENT_DATA`.
2. Nguoc lai, neu `performance_score < 60` hoac `overdue_rate >= 30`, `risk_level = HIGH`.
3. Nguoc lai, neu `performance_score >= 80` va `overdue_rate < 10`, `risk_level = LOW`.
4. Cac truong hop con lai, `risk_level = MEDIUM`.

Gia tri mac dinh:

- `MIN_MEMBER_ISSUES = 3`

Ly do:

- Thu tu tren loai bo tinh chong lan giua `LOW`, `MEDIUM`, `HIGH`.

### 5.6 API summary

- Endpoint: `GET /api/member-performance/summary`

Query params:

| Param | Bat buoc | Mo ta |
|---|---|---|
| `from_date` | Khong | Ngay bat dau loc theo `redmine_updated_on`, dinh dang `YYYY-MM-DD` |
| `to_date` | Khong | Ngay ket thuc loc theo `redmine_updated_on`, dinh dang `YYYY-MM-DD` |
| `risk_level` | Khong | Loc theo `LOW`, `MEDIUM`, `HIGH`, `INSUFFICIENT_DATA` |
| `sort_by` | Khong | `performance_score`, `overdue_issues`, `assigned_issues`, `member_name` |
| `order` | Khong | `asc` hoac `desc`, mac dinh `desc` |

Rules:

- Phase nay khong co query param `project_id` vi he thong chi co 1 current project.
- `from_date` va `to_date` la inclusive.
- Neu khong gui date range, he thong thong ke tren toan bo issue cua current project.
- API phai group issue theo member key.
- Member key uu tien la:
  - `assignee_id` neu co
  - nguoc lai dung nhom ky thuat `unassigned`

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
  "items": [
    {
      "member_key": "user:12",
      "member_id": 12,
      "member_name": "Nguyen Van A",
      "assigned_issues": 20,
      "open_issues": 8,
      "closed_issues": 12,
      "overdue_issues": 3,
      "in_progress_issues": 4,
      "completion_rate": 60.0,
      "overdue_rate": 15.0,
      "avg_done_ratio": 72.5,
      "high_priority_open": 2,
      "workload_score": 20,
      "performance_score": 68.5,
      "risk_level": "MEDIUM",
      "insufficient_data": false
    }
  ],
  "total": 1
}
```

Sorting rules:

- `member_name` sap xep theo alphabet.
- Cac metric so sap xep theo gia tri.
- Mac dinh: `sort_by=performance_score`, `order=desc`.

### 5.7 API member issue detail

- Endpoint: `GET /api/member-performance/{member_key}/issues`

Path param:

- `member_key`

Query params:

| Param | Bat buoc | Mo ta |
|---|---|---|
| `status_id` | Khong | Loc theo status id |
| `priority_id` | Khong | Loc theo priority id |
| `overdue_only` | Khong | `true/false` |
| `page` | Khong | Mac dinh `1` |
| `page_size` | Khong | Mac dinh `20`, toi da `100` |

Rules:

- Phase nay khong co `project_id`.
- API chi tra issue cua current project.
- `member_key=unassigned` tra nhom issue khong co assignee.
- `member_key=user:{assignee_id}` tra issue cua assignee do.

Response `200 OK`:

```json
{
  "member_key": "user:12",
  "member_id": 12,
  "member_name": "Nguyen Van A",
  "items": [
    {
      "redmine_issue_id": 12345,
      "subject": "Fix login bug",
      "status_id": 2,
      "status_name": "In Progress",
      "priority_id": 4,
      "priority_name": "High",
      "due_date": "2026-05-10",
      "done_ratio": 30,
      "is_overdue": true,
      "redmine_url": "https://redmine.example.com/issues/12345"
    }
  ],
  "page": 1,
  "page_size": 20,
  "total": 1
}
```

### 5.8 API risk members

- Endpoint: `GET /api/member-performance/risk-members`

Query params:

| Param | Bat buoc | Mo ta |
|---|---|---|
| `from_date` | Khong | Ngay bat dau loc theo `redmine_updated_on` |
| `to_date` | Khong | Ngay ket thuc loc theo `redmine_updated_on` |
| `min_risk_level` | Khong | `MEDIUM` hoac `HIGH`; mac dinh `MEDIUM` |

Rules:

- Phase nay khong co `project_id`.
- API nay la subset cua summary, chi tra member co `risk_level` tu nguong tro len.
- `INSUFFICIENT_DATA` khong tu dong nam trong `HIGH`; frontend co the hien thi rieng.

Response `200 OK`:

```json
{
  "items": [
    {
      "member_key": "user:12",
      "member_id": 12,
      "member_name": "Nguyen Van A",
      "risk_level": "HIGH",
      "reasons": [
        "Overdue rate is 35%",
        "High priority open issues: 4"
      ]
    }
  ],
  "total": 1
}
```

### 5.9 Data model

Phase nay uu tien:

- Khong tao bang summary rieng
- Tinh truc tiep tu bang `issues`

Bang `issues` duoc tai su dung cac field:

- `project_id`
- `assignee_id`
- `assignee_name`
- `status_id`
- `status_name`
- `priority_id`
- `priority_name`
- `due_date`
- `done_ratio`
- `is_closed`
- `redmine_updated_on`

Neu du lieu lon hon va can snapshot lich su, phase sau moi xem xet bang:

- `member_performance_snapshots`

### 5.10 Business rules

- Chi thong ke issue cua current project.
- Khong cho user truyen `project_id` trong phase nay.
- Date range trong MVP dua tren `redmine_updated_on`.
- `status_id = 2` duoc xem la `In Progress`.
- Closed issue duoc xac dinh bang `issues.is_closed`.
- Khong duoc suy luan member theo `assignee_name` neu `assignee_id` da co.
- Issue khong co assignee duoc gom vao nhom `Unassigned`.
- `priority_id in {3,4}` duoc xem la nhom uu tien cao.
- `performance_score` chi la chi so tham khao.
- Neu member co it hon `MIN_MEMBER_ISSUES`, he thong phai hien thi `INSUFFICIENT_DATA`.

## 6. Yeu cau phi chuc nang

| # | Danh muc | Yeu cau |
|---|---|---|
| 1 | Hieu nang | MVP tinh truc tiep tu bang `issues`; API phai phan hoi trong muc hop ly voi du lieu issue da sync cua current project |
| 2 | Bao mat | Chi user da dang nhap moi xem duoc thong ke member; API khong tra `raw_data_json` |
| 3 | Tinh san sang | Khong duoc crash neu chua co current project hoac chua co issue; API tra danh sach rong |
| 4 | Kha nang quan sat | Backend log thoi gian tong hop va so member duoc tra; khong log du lieu nhay cam |

## 7. Tieu chi chap nhan

| # | ID | Mo ta | Loai kiem thu |
|---|---|---|---|
| 1 | PERF-AC-001 | User xem duoc danh sach hieu suat member cua current project | API integration + UI |
| 2 | PERF-AC-002 | He thong hien thi dung assigned/open/closed/overdue/in progress theo member | API integration |
| 3 | PERF-AC-003 | He thong tinh dung `completion_rate` | API integration |
| 4 | PERF-AC-004 | He thong tinh dung `overdue_rate` | API integration |
| 5 | PERF-AC-005 | He thong tinh dung `performance_score` theo cong thuc MVP | API integration |
| 6 | PERF-AC-006 | He thong phan loai dung `LOW/MEDIUM/HIGH/INSUFFICIENT_DATA` | API integration |
| 7 | PERF-AC-007 | User filter duoc theo date range va risk level | API integration + UI |
| 8 | PERF-AC-008 | User mo duoc danh sach issue cua tung member | API integration + UI |
| 9 | PERF-AC-009 | Issue khong co assignee duoc gom vao `Unassigned` | API integration |
| 10 | PERF-AC-010 | Member co it hon nguong toi thieu duoc danh dau `INSUFFICIENT_DATA` | API integration |
| 11 | PERF-AC-011 | User chua dang nhap khong xem duoc member performance | Authorization |

## 8. Vi du

### Cac luong binh thuong

1. User mo Member Performance Page va xem danh sach hieu suat member cua current project.
2. User filter theo `from_date`, `to_date`, `risk_level`.
3. User mo danh sach issue cua tung member.
4. He thong gom issue khong co assignee vao nhom `Unassigned`.

### Cac luong loi

1. User chua dang nhap goi API, backend tra `401 Not authenticated`.
2. `member_key` khong hop le, backend tra `404` hoac `422` theo contract implementation.

### Cac truong hop bien

1. Member co it hon `MIN_MEMBER_ISSUES` thi hien thi `INSUFFICIENT_DATA`.
2. Issue khong co assignee duoc gom vao `Unassigned`.
3. Chua co current project hoac chua co issue thi API tra danh sach rong.

## 9. Wireframe ASCII (Tuy chon)

### Member Performance Page

```text
+------------------------------------------------------------------------------------------------+
| Member Performance                                                                             |
+------------------------------------------------------------------------------------------------+
| Current Project: Nishimatsuya                                                                  |
| Date [ From - To ] Risk [v] Sort [v] Order [v] [ Apply ]                                      |
+------------------------------------------------------------------------------------------------+
| Member        | Score | Risk              | Assigned | Open | Closed | Overdue | In Progress |
+------------------------------------------------------------------------------------------------+
| Nguyen Van A  | 68.5  | MEDIUM            | 20       | 8    | 12     | 3       | 4           |
| Unassigned    | 0.0   | INSUFFICIENT_DATA | 2        | 2    | 0      | 0       | 0           |
+------------------------------------------------------------------------------------------------+
```

### Member Detail Drawer/Page

```text
+------------------------------------------------------------------------------------------------+
| Member: Nguyen Van A                                                                           |
+------------------------------------------------------------------------------------------------+
| Score: 68.5 | Risk: MEDIUM | Completion: 60% | Overdue: 15%                                   |
+------------------------------------------------------------------------------------------------+
| ID | Subject | Status | Priority | Due Date | Done | Redmine                                  |
+------------------------------------------------------------------------------------------------+
```

Ghi chu:

- Cac trang thai chinh: `LOW`, `MEDIUM`, `HIGH`, `INSUFFICIENT_DATA`
- Can co thong diep empty state neu chua co current project hoac chua co issue
- Frontend khong hien thi project dropdown trong phase nay

## 10. Cac van de mo

| # | Cau hoi | Nguoi phu trach | Han chot |
|---|---|---|---|
| PERF-OI-001 | Da chot uu tien dung `assignee_id`; chi gom `Unassigned` khi thieu assignee | Product + Backend | Da chot |
| PERF-OI-002 | Da chot closed issue dung `issues.is_closed` theo mapping backend, khong hardcode theo `status_name` | Product + Backend | Da chot |
| PERF-OI-003 | Co can dua `spent_hours` hoac `estimated_hours` vao score o phase sau khong | Product | Bo qua|
| PERF-OI-004 | Co can cho phep drill-down tu risk chart hoac dashboard sang member performance khong | Product + Frontend | [MISSING] |
| PERF-OI-005 | Co can snapshot lich su theo ngay/tuan sau MVP khong | Product + Backend | Bo qua |

## 11. Rui ro

| # | Rui ro | Kha nang xay ra | Muc do anh huong | Bien phap giam thieu |
|---|---|---|---|---|
| 1 | Score bi hieu nham thanh danh gia nang luc nhan su chinh thuc | Trung binh | Cao | Ghi ro day la chi so tham khao |
| 2 | Member co it issue gay mau nho, score khong on dinh | Cao | Trung binh | Dung `INSUFFICIENT_DATA` |
| 3 | Cau hinh closed status sai lam sai metric | Trung binh | Cao | Tai su dung `issues.is_closed` da duoc dong bo theo mapping backend |
| 4 | Assignee bi thieu hoac null gay kho hieu | Trung binh | Trung binh | Gom vao `Unassigned` va hien thi ro tren UI |

------------------------------------------------------------------------

## Bang truy vet

| # | AC | Man hinh/API | DB | Logs | Quyen | Loai kiem thu |
|---|---|---|---|---|---|---|
| 1 | PERF-AC-001 | Member Performance Page / `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration + UI |
| 2 | PERF-AC-002 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 3 | PERF-AC-003 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 4 | PERF-AC-004 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 5 | PERF-AC-005 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 6 | PERF-AC-006 | `GET /api/member-performance/summary`, `GET /api/member-performance/risk-members` | `issues` | Aggregate log | Authenticated user | API integration |
| 7 | PERF-AC-007 | Member Performance Page / `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration + UI |
| 8 | PERF-AC-008 | Member Detail Drawer/Page / `GET /api/member-performance/{member_key}/issues` | `issues` | Aggregate log | Authenticated user | API integration + UI |
| 9 | PERF-AC-009 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 10 | PERF-AC-010 | `GET /api/member-performance/summary` | `issues` | Aggregate log | Authenticated user | API integration |
| 11 | PERF-AC-011 | Tat ca API member performance | N/A | Authorization failure log | Unauthenticated user | Authorization |
