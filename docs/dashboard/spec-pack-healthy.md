# Gói đặc tả — [MISSING] (Project Health)

> Tạo: [MISSING] · Giai đoạn: [MISSING]  
> **Nguồn tham chiếu duy nhất cho thay đổi này.**  
> Không triển khai bất kỳ nội dung nào không được viết ở đây. Các điểm chưa rõ → Open Issues.

---

## 1. Bối cảnh / Mục đích

Tính **sức khỏe dự án (Project Health)** dựa trên dữ liệu có thể lấy từ Redmine.

Redmine không có sẵn một chỉ số chuẩn gọi là “Project Health”, vì vậy cần tổng hợp nhiều chỉ số như tiến độ, issue, bug, trễ hạn và effort để đánh giá tình trạng dự án.

## 2. Phạm vi

### Trong phạm vi
- Sử dụng các trường Redmine: `% Done`, `Status`, `Target version`, `Start date`, `Due date`, `Tracker`, `Priority`, `Estimated hours`, `Spent hours`, `Assignee`, `Updated`, `Created`.
- Tính các chỉ số:
  - Tiến độ so với deadline
  - Tỷ lệ issue đã đóng
  - Issue quá hạn
  - Bug / Defect còn mở
  - Effort: Estimated hours so với Spent hours
  - Issue không được cập nhật lâu
- Tính Project Health Score tối đa 12 điểm.
- Phân loại sức khỏe dự án theo Green / Yellow / Red.
- Gợi ý hành động theo trạng thái Green / Yellow / Red.
- Cung cấp template báo cáo ngắn.

### Ngoài phạm vi

- [MISSING]

## 3. Thuật ngữ

| #   | Thuật ngữ | Định nghĩa |
| --- | --------- | ---------- |
| 1   | Project Health | Chỉ số sức khỏe dự án được tổng hợp từ nhiều chỉ số như tiến độ, issue, bug, trễ hạn và effort |
| 2   | Planned Progress (%) | `Số ngày đã trôi qua / Tổng số ngày kế hoạch * 100` |
| 3   | Actual Progress (%) | Trung bình `% Done` của các issue |
| 4   | Schedule Gap (%) | `Actual Progress - Planned Progress` |
| 5   | Closed Rate (%) | `Số issue đã đóng / Tổng số issue * 100` |
| 6   | Overdue Issue | Issue chưa đóng và `Due date < ngày hiện tại` |
| 7   | Overdue Rate (%) | `Số issue quá hạn / Tổng số issue chưa đóng * 100` |
| 8   | Open Bug Rate (%) | `Số bug chưa đóng / Tổng số issue chưa đóng * 100` |
| 9   | Effort Ratio (%) | `Spent hours / Estimated hours * 100` |
| 10  | Stale Issue | Issue chưa đóng và `Updated` quá 7 ngày |
| 11  | Stale Rate (%) | `Số stale issue / Tổng số issue chưa đóng * 100` |

## 4. Hiện trạng / Trạng thái mục tiêu

| #   | Khía cạnh | Hiện trạng | Trạng thái mục tiêu |
| --- | --------- | ---------- | ------------------- |
| 1   | Chỉ số Project Health trong Redmine | Redmine không có sẵn một chỉ số chuẩn gọi là “Project Health” | Tổng hợp nhiều chỉ số từ dữ liệu Redmine để đánh giá tình trạng dự án |
| 2   | Dữ liệu đầu vào | Có thể lấy dữ liệu từ issues | Sử dụng các trường Redmine được liệt kê trong tài liệu |
| 3   | Đánh giá theo thời gian | [MISSING] | Nên theo dõi theo tuần để thấy xu hướng |

## 5. Chi tiết đặc tả

### 5.1. Dữ liệu đầu vào

Có thể lấy dữ liệu bằng cách export issue từ Redmine ra CSV hoặc Excel.

| Nhóm dữ liệu | Trường Redmine |
|---|---|
| Tiến độ | `% Done`, `Status`, `Target version` |
| Kế hoạch | `Start date`, `Due date` |
| Loại công việc | `Tracker` |
| Ưu tiên | `Priority` |
| Effort | `Estimated hours`, `Spent hours` |
| Người phụ trách | `Assignee` |
| Trạng thái | `Status` |
| Ngày cập nhật | `Updated` |
| Ngày tạo | `Created` |

