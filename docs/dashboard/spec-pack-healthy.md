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
  - Tỷ lệ issue đã đóng(nếu chưa close thì nếu issue có status_id =3 thì cũng xem như issue đã đóng)
  - Issue quá hạn
  - Bug / Defect còn mở
  - Effort: Estimated hours so với Spent hours
  - Issue không được cập nhật lâu
- Tính Project Health Score tối đa 12 điểm.
- Phân loại sức khỏe dự án theo Green / Yellow / Red.
- Gợi ý hành động theo trạng thái Green / Yellow / Red.
- Cung cấp template báo cáo ngắn.
- Theo dõi Health Trend theo ngày/tuần.
- Phân tích nguyên nhân chính khiến score thấp hoặc giảm.
- Phát hiện cảnh báo sớm dựa trên rule.
- Đề xuất hành động cụ thể dựa trên risk driver.
- Cho phép cấu hình threshold, weight, closed status và bug tracker.
- Hiển thị dashboard nhiều dự án và drill-down issue rủi ro.

### Ngoài phạm vi

- Tự động thay đổi dữ liệu trong Redmine.
- Tự động assign/reassign issue trên Redmine.
- Thay thế quyết định của PM / BrSE / Leader.
- Dự đoán chính xác ngày hoàn thành dự án bằng AI/ML nâng cao.
- Tích hợp trực tiếp API Redmine ở giai đoạn đầu nếu MVP chỉ dùng sử dụng dữ liệu đã được đồng bộ từ Redmine về DB local.

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
| 3   | Đánh giá theo thời gian | Chưa có lịch sử điểm health theo ngày/tuần | Theo dõi theo tuần để thấy xu hướng tăng/giảm của Project Health |
| 4   | Phân tích nguyên nhân | Chưa chỉ ra nguyên nhân chính khiến điểm thấp | Xác định top risk drivers theo assignee, tracker/module, overdue, bug, effort |
| 5   | Đề xuất hành động | Chỉ có gợi ý chung theo Green/Yellow/Red | Đề xuất hành động cụ thể dựa trên dữ liệu rủi ro |
| 6   | Cảnh báo sớm | Chỉ đánh giá sau khi tính score | Phát hiện xu hướng xấu trước khi dự án chuyển sang Red |
| 7   | Cấu hình scoring | Công thức/ngưỡng đang cố định | Cho phép cấu hình status closed, tracker bug, threshold và trọng số metric |

## 5. Chi tiết đặc tả

### 5.1. Dữ liệu đầu vào

Dữ liệu issue được đồng bộ định kỳ từ Redmine về DB local và sử dụng trực tiếp từ DB.

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

### 5.13. Health Trend

Ý nghĩa: theo dõi sự thay đổi sức khỏe dự án theo thời gian thay vì chỉ đánh giá tại một thời điểm.

#### Dữ liệu cần lưu

Mỗi lần import dữ liệu Redmine và tính health, hệ thống cần lưu lại snapshot:

| Trường | Ý nghĩa |
|---|---|
| Snapshot date | Ngày tính health |
| Project ID / Project name | Dự án được đánh giá |
| Health score | Tổng điểm |
| Health status | Green / Yellow / Red |
| Metric scores | Điểm từng chỉ số thành phần |
| Main risk drivers | Các nguyên nhân chính tại thời điểm đó |

#### Cách đánh giá trend

```text
Health Trend = Score hiện tại - Score kỳ trước
```

| Điều kiện | Ý nghĩa |
|---|---|
| Health Trend > 0 | Dự án đang cải thiện |
| Health Trend = 0 | Dự án ổn định |
| Health Trend < 0 | Dự án đang xấu đi |

#### Cảnh báo theo trend

| Điều kiện | Mức cảnh báo |
|---|---|
| Score giảm 2 kỳ liên tiếp | Warning |
| Score giảm từ Green xuống Yellow | Warning |
| Score giảm từ Yellow xuống Red | Critical |
| Score <= 6 trong 2 kỳ liên tiếp | Critical |

### 5.14. Root Cause Analysis

