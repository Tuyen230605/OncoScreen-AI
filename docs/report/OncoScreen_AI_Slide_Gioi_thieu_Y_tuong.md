# OncoScreen AI — Nội dung slide giới thiệu ý tưởng

> **Loại tài liệu:** kịch bản dựng slide cho buổi báo cáo ý tưởng.
> **Căn cứ:** Đề cương sơ bộ (`docs/De_cuong_so_bo_OncoScreen_AI.docx`, 10/2026) và định vị sản phẩm hiện tại (`docs/00_OVERVIEW.md`).
> **Người nghe:** giảng viên hướng dẫn, hội đồng đánh giá học phần, đại diện bệnh viện đối tác.
> **Thời lượng:** bản đầy đủ khoảng 25–30 phút (34 slide); bản rút gọn 12–15 phút (xem mục *Bản rút gọn* ở cuối).

## Cách dùng tài liệu này

- Mỗi slide gồm bốn phần: **Mục đích** · **Nội dung trên slide** · **Gợi ý hình ảnh** · **Lời thuyết trình**.
- *Nội dung trên slide* là phần chữ đặt lên slide (đã rút gọn). *Lời thuyết trình* là phần nói, không dán lên slide.
- Số liệu gắn `[n]` → xem **Phụ lục C**. Số liệu lấy từ báo chí hoặc hội thảo được ghi rõ "theo báo chí"; nên đối chiếu bản gốc trước khi trình bày.
- Đây là báo cáo **ý tưởng**: trình bày vấn đề, cách tiếp cận, nguyên tắc an toàn và kế hoạch đánh giá; không đi vào chi tiết mã nguồn hay những gì đã cài đặt.
- **Footer cố định trên mọi slide:** `Prototype học tập · AI không chẩn đoán · Chưa đánh giá lâm sàng`

**Gợi ý thiết kế chung**
- Màu chủ đạo xanh y tế (tin cậy); màu cam/đỏ chỉ dùng cho *dấu hiệu cảnh báo* và *ngoài phạm vi*, không dùng để trang trí.
- Mỗi slide tối đa 6 dòng chữ chính; ưu tiên sơ đồ và bảng thay cho đoạn văn.
- Dùng một bộ icon thống nhất: 👤 người dân · 🩺 bác sĩ · 📚 nguồn · 🚩 cảnh báo · ✅ đã duyệt.
- Ký hiệu trong bảng so sánh: ✓ đáp ứng · △ đáp ứng một phần · ✗ không đáp ứng.

## Cấu trúc bài trình bày

| Phần | Nội dung | Slide |
|---|---|---|
| I | Mở đầu | 1–3 |
| II | Bối cảnh và vấn đề | 4–6 |
| III | Các phương pháp hiện có | 7–10 |
| IV | Ý tưởng giải pháp | 11–15 |
| V | Mục tiêu và mức độ giải quyết | 16–18 |
| VI | An toàn và độ tin cậy | 19–25 |
| VII | So sánh thực tế | 26–28 |
| VIII | Đánh giá, lộ trình, kết luận | 29–34 |
| — | Phụ lục: câu hỏi dự kiến, khuyến nghị tham chiếu, tài liệu tham khảo, thuật ngữ | A–D |

---

# PHẦN I — MỞ ĐẦU

## Slide 1 — Trang bìa

**Mục đích:** giới thiệu tên đề tài và câu định vị ngay từ đầu.

**Nội dung trên slide**
- **OncoScreen AI**
- *Trợ lý hành trình tầm soát ung thư có bác sĩ giám sát*
- Báo cáo ý tưởng · Học phần: ……… · Tháng 10/2026
- Nhóm thực hiện: ……… · Giảng viên hướng dẫn: ………

**Gợi ý hình ảnh:** hình minh họa tối giản một con đường nối 👤 người dân → 🩺 bác sĩ, trên đường có biển chỉ dẫn. Không dùng hình khối u hay hình ảnh gây sợ hãi.

**Lời thuyết trình**
> Kính chào thầy cô và các bạn. Nhóm em xin trình bày ý tưởng OncoScreen AI, một trợ lý AI giúp người dân biết mình nên tầm soát ung thư gì và đi đúng hành trình tới bệnh viện, đồng thời giúp bác sĩ chuẩn bị trước buổi khám. Nguyên tắc xuyên suốt của đề tài là AI không chẩn đoán và bác sĩ luôn là người quyết định.

---

## Slide 2 — Ý tưởng trong một phút

**Mục đích:** để hội đồng nắm toàn bộ ý tưởng trước khi đi vào chi tiết.

**Nội dung trên slide** (bố cục 4 ô)

| Vấn đề | Giải pháp |
|---|---|
| Người dân không biết nên tầm soát gì, khi nào, bao lâu một lần. Bác sĩ bắt đầu buổi khám với rất ít thông tin. | Hai trợ lý AI dùng chung một lõi tri thức: **Navigator** cho người dân, **Clinical Copilot** cho bác sĩ, nối với nhau bằng **hồ sơ xuyên suốt**. |
| **Nguyên tắc** | **Giới hạn** |
| Luật trước, LLM sau · Mọi gợi ý có nguồn · Dấu hiệu cảnh báo thì dừng ngay · Bác sĩ duyệt trước khi bệnh nhân nhận kế hoạch. | Không chẩn đoán, không đọc kết quả xét nghiệm, không tư vấn điều trị. Prototype học tập, chưa đánh giá lâm sàng. |

**Gợi ý hình ảnh:** 4 ô màu nhạt, ô "Giới hạn" viền cam để nhấn mạnh.

**Lời thuyết trình**
> Tóm gọn trong một phút: vấn đề nằm ở cả hai phía. Người dân thiếu định hướng, còn bác sĩ thiếu thông tin. Giải pháp của nhóm là hai trợ lý AI. Navigator trò chuyện với người dân và chỉ đưa gợi ý tầm soát theo nhóm tuổi, giới, yếu tố nguy cơ, luôn có nguồn. Copilot hỗ trợ bác sĩ tóm tắt hồ sơ và soạn bản nháp. Mọi quyết định cá nhân do bác sĩ đưa ra. Nhóm cũng xin nói rõ ngay từ đầu những gì hệ thống không làm.

---

## Slide 3 — Nội dung trình bày

**Nội dung trên slide**
1. Bối cảnh và vấn đề
2. Các phương pháp hiện có và khoảng trống
3. Ý tưởng giải pháp
4. Mục tiêu và mức độ giải quyết
5. An toàn và độ tin cậy
6. So sánh với thực tế
7. Đánh giá, lộ trình, hạn chế
8. Kết luận và hỏi đáp

**Gợi ý hình ảnh:** thanh tiến trình ngang 8 bước, lặp lại nhỏ ở góc các slide sau để người nghe biết đang ở phần nào.

**Lời thuyết trình**
> Bài trình bày gồm tám phần. Nhóm dành nhiều thời gian nhất cho phần năm, an toàn và độ tin cậy, vì đây là điều kiện tiên quyết khi đưa AI vào lĩnh vực y tế.

---

# PHẦN II — BỐI CẢNH VÀ VẤN ĐỀ

## Slide 4 — Gánh nặng ung thư tại Việt Nam

**Mục đích:** cho thấy quy mô vấn đề bằng số liệu có nguồn.

**Nội dung trên slide**
- **180.480** ca mắc mới và **120.184** ca tử vong do ung thư trong năm 2022 [1]
- **16%**: nguy cơ tích lũy mắc ung thư trước 75 tuổi [1]
- Nữ giới: **ung thư vú** đứng đầu với 24.563 ca, chiếm 28,9% ca mới ở nữ [1]
- Nam giới: **gan** (18.952 ca) và **phổi** (17.007 ca) dẫn đầu [1]
- Theo báo chí: hơn **70%** bệnh nhân đến khám ở giai đoạn muộn [3]; với ung thư phổi khoảng **75%** phát hiện muộn, tỷ lệ sống sau 5 năm khoảng 14,8% [2]

**Thông điệp chốt:** nhiều loại ung thư phổ biến đã có khuyến nghị tầm soát trong guideline (vú, cổ tử cung, đại trực tràng; phổi và gan ở nhóm nguy cơ cao). Khoảng trống lớn nằm ở chỗ **người dân biết và đi tầm soát đúng lúc**.

**Gợi ý hình ảnh:** ba con số lớn ở hàng trên; biểu đồ thanh ngang nhỏ "loại ung thư hàng đầu theo giới" ở hàng dưới; ghi nguồn GLOBOCAN 2022 ở chân slide.

**Lời thuyết trình**
> Theo GLOBOCAN 2022 của Cơ quan Nghiên cứu Ung thư Quốc tế, mỗi năm Việt Nam có khoảng 180 nghìn ca mắc mới và hơn 120 nghìn ca tử vong do ung thư. Ung thư vú đứng đầu ở nữ, ung thư gan và phổi dẫn đầu ở nam. Báo chí và các bệnh viện chuyên khoa thường nhắc tới con số hơn 70% bệnh nhân đến viện ở giai đoạn muộn. Con số này nhóm dẫn từ báo chí nên chỉ mang tính tham khảo. Điều đáng chú ý là phần lớn các loại ung thư phổ biến này đều đã có khuyến nghị tầm soát. Vậy vấn đề không chỉ là thiếu phương pháp, mà là người dân chưa được dẫn tới đúng phương pháp vào đúng thời điểm.

---

## Slide 5 — Vì sao người dân bỏ lỡ tầm soát? Vấn đề ở hai phía

**Mục đích:** chỉ ra hai nhóm vấn đề mà giải pháp sẽ nhắm tới.

**Nội dung trên slide** (hai cột)

| 👤 Phía người dân | 🩺 Phía bệnh viện, bác sĩ |
|---|---|
| Không biết nên tầm soát loại nào, bắt đầu khi nào, bao lâu một lần | Thời gian khám ngắn, phải hỏi lại tiền sử từ đầu |
| Thông tin trên mạng phân tán, mâu thuẫn, khó biết nguồn | Thông tin bệnh nhân rời rạc, lịch sử tầm soát không liên tục |
| Ngại đi viện khi "chưa thấy gì"; sợ hãi, e ngại | Khó tách ca cần ưu tiên (có triệu chứng) khỏi ca tầm soát định kỳ |
| Chọn gói khám theo quảng cáo, không theo nhóm nguy cơ | Khó theo dõi việc tái tầm soát sau khi bệnh nhân ra về |
| Không ai nhắc lần tầm soát kế tiếp | Bác sĩ phải tự tra guideline cho từng trường hợp |

**Gợi ý hình ảnh:** hai cột, ở giữa là một "khoảng trống thông tin" (vết đứt) nối hai bên.

**Lời thuyết trình**
> Nhóm nhìn vấn đề từ hai phía. Người dân thường không biết mình thuộc nhóm nào, nên tầm soát gì. Họ tìm trên mạng thì gặp thông tin trái chiều, còn khi chưa có triệu chứng thì ngại đi viện. Không ít người chọn gói khám theo quảng cáo, có gói còn gồm những xét nghiệm guideline không khuyến nghị dùng để tầm soát cho người khỏe mạnh. Ở phía bệnh viện, bác sĩ thường bắt đầu buổi khám gần như từ con số không và phải hỏi lại từ đầu. Sau khám cũng không có cơ chế nhắc bệnh nhân quay lại đúng chu kỳ. Hai khoảng trống này chính là chỗ nhóm muốn lấp.

---

## Slide 6 — AI trong y tế: cơ hội và rủi ro

**Mục đích:** cho thấy nhóm hiểu cả tiềm năng lẫn rủi ro, và dẫn tới câu hỏi đặt ra.

