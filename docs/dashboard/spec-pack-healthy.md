# Gói Đặc Tả Project Health KPI Pack

> Tạo: 2026-05-06
> Giai đoạn: MVP / Demo nội bộ
> Tài liệu này là nguồn tham chiếu duy nhất cho phạm vi triển khai của KPI Pack.

---

## 1. Bối cảnh / Mục đích

Ứng dụng hiện tại đã có phần đánh giá Project Health tổng quát. Tuy nhiên người dùng vẫn thiếu phần giải thích cụ thể nguyên nhân vì sao một dự án đang ở trạng thái Green / Yellow / Red.

Mục tiêu của gói KPI này là bổ sung 3 chỉ số đơn giản, dễ hiểu, và có giá trị quản lý thực tế:

1. **Ticket Aging**
   Phát hiện issue mở quá lâu và có nguy cơ bị bỏ quên.
2. **Assignee Overload**
   Phát hiện thành viên đang gánh workload cao bất thường.
3. **Reopen Rate**
   Phản ánh chất lượng xử lý issue thông qua tỷ lệ issue bị mở lại sau khi đã đóng.

Mục tiêu của KPI Pack là giúp PL/PM trả lời nhanh 4 câu hỏi:

- Issue nào đang bị stuck.
- Ai đang có nguy cơ quá tải.
- Chất lượng xử lý issue có dấu hiệu bất ổn hay không.
- Hành động ưu tiên tiếp theo là gì.

---

## 2. Phạm vi

### Trong phạm vi

- Sử dụng dữ liệu issue đã đồng bộ từ Redmine về DB local.
- Tính và hiển thị 3 KPI:
  - Ticket Aging
  - Assignee Overload
  - Reopen Rate
- Hiển thị 3 KPI trên dashboard của project hiện tại.
- Cho phép drill-down từ từng KPI xuống danh sách issue liên quan.
- Sinh `Main Risk Drivers` và `Suggested Actions` dựa trên 3 KPI trên.
- Cho phép cấu hình:
  - Closed status IDs
  - Aging thresholds
  - Overload thresholds
  - Reopen thresholds

### Ngoài phạm vi

- Không tự động cập nhật dữ liệu lên Redmine.
- Không tự động assign hoặc reassign issue.
- Không gửi email hoặc chat notification.
- Không dùng AI/ML để dự đoán ngày hoàn thành dự án.
- Không xếp hạng hiệu suất cá nhân.
- Không thay thế quyết định của PL/PM.
- Không thay đổi công thức tính Project Health tổng hiện tại trong giai đoạn MVP này.

---

## 3. Nguyên tắc MVP

Để giữ phạm vi gọn và triển khai được nhanh, MVP tuân thủ các nguyên tắc sau:

1. Chỉ tính đúng 3 KPI trong tài liệu này.
2. Ưu tiên công thức đơn giản, dễ kiểm chứng.
3. Chỉ dùng dữ liệu đã xác nhận sẵn có trong local DB.
4. Nếu một KPI phụ thuộc vào dữ liệu chưa sẵn sàng thì KPI đó phải hiển thị `N/A` kèm cảnh báo data quality, không tự suy diễn bằng logic phức tạp ngoài spec.
5. `Project Health Score` hiện tại nếu còn được hiển thị thì được xem là phần hiện hữu của hệ thống; KPI Pack chỉ đóng vai trò giải thích bổ sung, không định nghĩa lại score tổng trong tài liệu này.

---

## 4. Thuật ngữ

