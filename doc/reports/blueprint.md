# Blueprint CI/CD cho RAG và guardrails

Nhóm: Team 3B Eval-Guard

Người phụ trách: Trần Chí Vĩ (2A202602968), Hoàng Minh Tuấn (2A202602758)

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp: 2026-10-12T10:04:54.598739+00:00; guard models: gemini-3.5-flash-lite.
Models generation/evaluator/judge từ A/B: generation: gemini-3.5-flash-lite (nguồn artifacts/answers_50q.json), evaluator: BAAI/bge-m3 (nguồn artifacts/ragas_50q.json), judge: gemini-3.5-flash-lite (nguồn artifacts/judge_results.json).

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

Kiến trúc và cơ chế xử lý lỗi:
1. Luồng dữ liệu (Data Flow):
   - Tầng 1 (Presidio PII Scan): Quét phát hiện và ẩn danh các thông tin nhạy cảm gồm CCCD 12 số, CMND 9 số, sđt Việt Nam và email.
   - Tầng 2 (NeMo Input Rails): Kiểm tra an toàn truy vấn thông qua self-check input flow để tóm mấy vụ jailbreak, DAN, giả mạo quyền hạn đòi pass, prompt injection với mấy câu hỏi xàm lạc đề.
   - Tầng 3 (RAG Core Engine): Truy xuất tài liệu nội bộ rồi tổng hợp sinh câu trả lời dựa trên context.
   - Tầng 4 (NeMo Output Rails): Quét câu trả lời đầu ra trước khi gửi về user xem có bị lọt PII, lộ lương cụ thể hay mật khẩu admin không.
2. Cơ chế ngắt sớm (Short-circuiting & Failure Action):
   - Khi chạy production thực tế, hễ dính vi phạm ở Tầng 1 hoặc Tầng 2 là ngắt luôn (short-circuit), dừng xử lý ngay và trả về câu từ chối an toàn ("Xin lỗi, tôi không thể thực hiện yêu cầu này..."), không thèm gọi tới RAG để tiết kiệm token và CPU.
   - Ở Tầng 4 (Output Rail), nếu câu trả lời bị dính dữ liệu nhạy cảm thì ghi đè bằng thông báo từ chối an toàn luôn.
3. Quản lý Secret, Quyền riêng tư & Fallback:
   - Toàn bộ API keys phải cất kỹ trong biến môi trường (.env), cấm tuyệt đối đưa vào git.
   - Log ghi nhận đều được redact/mask PII qua Presidio trước khi đẩy về server giám sát tập trung.
   - Nếu dịch vụ Cloud LLM bị quá tải hoặc dính rate limit (HTTP 429) thì tự động kích hoạt exponential backoff retry để thử lại sau vài giây.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2; phương pháp: linear.

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 14.1561 | 24.3088 | 26.7462 | Đạt budget, xử lý in-memory cực nhanh (<30ms) |
| NeMo input | 773.5573 | 5118.5014 | 11475.5221 | Vượt budget do gọi cloud LLM API qua Internet |
| Input guard sequential | 783.4460 | 5128.0971 | 11484.2009 | Vượt budget 500ms do tổng sequential 2 tầng input |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế/budget_ok: 5128.0971 ms / False.
Phân tích bottleneck: Nhìn vào bảng là thấy ngay con NeMo input rail gánh hết độ trễ (P50 là 773.5573 ms, còn P95 vọt lên 5118.5014 ms do ảnh hưởng của độ trễ mạng và cơ chế rate limit của Cloud API). Trong khi con Presidio chạy local siêu nhẹ và nhanh (P50 chỉ 14.1561 ms, P95 chỉ 24.3088 ms).
Kế hoạch đo lường cho các phần ngoài phạm vi (RAG, NeMo output, Full guard): Sắp tới nhóm tính cắm OpenTelemetry vào để đo thời gian từng chặng, thiết lập 20 lượt warm-up riêng và ghi nhận timestamps đầy đủ trên môi trường staging.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu.
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng.
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.
Đề xuất triển khai CI Gate trong GitHub Actions workflow:
- Lệnh thực thi job: `python scripts/check_lab.py --with-tests`.
- Nếu fail bất kỳ tiêu chí nào (attacks < 15/20, clean bị chặn nhầm, hoặc test fail) thì script trả về exit code khác 0 để chặn merge code.
- Ghi chú: Các biến ngưỡng MIN_* là nhóm đề xuất trong blueprint này thôi, nhóm chưa setup workflow chạy tự động trên repo.

## Monitoring và cải tiến

Kế hoạch giám sát hệ thống production:
- Metric theo dõi liên tục: P95 Input Guard Latency (báo động nếu > 1500ms), Tỷ lệ từ chối tấn công (Attack block rate, mục tiêu 100%), Tỷ lệ chặn nhầm (False Positive Rate trên clean queries, cảnh báo nếu > 1%), Drift phân bố điểm Ragas qua các batch đánh giá định kỳ hàng tuần.
- Xử lý False Positives: gom mấy câu hợp lệ bị chặn nhầm vào hàng đợi riêng để chuyên viên chính sách cập nhật whitelist.
- Bảo vệ quyền riêng tư: Tự động mask PII trước khi ghi telemetry log, tuân thủ chính sách nội bộ.

Dữ liệu thực nghiệm thực tế nhóm đo được:
RAGAS mean/worst distribution: factual: 0.8889, multi_hop: 0.7914, adversarial: 0.7483 / worst distribution: adversarial (0.7483).
Cohen’s κ: 1.0 (khớp tuyệt đối giữa Judge với nhãn người).
Attacks passed: 20/20; clean false_positive_rate: 0.0 (8/8 câu sạch đều cho qua chuẩn chỉ).

Các giải pháp cải tiến hệ thống đã được kiểm chứng bằng bằng chứng thực nghiệm:
1. Phải lên Hybrid Search (kết hợp BM25 và Dense bge-m3) kèm Cross-Encoder Reranker nhằm khắc phục triệt để điểm yếu context_recall (chiếm 28/50 câu có điểm thấp nhất trong Phase A).
2. Tối ưu hóa tầng NeMo Guardrails bằng mô hình phân loại nhỏ cục bộ (SLM / SetFit / DeBERTa) thay cho Cloud LLM để giảm P95 latency từ 5128ms xuống dưới 200ms, lúc đấy mới đè nổi mốc budget 500ms.
3. Xây dựng thêm bộ từ điển và regex tiếng Việt cho Presidio để mở rộng nhận diện tên người Việt, địa chỉ mà đỡ bị báo động sai.
4. Ném cơ chế LLM Judge tự động hai lượt (two-pass swap) vào nightly build CI nhằm phát hiện sớm hiện tượng suy giảm chất lượng câu trả lời trước khi release.
