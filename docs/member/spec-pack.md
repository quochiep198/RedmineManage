# Gói đặc tả — Member Management & Reminder

> Tạo: 2026-05-06 · Giai đoạn: MVP / Demo nội bộ  
> **Nguồn tham chiếu duy nhất cho thay đổi này.**  
> Không triển khai bất kỳ nội dung nào không được viết ở đây. Các điểm chưa rõ → Open Issues.

---

## 1. Bối cảnh / Mục đích

PL/PM cần một màn hình để theo dõi tình trạng công việc của từng member dựa trên dữ liệu Redmine đã được đồng bộ về DB local.

Chức năng này không nhằm mục đích chấm điểm nhân sự hoặc xếp hạng cá nhân. Mục tiêu là hỗ trợ PL/PM:

- Phát hiện member đang quá tải.
- Phát hiện issue bị quá hạn hoặc lâu chưa cập nhật.
- Phát hiện issue có nguy cơ bị bỏ quên.
- Phát hiện member cần được hỗ trợ.
- Tạo và quản lý reminder cho đúng member, đúng issue, đúng lý do.

Tên chức năng đề xuất:

```text
Member Management & Reminder
```

hoặc:

```text
Member Work Insight & Reminder
```

---

## 2. Phạm vi

### Trong phạm vi

- Hiển thị danh sách member trong project hiện tại.
- Hiển thị workload và risk của từng member.
- Tính các chỉ số chính:
  - Open Issue Count
  - Estimated Workload
  - Overdue Issue Count
  - Ticket Aging Count
  - Reopen Count
  - Stale Update Count
  - Workload Share
- Xác định issue cần reminder.
- Hiển thị danh sách issue cần reminder theo member.
- Cho phép PL/PM tạo reminder thủ công hoặc từ gợi ý của hệ thống.
- Cho phép cập nhật trạng thái reminder:
  - Not Sent
  - Sent
  - Acknowledged
  - Resolved
  - Snoozed
  - Ignored
- Lưu lịch sử reminder vào DB local.
- Hiển thị suggested actions để PL/PM hỗ trợ member.

### Ngoài phạm vi

- Không dùng chức năng này để đánh giá nhân sự chính thức.
- Không xếp hạng member theo năng lực.
- Không tự động thay đổi assignee trên Redmine.
- Không tự động cập nhật trạng thái issue trên Redmine.
- Không bắt buộc gửi email/chat thật trong MVP.
- Không thay thế quyết định của PL/PM.
- Không đánh giá performance ngoài dữ liệu issue Redmine.

---

## 3. Thuật ngữ

| # | Thuật ngữ | Định nghĩa |
|---|---|---|
| 1 | Member | Người được assign issue trong project |
| 2 | Open Issue | Issue chưa thuộc nhóm closed status |
| 3 | Estimated Workload | Tổng estimated hours của các issue chưa đóng thuộc member |
| 4 | Workload Share | Tỷ lệ workload của member trên tổng workload project |
| 5 | Overdue Issue | Issue chưa đóng và due_date nhỏ hơn ngày hiện tại |
| 6 | Ticket Aging | Issue chưa đóng tồn tại hoặc nằm ở trạng thái hiện tại quá lâu |
| 7 | Stale Update | Issue chưa đóng nhưng lâu chưa được cập nhật |
| 8 | Reopen Count | Số issue của member đã từng bị reopen |
| 9 | Member Work Risk | Mức rủi ro công việc của member dựa trên workload, overdue, aging, reopen và stale update |
| 10 | Reminder | Nhắc nhở được tạo cho member để cập nhật hoặc xử lý issue |
| 11 | Reminder Reason | Lý do cần reminder, ví dụ Overdue, Aging, Stale, Reopened |
| 12 | Reminder Status | Trạng thái xử lý reminder |

---

## 4. Hiện trạng / Trạng thái mục tiêu