| # | Thuật ngữ | Định nghĩa |
|---|---|---|
| 1 | Open Issue | Issue có `status_id` không thuộc danh sách Closed Status IDs |
| 2 | Closed Issue | Issue có `status_id` thuộc danh sách Closed Status IDs |
| 3 | Aging Days | Số ngày tính từ ngày tạo issue đến ngày tính KPI |
| 4 | Aging Issue | Open issue có `Aging Days` vượt ngưỡng warning |
| 5 | Assignee Workload | Tổng `estimated_hours` của các open issue được gán cho một assignee |
| 6 | Workload Share | Tỷ trọng workload của một assignee trên tổng workload open issue của project |
| 7 | Reopened Issue | Issue có lịch sử chuyển trạng thái từ closed status sang open status |
| 8 | Reopen Rate | Tỷ lệ `Reopened Issue / Closed Issue Count` trong cửa sổ thời gian tính toán |
| 9 | KPI Threshold | Ngưỡng phân loại `Good / Warning / Critical` |
| 10 | Calculation Date | Ngày hệ thống dùng để tính KPI |

---

## 5. Dữ liệu đầu vào

### 5.1. Bảng dữ liệu sử dụng

| Bảng | Bắt buộc | Mục đích |
|---|---|---|
| `issues` | Có | Lấy dữ liệu issue hiện tại |
| `users` | Có | Lấy tên assignee |
| `issue_statuses` | Có | Mapping trạng thái issue |
| `trackers` | Có | Hiển thị loại issue nếu cần |
| `journals` | Chỉ bắt buộc cho Reopen Rate | Đọc lịch sử thay đổi issue |
| `journal_details` | Chỉ bắt buộc cho Reopen Rate | Đọc thay đổi `status_id` |

### 5.2. Trường dữ liệu tối thiểu

| Trường | Bảng | Mục đích |
|---|---|---|
| `id` | `issues` | ID issue |
| `subject` | `issues` | Tiêu đề issue |
| `project_id` | `issues` | Xác định project |
| `status_id` | `issues` | Trạng thái hiện tại |
| `assigned_to_id` | `issues` | Assignee |
| `priority_id` | `issues` | Độ ưu tiên |
| `tracker_id` | `issues` | Loại issue |
| `estimated_hours` | `issues` | Tính workload |
| `created_on` | `issues` | Tính aging |
| `closed_on` | `issues` | Đếm closed issue trong time window nếu có |
| `due_date` | `issues` | Phục vụ drill-down / context |

### 5.3. Tiền điều kiện dữ liệu

- `Ticket Aging` và `Assignee Overload` phải tính được chỉ với dữ liệu từ bảng `issues`.
- `Reopen Rate` chỉ được tính khi local DB có đủ `journals` và `journal_details`.
- Trong phase MVP này, phần sync `journals` và `journal_details` là hạng mục bắt buộc để triển khai `Reopen Rate`.
- Nếu tại runtime vẫn thiếu dữ liệu history status:
  - `Ticket Aging` vẫn tính bình thường theo `created_on`.
  - `Reopen Rate` hiển thị `N/A`.
  - Dashboard hiển thị cảnh báo `Reopen data unavailable`.

---

## 6. Cấu hình chung

Tất cả cấu hình trong MVP phải dùng **status ID**, không dùng status name trong logic tính toán.

| Cấu hình | Giá trị mặc định đề xuất | Ghi chú |
|---|---|---|
| `closed_status_ids` | `[3, 4, 5]` | Đã chốt |
| `aging_warning_days` | `7` | Warning khi `Aging Days >= 7` |
| `aging_critical_days` | `14` | Critical khi `Aging Days >= 14` |
| `overload_warning_hours` | `160` | Warning khi workload theo giờ >= 160 |
| `overload_critical_hours` | `200` | Critical khi workload theo giờ >= 200 |
| `overload_warning_share_pct` | `30` | Warning khi workload share >= 30% |
| `overload_critical_share_pct` | `50` | Critical khi workload share >= 50% |
| `reopen_warning_pct` | `5` | Warning khi reopen rate >= 5% |
| `reopen_critical_pct` | `15` | Critical khi reopen rate >= 15% |
| `reopen_window_days` | `15` | Chỉ tính các lần closed / reopened trong 15 ngày gần nhất |
| `calculation_date` | Ngày hiện tại | Dùng cho toàn bộ KPI |