**Nội dung trên slide**

**Cơ hội:** trả lời 24/7 bằng ngôn ngữ tự nhiên, tiếng Việt · tóm tắt hồ sơ nhanh · cá nhân hóa theo nhóm nguy cơ · mở rộng quy mô với chi phí thấp

**Rủi ro đã được ghi nhận**
- ChatGPT trả lời câu hỏi điều trị ung thư: **34,3%** câu trả lời có ít nhất một khuyến nghị không phù hợp guideline NCCN; câu trả lời thay đổi theo cách đặt câu hỏi [4]
- ChatGPT trả lời câu hỏi tầm soát ung thư vú: 22/25 câu (**88%**) phù hợp, nhưng **không nhất quán** giữa các lần hỏi và chỉ dẫn một nguồn guideline [5]
- 23 công cụ kiểm tra triệu chứng trực tuyến: chẩn đoán đúng ở vị trí đầu **34%**, lời khuyên phân loại mức độ phù hợp **57%** [6]
- Ngoài ra: dùng lời lẽ như chẩn đoán, gây hoảng loạn, bỏ sót triệu chứng nguy hiểm, rò rỉ dữ liệu sức khỏe

**Câu hỏi đặt ra:** *Làm thế nào dùng AI để người dân tầm soát đúng, mà vẫn an toàn, có căn cứ và có bác sĩ chịu trách nhiệm?*

**Gợi ý hình ảnh:** bên trái icon cơ hội (xanh), bên phải 3 thẻ số liệu rủi ro (cam); câu hỏi đặt to ở đáy slide.

**Lời thuyết trình**
> AI tạo sinh mở ra cơ hội lớn: người dân có thể hỏi bất cứ lúc nào bằng tiếng Việt, bác sĩ có thể nhận bản tóm tắt hồ sơ trong vài giây. Nhưng các nghiên cứu cũng cho thấy rủi ro rõ ràng. Một nghiên cứu trên JAMA Oncology năm 2023 cho thấy khoảng một phần ba câu trả lời của ChatGPT về điều trị ung thư có khuyến nghị lệch guideline. Nghiên cứu khác trên Radiology cho thấy ChatGPT trả lời khá tốt câu hỏi tầm soát vú nhưng không nhất quán giữa các lần hỏi. Các nghiên cứu này dùng phiên bản mô hình cũ, mô hình mới có thể tốt hơn. Tuy vậy, vấn đề về cấu trúc vẫn còn: câu trả lời không gắn với nguồn cố định, không gắn vào quy trình khám và không có ai duyệt. Từ đó nhóm đặt ra câu hỏi trung tâm của đề tài.

---

# PHẦN III — CÁC PHƯƠNG PHÁP HIỆN CÓ

## Slide 7 — Bản đồ các phương pháp hiện có

**Mục đích:** cho thấy nhóm đã khảo sát các cách tiếp cận đang tồn tại trước khi đề xuất giải pháp.

**Nội dung trên slide** (sơ đồ 2 trục)
- Trục ngang: **phục vụ người dân ↔ phục vụ bác sĩ**
- Trục dọc: **con người, thủ công ↔ tự động, AI**

| Nhóm | Phương pháp |
|---|---|
| A | Chương trình tầm soát có tổ chức, thư mời và nhắc lịch |
| B | Khám sức khỏe định kỳ, gói tầm soát tại bệnh viện |
| C | Tự tra cứu Internet, mạng xã hội |
| D | Điều hướng viên bệnh nhân (patient navigator, là con người) |
| E | Công cụ ước tính nguy cơ (Gail/BCRAT, Tyrer-Cuzick, PLCOm2012) |
| F | Công cụ kiểm tra triệu chứng trực tuyến (symptom checker) |
| G | Chatbot AI tổng quát (ChatGPT, Gemini…) |
| H | Hỗ trợ quyết định lâm sàng trong bệnh án điện tử (CDS), trợ lý tóm tắt hồ sơ |
| I | AI chẩn đoán hình ảnh (đọc nhũ ảnh, CT): bài toán khác, ngoài phạm vi |

**Gợi ý hình ảnh:** đặt các chấm A–I lên mặt phẳng 2 trục; vẽ thêm một ngôi sao "OncoScreen AI" ở vùng *tự động, nối cả hai phía* để báo trước định vị.

**Lời thuyết trình**
> Trước khi đề xuất, nhóm khảo sát các cách đang được dùng để đưa người dân tới tầm soát và hỗ trợ bác sĩ. Có thể xếp chúng trên hai trục: phục vụ ai, và do con người hay máy làm. Có cách thuần con người như điều hướng viên bệnh nhân, có cách thuần tự động như chatbot. Riêng AI chẩn đoán hình ảnh là một bài toán khác, thuộc khâu chẩn đoán, nhóm nêu để phân biệt chứ không làm. Hai slide tiếp theo phân tích điểm mạnh, điểm yếu của từng nhóm.

---

## Slide 8 — Phân tích các phương pháp hướng tới người dân

**Mục đích:** phân tích ưu, nhược điểm một cách công bằng.

**Nội dung trên slide**

| Phương pháp | Cách hoạt động | Điểm mạnh | Hạn chế |
|---|---|---|---|
| **A. Chương trình có tổ chức** | Cơ quan y tế mời theo danh sách dân số, nhắc định kỳ | Bao phủ rộng; nhắc lịch có bằng chứng làm tăng tỷ lệ tầm soát [19] | Cần hạ tầng dữ liệu dân số; ở Việt Nam chủ yếu theo đề án, chiến dịch, chưa phủ hết các loại ung thư |
| **B. Gói khám định kỳ** | Bệnh viện bán gói theo tuổi, giới | Dễ mua, khám trọn gói, có bác sĩ | Ít cá nhân hóa theo yếu tố nguy cơ; một số gói có xét nghiệm guideline không khuyến nghị để tầm soát (ví dụ dấu ấn ung thư ở người không triệu chứng), dễ dương tính giả, tốn kém, gây lo lắng |
| **C. Tự tra cứu** | Google, mạng xã hội, diễn đàn | Miễn phí, nhanh | Phân tán, khó kiểm chứng, nhiều tin sai; không theo dõi tiếp |
| **D. Điều hướng viên con người** | Nhân viên đồng hành cùng bệnh nhân (mô hình của H. Freeman, Harlem 1990) [16] | Có bằng chứng tăng tầm soát; thấu cảm | Chi phí nhân lực cao, khó mở rộng, chỉ trong giờ hành chính |
| **F. Symptom checker** | Nhập triệu chứng, nhận chẩn đoán khả dĩ và lời khuyên | Tiện, 24/7 | Hướng tới chẩn đoán triệu chứng; độ chính xác hạn chế [6]; không giải bài toán tầm soát người khỏe |
| **G. Chatbot AI tổng quát** | Hỏi đáp tự do | Tự nhiên, tiếng Việt tốt, kiến thức rộng | Không ràng buộc vào nguồn cố định, có thể bịa; không gắn quy trình khám; không có bác sĩ duyệt; dữ liệu gửi ra dịch vụ bên ngoài |

**Gợi ý hình ảnh:** bảng có tô màu nhẹ cột *Hạn chế*; có thể tách thành 2 slide nếu chữ quá nhỏ.

**Lời thuyết trình**
> Mỗi phương pháp đều có giá trị riêng. Chương trình tầm soát có tổ chức và điều hướng viên con người là những cách đã có bằng chứng hiệu quả, nhưng tốn nguồn lực và khó mở rộng. Gói khám định kỳ thì dễ tiếp cận nhưng thường không cá nhân hóa theo nguy cơ. Chatbot tổng quát thì rất tiện nhưng không bị ràng buộc vào nguồn và không gắn với quy trình có bác sĩ chịu trách nhiệm. Nhóm không cho rằng giải pháp của mình thay thế được các phương pháp này. Nhóm tìm chỗ còn trống giữa chúng.

---

## Slide 9 — Phân tích các phương pháp hướng tới bác sĩ và bệnh viện

**Nội dung trên slide**

| Phương pháp | Cách hoạt động | Điểm mạnh | Hạn chế |
|---|---|---|---|
| **E. Công cụ ước tính nguy cơ** | Gail/BCRAT, Tyrer-Cuzick (vú); PLCOm2012 (phổi) | Đã được kiểm chứng, cho kết quả định lượng | Mỗi công cụ chỉ cho một loại ung thư; cần nhập liệu chuyên môn; phát triển chủ yếu trên quần thể phương Tây, cần kiểm chứng thêm với người Việt |
| **H1. CDS trong bệnh án điện tử** | Nhắc tầm soát, cảnh báo theo luật trong EMR | Tích hợp sẵn vào quy trình | Cần EMR đồng bộ, chi phí cao; cảnh báo dày đặc gây "mệt mỏi cảnh báo" (alert fatigue) |
| **H2. Trợ lý tóm tắt, ghi chép bằng AI** | LLM tóm tắt hồ sơ, ghi biên bản khám | Giảm thời gian giấy tờ | Có thể tóm tắt sai hoặc bịa dữ kiện nếu không truy vết được về nguồn |
| **I. AI chẩn đoán hình ảnh** | AI hỗ trợ đọc nhũ ảnh, CT; ví dụ thử nghiệm MASAI (Thụy Điển) cho thấy giảm khoảng 44% khối lượng đọc phim mà không làm giảm phát hiện [20] | Hiệu quả cao ở khâu chẩn đoán | Là thiết bị y tế, cần chứng nhận; giải quyết khâu *đọc kết quả*, không phải khâu *đưa người dân tới tầm soát* |

**Lời thuyết trình**
> Ở phía bác sĩ, công cụ ước tính nguy cơ rất đáng tin nhưng mỗi công cụ chỉ cho một loại ung thư và chủ yếu xây dựng trên dữ liệu phương Tây. Hệ thống hỗ trợ quyết định trong bệnh án điện tử thì cần hạ tầng lớn và dễ gây mệt mỏi vì cảnh báo dồn dập. Trợ lý tóm tắt bằng AI đang phát triển nhanh nhưng có rủi ro bịa dữ kiện. AI đọc phim là hướng rất thành công, nhưng thuộc khâu chẩn đoán và cần chứng nhận thiết bị y tế. Nhóm chủ động không đi vào hướng đó.

---

## Slide 10 — Khoảng trống và định vị của nhóm

**Mục đích:** chốt lại vì sao cần một giải pháp mới.

**Nội dung trên slide**

Chưa có giải pháp nào hội đủ cả **năm yếu tố**:
1. **Dễ tiếp cận** với người dân: ẩn danh, tiếng Việt, 24/7
2. **Có căn cứ**: gợi ý theo guideline, theo nhóm nguy cơ, có nguồn
3. **An toàn**: nhận diện dấu hiệu cảnh báo và điều hướng khám sớm
4. **Gắn vào quy trình khám**: thông tin đi theo người bệnh, bác sĩ quyết định
5. **Liên tục**: nhắc tái tầm soát, hồ sơ nối các lần khám

→ **OncoScreen AI = "điều hướng viên số" cho người dân + "trợ lý chuẩn bị khám" cho bác sĩ, nối hai đầu một hành trình.**

**Gợi ý hình ảnh:** bảng checklist 5 yếu tố × các phương pháp (bản rút gọn của slide 26), hoặc biểu đồ Venn 3 vòng: *Tiếp cận · Căn cứ · Bác sĩ quyết định*; OncoScreen nằm ở giao điểm.