| # | Khía cạnh | Hiện trạng | Trạng thái mục tiêu |
|---|---|---|---|
| 1 | Theo dõi member | PL/PM phải xem issue thủ công trong Redmine | Có màn hình tổng hợp member và tình trạng công việc |
| 2 | Workload | Chưa nhìn nhanh ai đang quá tải | Hiển thị workload, workload share và overload risk |
| 3 | Issue cần follow | Phải tự lọc overdue/stale issue | Hệ thống tự gợi ý issue cần reminder |
| 4 | Reminder | Nhắc thủ công, khó theo dõi lịch sử | Lưu reminder status và lịch sử reminder |
| 5 | Hỗ trợ member | PL/PM khó biết ai cần support | Hiển thị Member Work Risk và suggested actions |

---

## 5. Chi tiết đặc tả

### 5.1. Nguồn dữ liệu

Dữ liệu issue được đồng bộ từ Redmine về DB local.

Các bảng Redmine mirror cần dùng:

| Bảng | Mục đích |
|---|---|
| issues | Lấy issue, assignee, status, priority, due date, estimate |
| users | Lấy thông tin member |
| issue_statuses | Xác định status hiện tại |
| trackers | Xác định loại issue |
| journals | Lấy lịch sử thay đổi issue |
| journal_details | Lấy lịch sử đổi status để xác định reopen |
| versions | Lấy target version nếu cần |
| time_entries | Lấy spent hours nếu cần mở rộng |

Bảng mới cần thêm:

```text
member_reminders
```

---

### 5.2. Màn hình chính — Member Management & Reminder

Màn hình gồm 4 khu vực:

1. Summary
2. Member List
3. Selected Member Detail
4. Issues Need Reminder

#### 5.2.1. Summary

Hiển thị tổng quan project hiện tại:

| Field | Mô tả |
|---|---|
| Project | Project hiện tại |
| Period | Khoảng thời gian xem dữ liệu |
| Total Members | Số member có issue trong project |
| Overloaded Members | Số member có workload risk Warning/Critical |
| Issues Need Reminder | Số issue cần reminder |
| High Risk Members | Số member có Member Work Risk cao |

#### 5.2.2. Member List

Danh sách member cần hiển thị:

| Field | Mô tả |
|---|---|
| Member | Tên member |
| Open Issues | Số issue chưa đóng |
| Estimated Workload | Tổng estimated hours của issue chưa đóng |
| Workload Share | Tỷ lệ workload so với toàn project |
| Overdue Issues | Số issue quá hạn |
| Aging Issues | Số issue aging vượt ngưỡng |
| Reopened Issues | Số issue bị reopen |
| Stale Issues | Số issue lâu chưa cập nhật |
| Member Work Risk | Good / Need Attention / High Risk |
| Reminder Needed | Số issue cần reminder |

#### 5.2.3. Selected Member Detail

Khi chọn một member, hiển thị:

| Field | Mô tả |
|---|---|
| Member name | Tên member |
| Open issue count | Số issue chưa đóng |
| Estimated workload | Tổng effort còn lại |
| Overdue issue count | Số issue quá hạn |
| Aging issue count | Số issue aging |
| Reopen count | Số issue từng bị reopen |
| Stale update count | Số issue lâu chưa cập nhật |
| Main risks | Rủi ro chính của member |
| Suggested actions | Gợi ý hành động cho PL/PM |

#### 5.2.4. Issues Need Reminder

Danh sách issue cần reminder:

| Field | Mô tả |
|---|---|
| Issue ID | ID issue Redmine |
| Subject | Tiêu đề issue |
| Assignee | Member đang phụ trách |
| Reason | Lý do cần reminder |
| Priority | Độ ưu tiên |
| Due date | Deadline |
| Last update | Ngày cập nhật cuối |
| Aging days | Số ngày aging |
| Reminder status | Trạng thái reminder |
| Last reminder date | Lần reminder gần nhất |

---

### 5.3. KPI cho Member

#### 5.3.1. Open Issue Count

```text
Open Issue Count =
  COUNT(issues.id)
  WHERE assigned_to_id = member_id
  AND status_id NOT IN Closed Status
```

Ý nghĩa:

- Member đang giữ bao nhiêu issue chưa hoàn tất.
- Dùng làm chỉ báo workload cơ bản.

#### 5.3.2. Estimated Workload

```text
Estimated Workload =
  SUM(issues.estimated_hours)
  WHERE assigned_to_id = member_id
  AND status_id NOT IN Closed Status
```