---

## 7. KPI 1: Ticket Aging

### 7.1. Mục đích

Phát hiện open issue tồn tại quá lâu để PL/PM chủ động review blocker hoặc ownership.

### 7.2. Công thức MVP

MVP chỉ dùng công thức đơn giản:

```text
Aging Days = Calculation Date - issues.created_on
```

Chỉ tính cho `Open Issue`.

### 7.3. Không dùng trong MVP

- Không tính `Aging In Current Status`.
- Không đọc history status để tìm `Last Status Changed Date`.
- Không phân biệt aging theo từng trạng thái workflow.

Phần này có thể làm ở phase sau nếu dữ liệu history được xác nhận đầy đủ.

### 7.4. Phân loại

| Điều kiện | Trạng thái |
|---|---|
| `Aging Days < aging_warning_days` | Good |
| `aging_warning_days <= Aging Days < aging_critical_days` | Warning |
| `Aging Days >= aging_critical_days` | Critical |

### 7.5. Output

| Trường | Mô tả |
|---|---|
| `total_open_issues` | Tổng open issue |
| `aging_issue_count` | Số issue vượt ngưỡng warning |
| `critical_aging_issue_count` | Số issue vượt ngưỡng critical |
| `average_aging_days` | Aging trung bình |
| `max_aging_days` | Aging lớn nhất |
| `top_aging_issues` | Danh sách issue aging cao nhất |

### 7.6. Drill-down

| Trường | Mô tả |
|---|---|
| Issue ID | ID issue |
| Subject | Tiêu đề issue |
| Status | Trạng thái hiện tại |
| Priority | Độ ưu tiên |
| Assignee | Người phụ trách |
| Created On | Ngày tạo |
| Aging Days | Số ngày aging |
| Risk Level | Good / Warning / Critical |

### 7.7. Suggested Actions

- Review trước các issue aging ở mức Critical.
- Ưu tiên issue aging có priority cao.
- Nếu aging tập trung ở một assignee thì kiểm tra blocker hoặc workload của người đó.

---

## 8. KPI 2: Assignee Overload

### 8.1. Mục đích

Phát hiện tình trạng workload mất cân bằng giữa các thành viên để PL/PM chủ động điều phối.

### 8.2. Công thức chính

MVP dùng `estimated_hours` làm nguồn chính thức để tính overload.

```text
Assignee Workload Hours =
  SUM(issues.estimated_hours)
  WHERE issue là Open Issue
  GROUP BY assigned_to_id
```

```text
Workload Share (%) =
  Assignee Workload Hours / Total Open Workload Hours của project * 100
```

### 8.3. Quy tắc fallback

- Nếu issue không có `estimated_hours`, giá trị đó được xem là `0` trong phép cộng workload hours.
- MVP **không fallback sang open issue count để chấm risk level**.
- Open issue count chỉ được hiển thị như thông tin bổ sung trong drill-down.
- Nếu tỷ lệ open issue thiếu `estimated_hours` lớn hơn hoặc bằng `30%`, dashboard phải hiển thị cảnh báo `Workload data may be incomplete`.

Lý do: fallback từ giờ sang số lượng issue dễ làm thay đổi meaning của KPI và gây khó giải thích cho người dùng.

### 8.4. Phân loại risk level

Risk level của một assignee được lấy theo **mức cao hơn** giữa:

1. Phân loại theo `Workload Hours`
2. Phân loại theo `Workload Share`

#### Theo Workload Hours

| Điều kiện | Trạng thái |
|---|---|
| `< overload_warning_hours` | Good |
| `>= overload_warning_hours` và `< overload_critical_hours` | Warning |
| `>= overload_critical_hours` | Critical |

#### Theo Workload Share

