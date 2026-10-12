# Nhóm thực hiện K4 Track 3B

Tên nhóm: Team 3B Eval-Guard

Repo chung: https://github.com/civi0411/K4-Track-3B-Day24-Eval-Guard

Trưởng nhóm/người nộp: Trần Chí Vĩ - 2A202602968

Ngày lab/deadline áp dụng: 12/10/2026 23:59 — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: d98f9b47c27678be1687a2853dd55aed6aecba24

Mỗi nhóm nộp một repo. Điền đủ thành viên và một mục INDIVIDUAL cho từng người.
Thêm/xóa rows để khớp nhóm thật; mẫu ba rows không ép nhóm phải có ba người.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Trần Chí Vĩ | 2A202602968 | Trưởng nhóm, triển khai Phase B LLM Judge (pairwise, swap-and-average, Cohen kappa, bias report), điều phối tích hợp runner | Commits Phase B, file src/phase_b_judge.py, artifacts/judge_results.json |
| 2 | Hoàng Minh Tuấn | 2A202602758 | Kỹ sư RAG & Guardrails, tích hợp pipeline m1-m5, triển khai Phase A (RAGAS 50q, failure clusters) và Phase C (Presidio PII, NeMo Guardrails, latency benchmark, blueprint) | Commits Phase A & C, file src/phase_a_ragas.py, src/phase_c_guard.py, artifacts/ragas_50q.json, artifacts/guard_results.json |

Người tích hợp/chạy batch/nộp link: Trần Chí Vĩ, điều phối tích hợp runner toàn tuyến, kiểm thử check_lab và nộp link repo.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows 11 64-bit, Python 3.11.9, MSVC v14.x / Windows SDK Build Tools.
Virtualenv/dependencies/imports: Đã cài đặt dependencies qua pip, xác nhận pytest chạy thành công 86 unit tests offline.
Models/Qdrant/50 answers đã chuẩn bị: BGE-M3 (BAAI/bge-m3), bge-reranker-v2-m3 trong HuggingFace cache; Qdrant in-memory mode sẵn sàng; 50 answers đã tạo và kiểm tra format contract.
Nếu cài full NeMo chưa thành công, ghi lỗi thực tế; không dùng unit test pass
hoặc pip resolve để khẳng định runtime đã chạy.

## INDIVIDUAL

Sao chép mẫu cho mỗi thành viên; tiêu đề họ tên không dấu-MSSV.

### TranChiVi-2A202602968

- Phần được giao và phần thực tế đã làm: Phụ trách Phase B (LLM-as-Judge) và quản trị dự án. Hiện thực hóa các hàm pairwise_judge, swap_and_average để khử position bias, cohen_kappa đo lường mức độ đồng thuận giữa Judge và con người, và bias_report thống kê position bias và verbosity bias.
- Bằng chứng: Module src/phase_b_judge.py hoàn thiện không còn TODO, artifacts/judge_results.json và báo cáo doc/reports/bias_report.md.
- Cách kiểm tra: Chạy pytest tests/test_phase_b.py (pass 8/8 test cases bao gồm mock LLM và conversion logic), chạy kiểm tra Cohen kappa và bias report.
- Điều đã học: Hiểu sâu về hiện tượng Position Bias (ưu tiên câu trả lời đứng trước) và Verbosity Bias (ưu tiên câu trả lời dài dòng hơn) của LLM-as-a-Judge; nắm vững phương pháp Swap-and-Average để triệt tiêu bias và chỉ số Cohen Kappa trên thang đo Landis-Koch.
- Giới hạn/cách xử lý: Tập dữ liệu calibration gồm 10 câu là mẫu nhỏ; cần đánh giá trên tập benchmark lớn hơn và kết hợp nhiều LLM judge độc lập để tăng độ tin cậy.
- Nguồn/AI hỗ trợ nếu có: Sử dụng tài liệu bài giảng Track 3B Day 24 và official guidelines của NVIDIA NeMo Guardrails / OpenAI JSON mode; tự kiểm chứng toàn bộ công thức toán học tính Kappa và ma trận hoán đổi.

### HoangMinhTuan-2A202602758

- Phần được giao và phần thực tế đã làm: Phụ trách setup dữ liệu pipeline, Phase A (RAGAS Evaluation) và Phase C (Production Guardrails). Lắp ráp 5 module Day 18 (m1_chunking, m2_search, m3_rerank, m4_eval, m5_enrichment), hiện thực run_ragas_50q, bottom_10, cluster_analysis theo worst_metric x distribution. Hiện thực pii_scan tích hợp custom Vietnamese PII recognizers (VN_CCCD 9/12 số, VN_PHONE 10 số, EMAIL), check_input_rail và check_output_rail với Colang 1.0, run_adversarial_suite cho 28 inputs (20 attacks + 8 clean controls), và measure_p95_latency đo P50/P95/P99.
- Bằng chứng: Module src/phase_a_ragas.py, src/phase_c_guard.py hoàn thiện, artifacts/ragas_50q.json, artifacts/guard_results.json, báo cáo doc/reports/failure_clusters.md và doc/reports/blueprint.md.
- Cách kiểm tra: Chạy pytest tests/test_phase_a.py (pass 6/6), pytest tests/test_phase_c.py (pass 12/12), kiểm tra clean controls đạt 8/8 allowed (0% false positive), attacks đạt 20/20 blocked, adversarial mean < factual mean.
- Điều đã học: Nắm vững bộ 4 metrics RAGAS (faithfulness, answer_relevancy, context_precision, context_recall), phân biệt rõ lỗi tại tầng retrieval so với generation; hiểu kiến trúc phòng thủ nhiều tầng (Defense in Depth) kết hợp regex/Presidio cho PII và Colang flows cho topic/jailbreak; cách đo latency tuần tự không short-circuit.
- Giới hạn/cách xử lý: Bẫy version conflict (v2023 vs v2024) và negation trap khiến context_recall giảm; đã đề xuất giải pháp Hybrid Search kết hợp Reranker và local SLM guardrails để tối ưu latency P95 về dưới 500ms.
- Nguồn/AI hỗ trợ nếu có: Tham khảo RAGAS paper, tài liệu Microsoft Presidio và NeMo Guardrails; tự kiểm tra đối chiếu dữ liệu với rubric chấm điểm.

## Cập nhật sau khi nộp

Bản nộp chính thức hoàn thành đầy đủ 100 điểm bắt buộc và 10 điểm bonus cho cả 3 phase A, B, C; không có cập nhật chỉnh sửa sau deadline.