Nếu `estimated_hours` thiếu, hiển thị cảnh báo data quality và fallback sang Open Issue Count.

#### 5.3.3. Workload Share

```text
Workload Share (%) =
  Member Estimated Workload / Total Project Estimated Workload * 100
```

Nếu không đủ estimated hours:

```text
Workload Share (%) =
  Member Open Issue Count / Total Project Open Issue Count * 100
```

#### 5.3.4. Overdue Issue Count

```text
Overdue Issue Count =
  COUNT(issues.id)
  WHERE assigned_to_id = member_id
  AND status_id NOT IN Closed Status
  AND due_date < Current Date
```

#### 5.3.5. Ticket Aging Count

```text
Ticket Aging Count =
  COUNT(issues.id)
  WHERE assigned_to_id = member_id
  AND status_id NOT IN Closed Status
  AND Aging Days >= Aging Warning Threshold
```

MVP:

```text
Aging Days = Current Date - issues.created_on
```

Nâng cao:

```text
Aging Days = Current Date - Last Status Changed Date
```

#### 5.3.6. Stale Update Count

```text
Stale Update Count =
  COUNT(issues.id)
  WHERE assigned_to_id = member_id
  AND status_id NOT IN Closed Status
  AND Current Date - updated_on >= Stale Update Threshold
```

#### 5.3.7. Reopen Count

```text
Reopen Count =
  COUNT(DISTINCT issue_id)
  WHERE issue từng chuyển từ Closed Status sang Open Status
  AND issue.assigned_to_id = member_id
```

Dữ liệu lấy từ `journals` và `journal_details`.

---

### 5.4. Member Work Risk

#### 5.4.1. Mục đích

Member Work Risk giúp PL/PM biết member nào cần được theo dõi hoặc hỗ trợ.

Lưu ý:

```text
Member Work Risk không phải điểm đánh giá năng lực cá nhân.
Đây là chỉ báo rủi ro công việc để hỗ trợ quản lý dự án.
```

#### 5.4.2. Công thức

```text
Member Work Risk Score =
  Overload Score
+ Aging Score
+ Overdue Score
+ Reopen Score
+ Stale Update Score
```

#### 5.4.3. Cách chấm điểm đề xuất

##### Overload Score

| Điều kiện | Điểm |
|---|---:|
| Workload < 80h hoặc Workload Share < 30% | 0 |
| Workload từ 80h đến dưới 120h hoặc Share từ 30% đến dưới 50% | 1 |
| Workload >= 120h hoặc Share >= 50% | 2 |

##### Aging Score

| Điều kiện | Điểm |
|---|---:|
| Aging issue = 0 | 0 |
| Aging issue từ 1 đến 3 | 1 |
| Aging issue > 3 | 2 |

##### Overdue Score

| Điều kiện | Điểm |
|---|---:|
| Overdue issue = 0 | 0 |
| Overdue issue từ 1 đến 3 | 1 |
| Overdue issue > 3 | 2 |

##### Reopen Score

| Điều kiện | Điểm |
|---|---:|
| Reopen issue = 0 | 0 |
| Reopen issue từ 1 đến 2 | 1 |
| Reopen issue > 2 | 2 |

##### Stale Update Score

| Điều kiện | Điểm |
|---|---:|
| Stale issue = 0 | 0 |
| Stale issue từ 1 đến 3 | 1 |
| Stale issue > 3 | 2 |

#### 5.4.4. Phân loại

| Tổng điểm | Trạng thái | Ý nghĩa |
|---:|---|---|
| 0–2 | Good | Tình trạng bình thường |
| 3–5 | Need Attention | Cần PL/PM theo dõi |
| 6+ | High Risk | Cần hỗ trợ hoặc follow ngay |

---

### 5.5. Logic xác định issue cần reminder

Một issue cần reminder nếu thỏa ít nhất một điều kiện:

| Điều kiện | Reminder Reason |
|---|---|
| Issue chưa đóng và due_date < Current Date | Overdue |
| Issue chưa đóng và updated_on quá 3 ngày | No recent update |
| Issue aging >= 7 ngày | Aging issue |
| Issue priority High/Critical và stale | High priority stale |
| Issue bị reopen nhưng chưa có update mới | Reopened issue |

