# DASH-HEALTH-001 - KPI Pack Healthy: Implementation Plan

> Tạo: 2026-05-06
> Dựa trên: [spec-pack-healthy.md](./spec-pack-healthy.md)
> Codebase review: 2026-05-06

---

## 1. Mục tiêu

Triển khai KPI Pack cho dashboard project hiện tại với đúng 3 KPI:

1. `Ticket Aging`
2. `Assignee Overload`
3. `Reopen Rate`

Kế hoạch này bám theo spec MVP đã chốt:

- `closed_status_ids = [3, 4, 5]`
- `overload_warning_hours = 160`
- `overload_critical_hours = 200`
- `reopen_window_days = 15`
- dashboard có thêm nút `Sync`

---

## 2. Kết luận review hiện trạng

| # | Hạng mục | Hiện trạng | Tác động |
|---|---|---|---|
| 1 | Dashboard summary API | `GET /api/dashboard/summary` đã có | Có thể tái sử dụng route, nhưng phải thay logic health hiện tại |
| 2 | Sync button backend | `POST /api/dashboard/sync-issues` đã có | Đủ nền cho nút `Sync` |
| 3 | Health engine hiện tại | `backend/app/services/dashboard_health.py` đang tính 6 metric cũ: progress, closed_rate, overdue_rate, bug_rate, effort_ratio, stale_rate | Không khớp spec mới 3 KPI, cần refactor lớn |
| 4 | Dashboard schema | `backend/app/schemas/dashboard.py` đang model theo health engine cũ | Cần đổi contract response cho phù hợp KPI Pack |
| 5 | Issue source | Bảng `issues` đã có đủ phần lớn field cho Aging và Overload | Dùng lại được |
| 6 | Reopen source | Chưa thấy model / sync flow cho `journals`, `journal_details` | Đây là gap bắt buộc để làm `Reopen Rate` đúng spec |
| 7 | Snapshot | Đã có `DashboardHealthSnapshot` trong code hiện tại | Có thể tái sử dụng, nhưng payload snapshot cần đổi theo 3 KPI mới |
| 8 | Config | Đã có `DashboardHealthConfig` | Có thể tái sử dụng nhưng phải đổi threshold/config shape |

---

## 3. Phạm vi triển khai

### Trong phạm vi

- Refactor backend health service từ 6 metric cũ sang 3 KPI mới
- Cập nhật API dashboard summary
- Bổ sung logic sync cho dữ liệu reopen history
- Cập nhật dashboard UI theo wireframe mới
- Thêm nút `Sync` trên KPI Dashboard
- Hỗ trợ drill-down cho 3 KPI

### Ngoài phạm vi

- Không thay đổi luồng auth tổng thể
- Không thay đổi current project selection
- Không bổ sung AI-generated suggestion
- Không triển khai per-project health config trong phase này

---

## 4. File map dự kiến

### Backend

| # | Mục đích | File | Trạng thái |
|---|---|---|---|
| 1 | Refactor KPI engine | `backend/app/services/dashboard_health.py` | Cần sửa lớn |
| 2 | Cập nhật response schema dashboard | `backend/app/schemas/dashboard.py` | Cần sửa |
| 3 | Cập nhật summary route | `backend/app/routes/dashboard.py` | Cần sửa |
| 4 | Đồng bộ issue + reopen history | `backend/app/routes/issues.py` | Cần sửa |
| 5 | Bổ sung service sync history Redmine | `backend/app/services/redmine_client.py` hoặc service mới | Có thể cần tạo mới |
| 6 | Config model | `backend/app/models/dashboard_health_config.py` | Cần sửa payload default |
| 7 | Snapshot model | `backend/app/models/dashboard_health_snapshot.py` | Có thể giữ nguyên structure, đổi payload JSON |

### Frontend

| # | Mục đích | File | Trạng thái |
|---|---|---|---|
| 1 | Dashboard page | `frontend/src/pages/DashboardSummaryPage.jsx` | Cần sửa lớn |
| 2 | Styles | `frontend/src/styles.css` | Cần sửa |
| 3 | API call sync/summary | `frontend/src/api/...` | Có thể cần sửa nhẹ |

### Docs

