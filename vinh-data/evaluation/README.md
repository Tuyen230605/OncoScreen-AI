# NCCN Clinical Decision Benchmark Suite (OncoScreen-AI)

Bộ dữ liệu kiểm định lâm sàng được trích xuất từ **NCCN MedGUIDE Decision Trees (2025)**, chỉ tập trung vào các tình huống tầm soát, giám sát và xử trí phát hiện sớm (loại trừ các ca hóa trị/giai đoạn muộn).

- **Tổng số ca lâm sàng kiểm thử**: 490 ca
- **Tệp dữ liệu**: `nccn_screening_eval_suite.jsonl`
- **Các phân nhóm tình huống**:
  * `liver_hcc_surveillance`: Giám sát ung thư biểu mô tế bào gan (HCC) bằng Siêu âm + AFP ở người xơ gan, viêm gan B/C mạn tính.
  * `lung_nodule_management`: Xử trí và phân loại nốt phổi phát hiện tình cờ / qua chụp CT ngực liều thấp (Lung-RADS).
  * `colorectal_surveillance`: Theo dõi nội soi và dấu ấn sinh học CEA đại trực tràng.

Mỗi bản ghi chứa: `profile` (tóm tắt bệnh án), `prompt` (câu hỏi trắc nghiệm lâm sàng), `options` (các hướng xử trí), `answer_text` (quyết định chuẩn theo lưu đồ NCCN).