#### 5.5.1. Rule ưu tiên reminder

Nếu một issue thỏa nhiều điều kiện, ưu tiên reason theo thứ tự:

1. High priority stale
2. Overdue
3. Reopened issue
4. Aging issue
5. No recent update

#### 5.5.2. Reminder severity

| Điều kiện | Severity |
|---|---|
| High priority stale | Critical |
| Overdue priority High/Critical | Critical |
| Overdue | Warning |
| Reopened issue | Warning |
| Aging issue | Warning |
| No recent update | Info |

---

### 5.6. Reminder Workflow

```text
1. Hệ thống scan issue từ DB local.
2. Detect issue cần remind.
3. Gom nhóm issue theo assignee.
4. PL/PM xem danh sách reminder suggestion.
5. PL/PM chọn issue cần gửi reminder.
6. Hệ thống tạo record trong member_reminders.
7. Reminder status ban đầu là Not Sent hoặc Sent tùy thao tác.
8. Sau khi member update issue, reminder chuyển sang Resolved.
9. PL/PM có thể Snooze hoặc Ignore reminder.
```

---

### 5.7. Reminder Status

| Status | Ý nghĩa |
|---|---|
| Not Sent | Reminder được gợi ý nhưng chưa gửi |
| Sent | PL/PM đã gửi reminder |
| Acknowledged | Member đã phản hồi hoặc xác nhận |
| Resolved | Issue đã được update/xử lý |
| Snoozed | Tạm hoãn reminder |
| Ignored | PL/PM bỏ qua reminder |

---

### 5.8. Reminder Message Template

```text
Hi [Member],

Please update the following Redmine issues:

1. #[Issue ID] [Subject]
   Reason: [Reminder Reason]
   Due date: [Due Date]
   Last update: [Last Update]
   Aging: [Aging Days] days

Please update status, blocker, or expected completion date.
```

Phiên bản tiếng Việt:

```text
Hi [Member],

Vui lòng cập nhật các issue Redmine sau:

1. #[Issue ID] [Subject]
   Lý do: [Reminder Reason]
   Due date: [Due Date]
   Cập nhật gần nhất: [Last Update]
   Aging: [Aging Days] ngày

Vui lòng cập nhật trạng thái, blocker hoặc ngày dự kiến hoàn thành.
```

---

### 5.9. DB bổ sung

#### 5.9.1. Bảng `member_reminders`

| Field | Type | Mô tả |
|---|---|---|
| id | bigint | Reminder ID |
| project_id | bigint | Project ID |
| issue_id | bigint | Issue ID |
| assignee_id | bigint | Member ID |
| reason | varchar | Overdue / Aging / Stale / Reopen |
| severity | varchar | Info / Warning / Critical |
| status | varchar | Not Sent / Sent / Acknowledged / Resolved / Snoozed / Ignored |
| reminder_message | text | Nội dung reminder |
| sent_at | datetime | Thời điểm gửi |
| acknowledged_at | datetime | Thời điểm member xác nhận |
| resolved_at | datetime | Thời điểm resolved |
| snoozed_until | datetime | Thời điểm snooze đến |
| ignored_at | datetime | Thời điểm ignore |
| created_by | bigint | User tạo reminder |
| created_at | datetime | Ngày tạo |
| updated_at | datetime | Ngày cập nhật |

#### 5.9.2. Gợi ý index

| Index | Mục đích |
|---|---|
| project_id, assignee_id | Query reminder theo project/member |
| issue_id | Kiểm tra reminder của issue |
| status | Lọc reminder theo trạng thái |
| severity | Lọc reminder theo mức độ |
| created_at | Sort lịch sử reminder |

---

### 5.10. Suggested Actions

| Tình huống | Suggested Action |
|---|---|
| Member overload | Review workload và cân nhắc hỗ trợ member |
| Member có nhiều overdue issue | Kiểm tra blocker và ưu tiên xử lý issue quá hạn |
| Member có nhiều aging issue | Nhắc member cập nhật tình trạng hoặc chia nhỏ issue |
| Member có nhiều reopen issue | Review root cause: requirement, review, test hoặc implementation |
| Member có nhiều stale issue | Gửi reminder yêu cầu cập nhật trạng thái |
| Workload lệch lớn trong team | Cân nhắc redistribute issue ít ưu tiên |