| # | Mục đích | File | Trạng thái |
|---|---|---|---|
| 1 | Spec | `docs/dashboard/spec-pack-healthy.md` | Đã chốt |
| 2 | Impl plan | `docs/dashboard/impl-plan.md` | File này |

---

## 5. Mapping spec -> implementation

| Spec item | Implementation dự kiến |
|---|---|
| Ticket Aging dùng `created_on` | Tính trực tiếp từ `Issue.redmine_created_on` hoặc field mapped tương đương |
| Assignee Overload dùng `estimated_hours` | Aggregate open issue theo assignee |
| Risk level overload lấy mức cao hơn giữa `hours` và `share` | Rule-based trong service |
| Thiếu estimate >= 30% | Trả data quality warning trong payload |
| Reopen Rate dùng `journals` + `journal_details` | Phải có thêm sync và storage cho history status |
| Reopen window = 15 ngày | Áp dụng trong truy vấn / aggregate reopen |
| Main Risk Drivers | Generate rule-based từ đúng 3 KPI |
| Suggested Actions | Generate rule-based từ đúng 3 KPI |
| Nút `Sync` | Frontend gọi `POST /api/dashboard/sync-issues`, refresh summary khi thành công |

---

## 6. Thiết kế kỹ thuật đề xuất

### 6.1. KPI engine mới

Refactor `dashboard_health.py` để chỉ còn 3 nhóm logic:

1. `calculate_ticket_aging`
2. `calculate_assignee_overload`
3. `calculate_reopen_rate`

Không giữ lại logic scoring cũ:

- `progress`
- `closed_rate`
- `overdue_rate`
- `bug_rate`
- `effort_ratio`
- `stale_rate`

### 6.2. Response contract đề xuất

`GET /api/dashboard/summary` nên trả:

```text
project
last_updated
health_summary
kpi_cards[]
main_risk_drivers[]
suggested_actions[]
data_quality_warnings[]
drilldown_support
```

Đề xuất `kpi_cards[]`:

```text
[
  {
    code: "ticket_aging",
    label: "Ticket Aging",
    status: "Critical",
    summary: "8 issues aging >= 14 days",
    details: {...}
  }
]
```

`health_summary` trong phase này chỉ nên là phần bao ngoài để UI hiển thị nhất quán, không tái dùng score 12 từ engine cũ.

Đề xuất:

```text
health_summary:
  {
    status: "Yellow",
    score_label: "Existing Score: 7 / 12",
    trend_value: null,
    trend_direction: "none"
  }
```

Lý do: spec đã chốt KPI Pack chỉ là lớp giải thích bổ sung, không định nghĩa lại score tổng.

### 6.3. Ticket Aging

Input:

- issue open
- `created_on`
- assignee
- priority

Output:

- `total_open_issues`
- `aging_issue_count`
- `critical_aging_issue_count`
- `average_aging_days`
- `max_aging_days`
- `top_aging_issues`

### 6.4. Assignee Overload

Rule chính:

- chỉ dùng `estimated_hours`
- issue thiếu estimate được tính `0h`
- không fallback sang issue count để chấm risk

Output:

- per-assignee workload hours
- workload share
- risk level
- risk reason
- warning nếu open issue thiếu estimate >= 30%

### 6.5. Reopen Rate

Muốn làm đúng spec thì cần:

1. Sync `journals`
2. Sync `journal_details`
3. Lưu history status change ở local DB
4. Aggregate transition `closed -> open` trong 15 ngày gần nhất

Nếu chưa có đủ dữ liệu ở runtime:

- KPI vẫn trả về card `Reopen Rate`
- `status = N/A`
- `summary = Reopen data unavailable`

### 6.6. Sync button

UI:

- thêm nút `Sync` ở header dashboard

Backend:

- dùng `POST /api/dashboard/sync-issues`
- sau sync thành công:
  - refresh issue data
  - refresh reopen history nếu có
  - persist snapshot mới nếu còn dùng snapshot
  - frontend gọi lại summary

---

## 7. Kế hoạch triển khai

### Phase 1 - Refactor backend contract

1. Chốt shape response mới cho dashboard summary.
2. Sửa `backend/app/schemas/dashboard.py`.
3. Sửa `backend/app/routes/dashboard.py` để trả payload theo 3 KPI.

Expected output:

- API summary không còn phụ thuộc contract 6 metric cũ.