### 5.2. Tiến độ so với deadline

Ý nghĩa: đánh giá dự án đang đi đúng tiến độ hay bị chậm so với kế hoạch.

Cách tính:

```text
Planned Progress (%) = Số ngày đã trôi qua / Tổng số ngày kế hoạch * 100
Actual Progress (%) = Trung bình % Done của các issue
Schedule Gap (%) = Actual Progress - Planned Progress
```

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Actual Progress >= Planned Progress | 2 |
| Actual Progress chậm hơn kế hoạch <= 10% | 1 |
| Actual Progress chậm hơn kế hoạch > 10% | 0 |

### 5.3. Tỷ lệ issue đã đóng

Ý nghĩa: đánh giá mức độ hoàn thành công việc.

Cách tính:

```text
Closed Rate (%) = Số issue đã đóng / Tổng số issue * 100
```

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Closed Rate >= 80% | 2 |
| Closed Rate từ 50% đến dưới 80% | 1 |
| Closed Rate < 50% | 0 |

### 5.4. Issue quá hạn

Ý nghĩa: đánh giá mức độ kiểm soát deadline.

Cách tính:

```text
Overdue Issue = Issue chưa đóng và Due date < ngày hiện tại
Overdue Rate (%) = Số issue quá hạn / Tổng số issue chưa đóng * 100
```

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Overdue Rate = 0% | 2 |
| Overdue Rate <= 10% | 1 |
| Overdue Rate > 10% | 0 |

### 5.5. Bug / Defect còn mở

Ý nghĩa: đánh giá chất lượng dự án.

Cách tính:

```text
Open Bug Rate (%) = Số bug chưa đóng / Tổng số issue chưa đóng * 100
```

Trong Redmine, bug thường được xác định bằng `Tracker = Bug` hoặc `Tracker = Defect`.

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Open Bug Rate <= 10% | 2 |
| Open Bug Rate từ trên 10% đến 25% | 1 |
| Open Bug Rate > 25% | 0 |

### 5.6. Effort: Estimated hours so với Spent hours

Ý nghĩa: đánh giá độ chính xác của estimate và nguy cơ vượt effort.

Cách tính:

```text
Effort Ratio (%) = Spent hours / Estimated hours * 100
```

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Effort Ratio <= 100% | 2 |
| Effort Ratio từ trên 100% đến 120% | 1 |
| Effort Ratio > 120% | 0 |

Lưu ý: nếu `Estimated hours` bị thiếu nhiều, chỉ số này không đáng tin cậy.

### 5.7. Issue không được cập nhật lâu

Ý nghĩa: phát hiện issue có nguy cơ bị bỏ quên.

Cách tính:

```text
Stale Issue = Issue chưa đóng và Updated quá 7 ngày
Stale Rate (%) = Số stale issue / Tổng số issue chưa đóng * 100
```

Cách chấm điểm:

| Điều kiện | Điểm |
|---|---:|
| Stale Rate <= 5% | 2 |
| Stale Rate từ trên 5% đến 15% | 1 |
| Stale Rate > 15% | 0 |

### 5.8. Công thức tính Project Health Score

Tổng điểm tối đa: **12 điểm**

```text
Project Health Score =
  Điểm tiến độ
+ Điểm tỷ lệ issue đã đóng
+ Điểm issue quá hạn
+ Điểm bug còn mở
+ Điểm effort
+ Điểm issue không cập nhật lâu
```

### 5.9. Phân loại sức khỏe dự án

| Tổng điểm | Trạng thái | Ý nghĩa |
|---:|---|---|
| 10 - 12 | Green | Dự án khỏe, đang được kiểm soát tốt |
| 7 - 9 | Yellow | Có rủi ro, cần theo dõi sát |
| 0 - 6 | Red | Dự án có vấn đề nghiêm trọng, cần hành động ngay |

### 5.10. Gợi ý hành động theo trạng thái

#### Green

- Tiếp tục theo dõi định kỳ.
- Giữ nhịp update issue.
- Không cần escalation.