---

## 6. Yêu cầu phi chức năng

| # | Danh mục | Yêu cầu |
|---|---|---|
| 1 | Hiệu năng | Load màn hình member với tối thiểu 5.000 issue trong vòng 10 giây |
| 2 | Bảo mật | Chỉ hiển thị dữ liệu thuộc project mà user có quyền xem |
| 3 | Tính sẵn sàng | Nếu thiếu dữ liệu journals/journal_details, vẫn hiển thị workload, overdue và stale update |
| 4 | Khả năng quan sát | Ghi log khi scan reminder, tạo reminder, đổi status reminder |
| 5 | Khả năng cấu hình | Cho phép cấu hình closed status, stale threshold, aging threshold, overload threshold |
| 6 | Tính minh bạch | UI phải hiển thị rõ chức năng này không dùng để đánh giá nhân sự chính thức |

---

## 7. Tiêu chí chấp nhận

| # | ID | Mô tả | Loại kiểm thử |
|---|---|---|---|
| 1 | MEMBER-AC-001/v1 | Hiển thị danh sách member trong project hiện tại | UI test |
| 2 | MEMBER-AC-002/v1 | Tính được Open Issue Count theo từng member | Unit test |
| 3 | MEMBER-AC-003/v1 | Tính được Estimated Workload theo từng member | Unit test |
| 4 | MEMBER-AC-004/v1 | Tính được Workload Share theo từng member | Unit test |
| 5 | MEMBER-AC-005/v1 | Tính được Overdue Issue Count theo từng member | Unit test |
| 6 | MEMBER-AC-006/v1 | Tính được Ticket Aging Count theo từng member | Unit test |
| 7 | MEMBER-AC-007/v1 | Tính được Stale Update Count theo từng member | Unit test |
| 8 | MEMBER-AC-008/v1 | Tính được Reopen Count theo từng member từ journals/journal_details | Unit / Integration test |
| 9 | MEMBER-AC-009/v1 | Tính được Member Work Risk Score và phân loại Good / Need Attention / High Risk | Unit test |
| 10 | MEMBER-AC-010/v1 | Hiển thị member detail khi chọn một member | UI test |
| 11 | MEMBER-AC-011/v1 | Detect được issue cần reminder theo rule đã định nghĩa | Unit test |
| 12 | MEMBER-AC-012/v1 | Hiển thị danh sách Issues Need Reminder | UI test |
| 13 | MEMBER-AC-013/v1 | Tạo được reminder record trong bảng member_reminders | Integration test |
| 14 | MEMBER-AC-014/v1 | Cập nhật được Reminder Status | Integration test |
| 15 | MEMBER-AC-015/v1 | Tự động chuyển reminder sang Resolved khi issue được update/xử lý | Integration test |
| 16 | MEMBER-AC-016/v1 | Sinh được reminder message từ template | Unit test |
| 17 | MEMBER-AC-017/v1 | Hiển thị suggested actions theo tình trạng member | Unit / UI test |
| 18 | MEMBER-AC-018/v1 | UI hiển thị ghi chú không dùng chức năng này để đánh giá nhân sự chính thức | UI test |

---

## 8. Ví dụ

### 8.1. Luồng bình thường

1. PL/PM mở màn hình Member Management & Reminder.
2. Hệ thống load danh sách member trong project hiện tại.
3. Hệ thống tính KPI theo từng member.
4. Hệ thống phân loại Member Work Risk.
5. PL/PM chọn một member.
6. Hệ thống hiển thị member detail và issue cần reminder.
7. PL/PM chọn issue và bấm Send Reminder.
8. Hệ thống tạo reminder record.
9. Reminder status chuyển sang Sent.
10. Sau khi member update issue, reminder chuyển sang Resolved.

### 8.2. Ví dụ output