### Phase 2 - Refactor KPI engine

1. Viết lại `dashboard_health.py` theo 3 KPI.
2. Xóa hoặc cô lập logic 6 metric cũ.
3. Tạo helper generate:
   - KPI cards
   - main risk drivers
   - suggested actions
   - data quality warnings

Expected output:

- Backend tính đúng 3 KPI theo spec.

### Phase 3 - Reopen data foundation

1. Kiểm tra Redmine API cần include/endpoint nào để lấy `journals`.
2. Thiết kế local storage cho journal history nếu repo chưa có.
3. Mở rộng sync flow để kéo history reopen.
4. Tính `Reopen Rate` theo window 15 ngày.

Expected output:

- `Reopen Rate` có thể tính được từ dữ liệu local đúng spec.

### Phase 4 - Dashboard UI

1. Cập nhật `DashboardSummaryPage.jsx`.
2. Render:
   - header + `Sync`
   - existing health summary
   - 3 KPI cards
   - main risk drivers
   - suggested actions
3. Gắn click drill-down cho từng KPI.
4. Sau sync thành công, reload summary.

Expected output:

- UI khớp wireframe mới.

### Phase 5 - Verification

1. Test project không có issue.
2. Test issue có aging.
3. Test overload theo `160/200`.
4. Test thiếu estimate >= 30%.
5. Test thiếu reopen history.
6. Test reopen history trong 15 ngày.
7. Test nút `Sync`.

Expected output:

- Tính đúng KPI và UI hoạt động ổn định.

---

## 8. Gap cần xử lý trước khi code

| ID | Vấn đề | Quyết định / hướng xử lý |
|---|---|---|
| GAP-1 | Code hiện tại đang gắn chặt với 6 metric cũ | Chấp nhận refactor lớn `dashboard_health.py` |
| GAP-2 | Chưa có dữ liệu local cho `journals` / `journal_details` | Bắt buộc bổ sung trong phase MVP này |
| GAP-3 | Snapshot hiện tại đang lưu payload cũ | Cho phép đổi shape JSON snapshot |
| GAP-4 | Existing score `7 / 12` không do KPI Pack định nghĩa | UI giữ vai trò hiển thị tham chiếu, không tính lại |
| GAP-5 | Chưa rõ frontend hiện có drill-down component riêng chưa | Ưu tiên reuse issue list hiện có |

---

## 9. Test cases chính

| ID | Test case | Kết quả mong đợi |
|---|---|---|
| TC-1 | Open issue tạo 10 ngày trước | `Ticket Aging = Warning` nếu ngưỡng 7/14 |
| TC-2 | Assignee có 165h open workload | `Assignee Overload = Warning` |
| TC-3 | Assignee có 205h open workload | `Assignee Overload = Critical` |
| TC-4 | Assignee có 45% workload share nhưng < 160h | Risk level vẫn là `Warning` |
| TC-5 | Thiếu estimate ở 35% open issue | Có `Workload data may be incomplete` |
| TC-6 | Thiếu journals/journal_details | `Reopen Rate = N/A` |
| TC-7 | Có closed -> open trong 15 ngày | `Reopen Rate` tính đúng |
| TC-8 | Bấm `Sync` thành công | Summary reload với `Last Updated` mới |

---

## 10. Thứ tự thực hiện đề xuất

1. Refactor schema dashboard.
2. Refactor `dashboard_health.py`.
3. Refactor dashboard route.
4. Bổ sung sync reopen history.
5. Cập nhật UI dashboard.
6. Verify manual + automated test nếu có.

---

## 11. Kết luận

Phần khó nhất không nằm ở `Ticket Aging` hay `Assignee Overload`, mà nằm ở `Reopen Rate` vì hiện trạng code chưa có nền dữ liệu history status ở local DB. Vì vậy nên triển khai theo thứ tự:

1. dựng lại contract + KPI engine cho 2 KPI tính được ngay,
2. bổ sung sync history,
3. hoàn tất `Reopen Rate`,
4. ghép lại UI hoàn chỉnh.

Nếu cần giao từng phần, có thể tách làm 2 mốc:

- Milestone 1: Aging + Overload + Sync button
- Milestone 2: Reopen Rate + drill-down hoàn chỉnh
