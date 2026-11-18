# Báo cáo Day 09 — Bùi Kim Trại, 2A202603176

## 1. Kết luận trước

**Hold:** từ 224 ảnh, intake loại 19, giữ 205. Sau autofix và người duyệt mô phỏng 80/80 ảnh, còn 0 ERROR nhưng 38/205 ảnh có WARN chưa duyệt (18,54% ≥ 10%). `clean_v1` là bản nháp, chưa phát hành.

## 2. Lỗi và phân việc

`02_error_list_v1`: 19 ERROR intake/224 ảnh; QC trên 205 ảnh có 36 ERROR và 153 WARN. Issue không đồng nghĩa lỗi thật; ảnh có thể xuất hiện ở nhiều mã. Dấu “—” là issue cấp dataset.

| Mã lỗi | Issue | Ảnh | Xử lý |
|---|---:|---:|---|
| BAD_SIZE | 3 | 3 | Máy loại ảnh |
| CORRUPT_IMAGE | 2 | 2 | Máy loại ảnh |
| DUP_IMAGE_EXACT | 8 | 8 | Máy loại, giữ đại diện |
| DUP_IMAGE_NEAR | 2 | 2 | Máy loại; người đối chiếu |
| LEAK_TEST | 4 | 4 | Máy loại khỏi train |
| BAD_CLASS_ID | 6 | 6 | Máy xóa dòng, ghi log |
| BAD_CLASS_NAME | 2 | — | Máy chuẩn hóa tên lớp |
| BAD_FORMAT | 3 | 3 | Máy xóa dòng, ghi log |
| BOX_OUT_OF_IMAGE | 8 | 8 | Máy cắt; xóa nếu hết diện tích |
| BOX_ZERO | 4 | 4 | Máy xóa dòng |
| DUP_BOX | 7 | 7 | Máy xóa dòng sau |
| MISSING_LABEL_FILE | 6 | 6 | Người gán; máy ghi needs_label |
| BOX_HUGE | 3 | 3 | Người xác minh |
| BOX_TINY | 6 | 4 | Người kiểm theo guideline |
| CLASS_RARE | 4 | — | Người đánh giá phân bố lớp |
| EMPTY_LABEL | 12 | 12 | Người phân biệt nền/thiếu nhãn |
| POSSIBLE_FALSE_POS | 29 | 27 | Người xác minh nhãn thừa |
| POSSIBLE_LOOSE_BOX | 28 | 24 | Người kiểm/chỉnh box |
| POSSIBLE_MISSING | 53 | 52 | Người xác minh/bổ sung |
| POSSIBLE_WRONG_CLASS | 18 | 18 | Người xác minh/sửa lớp |

Máy ghi 35 action: 20 drop_line, 8 clip_box, 1 rename_classes, 6 needs_label; needs_label không tạo nhãn rỗng. Hàng đợi 125 ảnh: `img_0020` đứng đầu, điểm 11.524 từ FIXED_DROP_LINE/MISSING/WRONG_CLASS, cao hơn 10.0 của từng ảnh thiếu nhãn. 80 ảnh được duyệt gồm 6 ảnh thiếu nhãn và 74 ảnh có 94 cảnh báo ngữ nghĩa: 51 MISSING, 18 WRONG_CLASS, 13 FALSE_POS, 12 LOOSE_BOX. Đây không phải 94 lỗi thật đã xác nhận.

## 3. Calibration hai ngưỡng

Các ô dưới là precision/recall, làm tròn như báo cáo script.

| Tham số, mã đo | Khởi đầu → chọn | P/R trước → sau |
|---|---|---|
| phash_dist, DUP_IMAGE_NEAR | 2 → 4 | 1.00/0.50 → 1.00/0.67 |
| conf, WRONG_CLASS | 0.25 → 0.6 | 0.56/0.83 → 0.62/0.83 |
| conf, MISSING | 0.25 → 0.6 | 0.50/1.00 → 0.57/1.00 |
| conf, LOOSE_BOX | 0.25 → 0.6 | 0.29/0.40 → 0.20/0.20 |
| conf, FALSE_POS | 0.25 → 0.6 | 0.31/1.00 → 0.31/1.00 |

Chọn phash_dist=4: ngưỡng nhỏ nhất cải thiện recall gần trùng; 6–14 không thêm lợi ích. Precision cần cao vì cờ sai dẫn tới loại ảnh; 16 bắt 5/6 nhưng cần kiểm raw trước khi dùng. Conf=0.6 giữ recall thiếu nhãn/sai lớp và tăng precision; đánh đổi là giảm recall box lỏng. Conf=0.8 chỉ bắt 6/8 lỗi thiếu nhãn, thay vì 8/8. FALSE_POS dùng fp_conf riêng.