| Điều kiện | Trạng thái |
|---|---|
| `< overload_warning_share_pct` | Good |
| `>= overload_warning_share_pct` và `< overload_critical_share_pct` | Warning |
| `>= overload_critical_share_pct` | Critical |

### 8.5. Output

| Trường | Mô tả |
|---|---|
| `assignee` | Người phụ trách hoặc `Unassigned` |
| `open_issue_count` | Số open issue |
| `total_estimated_hours` | Tổng workload hours |
| `workload_share_pct` | Tỷ lệ workload của assignee |
| `high_priority_issue_count` | Số issue priority cao |
| `overdue_issue_count` | Số issue quá hạn nếu có due date |
| `risk_level` | Good / Warning / Critical |
| `risk_reason` | Lý do bị gắn cờ theo hours hoặc share |

### 8.6. Drill-down

| Trường | Mô tả |
|---|---|
| Issue ID | ID issue |
| Subject | Tiêu đề |
| Status | Trạng thái hiện tại |
| Priority | Độ ưu tiên |
| Estimated Hours | Estimate |
| Due Date | Deadline |
| Aging Days | Số ngày aging |
| Risk Reason | Lý do issue góp phần tạo overload |

### 8.7. Suggested Actions

- Review lại phân bổ task cho assignee ở mức Critical.
- Nếu assignee có nhiều issue priority cao hoặc overdue thì kiểm tra blocker trước.
- Nếu workload share quá lệch thì cân nhắc phân phối lại task.

---

## 9. KPI 3: Reopen Rate

### 9.1. Mục đích

Đánh giá chất lượng xử lý issue thông qua tỷ lệ issue bị mở lại sau khi đã đóng.

### 9.2. Điều kiện tính được KPI

KPI này chỉ tính khi:

- Có dữ liệu `journals`
- Có dữ liệu `journal_details`
- Có cấu hình `closed_status_ids`

Nếu thiếu một trong các điều kiện trên thì hiển thị:

```text
Reopen Rate = N/A
Reason = Reopen data unavailable
```

### 9.3. Time window

Để phản ánh sức khỏe hiện tại thay vì toàn bộ lịch sử project, MVP chỉ tính trên **15 ngày gần nhất** tính từ `Calculation Date`.

Có thể cấu hình lại bằng `reopen_window_days`.

### 9.4. Logic xác định Reopened Issue

Một issue được xem là reopened nếu trong cửa sổ thời gian tính toán có ít nhất một lần chuyển trạng thái:

```text
closed_status_id -> open_status_id
```

Tức là:

```text
journal_details.prop_key = 'status_id'
AND old_value IN closed_status_ids
AND value NOT IN closed_status_ids
```

### 9.5. Công thức

```text
Reopen Rate (%) =
  Reopened Issue Count / Closed Issue Count * 100
```

Trong đó:

- `Closed Issue Count` là số issue có ít nhất một lần chuyển sang closed status trong cửa sổ thời gian tính toán.
- `Reopened Issue Count` là số issue trong tập trên có ít nhất một lần bị mở lại trong cùng cửa sổ thời gian.

### 9.6. Quy tắc edge case

- Một issue bị reopen nhiều lần vẫn chỉ tính là `1 reopened issue` trong mẫu số KPI.
- Số lần reopen vẫn phải được lưu để hiển thị drill-down.
- Nếu `Closed Issue Count = 0` thì `Reopen Rate = N/A`.

### 9.7. Phân loại

| Điều kiện | Trạng thái |
|---|---|
| `Reopen Rate < reopen_warning_pct` | Good |
| `>= reopen_warning_pct` và `< reopen_critical_pct` | Warning |
| `>= reopen_critical_pct` | Critical |

### 9.8. Output

| Trường | Mô tả |
|---|---|
| `closed_issue_count` | Số issue đã closed trong window |
| `reopened_issue_count` | Số issue bị reopen trong window |
| `reopen_rate_pct` | Tỷ lệ reopen |
| `reopen_count_by_assignee` | Thống kê reopen theo assignee |
| `reopen_count_by_tracker` | Thống kê reopen theo tracker |