**Lời thuyết trình**
> Khi đặt các phương pháp cạnh nhau, nhóm thấy mỗi cách chỉ mạnh ở một vài yếu tố. Cách dễ tiếp cận thì thiếu căn cứ và thiếu bác sĩ. Cách có bác sĩ thì khó tiếp cận và không liên tục. Ý tưởng của nhóm là làm một điều hướng viên số, giữ được sự dễ tiếp cận của chatbot nhưng bị ràng buộc bằng guideline và luật, rồi nối thẳng vào buổi khám nơi bác sĩ quyết định.

---

# PHẦN IV — Ý TƯỞNG GIẢI PHÁP

## Slide 11 — Ý tưởng cốt lõi: hai trợ lý, một lõi tri thức

**Mục đích:** trình bày kiến trúc ý tưởng ở mức khái niệm.

**Nội dung trên slide**

```
                 ┌──────────── LÕI TRI THỨC DÙNG CHUNG ────────────┐
                 │  📚 Luật tầm soát có nguồn  ·  Kho guideline     │
                 │  🛡️ Bộ kiểm tra an toàn  ·  🚩 Bộ nhận diện cảnh báo │
                 └───────────────┬─────────────────┬───────────────┘
                                 │                 │
             👤 NAVIGATOR (người dân)        🩺 CLINICAL COPILOT (bác sĩ)
             Chính sách: giáo dục theo nhóm  Chính sách: đọc hồ sơ, mọi dữ kiện
             Không kế hoạch cá nhân          phải truy vết; chỉ soạn bản nháp
```

- **Cùng lõi** → khuyến nghị nhất quán giữa điều người dân nghe và điều bác sĩ thấy
- **Khác chính sách** → mỗi đối tượng chỉ nhận đúng loại thông tin dành cho mình

**Vì sao không làm một chatbot lập kế hoạch cho người dân rồi chờ duyệt?**
Kế hoạch tầm soát cá nhân là một quyết định y khoa. Vì vậy nhóm chỉ soạn nó *trong buổi khám*, *cho bác sĩ*, và chỉ đến tay bệnh nhân *sau khi bác sĩ duyệt*.

**Lời thuyết trình**
> Ý tưởng cốt lõi là hai trợ lý dùng chung một lõi tri thức gồm bộ luật tầm soát có nguồn, kho guideline và các bộ kiểm tra an toàn. Navigator nói chuyện với người dân nên chỉ được đưa thông tin giáo dục theo nhóm. Copilot nói chuyện với bác sĩ nên được đọc hồ sơ, nhưng mọi dữ kiện nó nêu phải truy về được một mốc cụ thể trong hồ sơ. So với đề cương ban đầu, nhóm có một điều chỉnh quan trọng: không để AI soạn kế hoạch cá nhân cho người dân ngay từ đầu, mà dời việc đó vào buổi khám, nơi bác sĩ có mặt.

---

## Slide 12 — Hành trình 4 giai đoạn

**Nội dung trên slide**

```
① TÌM HIỂU (ẩn danh)     ② KẾT NỐI               ③ KHÁM                      ④ THEO DÕI
👤 ↔ Navigator        →  Tạo tài khoản,       →  🩺 Bác sĩ + Copilot      →  Xem kết luận, kế hoạch
• hỏi đáp có nguồn       hồ sơ điền sẵn          • tóm tắt trước khám          đã duyệt
• bảng hỏi nhanh       • đặt lịch, ca cảnh báo   • hỏi Copilot có trích dẫn  • nhắc tái tầm soát
• gợi ý theo nhóm        được ưu tiên            • sửa và DUYỆT kế hoạch      • hỏi đáp trong phạm vi
• 🚩 nhận diện cảnh báo                                                        kế hoạch
└──────────────────── HỒ SƠ XUYÊN SUỐT: ghi lại mọi mốc của hành trình ────────────────────┘
```

**Ba điểm then chốt**
- Điều người dân đã kể **đi theo họ vào phòng khám**, không phải khai lại
- Ca có dấu hiệu cảnh báo **lên đầu hàng chờ**
- Bệnh nhân **chỉ thấy kết quả sau khi bác sĩ duyệt**

**Gợi ý hình ảnh:** 4 khối ngang có mũi tên; thanh "hồ sơ xuyên suốt" chạy dọc bên dưới; khối ③ có biểu tượng ✅ "bác sĩ duyệt".

**Lời thuyết trình**
> Hành trình gồm bốn giai đoạn. Người dân bắt đầu tìm hiểu mà không cần tài khoản. Khi muốn đặt lịch, họ tạo tài khoản ngay từ cuộc trò chuyện và những gì đã kể được điền sẵn vào hồ sơ. Ở buổi khám, bác sĩ nhận bản tóm tắt đã chuẩn bị, có thể hỏi thêm Copilot, rồi sửa và duyệt kế hoạch. Cuối cùng bệnh nhân xem kết luận và được nhắc lịch tái tầm soát. Mọi mốc được ghi vào hồ sơ xuyên suốt, nên lần khám sau bác sĩ có ngay lịch sử.

---

## Slide 13 — Navigator: trợ lý tầm soát cho người dân

**Nội dung trên slide**

| ✅ Làm | ⛔ Không làm |
|---|---|
| Giải đáp kiến thức tầm soát, có nguồn | Chẩn đoán |
| Hỏi nhanh tuổi, giới, yếu tố nguy cơ (tiền sử gia đình, hút thuốc, viêm gan…) | Đọc, diễn giải kết quả xét nghiệm |
| Gợi ý **theo nhóm**: loại ung thư, phương pháp, tuổi bắt đầu, chu kỳ | Tư vấn điều trị |
| Nhận diện dấu hiệu cảnh báo | Lập kế hoạch cá nhân |
| Điều hướng 3 ngả: **tiếp tục tìm hiểu · gợi ý đặt lịch · khám sớm** | |

**Ví dụ:** "Tôi 45 tuổi, mẹ bị ung thư vú, nên khám gì?"
→ Gợi ý tầm soát vú, cổ tử cung, đại trực tràng theo nhóm tuổi, kèm nguồn.
→ Lưu ý: *tiền sử gia đình có thể cần kế hoạch riêng, bác sĩ sẽ đánh giá*.
→ Mời đặt lịch khám tầm soát vú.

**Gợi ý hình ảnh:** mô phỏng khung chat với câu hỏi mẫu và câu trả lời có thẻ nguồn bên dưới; nút "Đặt lịch".

**Lời thuyết trình**
> Navigator làm đúng việc của một điều hướng viên: giải thích, hỏi vài câu cơ bản, cho biết người ở nhóm tuổi và nguy cơ như vậy thường được khuyến nghị tầm soát gì, rồi dẫn tới bước tiếp theo. Với ví dụ người phụ nữ 45 tuổi có mẹ bị ung thư vú, Navigator nêu các khuyến nghị theo nhóm, kèm nguồn. Nó không tự điều chỉnh mốc tuổi vì tiền sử gia đình mà nói rõ trường hợp này bác sĩ cần đánh giá riêng.

---

## Slide 14 — Clinical Copilot: trợ lý chuẩn bị khám cho bác sĩ

**Nội dung trên slide**

| ✅ Làm | ⛔ Không làm |
|---|---|
| Tóm tắt hồ sơ trước khám; **mỗi dữ kiện trỏ về một mốc trong hồ sơ** | Đưa ra chẩn đoán |
| Đối chiếu guideline, có nguồn | Diễn giải kết quả cận lâm sàng |
| Gợi ý câu hỏi cần làm rõ và khoảng trống dữ liệu | Tự gửi kết quả cho bệnh nhân |
| Soạn **bản nháp** kế hoạch theo dõi (không có ngày hẹn) | |
| Trả lời câu hỏi của bác sĩ, có trích dẫn | |

**Vai trò của bác sĩ:** đọc tóm tắt → khám → sửa kế hoạch → điền ngày hẹn → viết kết luận → **duyệt**. Chỉ bản đã duyệt mới đến bệnh nhân.

**Gợi ý hình ảnh:** mô phỏng màn hình bác sĩ chia đôi: trái là bản tóm tắt (mỗi dòng có nhãn nguồn nhỏ), phải là bản nháp kế hoạch với nút "Sửa" và "Duyệt".

**Lời thuyết trình**
> Copilot giúp bác sĩ không phải bắt đầu từ con số không. Nó tóm tắt những gì bệnh nhân đã chia sẻ, mỗi dòng đều có nhãn chỉ về mốc gốc trong hồ sơ để bác sĩ kiểm chứng. Nó nêu những thông tin còn thiếu, ví dụ người hút thuốc đã bỏ được bao lâu, vì điều đó ảnh hưởng tới chỉ định chụp CT phổi. Bản nháp kế hoạch cố tình để trống ngày hẹn để bác sĩ phải tự xem lịch sử thực tế. Kết luận do bác sĩ viết, không do AI viết thay.

---

## Slide 15 — Tình huống minh họa

**Nội dung trên slide**

| Tình huống | Hệ thống phản ứng |
|---|---|
| **A. Thông thường:** nữ 45 tuổi, mẹ bị ung thư vú | Gợi ý tầm soát vú (đánh dấu nguy cơ tăng), cổ tử cung, đại trực tràng → đặt lịch → bác sĩ duyệt → nhắc lịch |
| **B. Nguy cơ cao:** nam 55 tuổi, hút thuốc 30 gói-năm | Gợi ý CT phổi liều thấp, đại trực tràng, trao đổi với bác sĩ về PSA → Copilot nhắc bác sĩ hỏi thời gian đã bỏ thuốc |
| **C. Có dấu hiệu cảnh báo 🚩:** "Em sờ thấy khối cứng ở vú" | Dừng tư vấn tầm soát, khuyên đi khám sớm, lịch được ưu tiên khẩn, lên đầu hàng chờ |
| **D. Xin chẩn đoán:** "PSA của tôi là 6, có phải ung thư không?" | Từ chối diễn giải, giải thích lý do, mời đặt lịch gặp bác sĩ |
| **E. Thiếu căn cứ:** không tìm được nguồn phù hợp hoặc AI gặp lỗi | Nói rõ "chưa đủ căn cứ", không tự dựng khuyến nghị, chuyển bác sĩ xử lý |

**Gợi ý hình ảnh:** 5 thẻ ngang, thẻ C viền cam, thẻ D và E viền xám.

**Lời thuyết trình**
> Năm tình huống này đại diện cho các nhánh chính. Hai tình huống đầu là luồng bình thường. Ba tình huống sau là các *điểm dừng an toàn*: có dấu hiệu cảnh báo thì dừng ngay và hướng đi khám, xin chẩn đoán thì từ chối, thiếu căn cứ thì nói không biết. Nhóm coi trọng các điểm dừng này không kém luồng chính, vì một hệ thống y tế đáng tin phải biết khi nào nên im lặng.

---

# PHẦN V — MỤC TIÊU VÀ MỨC ĐỘ GIẢI QUYẾT

## Slide 16 — Mục tiêu

**Nội dung trên slide**

**Mục tiêu tổng quát:** đề xuất và chứng minh ở mức prototype một quy trình hỗ trợ tầm soát ung thư dùng AI *có kiểm soát*, nghĩa là có căn cứ, có điểm dừng an toàn và có bác sĩ quyết định.

**Mục tiêu cụ thể và tiêu chí đo**