#### Yellow

- Review các issue quá hạn.
- Kiểm tra lại estimate.
- Ưu tiên xử lý bug đang mở.
- Yêu cầu assignee update issue chưa cập nhật lâu.
- Báo cáo rủi ro cho PM / BrSE / khách hàng nếu cần.

#### Red

- Tổ chức meeting review tình trạng dự án.
- Xác định nguyên nhân chính: scope, effort, bug, resource hay estimate.
- Re-plan schedule nếu cần.
- Escalate sớm cho stakeholder.
- Tập trung xử lý blocker và issue quá hạn.

### 5.11. Lưu ý khi áp dụng

- Không nên đánh giá sức khỏe dự án chỉ bằng một snapshot.
- Nên theo dõi theo tuần để thấy xu hướng.
- Cùng một điểm số nhưng xu hướng khác nhau sẽ có ý nghĩa khác nhau:
  - Điểm 8 và đang tăng: tình hình tốt lên.
  - Điểm 8 nhưng đang giảm: cần cảnh giác.
- Redmine chỉ cung cấp dữ liệu, còn việc đánh giá phụ thuộc vào quy chuẩn của team.
- Nên thống nhất cách tính với PM / BrSE / Leader trước khi dùng làm báo cáo chính thức.

### 5.12. Template báo cáo ngắn

```text
Project Health: Green / Yellow / Red
Score: X / 12

Summary:
- Progress:
- Closed Rate:
- Overdue:
- Bug:
- Effort:
- Stale Issue:

Main Risks:
1.
2.
3.

Actions:
1.
2.
3.
```

## 6. Yêu cầu phi chức năng

| #   | Danh mục          | Yêu cầu |
| --- | ----------------- | ------- |
| 1   | Hiệu năng         | [MISSING] |
| 2   | Bảo mật           | [MISSING] |
| 3   | Tính sẵn sàng     | [MISSING] |
| 4   | Khả năng quan sát | Nên theo dõi theo tuần để thấy xu hướng |

## 7. Tiêu chí chấp nhận

| #   | ID                | Mô tả | Loại kiểm thử |
| --- | ----------------- | ----- | ------------- |
| 1   | HEALTH-AC-001/v1 | Tính được Planned Progress, Actual Progress và Schedule Gap từ dữ liệu Redmine | [MISSING] |
| 2   | HEALTH-AC-002/v1 | Chấm điểm tiến độ so với deadline theo điều kiện đã định nghĩa | [MISSING] |
| 3   | HEALTH-AC-003/v1 | Tính được Closed Rate và chấm điểm theo điều kiện đã định nghĩa | [MISSING] |
| 4   | HEALTH-AC-004/v1 | Tính được Overdue Rate từ issue chưa đóng có Due date nhỏ hơn ngày hiện tại và chấm điểm theo điều kiện đã định nghĩa | [MISSING] |
| 5   | HEALTH-AC-005/v1 | Tính được Open Bug Rate với bug xác định bằng `Tracker = Bug` hoặc `Tracker = Defect` và chấm điểm theo điều kiện đã định nghĩa | [MISSING] |
| 6   | HEALTH-AC-006/v1 | Tính được Effort Ratio và chấm điểm theo điều kiện đã định nghĩa | [MISSING] |
| 7   | HEALTH-AC-007/v1 | Tính được Stale Rate với issue chưa đóng và `Updated` quá 7 ngày, sau đó chấm điểm theo điều kiện đã định nghĩa | [MISSING] |
| 8   | HEALTH-AC-008/v1 | Tính Project Health Score bằng tổng 6 điểm thành phần, tối đa 12 điểm | [MISSING] |
| 9   | HEALTH-AC-009/v1 | Phân loại Project Health thành Green, Yellow hoặc Red theo tổng điểm | [MISSING] |
| 10  | HEALTH-AC-010/v1 | Hiển thị hoặc xuất được template báo cáo ngắn gồm Project Health, Score, Summary, Main Risks và Actions | [MISSING] |

## 8. Ví dụ

### Các luồng bình thường