Ý nghĩa: xác định nguyên nhân chính khiến Project Health thấp hoặc giảm.

Hệ thống cần phân tích các issue rủi ro theo:

- Assignee
- Tracker
- Target version
- Priority
- Issue overdue
- Issue vượt effort
- Issue không cập nhật lâu
- Bug / Defect còn mở

#### Output ví dụ

```text
Main Risk Drivers:
1. 40% overdue issues thuộc về assignee A
2. 60% open bugs thuộc tracker/module Payment
3. 3 issues có Effort Ratio > 150%
4. 12 issues chưa được cập nhật quá 7 ngày
```

#### Quy tắc chọn top risk drivers

- Ưu tiên metric có điểm thấp nhất.
- Trong mỗi metric, lấy nhóm issue có tỷ trọng cao nhất.
- Chỉ hiển thị tối đa top 3 đến top 5 risk drivers.
- Mỗi risk driver cần có số lượng issue cụ thể và tỷ lệ phần trăm nếu tính được.

### 5.15. Early Warning System

Ý nghĩa: phát hiện rủi ro trước khi Project Health chuyển sang Red.

| # | Điều kiện | Mức cảnh báo |
|---|---|---|
| 1 | Progress không tăng trong 5 ngày làm việc | Warning |
| 2 | Overdue Rate tăng 2 kỳ liên tiếp | Warning |
| 3 | Bug Rate tăng hơn 20% so với kỳ trước | Warning |
| 4 | Effort Ratio vượt 120% | Critical |
| 5 | Health Score giảm từ Green xuống Yellow | Warning |
| 6 | Health Score giảm từ Yellow xuống Red | Critical |
| 7 | Stale Rate vượt 15% | Warning |
| 8 | Issue Priority High/Critical bị overdue | Critical |

### 5.16. Smart Action Suggestion

Ý nghĩa: hệ thống không chỉ báo dự án có vấn đề mà còn gợi ý hành động cụ thể.

| Rủi ro | Hành động đề xuất |
|---|---|
| Overdue Rate cao | Review danh sách issue quá hạn, ưu tiên issue High/Critical |
| Bug Rate cao | Tập trung fix bug theo module/tracker có nhiều bug nhất |
| Effort Ratio cao | Review lại estimate và scope của các issue vượt effort |
| Stale Rate cao | Yêu cầu assignee cập nhật issue chưa update lâu |
| Progress chậm | Re-plan schedule hoặc chia nhỏ issue lớn |
| Một assignee có quá nhiều overdue | Review workload và cân nhắc hỗ trợ/reassign |

#### Output ví dụ

```text
Suggested Actions:
1. Review 8 overdue issues, trong đó có 2 issue Priority High.
2. Ưu tiên xử lý module Payment vì chiếm 60% open bugs.
3. Yêu cầu assignee A cập nhật 5 stale issues.
4. Review estimate cho 3 issues có Effort Ratio > 150%.
```

### 5.17. Configurable Scoring Engine

Ý nghĩa: mỗi team/project có quy ước Redmine khác nhau, nên hệ thống cần cho phép cấu hình.

| Nhóm cấu hình | Nội dung |
|---|---|
| Closed status | Status nào được xem là đã đóng |
| Bug tracker | Tracker nào được xem là Bug/Defect |
| Stale threshold | Số ngày không update để xem là stale |
| Overdue threshold | Ngưỡng overdue để phân loại điểm |
| Effort threshold | Ngưỡng effort vượt estimate |
| Metric weight | Trọng số từng chỉ số |
| Health status threshold | Ngưỡng Green / Yellow / Red |

#### Quy tắc mặc định

- Closed issue: issue có status là Closed hoặc `status_id = 3`.
- Bug issue: `Tracker = Bug` hoặc `Tracker = Defect`.
- Stale issue: issue chưa đóng và không update quá 7 ngày.
- Score mặc định: 6 metric, mỗi metric tối đa 2 điểm, tổng tối đa 12 điểm.

#### Công thức có trọng số tùy chọn