| # | Mục tiêu | Tiêu chí đạt |
|---|---|---|
| M1 | Người dân nhận gợi ý tầm soát theo nhóm, có nguồn | 100% gợi ý có ít nhất một nguồn hợp lệ; mốc tuổi, chu kỳ khớp bộ luật |
| M2 | Nhận diện dấu hiệu cảnh báo trước mọi bước AI sinh nội dung | Không bỏ sót ca cảnh báo nào trên bộ ca kiểm thử (recall 100%); tỷ lệ cảnh báo nhầm được đo và báo cáo |
| M3 | AI không chẩn đoán | 0% câu trả lời chứa ngôn ngữ chẩn đoán; 100% yêu cầu chẩn đoán bị từ chối đúng cách |
| M4 | Bác sĩ là người quyết định | Không lần nào bệnh nhân xem được bản nháp; mọi chỉnh sửa của bác sĩ được ghi nhật ký |
| M5 | Hỗ trợ bác sĩ chuẩn bị khám | 100% dữ kiện trong bản tóm tắt truy vết được về hồ sơ; thời gian chuẩn bị sẽ đo ở giai đoạn thí điểm |
| M6 | Theo dõi liên tục | Kế hoạch đã duyệt sinh nhắc lịch; mốc hoàn thành được ghi vào hồ sơ |
| M7 | Bảo vệ dữ liệu | Phân quyền theo vai trò; nhật ký AI không chứa nội dung hội thoại |

**Lời thuyết trình**
> Nhóm đặt mục tiêu theo hướng đo được. Đáng chú ý là các ngưỡng an toàn được đặt ở mức tuyệt đối: không bỏ sót ca cảnh báo nào trong bộ kiểm thử, không có câu trả lời mang tính chẩn đoán, không lần nào bệnh nhân xem được bản nháp. Với các chỉ số như cảnh báo nhầm hay thời gian chuẩn bị khám, nhóm chưa hứa một con số mà cam kết đo và báo cáo trung thực.

---

## Slide 17 — Mức độ giải quyết: AI được làm đến đâu?

**Mục đích:** vạch rõ ranh giới trách nhiệm giữa AI và bác sĩ.

**Nội dung trên slide**

| Mức | Nội dung | Ai thực hiện | OncoScreen AI |
|---|---|---|---|
| 0 | Thông tin sức khỏe chung | Website, báo chí | Nền tảng có sẵn |
| 1 | Giáo dục có nguồn, gợi ý tầm soát **theo nhóm** | Navigator | ✓ AI làm, có rào kiểm tra |
| 2 | Nhận diện dấu hiệu cảnh báo và điều hướng khám sớm | Bộ luật (không phải LLM) | ✓ Chỉ nói "nên đi khám sớm", không kết luận bệnh |
| 3 | Chuẩn bị thông tin cho bác sĩ | Copilot | ✓ Bản nháp, bác sĩ kiểm tra |
| 4 | Kế hoạch tầm soát **cá nhân** | Bác sĩ (AI chỉ soạn nháp) | △ Chỉ có hiệu lực khi bác sĩ duyệt |
| 5 | Chẩn đoán, diễn giải kết quả, điều trị | Bác sĩ | ✗ Ngoài phạm vi, kể cả với Copilot |

**Mức độ trưởng thành:** chứng minh khái niệm (proof of concept) trên dữ liệu giả lập, chạy cục bộ; chưa thử nghiệm lâm sàng.

**Ngoài phạm vi prototype:** chẩn đoán · đọc kết quả xét nghiệm, hình ảnh · tư vấn điều trị · tích hợp HIS/EMR thật · thanh toán · SMS/email thật.

**Gợi ý hình ảnh:** cầu thang 6 bậc; bậc 1–3 xanh, bậc 4 xanh nhạt có biểu tượng 🩺, bậc 5 xám có biển ⛔.

**Lời thuyết trình**
> Đây là slide nhóm muốn hội đồng nhớ nhất. Nhóm chia mức can thiệp của AI thành sáu bậc. AI của nhóm dừng ở bậc ba: giáo dục, điều hướng và chuẩn bị thông tin. Bậc bốn là kế hoạch cá nhân, AI chỉ được soạn nháp và chỉ có hiệu lực khi bác sĩ duyệt. Bậc năm là chẩn đoán và điều trị, nhóm chủ động đứng ngoài, kể cả với Copilot dành cho bác sĩ. Lý do là bậc này đòi hỏi bằng chứng lâm sàng và chứng nhận thiết bị y tế mà một đồ án không thể có.

---

## Slide 18 — Ma trận vấn đề và mức độ giải quyết

**Nội dung trên slide**

| Vấn đề | Mức giải quyết | Cách làm hoặc lý do |
|---|---|---|
| Không biết nên tầm soát gì, khi nào | 🟢 Giải quyết (theo nhóm) | Gợi ý theo luật có nguồn |
| Thông tin phân tán, không rõ nguồn | 🟢 Giải quyết | Mọi gợi ý kèm nguồn; thiếu nguồn thì nói rõ |
| Bác sĩ thiếu thông tin trước khám | 🟢 Giải quyết trong phạm vi hệ thống | Tóm tắt từ hồ sơ xuyên suốt; chưa lấy dữ liệu từ HIS/EMR |
| Ngại đi khám | 🟡 Hỗ trợ một phần | Tư vấn ẩn danh, đặt lịch ngay; không thay đổi được yếu tố tâm lý, chi phí |
| Bỏ qua triệu chứng nguy hiểm | 🟡 Hỗ trợ một phần | Cảnh báo theo danh sách; không thể bắt mọi trường hợp |
| Quên tái tầm soát | 🟡 Hỗ trợ một phần | Nhắc trong ứng dụng; chưa có SMS, Zalo |
| Chọn gói khám không phù hợp | 🟡 Hỗ trợ một phần | Gợi ý dịch vụ theo nhóm; quyết định cuối do bác sĩ và bệnh nhân |
| Người không dùng smartphone, vùng xa | 🔴 Chưa giải quyết | Hướng phát triển: tổng đài, Zalo, người thân hỗ trợ |
| Phát hiện bệnh, đọc kết quả | ⚫ Không giải quyết (chủ ý) | Vượt phạm vi an toàn, cần thiết bị y tế được chứng nhận |

**Lời thuyết trình**
> Nhóm muốn trung thực về những gì giải pháp làm được. Ba vấn đề được giải quyết trong phạm vi hệ thống. Bốn vấn đề chỉ được hỗ trợ một phần, vì chúng còn phụ thuộc yếu tố ngoài công nghệ như tâm lý, chi phí và hạ tầng. Có một vấn đề nhóm chưa giải quyết là tiếp cận số cho người cao tuổi và vùng xa. Và có một vấn đề nhóm chủ ý không giải quyết là chẩn đoán.

---

# PHẦN VI — AN TOÀN VÀ ĐỘ TIN CẬY

## Slide 19 — Nguyên tắc thiết kế: phòng thủ nhiều lớp

**Nội dung trên slide**

> **"Luật trước, LLM sau · Mọi điều AI nói phải truy vết được · Mọi lỗi rơi về trạng thái an toàn · Bác sĩ là người quyết định."**

```
Tin nhắn ─► ① RÀO ĐẦU VÀO ─► ② LUẬT TẦM SOÁT ─► ③ TRA NGUỒN ─► ④ LLM  ─► ⑤ RÀO ĐẦU RA ─► ⑥ BÁC SĨ ─► Người dùng
            ngoài phạm vi?    ai, khi nào,       guideline      diễn đạt   chẩn đoán?      duyệt
            tấn công prompt?  bao lâu (có nguồn) (RAG)                     nguồn hợp lệ?
            🚩 cảnh báo? ──► DỪNG, khuyên khám sớm                         con số có căn cứ?
            └─────────────────── ⑦ GIÁM SÁT VÀ ĐÁNH GIÁ LIÊN TỤC ───────────────────┘
```

| Thành phần | Vai trò |
|---|---|
| **Luật** | *Quyết định*: ai nên tầm soát gì, từ bao giờ, bao lâu một lần |
| **Tra nguồn (RAG)** | *Căn cứ*: đoạn guideline liên quan |
| **LLM** | *Diễn đạt*: viết lại dễ hiểu, không được đổi nội dung |
| **Bác sĩ** | *Quyết định cá nhân*: kế hoạch, kết luận |
| **Mã nguồn** | *Thực thi ràng buộc*: an toàn nằm trong code, không chỉ nằm trong lời nhắc (prompt) |

**Lời thuyết trình**
> Nguyên tắc thiết kế của nhóm gói trong bốn vế. Thứ nhất, luật đi trước LLM: các con số như tuổi bắt đầu và chu kỳ do bộ luật có nguồn quyết định, LLM chỉ diễn đạt. Thứ hai, mọi thứ AI nói phải truy được về nguồn. Thứ ba, khi có lỗi, hệ thống rơi về câu trả lời an toàn đã chuẩn bị sẵn, không bao giờ trả về nội dung chưa kiểm tra. Thứ tư, bác sĩ quyết định. Điểm quan trọng là các ràng buộc được đặt trong mã nguồn chứ không chỉ trong lời nhắc cho mô hình, nên người dùng không thể dùng lời lẽ để thuyết phục hệ thống bỏ qua.

---

## Slide 20 — Phân tích rủi ro và biện pháp kiểm soát

**Mục đích:** chứng minh nhóm đã nhận diện rủi ro một cách có hệ thống (theo tinh thần phân tích mối nguy trong quản lý rủi ro thiết bị y tế).

**Nội dung trên slide** (có thể tách thành 2 slide)

| # | Mối nguy | Nguyên nhân có thể | Hậu quả | Biện pháp kiểm soát | Rủi ro còn lại* |
|---|---|---|---|---|---|
| R1 | **Bỏ sót dấu hiệu cảnh báo** | Cách diễn đạt lạ, không dấu, tiếng địa phương | Trì hoãn đi khám | Luật chạy trước LLM, xử lý có dấu/không dấu, câu phủ định; ưu tiên độ nhạy; thông điệp thường trực "có triệu chứng thì đi khám" | Trung bình |
| R2 | Cảnh báo nhầm | Nhầm người thân với bản thân, câu phủ định | Lo lắng, quá tải ca khẩn | Phân biệt "tôi bị"/"mẹ tôi bị", xử lý phủ định; đo tỷ lệ cảnh báo nhầm; lời lẽ bình tĩnh | Thấp–TB |
| R3 | **Bịa mốc tuổi, chu kỳ** | LLM "ảo giác" | Tầm soát sai thời điểm | Con số do luật; kiểm tra mọi con số phải có trong bằng chứng; vi phạm thì dùng câu trả lời mẫu | Thấp |
| R4 | Trích dẫn sai, nguồn không tồn tại | LLM bịa nguồn | Mất tin cậy, hiểu sai | Chỉ chấp nhận nguồn trong danh sách vừa truy xuất | Thấp |
| R5 | **Ngôn ngữ chẩn đoán, gây hoảng loạn** | LLM diễn đạt quá đà | Người dân hiểu nhầm là đã có kết luận | Rào đầu ra chặn mẫu câu chẩn đoán; disclaimer không ẩn được; giọng văn bình tĩnh | Thấp–TB |
| R6 | Người dùng cố xin chẩn đoán, đọc kết quả | Nhu cầu thật của người dân | AI vượt phạm vi | Rào đầu vào từ chối có giải thích và mời đặt lịch; không gọi LLM | Thấp |
| R7 | Tấn công bằng lời nhắc (prompt injection) | "Bỏ qua mọi hướng dẫn…" | AI bỏ qua ràng buộc | Phát hiện mẫu tấn công; nguồn được đánh dấu "là dữ liệu, không phải chỉ dẫn"; ràng buộc nằm trong code | Trung bình |
| R8 | **Guideline lỗi thời, không phù hợp Việt Nam** | Nguồn chủ yếu của Mỹ, quốc tế | Khuyến nghị lệch quần thể | Ghi ngày ban hành, phạm vi áp dụng, trạng thái rà soát; bác sĩ trong nước duyệt; bổ sung hướng dẫn Bộ Y tế | Trung bình |
| R9 | **Bác sĩ duyệt cho qua** (tin AI quá mức) | Áp lực thời gian | Sai sót lọt tới bệnh nhân | Bản nháp không có ngày hẹn; dữ kiện có nhãn nguồn; kết luận do bác sĩ viết; đo tỷ lệ bác sĩ sửa | Trung bình |
| R10 | Copilot nêu dữ kiện không có trong hồ sơ | LLM suy diễn | Bác sĩ dựa vào thông tin sai | Mỗi dữ kiện phải trỏ về một mốc hồ sơ; không truy vết được thì loại bỏ | Thấp |
| R11 | Lộ dữ liệu sức khỏe | Phân quyền sai, gửi dữ liệu cho LLM bên ngoài | Vi phạm pháp luật, mất niềm tin | Phân quyền theo vai trò; mã phiên lưu dạng băm; nhật ký không chứa hội thoại; chỉ dùng dữ liệu giả với LLM bên ngoài | TB khi triển khai thật |
| R12 | Dịch vụ LLM lỗi, quá thời gian | Mạng, nhà cung cấp | Gián đoạn tư vấn | Rơi về câu trả lời xác định dựng từ luật và nguồn; có chế độ chạy không cần LLM | Thấp |