### 9.9. Drill-down

| Trường | Mô tả |
|---|---|
| Issue ID | ID issue |
| Subject | Tiêu đề |
| Tracker | Loại issue |
| Assignee | Người phụ trách |
| Current Status | Trạng thái hiện tại |
| Reopen Count | Số lần reopen |
| Last Reopened Date | Ngày reopen gần nhất |
| Previous Closed Status ID | Status closed ngay trước lần reopen gần nhất |
| New Status ID | Status sau lần reopen gần nhất |

### 9.10. Suggested Actions

- Review nguyên nhân của các issue bị reopen.
- Nếu reopen tập trung ở một tracker thì kiểm tra lại chất lượng xử lý của nhóm issue đó.
- Nếu một issue bị reopen nhiều lần thì cần root-cause analysis.

---

## 10. Tích hợp vào dashboard

### 10.1. Vai trò của KPI Pack

KPI Pack là lớp giải thích bổ sung cho dashboard hiện tại.

Nó không thay đổi định nghĩa `Project Health Score` tổng trong MVP.

### 10.2. Cách hiển thị đề xuất

```text
Project Health: Yellow
Existing Score: 7 / 12

KPI Insights:
- Ticket Aging: Critical - 8 issues aging >= 14 days
- Assignee Overload: Warning - Assignee A has 165h and 45% workload share
- Reopen Rate: Warning - 8.5% in last 15 days
```

Dashboard nên có thêm nút `Sync` để user chủ động đồng bộ lại dữ liệu trước khi xem KPI mới nhất.

Yêu cầu cho nút `Sync` trong MVP:

- Vị trí: góc trên bên phải khu vực header dashboard.
- Mục đích: trigger đồng bộ lại dữ liệu issue từ nguồn hiện có về local DB trước khi tính lại KPI.
- Sau khi sync xong, dashboard hiển thị lại `Last Updated`.
- Nếu sync thất bại, hiển thị thông báo lỗi ngắn gọn cho user.

Lưu ý: nút `Sync` chỉ trigger quy trình đồng bộ dữ liệu; không thay đổi phạm vi chức năng của KPI Pack.

### 10.3. Main Risk Drivers

Hệ thống sinh tối đa 3 risk drivers, mỗi driver gắn với đúng một KPI trong 3 KPI của tài liệu này.

Ví dụ:

```text
Main Risk Drivers:
1. 8 open issues have aging >= 14 days.
2. Assignee A owns 45% of open estimated workload.
3. Reopen Rate is 8.5% in the last 15 days.
```

### 10.4. Suggested Actions

Ví dụ:

```text
Suggested Actions:
1. Review critical aging issues first.
2. Rebalance workload of Assignee A.
3. Analyze reopened issues to identify quality gaps.
```

---

## 11. Yêu cầu phi chức năng

| # | Danh mục | Yêu cầu |
|---|---|---|
| 1 | Hiệu năng | Tính 3 KPI cho tối thiểu 5.000 issue của một project trong vòng 10 giây |
| 2 | Bảo mật | Không hiển thị issue ngoài phạm vi quyền truy cập của user |
| 3 | Tính sẵn sàng | Nếu thiếu dữ liệu history thì chỉ `Reopen Rate` là `N/A`; hai KPI còn lại vẫn hoạt động |
| 4 | Quan sát | Ghi log `project_id`, số issue xử lý, thời gian tính KPI và lỗi dữ liệu |
| 5 | Cấu hình | Cho phép thay đổi thresholds và `closed_status_ids` |
| 6 | Mở rộng | Thiết kế theo hướng có thể thêm KPI mới sau MVP |

---

## 12. Tiêu chí chấp nhận

