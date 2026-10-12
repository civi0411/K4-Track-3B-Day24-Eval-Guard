# Đánh giá LLM Judge Phase B

Nhóm: Team 3B Eval-Guard

Người phụ trách: Trần Chí Vĩ (2A202602968), Hoàng Minh Tuấn (2A202602758)

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T09:23:21.889248+00:00.
Models generation/judge: gemini-3.5-flash-lite (generation), gemini-3.5-flash-lite (judge).

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| ID | Candidate A | Candidate B | Winner Pass 1 | Winner Pass 2 | Final Winner | Consistent | Scores Pass 1 | Scores Pass 2 | Reasoning |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 3 ngày làm việc | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B | B | B | True | A: 0.8, B: 1.0 | A: 0.7, B: 0.95 | Answer B đầy đủ thông tin hơn Answer A khi bao gồm cả chi tiết 'có lương', sát với chính sách tham chiếu. |
| 5 | Tổng Giám đốc (CEO) | Cần Giám đốc phòng ban phê duyệt. | A | A | A | True | A: 1.0, B: 0.0 | A: 1.0, B: 0.0 | Answer A trả lời chính xác và đầy đủ về người cần phê duyệt (Tổng Giám đốc/CEO) dựa trên chính sách cho đơn hàng trên 50 triệu, trong khi Answer B sai thông tin. |
| 12 | Tối thiểu **1 tháng lương**. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | tie | A | tie | False | A: 1.0, B: 1.0 | A: 1.0, B: 0.9 | Cả hai câu trả lời đều cung cấp thông tin chính xác theo chính sách tham chiếu; ở lượt 2 câu A súc tích hơn nên được ưu tiên nhẹ, kết quả chung cuộc quy về tie. |
| 21 | Dựa trên context: - Nhân viên 9 năm thâm niên được **18 ngày phép** (15 + 3). - Không tìm thấy thông tin về lương. | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B | B | B | True | A: 0.5, B: 1.0 | A: 0.5, B: 1.0 | Answer B trả lời đầy đủ cả hai ý của câu hỏi (số ngày phép và khoảng lương) dựa trên thông tin tham chiếu, trong khi Answer A bỏ sót ý về lương. |
| 41 | Dựa trên context, nhân viên chính thức được hưởng 15 ngày phép năm có lương (theo chính sách năm 2024)... | Nhân viên được nghỉ 12 ngày phép năm. | A | A | A | True | A: 0.85, B: 0.3 | A: 0.95, B: 0.3 | Answer A đã ưu tiên chính sách v2024 hiện hành (15 ngày cơ bản) và quy tắc thâm niên, trong khi Answer B lấy nhầm số liệu của chính sách v2023 đã bị thay thế. |

Position bias count/rate: 1 trường hợp (rate: 0.2 tương ứng 20.0%).
Verbosity win rate: 0.5 (50.0%); decisive cases: 4 câu phân định thắng bại.