```text
Member: Nguyen Van A
Status: Need Attention

Insights:
- Open issues: 14
- Estimated workload: 95h
- Overdue issues: 5
- Aging issues > 14 days: 3
- Reopened issues: 2
- Stale issues: 5

Suggested Actions:
1. Check blocker with Nguyen Van A.
2. Review overdue High/Critical issues.
3. Rebalance low-priority issues if needed.
4. Review reopened issues for root cause.
```

### 8.3. Luồng lỗi

1. Nếu không có dữ liệu member, hiển thị `No member data`.
2. Nếu issue không có assignee, nhóm vào `Unassigned`.
3. Nếu thiếu estimated_hours, hiển thị cảnh báo data quality.
4. Nếu không có journals/journal_details, không tính Reopen Count và hiển thị `N/A`.
5. Nếu không xác định được closed status, hiển thị lỗi cấu hình.

### 8.4. Trường hợp biên

1. Một issue có nhiều reminder: chỉ reminder active mới hiển thị ở danh sách chính.
2. Issue đã resolved: reminder active chuyển sang Resolved.
3. Issue bị snooze: không hiển thị lại cho đến khi hết `snoozed_until`.
4. Issue bị ignored: không tự động tạo reminder mới cho cùng reason trong kỳ hiện tại.
5. Member không còn issue open: Member Work Risk = Good nếu không có reminder active.
6. Issue priority High/Critical stale: severity = Critical.

---

## 9. Wireframe ASCII

### 9.1. Màn hình chính

```text
+------------------------------------------------------+
| Member Management & Reminder                         |
+------------------------------------------------------+
| Project: [Current Project]   Period: [This week ▼]   |
+------------------------------------------------------+
| Summary                                              |
| Members: 8 | Overloaded: 2 | Need Remind: 12 issues  |
+------------------------------------------------------+
| Member List                                          |
+--------+------+---------+-------+--------+------+------+
| Name   | Open | Overdue | Aging | Reopen | Load | Risk |
+--------+------+---------+-------+--------+------+------+
| A      | 14   | 5       | 3     | 2      | 95h  | Warn |
| B      | 6    | 0       | 1     | 0      | 35h  | Good |
| C      | 18   | 7       | 5     | 1      | 125h | High |
+------------------------------------------------------+
| Selected Member Detail                               |
| Member: A                                            |
| - Open issues: 14                                    |
| - Estimated workload: 95h                            |
| - Overdue issues: 5                                  |
| - Aging issues >14d: 3                               |
| - Reopened issues: 2                                 |
| - Stale issues: 5                                    |
+------------------------------------------------------+
| Issues Need Reminder                                 |
| ID  | Subject | Reason  | Last Update | Remind Status |
|101  | API bug | Overdue | 5 days ago  | Not Sent      |
|115  | UI fix  | Aging   | 12 days ago | Sent          |
+------------------------------------------------------+
| [Send Reminder] [Mark Acknowledged] [Snooze] [Ignore]|
+------------------------------------------------------+
```

### 9.2. Reminder Detail

```text
+------------------------------------------------------+
| Reminder Detail                                      |
+------------------------------------------------------+
| Issue: #101 API bug                                |
| Member: A                                            |
| Reason: Overdue                                      |
| Severity: Warning                                    |
| Due date: 2026-05-01                                 |
| Last update: 2026-05-05                              |
+------------------------------------------------------+
| Message Preview                                      |
| Hi A,                                                |
| Please update issue #101 API bug.                  |
| Reason: Overdue                                      |
| Please update status, blocker, or expected date.     |
+------------------------------------------------------+
| [Send] [Edit Message] [Cancel]                       |
+------------------------------------------------------+
```

---

## 10. Các vấn đề mở

| # | Câu hỏi | Người phụ trách | Hạn chót |
|---|---|---|---|
| OI-1 | Reminder có cần gửi thật qua email/chat ở MVP không? | PM / Dev Lead | [MISSING] |
| OI-2 | Closed status chính thức của project là gì? | PM / Redmine Admin | status_id in(3,4,5) |
| OI-3 | Ngưỡng stale update là 3 ngày hay theo cấu hình project? | PM / PL | [MISSING] |
| OI-4 | Ngưỡng workload 80h/120h có phù hợp với capacity thực tế không? | PM / PL | `overload_warning_hours = 160`, `overload_critical_hours = 200` |
| OI-5 | Member Work Risk có cần lưu snapshot theo tuần không? | PM / Dev Lead | [MISSING] |
| OI-6 | Reminder status Acknowledged được cập nhật thủ công hay tự động từ phản hồi member? | PM / Dev Lead | [MISSING] |
| OI-7 | Có cần phân quyền Admin/PM/Viewer cho thao tác reminder không? | PM / Dev Lead | [MISSING] |