```text
Weighted Health Score =
  Progress Score * Progress Weight
+ Closed Rate Score * Closed Rate Weight
+ Overdue Score * Overdue Weight
+ Bug Score * Bug Weight
+ Effort Score * Effort Weight
+ Stale Score * Stale Weight
```

Nếu chưa cấu hình weight, hệ thống dùng công thức mặc định tổng 12 điểm.

### 5.18. Multi-project Dashboard

Ý nghĩa: giúp PM/Manager nhìn nhanh sức khỏe của nhiều dự án.

| Trường | Ý nghĩa |
|---|---|
| Project name | Tên dự án |
| Health score | Điểm hiện tại |
| Health status | Green / Yellow / Red |
| Trend | Tăng / giảm / không đổi |
| Main risk | Rủi ro lớn nhất |
| Last updated | Thời điểm import/tính toán gần nhất |

#### Output ví dụ

```text
Project A: 10/12 Green  Trend +1  Main risk: None
Project B: 7/12  Yellow Trend -2  Main risk: Overdue
Project C: 5/12  Red    Trend -1  Main risk: Bug Rate
```

### 5.19. Drill-down

Ý nghĩa: từ dashboard tổng quan có thể xem danh sách issue gây rủi ro.

- Click Overdue → xem danh sách issue quá hạn.
- Click Bug Rate → xem danh sách bug/defect còn mở.
- Click Effort Ratio → xem issue vượt estimate.
- Click Stale Rate → xem issue chưa update lâu.
- Click Assignee → xem risk theo từng người phụ trách.
- Click Target version → xem risk theo version/milestone.

| Trường | Ý nghĩa |
|---|---|
| Issue ID | ID issue Redmine |
| Subject | Tiêu đề issue |
| Tracker | Loại issue |
| Status | Trạng thái |
| Priority | Độ ưu tiên |
| Assignee | Người phụ trách |
| Due date | Deadline |
| % Done | Tiến độ |
| Estimated hours | Estimate |
| Spent hours | Thực tế |
| Updated | Ngày cập nhật cuối |
| Risk reason | Lý do issue bị xem là rủi ro |


## 6. Yêu cầu phi chức năng

| #   | Danh mục          | Yêu cầu |
| --- | ----------------- | ------- |
| 1   | Hiệu năng         | Tính toán trên dữ liệu DB local tối thiểu 5.000 issue trong vòng 10 giây đối với file CSV/Excel thông thường |
| 2   | Bảo mật           | Không lưu mật khẩu Redmine; nếu tích hợp API thì token phải được mã hóa hoặc lưu bằng cơ chế bảo mật của hệ thống |
| 3   | Tính sẵn sàng     | Nếu import file lỗi, hệ thống phải hiển thị thông báo lỗi rõ ràng và không làm mất dữ liệu snapshot cũ |
| 4   | Khả năng quan sát | Theo dõi theo tuần để thấy xu hướng; lưu log import, thời điểm tính score và lỗi validate dữ liệu |
| 5   | Khả năng cấu hình | Cho phép cấu hình status closed, tracker bug, threshold, weight và ngưỡng Green/Yellow/Red |
| 6   | Tính dễ sử dụng   | Dashboard cần hiển thị health, trend, main risks và suggested actions trong một màn hình chính |

## 7. Tiêu chí chấp nhận

