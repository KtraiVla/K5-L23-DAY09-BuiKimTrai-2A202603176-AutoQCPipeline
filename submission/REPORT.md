# Báo cáo Day 09 — Bùi Kim Trai, 2A202603176

## 1. Kết luận trước

**Hold.** Pipeline nhận 224 ảnh, loại 19 ảnh ở intake và giữ lại 205 ảnh. Sau sửa tự động và người duyệt mô phỏng 80/80 ảnh, không còn lỗi bắt buộc nhưng còn 38/205 ảnh có cảnh báo chưa duyệt (18,54%), vượt ngưỡng 10%. Dataset `clean_v1` được xuất dưới dạng **bản nháp**, chưa được phát hành.

## 2. Lỗi và phân việc

Thống kê từ `02_error_list_v1.csv`: intake có 19 issue lỗi bắt buộc trên 224 ảnh; QC trên 205 ảnh được nhận có 36 issue lỗi bắt buộc và 153 issue cảnh báo. Số issue không nhất thiết bằng số dòng nhãn hoặc số lỗi thật đã xác nhận; một ảnh có thể xuất hiện ở nhiều mã.

| Mã lỗi | Issue / ảnh | Ai xử lý và cách xử lý |
|---|---:|---|
| BAD_SIZE | 3 / 3 | Máy loại ảnh không đạt kích thước |
| CORRUPT_IMAGE | 2 / 2 | Máy loại ảnh hỏng |
| DUP_IMAGE_EXACT | 8 / 8 | Máy loại ảnh trùng, giữ đại diện |
| DUP_IMAGE_NEAR | 2 / 2 | Máy phát hiện/loại; người đối chiếu tính hợp lý |
| LEAK_TEST | 4 / 4 | Máy loại ảnh rò rỉ từ test/val |
| BAD_CLASS_ID | 6 / 6 | Máy xóa dòng, ghi log |
| BAD_CLASS_NAME | 2 / cấp dataset | Máy chuẩn hóa tên lớp |
| BAD_FORMAT | 3 / 3 | Máy xóa dòng, ghi log |
| BOX_OUT_OF_IMAGE | 8 / 8 | Máy cắt box; xóa nếu không còn diện tích |
| BOX_ZERO | 4 / 4 | Máy xóa dòng |
| DUP_BOX | 7 / 7 | Máy xóa box lặp ở dòng sau |
| MISSING_LABEL_FILE | 6 / 6 | Người gán nhãn; máy chỉ ghi needs_label |
| BOX_HUGE | 3 / 3 | Người kiểm box lớn |
| BOX_TINY | 6 / 4 | Người kiểm vật nhỏ theo guideline |
| CLASS_RARE | 4 / cấp dataset | Người phụ trách đánh giá phân bố lớp |
| EMPTY_LABEL | 12 / 12 | Người phân biệt ảnh nền và thiếu nhãn |
| POSSIBLE_FALSE_POS | 29 / 27 | Người xác minh box có thể thừa |
| POSSIBLE_LOOSE_BOX | 28 / 24 | Người xác minh/chỉnh box lỏng |
| POSSIBLE_MISSING | 53 / 52 | Người xác minh/bổ sung nhãn thiếu |
| POSSIBLE_WRONG_CLASS | 18 / 18 | Người xác minh/sửa lớp |

Hàng đợi sau autofix có 125 ảnh. `img_0020` đứng đầu với điểm 11.524 vì có FIXED_DROP_LINE, POSSIBLE_MISSING và POSSIBLE_WRONG_CLASS; sáu ảnh thiếu file nhãn có điểm 10.0 mỗi ảnh đều ở nhóm đầu. Điểm tổng hợp khiến một ảnh có nhiều dấu hiệu có thể đứng trước ảnh thiếu nhãn.

Người duyệt mô phỏng đã xem 80 ảnh, gồm 6 ảnh thiếu nhãn và 74 ảnh có cảnh báo ngữ nghĩa trước duyệt. Trên 74 ảnh có 94 issue: 51 POSSIBLE_MISSING, 18 POSSIBLE_WRONG_CLASS, 13 POSSIBLE_FALSE_POS và 12 POSSIBLE_LOOSE_BOX. Đây là số cảnh báo được chuyển tới người duyệt, không phải 94 lỗi thật đã xác nhận hoặc số thay đổi thực tế.

## 3. Calibration hai ngưỡng