Calib 39 ảnh nhỏ, khác raw; precision 1.00 chưa chứng minh không loại nhầm. Tôi quan sát các cặp 39–12, 76–42, 80–71 giống nhau; 76 là bản phóng to của 42. Chưa khẳng định cả ba cặp được checker bắt. Sau calibration vẫn loại 19/224 ảnh; vài cặp quan sát chưa chứng minh mọi quyết định loại đều đúng.

## 4. Cửa chặn và điểm mù

Chạy `python -m pipeline.run --budget 0 --work work/run_nb --reports work/rep_nb --export-dir work/exp_nb`, rồi `echo $?`: cùng config_sha1, còn 6 ERROR/205 ảnh, reviewed=0, **Rework**, exported=null, mã **20**, không xuất dataset. Khác với Hold ở lần chạy chính: hết ERROR nhưng vượt ngưỡng WARN.

Hai điểm mù trên calib: phash_dist=4 chỉ bắt 4/6 ảnh gần trùng; conf=0.6 chỉ bắt 1/5 box lỏng. Không suy rộng tỷ lệ này sang raw. Các cặp quan sát ở mục 3 là bằng chứng kiểm bằng mắt, chưa thay thế duyệt toàn bộ.

## 5. Train: raw vs clean

Colab T4, yolo26n.pt, 20 epoch, batch 16, imgsz 640, seed 0/1 mỗi biến thể; chung val 40 ảnh/test 100 ảnh. [Notebook đã chạy](https://colab.research.google.com/drive/1KDTjVgK1vrKhYAwK6_wNFliA0k2NaTpa). Bảng do script sinh:

| Biến thể | Ảnh trong thư mục | Seed | mAP50 | mAP50-95 | Precision | Recall |
|---|---:|---:|---|---|---|---|
| raw | 224 | 2 | 0.726 ± 0.000 | 0.512 ± 0.004 | 0.764 ± 0.061 | 0.649 ± 0.028 |
| clean | 205 | 2 | 0.700 ± 0.030 | 0.486 ± 0.013 | 0.715 ± 0.073 | 0.615 ± 0.017 |

Log xác nhận raw thực dùng **213** ảnh (bỏ 11 ảnh/nhãn hỏng), clean đủ 205. mAP50 seed 0/1: raw 0.7256/0.7259, clean 0.6788/0.7219. Chênh trung bình **−0.0254**, so với SD clean **0.0305**, raw **0.00021** (0.000 là làm tròn). Clean thấp hơn ở hai seed; chưa đủ bằng chứng QC cải thiện model hoặc suy rộng mức giảm.

Giả thuyết: (1) raw có 4 ảnh trùng test, có thể ảnh hưởng điểm; chưa đo mức thổi phồng. Kiểm bằng thí nghiệm riêng loại ảnh rò rỉ, cùng seed/protocol. (2) Clean còn 38 ảnh cảnh báo chưa duyệt; AP50 truck trung bình giảm 0.6485→0.5588. Đối chiếu nhãn train liên quan truck. (3) Lượng/phân bố dữ liệu đổi: kiểm ảnh/lớp bị loại, đối chứng kích thước train, thêm seed và đánh giá độc lập. Không chọn lại ngưỡng theo test hiện tại. AP50 car trung bình tăng khoảng 0.0110, person 0.0053; chưa coi là cải thiện chắc chắn.

## 6. Quyết định và ghi chú AI

Giữ **Hold**. Release cần 0 ERROR và tối đa 20/205 ảnh cảnh báo chưa duyệt; không đổi ngân sách/trọng số/ngưỡng gate để ép đạt.

- Prompt chính (tóm tắt nội dung trao đổi): Hỗ trợ hoàn thiện bốn module `label_format`, `second_opinion`, `autofix`, `gate` theo docstring và test của repo; giải thích từng phần để tôi tự kiểm tra. **Đầu vào:** nhãn YOLO `id cx cy w h`, kích thước ảnh, dự đoán model và cấu hình. **Quy tắc:** kiểm định dạng/hình học; đối chiếu model chỉ để cảnh báo; chỉ tự sửa ERROR được phép trên bản sao; quyết định gate theo số ảnh WARN chưa duyệt. **Đầu ra:** danh sách `Issue` có mã lỗi/số dòng, log thay đổi và quyết định Release/Hold/Rework đúng giao diện có sẵn. **Giới hạn:** lấy ngưỡng từ cấu hình, không sửa `data/`, `tests/` hay mã viết sẵn; không tự sửa WARN hoặc thay quy tắc gate để ép Release.
- Cách kiểm: pytest 79 passed, hai sweep calib, xem raw, thí nghiệm budget=0; checker gốc Linux đầy đủ 0 lỗi/0 cảnh báo, mã 0; ba ca biên bổ sung đều qua.
- AI hướng dẫn thiếu rõ ràng: các đoạn mã rời rạc chưa rõ vị trí trong hàm khiến tôi ghép ngoài run và giữ NotImplementedError; đã khắc phục bằng mã đầy đủ, sửa thụt dòng và chạy test.