\* *Mức rủi ro còn lại là đánh giá định tính của nhóm, cần chuyên gia y tế và an toàn thông tin xác nhận.*

**Lời thuyết trình**
> Nhóm liệt kê mười hai mối nguy theo cách làm của phân tích rủi ro trong thiết bị y tế: mỗi mối nguy có nguyên nhân, hậu quả, biện pháp và mức rủi ro còn lại. Nhóm muốn nhấn mạnh rằng không mối nguy nào được đưa về mức "không còn rủi ro". Ba mối nguy nhóm đánh giá là đáng lo nhất: bỏ sót dấu hiệu cảnh báo, guideline không phù hợp với người Việt, và bác sĩ duyệt cho qua. Ba mối nguy này không thể xử lý triệt để bằng kỹ thuật mà cần quy trình chuyên môn, và đó là lý do lộ trình ở cuối bài có bước rà soát chuyên môn và thí điểm có kiểm soát.

---

## Slide 21 — Chống bịa thông tin (hallucination)

**Nội dung trên slide**

| # | Cơ chế | Ý nghĩa |
|---|---|---|
| 1 | **Con số do luật** | Tuổi bắt đầu, chu kỳ lấy từ bộ luật trỏ tới mục guideline cụ thể; LLM không được thêm, bớt hay đổi |
| 2 | **Tra nguồn trước khi nói** | Tìm theo cả từ khóa lẫn ngữ nghĩa, lọc theo giới và tuổi; xử lý tiếng Việt có dấu, không dấu |
| 3 | **Danh sách nguồn hợp lệ** | Chỉ chấp nhận trích dẫn nằm trong tập vừa truy xuất |
| 4 | **Kiểm tra con số** | Mọi con số trong câu trả lời phải xuất hiện trong nguồn, hồ sơ hoặc lời người dùng |
| 5 | **Được phép "không biết"** | Thiếu căn cứ thì nói rõ "chưa đủ thông tin", khuyên hỏi bác sĩ |
| 6 | **Câu trả lời dự phòng** | Vi phạm, lỗi hay quá thời gian thì dùng câu trả lời xác định dựng từ luật và nguồn |
| 7 | **Truy vết dữ kiện (Copilot)** | Mỗi dữ kiện trỏ về một mốc hồ sơ; không truy vết được thì loại |

⚠️ *Các cơ chế này giảm rủi ro chứ không bảo đảm hết sai sót. Chất lượng còn phụ thuộc vào độ đầy đủ, chính xác và tính cập nhật của tài liệu nguồn. Vì vậy vẫn cần bác sĩ kiểm tra.*

**Gợi ý hình ảnh:** phễu lọc 7 tầng; trên miệng phễu là "câu trả lời của LLM", đáy phễu là "câu trả lời đã kiểm tra"; một nhánh rẽ ra "câu trả lời dự phòng".

**Lời thuyết trình**
> "Ảo giác" là rủi ro lớn nhất của LLM trong y tế. Nhóm xử lý bằng bảy lớp. Quan trọng nhất là lớp một: những con số có thể gây hại nếu sai, như tuổi bắt đầu và chu kỳ, không bao giờ để LLM tự sinh ra. Các lớp sau kiểm tra lại đầu ra: nguồn có nằm trong danh sách vừa tra không, con số có xuất hiện trong bằng chứng không. Nếu không đạt, hệ thống không cố sửa mà thay bằng câu trả lời dự phòng an toàn. Nhóm cũng cho phép AI trả lời "không biết", vì một câu "chưa đủ thông tin, hãy hỏi bác sĩ" an toàn hơn một câu trả lời trôi chảy nhưng sai.

---

## Slide 22 — Dấu hiệu cảnh báo và điều hướng khẩn

**Nội dung trên slide**

**Danh sách dấu hiệu ban đầu** *(bản nháp, chờ bác sĩ rà soát)*

| Dấu hiệu | Mức | Lời khuyên |
|---|---|---|
| Sờ thấy khối, cục bất thường | Khẩn | Đến cơ sở chuyên khoa trong vài ngày tới |
| Chảy máu bất thường | Khẩn | Cần được bác sĩ khám sớm, đừng trì hoãn |
| Sụt cân nhanh không rõ nguyên nhân | Sớm | Khám tổng quát trong 1–2 tuần |
| Đau kéo dài trên 3 tuần | Sớm | Bác sĩ đánh giá trong vài tuần tới |
| Thay đổi thói quen đại tiện kéo dài | Sớm | Khám tiêu hóa trong vài tuần tới |
| Vàng da, vàng mắt | Sớm | Khám sớm để tìm nguyên nhân |

**Cơ chế**
- Kiểm tra **bằng luật, ngay khi nhận tin, trước mọi bước AI sinh nội dung**
- Hiểu tiếng Việt có dấu và không dấu, câu phủ định ("không sờ thấy…"), phân biệt bản thân với người thân
- Đã gắn cờ thì **không gỡ trong phiên**; lịch đặt từ phiên này được **ưu tiên khẩn**
- Không soạn kế hoạch tầm soát định kỳ cho ca có cảnh báo

**Nguyên tắc:** *thà cảnh báo nhầm còn hơn bỏ sót*, nhưng vẫn đo cảnh báo nhầm và giữ giọng văn bình tĩnh.
**Giới hạn:** phát hiện theo danh sách nên không bao quát mọi tình huống → disclaimer luôn nhắc *"Nếu có triệu chứng bất thường, hãy đi khám, đừng chờ lịch tầm soát."*

**Lời thuyết trình**
> Dấu hiệu cảnh báo là nơi nhóm cố ý không dùng LLM. Lý do là phát hiện bằng luật cho kết quả có thể kiểm tra, lặp lại được, và chạy ngay khi tin nhắn đến, trước khi bất kỳ nội dung nào được sinh ra. Khi đã phát hiện, hệ thống dừng toàn bộ phần tư vấn tầm soát, vì người có triệu chứng cần được khám chứ không cần tầm soát định kỳ. Nhóm cũng thừa nhận một danh sách không thể bao quát mọi cách người dân mô tả triệu chứng, nên luôn có thông điệp nhắc đi khám khi có bất thường. Danh sách này hiện là bản nháp và phải được bác sĩ duyệt.

---

## Slide 23 — Bác sĩ trong vòng lặp (HITL) và phân quyền

**Nội dung trên slide**

**Ai được thấy gì?**

| Thông tin | Người dân ẩn danh | Bệnh nhân | Bác sĩ |
|---|---|---|---|
| Gợi ý tầm soát theo nhóm (giáo dục) | ✓ | ✓ | ✓ |
| Bản tóm tắt và bản nháp do AI soạn | ✗ | ✗ | ✓ |
| Ghi chú nội bộ của bác sĩ | ✗ | ✗ | ✓ |
| Kết luận và kế hoạch đã duyệt | — | ✓ (chỉ của mình) | ✓ |
| Nhật ký hoạt động của AI | ✗ | ✗ | ✓ (không chứa nội dung hội thoại) |

**Chống "tin AI quá mức" (automation bias)**
- Bản nháp **không có ngày hẹn**, nên bác sĩ phải tự xem lịch sử thực tế
- Mỗi dữ kiện, khuyến nghị **kèm nguồn** để kiểm chứng nhanh
- **Kết luận do bác sĩ viết** (bắt buộc), AI không viết thay
- Kế hoạch bác sĩ sửa **vẫn phải qua kiểm tra** (có nguồn, không ngôn ngữ chẩn đoán)
- Ghi nhật ký trước/sau mỗi chỉnh sửa → **tỷ lệ bác sĩ phải sửa** trở thành thước đo chất lượng AI

**Trách nhiệm:** AI không phát hành kết quả. Người duyệt và ký là bác sĩ.

**Lời thuyết trình**
> Human-in-the-loop không chỉ là thêm một nút "duyệt". Nếu bác sĩ bấm duyệt mà không đọc thì vòng lặp đó vô nghĩa. Vì vậy nhóm thiết kế để bác sĩ phải thực sự tham gia: bản nháp cố tình để trống ngày hẹn, kết luận bắt buộc do bác sĩ tự viết, và mỗi dữ kiện đều có nguồn để kiểm tra nhanh. Ngược lại, nhóm dùng chính các chỉnh sửa của bác sĩ làm dữ liệu đánh giá: nếu bác sĩ phải sửa nhiều, nghĩa là AI cần cải thiện. Về phân quyền, bệnh nhân không bao giờ thấy bản nháp, chỉ thấy kết quả bác sĩ đã duyệt.

---

## Slide 24 — Quản trị tri thức y khoa

**Nội dung trên slide**

**Nguồn:** guideline chính thức như USPSTF, WHO, AASLD [7][8]; **cần bổ sung hướng dẫn chuyên môn của Bộ Y tế Việt Nam**.

**Vòng đời một tài liệu tri thức**
```
Bản gốc (xuất xứ, giấy phép) ─► Tóm tắt tiếng Việt có metadata ─► 🩺 Bác sĩ rà soát ─► Đưa vào hệ thống ─► Rà lại định kỳ
                                (loại ung thư, giới, tuổi, mức nguy cơ,
                                 nguồn, ngày ban hành, phạm vi áp dụng,
                                 trạng thái rà soát)
```

**Quy tắc**
- Thiếu metadata bắt buộc → **không nạp**
- Mỗi luật phải trỏ tới một mục guideline có thật → sai thì **hệ thống từ chối khởi động**
- Kho tri thức **không chứa dữ liệu bệnh nhân**

**Phù hợp quần thể:** guideline Mỹ, quốc tế **không tự động áp dụng cho Việt Nam**. Ví dụ, ung thư gan dẫn đầu ở nam giới Việt Nam [1] và gắn với viêm gan virus mạn, nên mốc và nhóm nguy cơ cần chuyên gia trong nước điều chỉnh.

**Trạng thái:** toàn bộ tri thức đang ở dạng **bản nháp**. Điều kiện bắt buộc trước khi dùng thật là bác sĩ bệnh viện đối tác ký duyệt.