| #   | ID                | Mô tả | Loại kiểm thử |
| --- | ----------------- | ----- | ------------- |
| 1   | HEALTH-AC-001/v1 | Tính được Planned Progress, Actual Progress và Schedule Gap từ dữ liệu Redmine | Unit test |
| 2   | HEALTH-AC-002/v1 | Chấm điểm tiến độ so với deadline theo điều kiện đã định nghĩa | Unit test |
| 3   | HEALTH-AC-003/v1 | Tính được Closed Rate và chấm điểm theo điều kiện đã định nghĩa | Unit test |
| 4   | HEALTH-AC-004/v1 | Tính được Overdue Rate từ issue chưa đóng có Due date nhỏ hơn ngày hiện tại và chấm điểm theo điều kiện đã định nghĩa | Unit test |
| 5   | HEALTH-AC-005/v1 | Tính được Open Bug Rate với bug xác định bằng `Tracker = Bug` hoặc `Tracker = Defect` và chấm điểm theo điều kiện đã định nghĩa | Unit test |
| 6   | HEALTH-AC-006/v1 | Tính được Effort Ratio và chấm điểm theo điều kiện đã định nghĩa | Unit test |
| 7   | HEALTH-AC-007/v1 | Tính được Stale Rate với issue chưa đóng và `Updated` quá 7 ngày, sau đó chấm điểm theo điều kiện đã định nghĩa | Unit test |
| 8   | HEALTH-AC-008/v1 | Tính Project Health Score bằng tổng 6 điểm thành phần, tối đa 12 điểm | Unit test |
| 9   | HEALTH-AC-009/v1 | Phân loại Project Health thành Green, Yellow hoặc Red theo tổng điểm | Unit test |
| 10  | HEALTH-AC-010/v1 | Hiển thị hoặc xuất được template báo cáo ngắn gồm Project Health, Score, Summary, Main Risks và Actions | UI / Export test |
| 11  | HEALTH-AC-011/v1 | Lưu được snapshot health theo ngày/tuần để tính Health Trend | Integration test |
| 12  | HEALTH-AC-012/v1 | Hiển thị được Health Trend tăng/giảm/không đổi so với kỳ trước | UI test |
| 13  | HEALTH-AC-013/v1 | Xác định được top 3 risk drivers dựa trên metric có điểm thấp và nhóm issue liên quan | Unit / Integration test |
| 14  | HEALTH-AC-014/v1 | Phát hiện được cảnh báo sớm theo các rule đã định nghĩa | Unit test |
| 15  | HEALTH-AC-015/v1 | Sinh được Suggested Actions dựa trên loại rủi ro phát hiện được | Unit / UI test |
| 16  | HEALTH-AC-016/v1 | Cho phép cấu hình closed status, bug tracker, threshold và metric weight | UI / Integration test |
| 17  | HEALTH-AC-017/v1 | Hiển thị được dashboard nhiều dự án với health, trend, main risk và last updated | UI test |
| 18  | HEALTH-AC-018/v1 | Cho phép drill-down từ metric rủi ro đến danh sách issue liên quan | UI / Integration test |

## 8. Ví dụ

### Các luồng bình thường

1. Dữ liệu issue đã được đồng bộ từ Redmine về DB local.
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

1. Nếu `Estimated hours` bị thiếu nhiều, chỉ số Effort Ratio không đáng tin cậy và cần hiển thị cảnh báo dữ liệu thiếu.
2. Nếu file import thiếu cột bắt buộc, hệ thống phải báo rõ tên cột bị thiếu.
3. Nếu dữ liệu ngày không đúng format, hệ thống bỏ qua dòng lỗi và ghi vào import log.
4. Nếu không có issue nào, hệ thống hiển thị trạng thái không đủ dữ liệu thay vì tính score sai.
5. Nếu không có dữ liệu kỳ trước, hệ thống không tính trend và hiển thị `No previous snapshot`.

### Các trường hợp biên

1. Cùng một điểm số nhưng xu hướng khác nhau sẽ có ý nghĩa khác nhau:
   - Điểm 8 và đang tăng: tình hình tốt lên.
   - Điểm 8 nhưng đang giảm: cần cảnh giác.
2. Issue không có Due date: không tính vào overdue nhưng vẫn hiển thị cảnh báo dữ liệu thiếu nếu tỷ lệ thiếu cao.
3. Issue không có Estimated hours: không tính vào Effort Ratio.
4. Project mới bắt đầu: Planned Progress có thể rất thấp, cần tránh chia cho 0 khi Start date = Due date.
5. Project đã quá Due date: Planned Progress được giới hạn tối đa 100%.
6. Issue đã đóng nhưng % Done chưa đạt 100%: ưu tiên status closed để xác định hoàn thành.

## 9. Wireframe ASCII (Tùy chọn)

### 9.1. Dashboard tổng quan