| # | ID | Mô tả | Loại kiểm thử |
|---|---|---|---|
| 1 | KPI-AC-001/v2 | Tính được `Ticket Aging` cho open issue dựa trên `created_on` | Unit test |
| 2 | KPI-AC-002/v2 | Phân loại `Ticket Aging` thành Good / Warning / Critical theo cấu hình | Unit test |
| 3 | KPI-AC-003/v2 | Hiển thị được top aging issues trên dashboard hoặc drill-down | UI test |
| 4 | KPI-AC-004/v2 | Tính được workload theo assignee bằng tổng `estimated_hours` của open issue | Unit test |
| 5 | KPI-AC-005/v2 | Tính được `workload_share_pct` theo assignee | Unit test |
| 6 | KPI-AC-006/v2 | Risk level của assignee lấy theo mức cao hơn giữa `hours` và `share` | Unit test |
| 7 | KPI-AC-007/v2 | Nếu tỷ lệ open issue thiếu estimate >= 30% thì hiển thị data quality warning | Unit / UI test |
| 8 | KPI-AC-008/v2 | Hiển thị được drill-down issue của assignee overload | UI test |
| 9 | KPI-AC-009/v2 | Xác định được reopened issue từ lịch sử closed -> open trong time window | Unit / Integration test |
| 10 | KPI-AC-010/v2 | Tính được `Reopen Rate` theo công thức `reopened / closed` trong time window | Unit test |
| 11 | KPI-AC-011/v2 | Nếu thiếu `journals` hoặc `journal_details` thì `Reopen Rate = N/A` | Integration test |
| 12 | KPI-AC-012/v2 | Hiển thị được drill-down issue reopen kèm `reopen_count` và `last_reopened_date` | UI test |
| 13 | KPI-AC-013/v2 | Sinh được tối đa 3 `Main Risk Drivers` từ đúng 3 KPI của tài liệu này | Unit / UI test |
| 14 | KPI-AC-014/v2 | Sinh được `Suggested Actions` tương ứng với KPI có rủi ro | Unit / UI test |
| 15 | KPI-AC-015/v2 | Dashboard hiển thị đủ 3 KPI trong phạm vi project hiện tại | UI test |

---

## 13. Luồng xử lý

### 13.1. Luồng bình thường

1. User mở dashboard của project hiện tại.
2. Hệ thống lấy issue của project từ local DB.
3. Hệ thống xác định `Open Issue` và `Closed Issue` dựa trên `closed_status_ids`.
4. Hệ thống tính:
   - Ticket Aging
   - Assignee Overload
   - Reopen Rate nếu có đủ history
5. Hệ thống hiển thị KPI summary.
6. Hệ thống sinh `Main Risk Drivers` và `Suggested Actions`.
7. User click vào KPI để xem drill-down.

### 13.2. Luồng lỗi / thiếu dữ liệu

1. Nếu không có issue nào trong project, hiển thị `No issue data`.
2. Nếu thiếu `journals` hoặc `journal_details`, `Reopen Rate` hiển thị `N/A`.
3. Nếu thiếu estimate ở nhiều open issue, hiển thị cảnh báo data quality cho `Assignee Overload`.
4. Nếu chưa cấu hình được `closed_status_ids`, hệ thống dùng giá trị mặc định và ghi warning log.

---

## 14. Edge cases

1. Issue không có assignee được nhóm vào `Unassigned`.
2. Issue không có `estimated_hours` được tính là `0h`.
3. Issue bị reopen nhiều lần chỉ tính là 1 reopened issue trong KPI, nhưng vẫn lưu `reopen_count`.
4. `Closed Issue Count = 0` thì `Reopen Rate = N/A`.
5. Project có rất ít issue thì KPI vẫn tính nhưng cần tránh diễn giải quá mạnh ở UI.

---

## 15. Quyết định đã chốt