Giải thích chi tiết:
- Vụ lệch vị trí (Position bias): Chỉ dính đúng 1 ca ở câu 12. Ở lượt 1 judge cho hòa (tie), sang lượt 2 đảo chỗ thì judge lại thích câu A hơn tẹo vì súc tích. Nhưng nhờ áp dụng luật swap-and-average (hai lượt phải cùng vote mới tính thắng) nên kết quả chốt lại vẫn là tie, triệt tiêu hoàn toàn ảnh hưởng của vị trí đứng trước hay đứng sau.
- Vụ thiên vị câu dài (Verbosity bias): Trong 4 câu có phân định thắng bại rõ ràng (câu 1, 5, 21, 41) thì đúng 2 câu dài hơn thắng và 2 câu ngắn hơn thắng, chia đều 50.0%. Điều này cho thấy judge nó chấm dựa vào độ chuẩn xác nội dung theo reference chứ ko phải cứ dài dòng hoa mỹ là ăn điểm (ví dụ câu 5 câu A trả lời đúng trọng tâm CEO nên thắng áp đảo câu B nói sai).

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json; không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference. Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| Question ID | Model Answer gốc | Judge Label | Reasoning | Human Label | Agree |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Câu trả lời đã nêu đúng số ngày nghỉ (3 ngày làm việc có lương khi kết hôn) theo đúng reference. | 1 | True |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Thiết bị trị giá 55 triệu (trên 50 triệu) theo reference cần Tổng Giám đốc (CEO) phê duyệt, nhưng answer lại trả lời là Giám đốc phòng ban nên sai. | 0 | True |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Answer trả lời chính xác và đầy đủ ý thiết yếu theo reference, đúng mức thưởng Tết tối thiểu 1 tháng lương cho nhân viên chính thức có từ 6 tháng trở lên. | 1 | True |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Câu trả lời đáp ứng chính xác số ngày phép (18 ngày) và khoảng lương (20-35 triệu) theo đúng chính sách v2024 trong reference. | 1 | True |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Câu trả lời chính xác theo reference, trả lời đủ các ý thiết yếu, không bỏ qua điều kiện quan trọng và xác định đúng số tiền hoàn trả 25 triệu. | 1 | True |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu thẩm quyền phê duyệt của Kế toán trưởng và tính sai phí phạt (quá hạn 30 ngày nhưng theo reference là phạt tính trên số ngày quá hạn, answer ghi phạt 2% tháng trên 8 triệu là thiếu công thức và sai thời gian tính phạt). | 0 | True |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Answer trả lời chính xác số ngày phép năm (19 ngày) và tổng phụ cấp hàng tháng (1.500.000 VNĐ) dựa hoàn toàn theo reference. | 1 | True |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Câu trả lời sử dụng thông tin từ phiên bản chính sách cũ (v2023 là 12 ngày) thay vì phiên bản hiện hành v2024 (15 ngày cơ bản), vi phạm yêu cầu ưu tiên v2024. | 0 | True |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 1 | Câu trả lời hoàn toàn chính xác theo reference, nêu đúng nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần, nắm bắt đúng ý phủ định. | 1 | True |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Reference quy định rõ ràng là CẤM sử dụng VPN cá nhân, bắt buộc dùng VPN WireGuard của công ty. Answer lại trả lời là được, vi phạm chính sách. | 0 | True |

Cohen’s κ: 1.0.
Observed/chance agreement và diễn giải:
- Observed agreement Po = 10 / 10 = 1.0 (khớp chuẩn 100% giữa phán đoán của LLM Judge với nhãn người gán).
- Chance agreement Pe: Phân bố nhãn có 6 câu Đạt (1) và 4 câu Không đạt (0) ở cả hai bên. Pe = (0.6 * 0.6) + (0.4 * 0.4) = 0.36 + 0.16 = 0.52.
- Hệ số Cohen's kappa: κ = (1.0 - 0.52) / (1 - 0.52) = 1.0. Con số 1.0 này vượt xa mốc bonus 0.6 theo rubric, cho thấy mức độ đồng thuận tuyệt đối giữa máy và người.

## Giới hạn và cách dùng judge

Giới hạn thực nghiệm:
- Bộ dữ liệu calibration mới chỉ có 10 câu nhãn người kèm 5 cặp so sánh A/B nên quy mô còn khá khiêm tốn.
- Model judge chạy gemini-3.5-flash-lite nên phán quyết vẫn dựa nhiều vào chất lượng văn bản ground truth đưa vào prompt. Nếu reference mà thiếu sót thì judge cũng dễ phán bừa.
Nguyên tắc ứng dụng:
- Đừng coi LLM Judge là chân lý tuyệt đối, chỉ nên dùng nó làm công cụ tự động hóa kiểm thử hồi quy trong pipeline CI/CD thôi.
- Bắt buộc phải duy trì cơ chế đánh giá hai lượt đổi chỗ để tránh thiên vị vị trí. Mấy ca nào nhạy cảm về chế độ chính sách hoặc khi hai lượt bị lệch kết quả (ra tie) thì nhất định phải kéo người thật (human-in-the-loop) vào duyệt lại lần cuối.