```text
+------------------------------------------------------+
| Project Health Analyzer                              |
+------------------------------------------------------+
| Project: [Project A v]      Last Updated: 2026-05-05 |
+------------------------------------------------------+
| Health: YELLOW              Score: 7 / 12            |
| Trend: -2 vs last week      Main Risk: Overdue       |
+------------------------------------------------------+
| Metrics                                              |
| Progress       [1/2]  Actual 55% / Planned 60%       |
| Closed Rate    [1/2]  70%                            |
| Overdue        [1/2]  8%                             |
| Bug Rate       [1/2]  12%                            |
| Effort         [1/2]  110%                           |
| Stale Issue    [2/2]  4%                             |
+------------------------------------------------------+
| Health Trend                                         |
| Week-3: 9 Green -> Week-2: 8 Green -> Week-1: 7 Yellow|
+------------------------------------------------------+
| Main Risk Drivers                                    |
| 1. 8 overdue issues                                  |
| 2. 60% bugs in Payment module                        |
| 3. 3 issues Effort Ratio > 150%                      |
+------------------------------------------------------+
| Suggested Actions                                    |
| 1. Review overdue High/Critical issues               |
| 2. Prioritize Payment bug fixing                     |
| 3. Ask assignee A to update stale issues             |
+------------------------------------------------------+
```

### 9.2. Multi-project Dashboard

```text
+------------------------------------------------------+
| Multi-project Health                                 |
+------------------------------------------------------+
| Project   | Score | Status | Trend | Main Risk       |
| Project A | 10/12 | Green  | +1    | None            |
| Project B | 7/12  | Yellow | -2    | Overdue         |
| Project C | 5/12  | Red    | -1    | Bug Rate        |
+------------------------------------------------------+
```

### 9.3. Drill-down issue rủi ro

```text
+------------------------------------------------------+
| Risk Detail: Overdue Issues                          |
+------------------------------------------------------+
| ID    | Subject      | Priority | Assignee | Due date   |
| #101  | Login bug    | High     | A        | 2026-05-01 |
| #108  | API timeout  | Critical | B        | 2026-05-02 |
+------------------------------------------------------+
```

### Ghi chú

- Các trạng thái chính: Green / Yellow / Red
- Thông điệp xác thực/lỗi cần rõ ràng, ví dụ: thiếu cột, sai format ngày, không đủ dữ liệu.
- Màn hình dashboard cần ưu tiên desktop; mobile có thể hiển thị dạng card theo từng metric.

## 10. Các vấn đề mở

| #    | Câu hỏi | Người phụ trách | Hạn chót |
| ---- | ------- | --------------- | -------- |
| OI-1 | Chưa có thông tin ticket ID, ngày tạo và giai đoạn | [MISSING] | [MISSING] |
| OI-2 | Có cần tích hợp trực tiếp Redmine API ở MVP hay chỉ sử dụng dữ liệu đã được đồng bộ từ Redmine về DB local? | PM / Dev Lead | [MISSING] |
| OI-3 | Danh sách status nào được xem là closed ngoài `status_id = 3`? | PM / Redmine Admin | [MISSING] |
| OI-4 | Ngưỡng Green/Yellow/Red và weight metric có dùng mặc định hay theo từng project? | PM / BrSE / Leader | [MISSING] |
| OI-5 | Có cần phân tích theo module không, nếu có module được lấy từ field nào trong Redmine? | PM / Dev Lead | [MISSING] |
| OI-6 | Có cần lưu snapshot vào DB hay chỉ export báo cáo sau mỗi lần import? | Dev Lead | [MISSING] |
| OI-7 | Có cần quyền phân biệt Admin/Viewer cho cấu hình scoring không? | PM / Dev Lead | [MISSING] |

## 11. Rủi ro