| Tham số / mã được đo | Khởi đầu → chọn | Precision trước → sau | Recall trước → sau |
|---|---|---|---|
| duplicates.phash_dist / DUP_IMAGE_NEAR | 2 → 4 | 1.00 → 1.00 | 0.50 → 0.67 |
| second_opinion.conf / POSSIBLE_WRONG_CLASS | 0.25 → 0.6 | 0.56 → 0.62 | 0.83 → 0.83 |
| second_opinion.conf / POSSIBLE_MISSING | 0.25 → 0.6 | 0.50 → 0.57 | 1.00 → 1.00 |
| second_opinion.conf / POSSIBLE_LOOSE_BOX | 0.25 → 0.6 | 0.29 → 0.20 | 0.40 → 0.20 |
| second_opinion.conf / POSSIBLE_FALSE_POS | 0.25 → 0.6 | 0.31 → 0.31 | 1.00 → 1.00 |

Chọn phash_dist=4 vì đây là ngưỡng nhỏ nhất trong sweep cải thiện recall ảnh gần trùng từ 3/6 lên 4/6 mà precision calib vẫn 1.00; tăng lên 6–14 không cải thiện thêm. Ngưỡng 16 bắt được 5/6 và là ứng viên đáng kiểm thêm, nhưng vì phát hiện trùng dẫn tới loại ảnh, tôi chọn thận trọng thay vì coi điểm calib cao nhất là đủ.

Chọn conf=0.6 để tăng precision sai lớp/thiếu nhãn mà giữ recall hai nhóm này. Đánh đổi là recall box lỏng giảm từ 0.40 xuống 0.20. Conf=0.8 tăng precision nhưng chỉ bắt 6/8 lỗi thiếu nhãn, thay vì 8/8 ở 0.6. FALSE_POS không đổi vì dùng fp_conf riêng.

Calib chỉ có 39 ảnh nên precision 1.00 chưa chứng minh không loại nhầm trên raw. Tôi quan sát các cặp 39–12, 76–42 và 80–71 có nội dung giống nhau; riêng ảnh 76 là bản phóng to của 42. Đây là quan sát bằng mắt, chưa khẳng định cả ba cặp đều được checker phát hiện. Sau calibration vẫn loại 19/224 ảnh; vài cặp đã xem chưa đủ chứng minh mọi quyết định loại đều đúng.

## 4. Cửa chặn và điểm mù

Chạy `python -m pipeline.run --budget 0 --work work/run_nb --reports work/rep_nb --export-dir work/exp_nb`, sau đó `echo $?`: còn 6 lỗi bắt buộc trên 205 ảnh, reviewed=0, decision=Rework, exported=null và mã thoát **20**. Thí nghiệm dùng cùng config_sha1 với lần chạy chính và chứng minh lỗi bắt buộc chặn xuất dataset. Lần chạy chính không còn ERROR nhưng 38/205 ảnh còn cảnh báo nên Hold, không được gọi là Release.

Hai điểm mù có bằng chứng trên calib: (1) phash_dist=4 chỉ phát hiện 4/6 ảnh gần trùng, bỏ sót 2/6; (2) conf=0.6 chỉ phát hiện 1/5 lỗi box lỏng, bỏ sót 4/5. Không diễn giải các tỷ lệ calib thành tỷ lệ bỏ sót trên raw. Trên raw, kiểm bằng mắt các cặp nêu ở mục 3 cũng chưa thay thế kiểm toàn bộ.

## 5. Train: raw vs clean

**Chưa chạy.** Báo cáo hiện tại chỉ đánh giá phần lõi; chưa có số liệu train raw/clean. Tôi chưa kết luận clean cho mAP tốt hơn raw. Số ảnh còn cảnh báo giảm từ 60/205 xuống 38/205 sau đổi ngưỡng cũng không tự chứng minh chất lượng nhãn hoặc model được cải thiện.

## 6. Quyết định và ghi chú AI

Giữ quyết định **Hold**, chỉ dùng export như bản nháp thử nghiệm. Với 205 ảnh, điều kiện để Release là không còn ERROR và còn tối đa 20 ảnh có cảnh báo chưa duyệt (dưới 10%). Cần xác minh/xử lý đúng quy trình; không thay ngân sách 80 ảnh, trọng số hay ngưỡng gate để ép Release.

- Prompt chính: nhờ AI hướng dẫn triển khai bốn module theo docstring/test của đề, giải thích cách kiểm và giới hạn sửa tệp.
- Cách kiểm: chạy pytest (79 passed), hai sweep calibration, quan sát ảnh raw, đối chiếu báo cáo/hàng đợi và thí nghiệm budget=0.
- Vướng mắc với hướng dẫn AI: các đoạn mã minh họa rời rạc ban đầu chưa làm rõ vị trí đặt trong hàm, khiến tôi ghép code ngoài run và giữ NotImplementedError. Tôi khắc phục bằng mã đầy đủ, kiểm thụt dòng và chạy test.