| ID | Nội dung | Quyết định |
|---|---|---|
| D-1 | Closed status mặc định cho KPI Pack | `closed_status_ids = [3, 4, 5]` |
| D-2 | Dữ liệu cho Reopen Rate | Trong phase MVP này phải bổ sung sync `journals` và `journal_details` |
| D-3 | Ngưỡng overload theo giờ | `overload_warning_hours = 160`, `overload_critical_hours = 200` |
| D-4 | Cửa sổ tính Reopen Rate | `reopen_window_days = 15` |

---

## 16. Rủi ro

| # | Rủi ro | Khả năng | Ảnh hưởng | Giảm thiểu |
|---|---|---|---|---|
| 1 | Thiếu history status khiến Reopen Rate không tính được | Trung bình | Cao | Cho phép `N/A` và hiển thị warning |
| 2 | `estimated_hours` nhập thiếu làm KPI overload thiếu chính xác | Cao | Trung bình | Gắn data quality warning khi thiếu estimate nhiều |
| 3 | Closed status khác nhau giữa các project | Trung bình | Cao | Dùng config theo `status_id` |
| 4 | KPI bị hiểu nhầm thành đánh giá cá nhân | Trung bình | Cao | Ghi rõ mục tiêu là hỗ trợ điều phối, không xếp hạng nhân sự |

---

## 17. Wireframe ASCII

### 17.1. KPI Dashboard

```text
+------------------------------------------------------+
| Project Health Analyzer                              |
+------------------------------------------------------+
| Project: [Current Project]   Last Updated: 2026-05-06 |
|                                         [Sync]       |
+------------------------------------------------------+
| Project Health: YELLOW       Existing Score: 7 / 12  |
+------------------------------------------------------+
| KPI Insights                                         |
+----------------------+--------------+----------------+
| KPI                  | Status       | Summary        |
+----------------------+--------------+----------------+
| Ticket Aging         | Critical     | 8 issues >=14d |
| Assignee Overload    | Warning      | A: 165h / 45%  |
| Reopen Rate          | Warning      | 8.5% / 15d     |
+------------------------------------------------------+
| Main Risk Drivers                                    |
| 1. 8 open issues have aging >= 14 days               |
| 2. Assignee A owns 45% of open workload              |
| 3. Reopen Rate is 8.5% in last 15 days               |
+------------------------------------------------------+
| Suggested Actions                                    |
| 1. Review critical aging issues                      |
| 2. Rebalance workload of Assignee A                  |
| 3. Analyze reopened issues                           |
+------------------------------------------------------+
```

### 17.2. Ticket Aging Drill-down

```text
+------------------------------------------------------+
| Ticket Aging Detail                                  |
+------------------------------------------------------+
| ID   | Subject       | Status | Assignee | Aging | Risk |
|------|---------------|--------|----------|-------|------|
| 101  | API timeout   | Doing  | A        | 18d   | Crit |
| 115  | UI fix        | New    | B        | 15d   | Crit |
| 120  | Batch error   | Review | A        | 9d    | Warn |
+------------------------------------------------------+
```

### 17.3. Assignee Overload Drill-down

```text
+------------------------------------------------------+
| Assignee Workload                                    |
+------------------------------------------------------+
| Assignee | Open Issues | Est. Hours | Share | Risk   |
|----------|-------------|------------|-------|--------|
| A        | 14          | 165h       | 45%   | Warning|
| B        | 6           | 35h        | 17%   | Good   |
| C        | 5           | 28h        | 13%   | Good   |
+------------------------------------------------------+
```

### 17.4. Reopen Rate Drill-down

```text
+------------------------------------------------------+
| Reopen Issues                                        |
+------------------------------------------------------+
| ID   | Subject       | Assignee | Reopen | Last Reopen |
|------|---------------|----------|--------|-------------|
| 201  | Payment bug   | A        | 2      | 2026-05-01  |
| 208  | Login issue   | B        | 1      | 2026-05-02  |
+------------------------------------------------------+
```