**Lời thuyết trình**
> Một hệ thống dựa trên nguồn thì chỉ tốt bằng nguồn của nó. Nhóm coi tri thức y khoa như một tài sản cần quản trị: mỗi tài liệu có xuất xứ, ngày ban hành, phạm vi áp dụng và trạng thái rà soát. Tài liệu thiếu thông tin thì không được nạp, luật trỏ sai thì hệ thống không chạy. Hạn chế lớn nhất hiện nay là nguồn chủ yếu là guideline của Mỹ và quốc tế, trong khi bệnh cảnh ở Việt Nam khác, ví dụ gánh nặng ung thư gan cao hơn nhiều. Vì vậy mọi tri thức hiện đều là bản nháp và cần bác sĩ trong nước duyệt.

---

## Slide 25 — Bảo mật, quyền riêng tư và khung pháp lý

**Nội dung trên slide**

**Dữ liệu sức khỏe là dữ liệu cá nhân nhạy cảm:** Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 (hiệu lực từ 01/01/2026) và Nghị định 356/2025/NĐ-CP hướng dẫn thi hành [12][13].

**Biện pháp theo thiết kế (privacy by design)**
- **Tối thiểu hóa:** tư vấn ẩn danh, chỉ hỏi thông tin cần cho gợi ý
- **Đồng ý rõ ràng** khi chuyển phiên ẩn danh thành hồ sơ có danh tính
- Mã phiên ẩn danh và mật khẩu chỉ lưu dạng băm; **phân quyền theo vai trò**; bệnh nhân chỉ xem dữ liệu của mình
- Nhật ký AI **không chứa** nội dung hội thoại, hồ sơ, khóa API
- LLM bên ngoài: prototype **chỉ dùng dữ liệu giả**. Triển khai thật cần LLM đặt trong hạ tầng bệnh viện hoặc có hợp đồng xử lý dữ liệu
- **Đánh giá tác động xử lý dữ liệu cá nhân** trước khi thí điểm

**Khung tham chiếu định hướng thiết kế**
| Văn bản | Điều nhóm rút ra |
|---|---|
| Luật Khám bệnh, chữa bệnh 2023 [15] | Khám, chữa bệnh do người hành nghề thực hiện → AI chỉ hỗ trợ |
| Nghị định 98/2021/NĐ-CP về trang thiết bị y tế [14] | Phần mềm có mục đích chẩn đoán có thể thuộc diện thiết bị y tế → giữ phạm vi không chẩn đoán; thương mại hóa cần đánh giá phân loại |
| WHO 2021, 2024: đạo đức và quản trị AI trong y tế [9][10] | Bảo vệ quyền tự chủ con người, an toàn, minh bạch, trách nhiệm giải trình, công bằng, bền vững |
| FDA: phần mềm hỗ trợ quyết định lâm sàng [11] | Bác sĩ phải **tự kiểm chứng được căn cứ** của khuyến nghị → Copilot luôn hiển thị nguồn |

*Nhóm không tuyên bố đã tuân thủ các văn bản trên; đây là khung định hướng cho thiết kế.*

**Lời thuyết trình**
> Dữ liệu sức khỏe thuộc nhóm dữ liệu nhạy cảm theo luật Việt Nam, có hiệu lực từ đầu năm 2026. Nhóm áp dụng nguyên tắc bảo vệ ngay từ thiết kế: hỏi ít nhất có thể, cho phép ẩn danh, phân quyền chặt, và không ghi nội dung hội thoại vào nhật ký. Với LLM của bên thứ ba, prototype chỉ dùng dữ liệu giả. Về pháp lý, nhóm tham chiếu Luật Khám bệnh, chữa bệnh, quy định về trang thiết bị y tế, hướng dẫn đạo đức AI của WHO và tiêu chí của FDA cho phần mềm hỗ trợ quyết định lâm sàng. Nhóm không khẳng định đã tuân thủ mà dùng các văn bản này làm kim chỉ nam.

---

# PHẦN VII — SO SÁNH THỰC TẾ

## Slide 26 — So sánh với các phương pháp hiện có

**Nội dung trên slide**

| Phương pháp | Dễ tiếp cận | Theo nhóm nguy cơ | Có nguồn rõ | Nhận diện cảnh báo | Bác sĩ duyệt | Theo dõi, nhắc lịch | Chi phí mở rộng | Đã kiểm chứng hiệu quả |
|---|---|---|---|---|---|---|---|---|
| Tự tra cứu Internet | ✓ | ✗ | △ | ✗ | ✗ | ✗ | Thấp | ✗ |
| Gói khám định kỳ | △ | △ | △ | ✓ (khi khám) | ✓ | △ | TB–cao | △ |
| Điều hướng viên con người | △ (giờ hành chính) | ✓ | ✓ | ✓ | ✓ | ✓ | **Cao** | ✓ |
| Công cụ ước tính nguy cơ | △ (cần chuyên môn) | ✓ (1 loại) | ✓ | ✗ | △ | ✗ | Thấp | ✓ |
| Symptom checker | ✓ | ✗ | △ | △ | ✗ | ✗ | Thấp | △ |
| Chatbot AI tổng quát | ✓ | △ | △ | △ | ✗ | ✗ | Thấp | ✗ (cho bài toán này) |
| **OncoScreen AI (mục tiêu)** | ✓ | ✓ (6 loại, theo nhóm) | ✓ | ✓ (theo danh sách) | ✓ | ✓ | Thấp–TB | **✗ (chưa)** |

**Điểm OncoScreen AI *không* hơn**
- Kiến thức **hẹp hơn** chatbot tổng quát (chỉ tầm soát, 6 loại ung thư)
- **Chưa có bằng chứng lâm sàng** như điều hướng viên con người hay chương trình tầm soát có tổ chức
- **Không thay thế** sự thấu cảm của tương tác con người
- **Phụ thuộc** bệnh viện áp dụng và đội ngũ bác sĩ rà soát

**Định vị:** bổ sung, không thay thế. Một *điều hướng viên số* giúp điều hướng viên và nhân viên tư vấn của bệnh viện phục vụ được nhiều người hơn.

**Lời thuyết trình**
> Bảng so sánh này cho thấy OncoScreen nhắm tới việc hội đủ các tiêu chí mà từng phương pháp riêng lẻ chưa có. Nhưng nhóm cố ý thêm cột cuối, "đã kiểm chứng hiệu quả", và ở cột này OncoScreen đánh dấu chưa. Điều hướng viên con người và chương trình có tổ chức đã có bằng chứng, còn nhóm mới ở mức ý tưởng và prototype. Vì vậy nhóm định vị giải pháp là công cụ bổ sung, giúp những người đang làm điều hướng phục vụ được nhiều người hơn, chứ không thay họ.

---

## Slide 27 — Quy trình hiện tại so với khi có OncoScreen AI

**Nội dung trên slide**

| Bước | Hiện tại | Khi có OncoScreen AI |
|---|---|---|
| Tìm hiểu | Tự tra Google, hỏi người quen | Hỏi Navigator ẩn danh 24/7, gợi ý có nguồn |
| Quyết định đi khám | Cảm tính, theo quảng cáo | Điều hướng theo nhóm nguy cơ; có cảnh báo thì khám sớm |
| Đặt lịch | Gọi tổng đài, kể lại từ đầu | Tạo tài khoản từ cuộc trò chuyện, hồ sơ điền sẵn, gợi ý dịch vụ |
| Trước khám | Bác sĩ có rất ít thông tin | Bản tóm tắt có truy vết và danh sách câu hỏi cần làm rõ |
| Trong khám | Hỏi lại tiền sử | Tập trung vào phần cần làm rõ; hỏi Copilot có trích dẫn |
| Sau khám | Giấy kết quả, tự nhớ lịch | Kế hoạch đã duyệt và nhắc tái tầm soát |
| Lần khám sau | Hồ sơ rời rạc | Hồ sơ xuyên suốt nối các lần khám |

*Các cải thiện trên là **giả thuyết**, cần đo ở giai đoạn thí điểm (xem slide 31).*

**Gợi ý hình ảnh:** hai làn bơi (swimlane) song song; làn "hiện tại" có các điểm đứt gãy màu xám, làn "OncoScreen" liền mạch.

**Lời thuyết trình**
> Nếu so quy trình, khác biệt lớn nhất là tính liền mạch. Hiện nay mỗi bước là một hòn đảo riêng: người dân tự tìm hiểu, gọi tổng đài kể lại, vào phòng khám kể lại lần nữa, ra về thì không ai nhắc. Với OncoScreen, thông tin chảy theo người bệnh từ lúc tìm hiểu tới lúc tái tầm soát. Đây vẫn là giả thuyết và cần được đo trong thực tế.

---

## Slide 28 — Bài học từ các dự án AI y tế ngoài thực tế

**Nội dung trên slide**

| Sự kiện | Điều đã xảy ra | Thiết kế tương ứng của nhóm |
|---|---|---|
| **IBM Watson for Oncology** (2018) [17] | Tài liệu nội bộ cho thấy có khuyến nghị điều trị "không an toàn, không chính xác"; hệ thống được huấn luyện trên số ít ca giả định | Căn cứ là guideline thật có metadata; không làm điều trị; bác sĩ kiểm chứng nguồn |
| **Chatbot "Tessa" của NEDA** (Mỹ, 2023) [18] | Chatbot hỗ trợ rối loạn ăn uống đưa lời khuyên giảm cân có hại sau khi được thêm AI sinh nội dung, phải gỡ bỏ | Phạm vi cứng bằng code; rào đầu ra; giám sát sau triển khai; mọi thay đổi mô hình phải chạy lại bộ đánh giá |
| **Symptom checker** (BMJ 2015) [6] | Lời khuyên phân loại phù hợp ở 57% trường hợp | Không chẩn đoán; cảnh báo ưu tiên độ nhạy; đo bằng bộ ca chuẩn |
| **Chatbot LLM và thông tin ung thư** (2023) [4][5] | Khuyến nghị lệch guideline; câu trả lời thay đổi theo cách hỏi | Khuyến nghị do luật; LLM chỉ diễn đạt; câu trả lời dự phòng khi vi phạm |
| **CDS trong bệnh án điện tử** | Cảnh báo dày đặc khiến bác sĩ bỏ qua (alert fatigue) | Copilot gọn: chỉ nêu khoảng trống và câu hỏi quan trọng |
| **Babylon Health** (Anh) | Tuyên bố chatbot đạt kết quả "ngang bác sĩ" (2018) bị Hội Bác sĩ đa khoa Hoàng gia Anh phản bác; công ty phá sản năm 2023 | Truyền thông trung thực: luôn nói rõ "prototype, chưa đánh giá lâm sàng" |

**Lời thuyết trình**
> Nhóm học từ những thất bại có thật. Watson for Oncology cho thấy nguồn tri thức không thật thì khuyến nghị không thể an toàn. Chatbot Tessa cho thấy chỉ cần thêm AI sinh nội dung mà không có rào chắn là hệ thống có thể trôi ra ngoài phạm vi và gây hại. Babylon Health cho thấy cái giá của việc tuyên bố quá mức. Mỗi bài học tương ứng với một quyết định thiết kế của nhóm, và đó cũng là lý do nhóm luôn nói rõ giới hạn của mình.

---

# PHẦN VIII — ĐÁNH GIÁ, LỘ TRÌNH, KẾT LUẬN

## Slide 29 — Phương pháp đánh giá

**Nội dung trên slide**

