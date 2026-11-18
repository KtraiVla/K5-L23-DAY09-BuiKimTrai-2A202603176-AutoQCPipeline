"""CHECK 2 — Dòng nhãn YOLO: sai định dạng, ID lớp lạ, box tràn ảnh, box rỗng, box lặp.   (Script 2 trong slide)   ★★

Test:  pytest tests/test_label_format.py -q

Mỗi dòng nhãn: `id cx cy w h` (5 số, toạ độ 0–1). Trả về list[Issue]; `Issue.line` = số dòng (đếm từ 1).

| code             | severity | khi nào                                                                  |
|------------------|----------|--------------------------------------------------------------------------|
| BAD_FORMAT       | ERROR    | không đúng 5 cột số (dùng `parse_yolo_line`, bắt `ValueError`)           |
| BAD_CLASS_ID     | ERROR    | id lớp ngoài 0..len(ds.classes)-1                                        |
| BOX_ZERO         | ERROR    | w <= 0 hoặc h <= 0                                                       |
| BOX_OUT_OF_IMAGE | ERROR    | mép box vượt [0,1] quá `cfg["label_format"]["overflow_tol"]`; extra={"overflow": mức tràn} |
| DUP_BOX          | ERROR    | cùng lớp với một dòng TRƯỚC ĐÓ và IoU > `dup_box_iou`; báo ở dòng SAU    |
| BOX_TINY         | WARN     | cạnh ngắn của box (px) < `min_box_px`  (cần `ds.image_size(stem)`)       |
| BOX_HUGE         | WARN     | w*h > `max_box_frac`                                                     |

Gợi ý
- Mép trái = x - w/2, mép phải = x + w/2 (xem câu hỏi "dòng YOLO nào lỗi?" trong slide).
- Một dòng hỏng (BAD_FORMAT, BAD_CLASS_ID, BOX_ZERO) thì `continue`, đừng kiểm tiếp hình học của dòng đó.
- Dòng thiếu cột làm script của slide dừng giữa chừng: đây là lý do phải `try/except`.
- `iou_xywh(a, b)` có sẵn trong common.py.
- Ngưỡng nằm trong `cfg["label_format"]` — đừng viết cứng số vào code.
"""
from ..common import ERROR, WARN, Issue, iou_xywh, parse_yolo_line  # noqa: F401


def run(ds, cfg):
    settings = cfg["label_format"]
    issues = []

    for path in ds.label_files():
        stem = path.stem
        size = ds.image_size(stem)
        previous = []

        def add(code, severity, line, message, **extra):
            issues.append(
                Issue(
                    "label_format",
                    severity,
                    code,
                    stem,
                    message,
                    line,
                    extra,
                )
            )

        for line, text in ds.read_label_lines(stem) or []:
            # 1. Kiểm tra định dạng dòng nhãn.
            try:
                cls, cx, cy, w, h = parse_yolo_line(text)
            except (ValueError, OverflowError) as exc:
                add(
                    "BAD_FORMAT",
                    ERROR,
                    line,
                    f"dòng nhãn sai: {exc}",
                )
                continue

            # 2. Kiểm tra ID lớp.
            if not 0 <= cls < len(ds.classes):
                add(
                    "BAD_CLASS_ID",
                    ERROR,
                    line,
                    f"ID lớp không hợp lệ: {cls}",
                )
                continue

            # 3. Kiểm tra chiều rộng và chiều cao.
            if w <= 0 or h <= 0:
                add(
                    "BOX_ZERO",
                    ERROR,
                    line,
                    "chiều rộng/cao phải dương",
                )
                continue

            box = (cx, cy, w, h)

            # 4. Tính mức tràn lớn nhất của bốn mép.
            overflow = max(
                0.0,
                w / 2 - cx,
                h / 2 - cy,
                cx + w / 2 - 1,
                cy + h / 2 - 1,
            )

            if overflow > settings["overflow_tol"]:
                add(
                    "BOX_OUT_OF_IMAGE",
                    ERROR,
                    line,
                    "box tràn ảnh",
                    overflow=overflow,
                )

            # 5. Kiểm tra box trùng dòng trước cùng lớp.
            is_duplicate = any(
                cls == old_cls
                and iou_xywh(box, old_box) > settings["dup_box_iou"]
                for old_cls, old_box in previous
            )

            if is_duplicate:
                add(
                    "DUP_BOX",
                    ERROR,
                    line,
                    "box trùng dòng trước cùng lớp",
                )

            previous.append((cls, box))

            # 6. Kiểm tra cạnh ngắn của box theo pixel.
            if size:
                image_width, image_height = size
                short_side = min(
                    w * image_width,
                    h * image_height,
                )

                if short_side < settings["min_box_px"]:
                    add(
                        "BOX_TINY",
                        WARN,
                        line,
                        "cạnh ngắn của box quá nhỏ",
                    )

            # 7. Kiểm tra diện tích box.
            if w * h > settings["max_box_frac"]:
                add(
                    "BOX_HUGE",
                    WARN,
                    line,
                    "box phủ gần hết ảnh",
                )

    return issues