---

## 11. Rủi ro

| # | Rủi ro | Khả năng xảy ra | Mức độ ảnh hưởng | Biện pháp giảm thiểu |
|---|---|---|---|---|
| 1 | Chức năng bị hiểu sai là đánh giá năng lực cá nhân | Trung bình | Cao | Ghi rõ mục tiêu là hỗ trợ workload và reminder, không dùng để đánh giá nhân sự |
| 2 | estimated_hours thiếu làm workload không chính xác | Cao | Trung bình | Fallback sang Open Issue Count và hiển thị data quality warning |
| 3 | Thiếu journals/journal_details làm Reopen Count không chính xác | Trung bình | Trung bình | Hiển thị `N/A` và ghi log thiếu dữ liệu |
| 4 | Reminder quá nhiều gây noise cho member | Trung bình | Trung bình | Hỗ trợ severity, snooze và ignore |
| 5 | Ngưỡng risk không phù hợp với từng project | Trung bình | Trung bình | Cho phép cấu hình threshold |
| 6 | PL/PM quên xử lý reminder đã gửi | Trung bình | Trung bình | Hiển thị reminder status và danh sách reminder active |

---

## Bảng truy vết

| # | AC | Màn hình/API | DB | Logs | Quyền | Loại kiểm thử |
|---|---|---|---|---|---|---|
| 1 | MEMBER-AC-001/v1 | Member Management screen | issues, users | Query log | Viewer | UI test |
| 2 | MEMBER-AC-002/v1 | Member KPI API | issues | Calculation log | Viewer | Unit test |
| 3 | MEMBER-AC-003/v1 | Member KPI API | issues | Calculation log | Viewer | Unit test |
| 4 | MEMBER-AC-004/v1 | Member KPI API | issues | Calculation log | Viewer | Unit test |
| 5 | MEMBER-AC-005/v1 | Member KPI API | issues | Calculation log | Viewer | Unit test |
| 6 | MEMBER-AC-006/v1 | Member KPI API | issues, journals, journal_details | Calculation log | Viewer | Unit test |
| 7 | MEMBER-AC-007/v1 | Member KPI API | issues | Calculation log | Viewer | Unit test |
| 8 | MEMBER-AC-008/v1 | Member KPI API | issues, journals, journal_details | Calculation log | Viewer | Unit / Integration test |
| 9 | MEMBER-AC-009/v1 | Member KPI API | issues, users | Calculation log | Viewer | Unit test |
| 10 | MEMBER-AC-010/v1 | Member Detail panel | issues, users | Query log | Viewer | UI test |
| 11 | MEMBER-AC-011/v1 | Reminder Detection API | issues, journals, journal_details | Reminder scan log | Viewer | Unit test |
| 12 | MEMBER-AC-012/v1 | Issues Need Reminder panel | issues, member_reminders | Query log | Viewer | UI test |
| 13 | MEMBER-AC-013/v1 | Create Reminder API | member_reminders | Reminder create log | PM / PL | Integration test |
| 14 | MEMBER-AC-014/v1 | Update Reminder API | member_reminders | Reminder update log | PM / PL | Integration test |
| 15 | MEMBER-AC-015/v1 | Reminder Resolve Job/API | member_reminders, issues | Reminder resolve log | System | Integration test |
| 16 | MEMBER-AC-016/v1 | Reminder Message Generator | member_reminders | Message generate log | PM / PL | Unit test |
| 17 | MEMBER-AC-017/v1 | Suggested Actions panel | issues, member_reminders | Suggestion log | Viewer | Unit / UI test |
| 18 | MEMBER-AC-018/v1 | Member Management screen | [MISSING] | [MISSING] | Viewer | UI test |