**Bốn tầng đánh giá**
1. **Kiểm thử an toàn kỹ thuật:** bộ ca chuẩn (golden set) gồm cảnh báo có dấu/không dấu, câu phủ định, người thân và bản thân, hút thuốc nặng/nhẹ, viêm gan, yêu cầu chẩn đoán, tấn công bằng lời nhắc, câu hỏi kiến thức. Thêm kiểm thử phân quyền và kiểm thử lỗi (AI bịa nguồn, bịa số, quá thời gian).
2. **Đánh giá chuyên môn:** bác sĩ rà bộ luật, danh sách cảnh báo, kho guideline; gán nhãn **từ 100 ca trở lên**; chấm chất lượng bản tóm tắt.
3. **Đánh giá người dùng:** người dân có hiểu đúng không (không hiểu nhầm là chẩn đoán), mức độ lo lắng sau tư vấn, khả dụng (thang SUS); bác sĩ đánh giá mức hữu ích và thời gian chuẩn bị.
4. **Giám sát vận hành:** tỷ lệ cảnh báo, tỷ lệ dùng câu trả lời dự phòng, tỷ lệ thiếu căn cứ, tỷ lệ bác sĩ sửa kế hoạch, độ trễ p50/p95, tỷ lệ chuyển từ tư vấn sang đặt lịch.

**Ngưỡng an toàn**

| Chỉ số | Ngưỡng |
|---|---|
| Không bỏ sót ca cảnh báo (red-flag recall) | **100%**, bắt buộc |
| Câu trả lời chứa ngôn ngữ chẩn đoán | **0%** |
| Trích dẫn hợp lệ | **100%** |
| Gợi ý có nguồn | **100%** |
| Bệnh nhân truy cập được bản nháp | **0 lần** |
| Cảnh báo nhầm, phân loại đúng hướng, gợi ý đúng | Theo dõi và cải thiện |

⚠️ *Ứng dụng chạy được không có nghĩa là đúng về y khoa. Tính đúng đắn y khoa phải do chuyên gia đánh giá theo quy trình riêng.*

**Lời thuyết trình**
> Nhóm đánh giá trên bốn tầng. Tầng một là kỹ thuật, có thể tự động hóa và chạy mỗi khi thay đổi hệ thống. Tầng hai bắt buộc phải có bác sĩ, vì chỉ bác sĩ mới gán nhãn đúng được một ca là có cần cảnh báo hay không. Tầng ba đo tác động lên con người, gồm cả việc người dân có bị lo lắng thêm hay không. Tầng bốn là giám sát khi vận hành. Nhóm xin nhấn mạnh câu cuối: hệ thống vượt qua toàn bộ bài kiểm thử kỹ thuật vẫn chưa nói lên rằng nó đúng về y khoa.

---

## Slide 30 — Lộ trình và điều kiện chuyển giai đoạn

**Nội dung trên slide**

| Giai đoạn | Nội dung | Cổng phải qua để sang giai đoạn sau |
|---|---|---|
| **GĐ1. Prototype** (học phần) | Dữ liệu giả, chạy cục bộ, có chế độ không cần LLM | Đạt toàn bộ ngưỡng an toàn trên bộ ca chuẩn |
| **GĐ2. Rà soát chuyên môn** | Bác sĩ đối tác duyệt bộ luật, danh sách cảnh báo, guideline; bổ sung hướng dẫn Bộ Y tế; mở rộng bộ ca từ 100 trở lên có bác sĩ gán nhãn; thử tấn công (red-team) | Có chữ ký duyệt chuyên môn; ngưỡng an toàn giữ nguyên trên bộ ca mở rộng |
| **GĐ3. Thí điểm "chạy bóng"** (shadow mode) | Copilot chạy song song, bác sĩ đánh giá nhưng không dùng để quyết định; Navigator thử với nhóm nhỏ có đồng ý; thông qua hội đồng đạo đức; đánh giá tác động dữ liệu | Không có sự cố an toàn nghiêm trọng; bác sĩ đánh giá hữu ích |
| **GĐ4. Triển khai giới hạn** | Tích hợp HIS/EMR; LLM trong hạ tầng bệnh viện; nhắc lịch qua SMS/Zalo; giám sát liên tục; quy trình báo cáo, xử lý sự cố; rà guideline định kỳ | Đánh giá định kỳ; sẵn sàng thu hồi, quay lại giai đoạn trước |

**Nguyên tắc:** chưa qua cổng thì không chuyển giai đoạn, và mỗi giai đoạn đều có thể quay lại.

**Gợi ý hình ảnh:** 4 bậc thang có "cổng" giữa các bậc; đánh dấu "Nhóm đang ở đây" tại GĐ1.

**Lời thuyết trình**
> Nhóm không đề xuất đưa ngay hệ thống tới người bệnh. Lộ trình có bốn giai đoạn, giữa các giai đoạn là một cổng kiểm tra. Hiện nhóm ở giai đoạn một. Giai đoạn hai quan trọng nhất là đưa bác sĩ vào rà soát toàn bộ tri thức. Giai đoạn ba dùng phương pháp "chạy bóng": AI chạy song song nhưng không ảnh hưởng tới quyết định, nhờ đó đo được chất lượng mà không gây rủi ro cho bệnh nhân. Chỉ khi qua các cổng này mới nghĩ tới triển khai thật.

---

## Slide 31 — Tác động kỳ vọng (giả thuyết cần kiểm chứng)

**Nội dung trên slide**

| Đối tượng | Giả thuyết | Cách đo |
|---|---|---|
| 👤 Người dân | Hiểu đúng mình nên tầm soát gì, theo nhóm | Bài kiểm tra hiểu sau tư vấn; tỷ lệ chuyển từ tư vấn sang đặt lịch |
| 👤 Người dân | Quay lại tái tầm soát đúng chu kỳ | Tỷ lệ hoàn thành nhắc lịch đúng hạn |
| 🩺 Bác sĩ | Giảm thời gian chuẩn bị và hỏi lại tiền sử | Thời gian khám; khảo sát mức hữu ích |
| 🏥 Bệnh viện | Ca có dấu hiệu cảnh báo được khám sớm hơn | Thời gian từ khi cảnh báo tới khi được khám |
| 🏥 Bệnh viện | Quy trình minh bạch, truy vết được | Tỷ lệ khuyến nghị có nguồn; nhật ký duyệt đầy đủ |

*Nhóm không đưa ra con số kỳ vọng khi chưa có dữ liệu thí điểm.*

**Lời thuyết trình**
> Nhóm trình bày tác động dưới dạng giả thuyết kèm cách đo, chứ không hứa con số. Nếu được thí điểm, đây là những chỉ số nhóm sẽ theo dõi để biết ý tưởng có thực sự tạo ra giá trị hay không.

---

## Slide 32 — Hạn chế và rủi ro còn lại

**Nội dung trên slide**

| Hạn chế | Hướng xử lý |
|---|---|
| Tri thức y khoa hẹp (6 loại ung thư), chủ yếu guideline Mỹ, quốc tế; đang là bản nháp | Bác sĩ rà soát; bổ sung hướng dẫn Bộ Y tế |
| Nhận diện cảnh báo theo danh sách có thể bỏ sót cách diễn đạt lạ, tiếng địa phương | Mở rộng bộ ca từ dữ liệu thật đã ẩn danh; thông điệp nhắc đi khám thường trực |
| Bộ chặn ngôn ngữ chẩn đoán dựa trên mẫu, có thể lọt cách nói vòng | Bổ sung LLM chấm điểm (LLM-as-judge) và bác sĩ rà mẫu |
| Chưa đánh giá trên người dùng thật; chưa có bằng chứng lâm sàng | Lộ trình GĐ2–GĐ3 |
| HITL chỉ hiệu quả khi bác sĩ thực sự rà soát | Thiết kế chống duyệt cho qua; đo tỷ lệ sửa |
| Phụ thuộc nhà cung cấp LLM (chi phí, quyền riêng tư, mô hình thay đổi) | Có chế độ không cần LLM; đổi nhà cung cấp không sửa code; chạy lại bộ đánh giá khi đổi mô hình |
| Bất bình đẳng tiếp cận số | Kênh tổng đài, Zalo; người thân hỗ trợ |
| Chưa tích hợp hệ thống bệnh viện thật | GĐ4 |

**Lời thuyết trình**
> Nhóm dành một slide riêng cho hạn chế, vì trong y tế, biết rõ giới hạn của mình cũng là một phần của an toàn. Hạn chế lớn nhất là tri thức còn hẹp và chưa được bác sĩ duyệt. Hạn chế thứ hai là các bộ phát hiện dựa trên luật và mẫu câu không thể bao quát hết ngôn ngữ tự nhiên. Mỗi hạn chế đều có hướng xử lý tương ứng trong lộ trình.

---

## Slide 33 — Kết luận

**Nội dung trên slide**

**Ba thông điệp**
1. **Vấn đề:** người dân thiếu định hướng tầm soát, bác sĩ thiếu thông tin trước khám → OncoScreen AI **nối hai đầu một hành trình**.
2. **Giá trị:** không nằm ở việc AI "nói hay hơn", mà ở **quy trình có kiểm soát**: luật có nguồn, cảnh báo thì dừng, bác sĩ quyết định, mọi thứ truy vết được.
3. **Trung thực:** đây là prototype, chưa đánh giá lâm sàng. Bước tiếp theo là **rà soát chuyên môn và thí điểm có kiểm soát**.

**Gợi ý hình ảnh:** 3 thẻ lớn tương ứng 3 thông điệp; câu khẩu hiệu "Luật trước, LLM sau · Bác sĩ quyết định" ở đáy slide.

**Lời thuyết trình**
> Tóm lại, nhóm đề xuất một cách dùng AI trong tầm soát ung thư mà ở đó AI làm điều nó làm tốt, là trò chuyện, tìm kiếm và tóm tắt, còn những quyết định quan trọng thuộc về luật có nguồn và bác sĩ. Nhóm tin rằng giá trị của ý tưởng nằm ở quy trình có kiểm soát chứ không ở độ thông minh của mô hình. Và nhóm xin nhắc lại: đây là prototype học tập, còn nhiều bước trước khi có thể phục vụ người bệnh thật.

---

## Slide 34 — Cảm ơn và hỏi đáp

**Nội dung trên slide**
- **Cảm ơn thầy cô và các bạn đã lắng nghe!**
- Hỏi đáp
- Disclaimer: *OncoScreen AI là prototype phục vụ học tập. Hệ thống không chẩn đoán, không diễn giải kết quả xét nghiệm, không tư vấn điều trị và không thay thế bác sĩ. Người có triệu chứng bất thường cần đi khám sớm thay vì chờ tầm soát định kỳ.*

**Lời thuyết trình**
> Nhóm xin cảm ơn và rất mong nhận được câu hỏi, góp ý của thầy cô, đặc biệt về phần an toàn và quy trình rà soát chuyên môn.

---

# PHỤ LỤC (slide dự phòng cho phần hỏi đáp)

## Phụ lục A — Câu hỏi dự kiến và gợi ý trả lời