| #   | Rủi ro | Khả năng xảy ra | Mức độ ảnh hưởng | Biện pháp giảm thiểu |
| --- | ------ | --------------- | ---------------- | -------------------- |
| 1   | Nếu `Estimated hours` bị thiếu nhiều, chỉ số Effort Ratio không đáng tin cậy | Trung bình | Cao | Hiển thị cảnh báo data quality và cho phép bỏ qua metric effort nếu thiếu dữ liệu nhiều |
| 2   | Đánh giá sức khỏe dự án chỉ bằng một snapshot có thể không phản ánh xu hướng | Cao | Cao | Lưu snapshot theo tuần để tính trend |
| 3   | Redmine chỉ cung cấp dữ liệu, còn việc đánh giá phụ thuộc vào quy chuẩn của team | Cao | Trung bình | Cho phép cấu hình threshold, weight, closed status và bug tracker |
| 4   | Công thức quá cứng khiến không phù hợp nhiều loại dự án | Trung bình | Cao | Xây dựng Configurable Scoring Engine |
| 5   | Suggested Actions quá chung chung, không tạo giá trị khi demo | Trung bình | Cao | Mapping action theo từng risk driver và hiển thị issue cụ thể |
| 6   | Dữ liệu Redmine không đầy đủ hoặc không đồng nhất giữa các project | Cao | Cao | Validate dữ liệu import, báo thiếu cột, báo tỷ lệ thiếu field quan trọng |
| 7   | User hiểu sai score là kết luận tuyệt đối | Trung bình | Trung bình | Hiển thị ghi chú score là chỉ báo hỗ trợ quyết định, không thay thế PM judgment |

---

## Bảng truy vết

| #   | AC                | Màn hình/API | DB | Logs | Quyền | Loại kiểm thử |
| --- | ----------------- | ------------ | --- | ---- | ----- | ------------- |
| 1   | HEALTH-AC-001/v1 | Sync DB / Calculation API | Không bắt buộc nếu MVP dùng file; cần DB nếu lưu snapshot | Import log | Viewer | Unit test |
| 2   | HEALTH-AC-002/v1 | Calculation API | Không bắt buộc | Calculation log | Viewer | Unit test |
| 3   | HEALTH-AC-003/v1 | Calculation API | Không bắt buộc | Calculation log | Viewer | Unit test |
| 4   | HEALTH-AC-004/v1 | Calculation API / Drill-down | Không bắt buộc | Calculation log | Viewer | Unit test |
| 5   | HEALTH-AC-005/v1 | Calculation API / Drill-down | Không bắt buộc | Calculation log | Viewer | Unit test |
| 6   | HEALTH-AC-006/v1 | Calculation API / Drill-down | Không bắt buộc | Calculation log | Viewer | Unit test |
| 7   | HEALTH-AC-007/v1 | Calculation API / Drill-down | Không bắt buộc | Calculation log | Viewer | Unit test |
| 8   | HEALTH-AC-008/v1 | Dashboard / Calculation API | Snapshot table nếu lưu history | Calculation log | Viewer | Unit test |
| 9   | HEALTH-AC-009/v1 | Dashboard | Snapshot table nếu lưu history | Calculation log | Viewer | Unit test |
| 10  | HEALTH-AC-010/v1 | Report screen / Export | Report history nếu cần | Export log | Viewer | UI / Export test |
| 11  | HEALTH-AC-011/v1 | Snapshot API | Health snapshot table | Snapshot log | Viewer | Integration test |
| 12  | HEALTH-AC-012/v1 | Dashboard Trend | Health snapshot table | Calculation log | Viewer | UI test |
| 13  | HEALTH-AC-013/v1 | Risk Driver panel | Issue snapshot / Risk summary table nếu lưu | Risk analysis log | Viewer | Unit / Integration test |
| 14  | HEALTH-AC-014/v1 | Warning panel | Warning table nếu lưu | Warning log | Viewer | Unit test |
| 15  | HEALTH-AC-015/v1 | Suggested Actions panel | Action suggestion table nếu lưu | Suggestion log | Viewer | Unit / UI test |
| 16  | HEALTH-AC-016/v1 | Configuration screen | Config table | Config change log | Admin | UI / Integration test |
| 17  | HEALTH-AC-017/v1 | Multi-project Dashboard | Health snapshot table | Dashboard log | Viewer | UI test |
| 18  | HEALTH-AC-018/v1 | Drill-down screen | Issue snapshot table nếu lưu | Drill-down query log | Viewer | UI / Integration test |