1. Export issue từ Redmine ra CSV hoặc Excel.
2. Tính các chỉ số: Progress, Closed Rate, Overdue, Bug, Effort, Stale Issue.
3. Cộng điểm các chỉ số để tính Project Health Score.
4. Phân loại Project Health theo Green / Yellow / Red.
5. Điền kết quả vào template báo cáo ngắn.

Ví dụ dữ liệu:

| Chỉ số | Kết quả | Điểm |
|---|---:|---:|
| Tiến độ thực tế chậm hơn kế hoạch 5% | Warning | 1 |
| Closed Rate = 70% | Warning | 1 |
| Overdue Rate = 8% | Warning | 1 |
| Open Bug Rate = 12% | Warning | 1 |
| Effort Ratio = 110% | Warning | 1 |
| Stale Rate = 4% | Good | 2 |

```text
Project Health Score = 1 + 1 + 1 + 1 + 1 + 2 = 7
```

Kết luận:

```text
Health = Yellow
```

Dự án chưa đến mức nguy hiểm, nhưng có nhiều dấu hiệu cần theo dõi.

### Các luồng lỗi

1. Nếu `Estimated hours` bị thiếu nhiều, chỉ số Effort Ratio không đáng tin cậy.
2. [MISSING]

### Các trường hợp biên

1. Cùng một điểm số nhưng xu hướng khác nhau sẽ có ý nghĩa khác nhau:
   - Điểm 8 và đang tăng: tình hình tốt lên.
   - Điểm 8 nhưng đang giảm: cần cảnh giác.
2. [MISSING]

## 9. Wireframe ASCII (Tùy chọn)

[MISSING]

### Tên màn hình / luồng

```text
[MISSING]
```

### Ghi chú

- Các trạng thái chính: Green / Yellow / Red
- Thông điệp xác thực / lỗi: [MISSING]
- Lưu ý về responsive hoặc mobile: [MISSING]

## 10. Các vấn đề mở

| #    | Câu hỏi | Người phụ trách | Hạn chót |
| ---- | ------- | --------------- | -------- |
| OI-1 | Chưa có thông tin ticket ID, ngày tạo và giai đoạn | [MISSING] | [MISSING] |
| OI-2 | Chưa xác định ngoài phạm vi | [MISSING] | [MISSING] |
| OI-3 | Chưa xác định cách phân biệt issue đã đóng ngoài trường `Status` | [MISSING] | [MISSING] |
| OI-4 | Chưa xác định quy chuẩn team dùng để đánh giá chính thức | [MISSING] | [MISSING] |
| OI-5 | Chưa có thông tin API, DB, logs hoặc permission cho chức năng này | [MISSING] | [MISSING] |

## 11. Rủi ro

| #   | Rủi ro | Khả năng xảy ra | Mức độ ảnh hưởng | Biện pháp giảm thiểu |
| --- | ------ | --------------- | ---------------- | -------------------- |
| 1   | Nếu `Estimated hours` bị thiếu nhiều, chỉ số Effort Ratio không đáng tin cậy | [MISSING] | [MISSING] | [MISSING] |
| 2   | Đánh giá sức khỏe dự án chỉ bằng một snapshot có thể không phản ánh xu hướng | [MISSING] | [MISSING] | Nên theo dõi theo tuần để thấy xu hướng |
| 3   | Redmine chỉ cung cấp dữ liệu, còn việc đánh giá phụ thuộc vào quy chuẩn của team | [MISSING] | [MISSING] | Nên thống nhất cách tính với PM / BrSE / Leader trước khi dùng làm báo cáo chính thức |

---

## Bảng truy vết

| #   | AC                | Màn hình/API | DB  | Logs | Quyền | Loại kiểm thử |
| --- | ----------------- | ------------ | --- | ---- | ----- | ------------- |
| 1   | HEALTH-AC-001/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 2   | HEALTH-AC-002/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 3   | HEALTH-AC-003/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 4   | HEALTH-AC-004/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 5   | HEALTH-AC-005/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 6   | HEALTH-AC-006/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 7   | HEALTH-AC-007/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 8   | HEALTH-AC-008/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 9   | HEALTH-AC-009/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
| 10  | HEALTH-AC-010/v1 | [MISSING] | [MISSING] | [MISSING] | [MISSING] | [MISSING] |