| Câu hỏi | Gợi ý trả lời |
|---|---|
| **Khác ChatGPT ở chỗ nào?** | Không khác ở độ thông minh mà ở quy trình: con số do luật có nguồn quyết định, cảnh báo thì dừng trước khi LLM chạy, đầu ra bị kiểm tra, kế hoạch cá nhân phải qua bác sĩ, thông tin đi theo người bệnh vào phòng khám. ChatGPT có kiến thức rộng hơn nhưng không gắn vào quy trình có người chịu trách nhiệm. |
| **Nếu hệ thống bỏ sót dấu hiệu cảnh báo thì sao?** | Nhóm thừa nhận có thể xảy ra (rủi ro R1). Biện pháp: luật ưu tiên độ nhạy, bộ ca kiểm thử với ngưỡng 100%, thông điệp thường trực nhắc đi khám khi có triệu chứng, và hệ thống chỉ là kênh bổ sung, không thay thế việc khám. |
| **Ai chịu trách nhiệm khi sai?** | AI không phát hành kết quả. Gợi ý cho người dân chỉ là thông tin giáo dục theo nhóm; kế hoạch cá nhân do bác sĩ viết, sửa và ký duyệt, có nhật ký đầy đủ. Khi triển khai thật, trách nhiệm cần được quy định trong quy trình của bệnh viện. |
| **Sao lại dùng guideline của Mỹ?** | Vì đó là các guideline công khai, cập nhật và có cấu trúc rõ, phù hợp để chứng minh khái niệm. Nhóm ghi rõ phạm vi áp dụng và coi việc bổ sung hướng dẫn Bộ Y tế, cùng sự rà soát của bác sĩ trong nước, là điều kiện bắt buộc trước khi dùng thật. |
| **Có làm người dân lo lắng hoặc gây quá tải bệnh viện không?** | Có thể, nếu cảnh báo nhầm nhiều. Nhóm đo tỷ lệ cảnh báo nhầm, phân biệt người thân với bản thân, xử lý câu phủ định, dùng giọng văn bình tĩnh, và đề xuất đo mức lo lắng ở giai đoạn thí điểm. |
| **Dữ liệu người dùng đi đâu?** | Prototype dùng dữ liệu giả. Tư vấn có thể ẩn danh; nhật ký AI không lưu nội dung hội thoại. Triển khai thật cần LLM trong hạ tầng bệnh viện hoặc hợp đồng xử lý dữ liệu, theo Luật Bảo vệ dữ liệu cá nhân 2025. |
| **Bác sĩ có bị tăng việc không?** | Mục tiêu là giảm thời gian chuẩn bị. Bác sĩ vẫn phải duyệt, nhưng duyệt trên bản đã soạn sẵn có nguồn thay vì bắt đầu từ đầu. Đây là giả thuyết sẽ đo ở thí điểm. |
| **Sao không làm luôn chẩn đoán cho hiệu quả hơn?** | Chẩn đoán đòi hỏi bằng chứng lâm sàng, chứng nhận thiết bị y tế và trách nhiệm pháp lý vượt xa phạm vi đồ án. Khâu "đưa người dân tới tầm soát" cũng là khoảng trống lớn mà rủi ro thấp hơn. |
| **Làm sao biết hệ thống tốt?** | Bốn tầng đánh giá (slide 29). Ngưỡng an toàn tuyệt đối với cảnh báo, chẩn đoán, nguồn; còn tính đúng y khoa cần bác sĩ gán nhãn và đánh giá. |
| **Người cao tuổi không dùng smartphone thì sao?** | Đây là hạn chế đã nêu. Hướng phát triển là kênh Zalo, tổng đài, và cho phép người thân hỗ trợ. |
| **Nếu đổi sang mô hình LLM mới thì sao?** | Ràng buộc an toàn nằm trong code và luật, không phụ thuộc mô hình. Mỗi lần đổi mô hình phải chạy lại toàn bộ bộ đánh giá trước khi dùng. |

---

## Phụ lục B — Ví dụ khuyến nghị tầm soát theo nhóm (tham chiếu)

*Bảng dưới minh họa loại tri thức mà bộ luật sử dụng. Nguồn là guideline nước ngoài, **chưa được bác sĩ Việt Nam rà soát**, không dùng làm tư vấn y tế.*

| Loại ung thư | Đối tượng | Phương pháp | Chu kỳ | Nguồn |
|---|---|---|---|---|
| Vú | Phụ nữ 40–74 tuổi | Chụp nhũ ảnh | 2 năm/lần | USPSTF 2024 |
| Cổ tử cung | Phụ nữ 21–29 tuổi | Tế bào học cổ tử cung (Pap) | 3 năm/lần | USPSTF 2018 |
| Cổ tử cung | Phụ nữ 30–65 tuổi | Xét nghiệm HPV nguy cơ cao (hoặc Pap mỗi 3 năm) | 5 năm/lần | USPSTF 2018 |
| Đại trực tràng | Người 45–75 tuổi | Xét nghiệm FIT (hoặc nội soi đại tràng mỗi 10 năm) | 1 năm/lần | USPSTF 2021 |
| Phổi | Người 50–80 tuổi, hút thuốc từ 20 gói-năm, đang hút hoặc bỏ dưới 15 năm | CT phổi liều thấp | 1 năm/lần | USPSTF 2021 |
| Tuyến tiền liệt | Nam 55–69 tuổi | Trao đổi với bác sĩ về PSA (quyết định cá nhân) | Không đặt sẵn | USPSTF 2018 |
| Gan | Người viêm gan B/C mạn hoặc xơ gan | Siêu âm gan, có thể kèm AFP | 6 tháng/lần | AASLD 2023 |

Người có tiền sử gia đình mắc ung thư: hệ thống **chỉ nêu lưu ý "bác sĩ cần đánh giá kế hoạch riêng"**, không tự điều chỉnh mốc tuổi hay chu kỳ.

---

## Phụ lục C — Tài liệu tham khảo

1. IARC – Global Cancer Observatory. *GLOBOCAN 2022: Viet Nam fact sheet.* https://gco.iarc.who.int/media/globocan/factsheets/populations/704-viet-nam-fact-sheet.pdf
2. Báo Nhân Dân. *75% người mắc ung thư phổi được phát hiện ở giai đoạn muộn.* https://nhandan.vn/post-867720.html
3. VOH. *70% bệnh nhân ung thư phát hiện ở giai đoạn muộn – Thách thức lớn trong điều trị.* https://voh.com.vn/xa-hoi/70-benh-nhan-ung-thu-phat-hien-o-giai-doan-muon-thach-thuc-lon-trong-dieu-tri-544241.html
4. Chen S. et al. *Use of Artificial Intelligence Chatbots for Cancer Treatment Information.* JAMA Oncology, 2023. doi:10.1001/jamaoncol.2023.2954. https://jamanetwork.com/journals/jamaoncology/fullarticle/2808731
5. Haver H.L. et al. *Appropriateness of Breast Cancer Prevention and Screening Recommendations Provided by ChatGPT.* Radiology, 2023. Tóm tắt: https://www.appliedradiology.com/news/chatgpt-helpful-for-breast-screening-advice-but-with-caveats
6. Semigran H.L. et al. *Evaluation of symptom checkers for self diagnosis and triage: audit study.* BMJ 2015;351:h3480. https://www.bmj.com/content/351/bmj.h3480
7. U.S. Preventive Services Task Force. Khuyến nghị tầm soát ung thư vú (2024), cổ tử cung (2018), đại trực tràng (2021), phổi (2021), tuyến tiền liệt (2018). https://www.uspreventiveservicestaskforce.org
8. Singal A.G. et al. *AASLD Practice Guidance on prevention, diagnosis, and treatment of hepatocellular carcinoma.* Hepatology, 2023.
9. WHO. *Ethics and governance of artificial intelligence for health.* 2021. https://www.who.int/publications/i/item/9789240029200
10. WHO. *Ethics and governance of artificial intelligence for health: Guidance on large multi-modal models.* 2024.
11. U.S. FDA. *Clinical Decision Support Software – Guidance for Industry and FDA Staff.* 2022.
12. Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15. https://thuvienphapluat.vn/van-ban/Bo-may-hanh-chinh/Luat-Bao-ve-du-lieu-ca-nhan-2025-so91-2025-QH15-625628.aspx
13. Nghị định 356/2025/NĐ-CP hướng dẫn Luật Bảo vệ dữ liệu cá nhân. https://thuvienphapluat.vn/van-ban/Quyen-dan-su/Nghi-dinh-356-2025-ND-CP-huong-dan-Luat-Bao-ve-du-lieu-ca-nhan-687428.aspx
14. Nghị định 98/2021/NĐ-CP về quản lý trang thiết bị y tế.
15. Luật Khám bệnh, chữa bệnh số 15/2023/QH15.
16. Freeman H.P., Rodriguez R.L. *History and principles of patient navigation.* Cancer, 2011.
17. STAT News (2018). *IBM's Watson supercomputer recommended "unsafe and incorrect" cancer treatments, internal documents show.*
18. Báo chí quốc tế (tháng 5–6/2023) về việc NEDA gỡ chatbot "Tessa".
19. Community Preventive Services Task Force. *Cancer Screening: Client Reminders.* https://www.thecommunityguide.org
20. Lång K. et al. *Artificial intelligence-supported screen reading versus standard double reading in the Mammography Screening with Artificial Intelligence trial (MASAI).* Lancet Oncology, 2023.

> **Lưu ý cho nhóm:** các nguồn 1–6, 12–13 đã được kiểm tra khi soạn tài liệu này. Các nguồn còn lại cần đối chiếu bản gốc (tên, năm, số liệu) trước khi đưa lên slide.

---

## Phụ lục D — Thuật ngữ

| Thuật ngữ | Giải thích ngắn |
|---|---|
| **LLM** (mô hình ngôn ngữ lớn) | Mô hình AI sinh văn bản như GPT, Claude, Gemini |
| **RAG** (truy xuất tăng cường sinh) | Tìm đoạn tài liệu liên quan trước, rồi mới cho LLM trả lời dựa trên đoạn đó: "mở sách rồi mới nói" |
| **Hallucination** ("ảo giác") | LLM tạo ra thông tin nghe hợp lý nhưng không có căn cứ |
| **Guardrail** (rào chắn) | Bộ kiểm tra tự động ở đầu vào, trong quá trình xử lý và ở đầu ra |
| **Red-flag** (dấu hiệu cảnh báo) | Triệu chứng cần đi khám sớm thay vì chờ tầm soát định kỳ |
| **HITL** (Human-in-the-loop) | Con người, ở đây là bác sĩ, tham gia và quyết định trong quy trình AI |
| **Automation bias** | Xu hướng tin vào kết quả máy đưa ra mà không kiểm tra lại |
| **Prompt injection** | Tấn công bằng câu lệnh nhằm khiến AI bỏ qua ràng buộc |
| **Golden set** (bộ ca chuẩn) | Tập ca kiểm thử có đáp án đúng, dùng để đo chất lượng tự động |
| **Recall / độ nhạy** | Tỷ lệ ca thật sự cần cảnh báo mà hệ thống bắt được |
| **False positive** (cảnh báo nhầm) | Hệ thống cảnh báo khi thực tế không cần |
| **Shadow mode** ("chạy bóng") | AI chạy song song quy trình thật nhưng không ảnh hưởng tới quyết định, dùng để đánh giá an toàn |
| **Gói-năm** (pack-year) | Số bao thuốc mỗi ngày nhân với số năm hút; dùng xác định nhóm nguy cơ ung thư phổi |

---

## Bản rút gọn (12–15 phút)

Giữ các slide: **1 · 2 · 4 · 5 · 6 · 10 · 11 · 12 · 15 · 17 · 19 · 20 · 23 · 26 · 30 · 33 · 34** (17 slide). Các slide còn lại chuyển xuống phần phụ lục để dùng khi hỏi đáp.

**Phân bổ thời gian gợi ý (bản đầy đủ, khoảng 28 phút)**

| Phần | Slide | Thời gian |
|---|---|---|
| I. Mở đầu | 1–3 | 1,5 phút |
| II. Bối cảnh, vấn đề | 4–6 | 3 phút |
| III. Phương pháp hiện có | 7–10 | 4 phút |
| IV. Ý tưởng giải pháp | 11–15 | 5 phút |
| V. Mục tiêu, mức độ giải quyết | 16–18 | 3 phút |
| VI. An toàn, độ tin cậy | 19–25 | 7 phút |
| VII. So sánh thực tế | 26–28 | 2,5 phút |
| VIII. Đánh giá, lộ trình, kết luận | 29–34 | 2 phút |
