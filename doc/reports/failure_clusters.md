# Phân tích lỗi Phase A

Nhóm: Team 3B Eval-Guard

Người phụ trách: Trần Chí Vĩ (2A202602968), Hoàng Minh Tuấn (2A202602758)

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T09:22:06.217151+00:00.
Generation mode/fallback và điều kiện chạy: chạy full 50 câu RAG bằng live API gemini-3.5-flash-lite, ko bị dính câu fallback nào cả (generation_mode=llm 100%), tính điểm Ragas dùng model evaluator bge-m3 tải chạy local.
Models generation/evaluator: gemini-3.5-flash-lite (generation), BAAI/bge-m3 (evaluator).

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.9359 | 0.8820 | 0.8929 |
| answer_relevancy | 0.8343 | 0.8447 | 0.7986 |
| context_precision | 0.9013 | 0.7730 | 0.7680 |
| context_recall | 0.8842 | 0.6661 | 0.5338 |
| avg_score | 0.8889 | 0.7914 | 0.7483 |

## Bottom 10 và nguyên nhân

| Rank | ID | Question | Distribution | Avg Score | Worst Metric | Diagnosis | Suggested Fix |
|---|---|---|---|---|---|---|---|
| 1 | 33 | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | multi_hop | 0.6654 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 2 | 50 | Nhân viên Manager có thể dùng VPN cá nhân (như NordVPN) khi WFH để tăng bảo mật thêm không? | adversarial | 0.6868 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 3 | 42 | Thâm niên bao nhiêu năm thì được cộng thêm ngày phép? | adversarial | 0.6946 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 4 | 35 | Nhân viên Junior P1 có lương cơ bản 12 triệu vừa vào thử việc: nhận lương bao nhiêu và phụ cấp gì tháng đầu tiên? | multi_hop | 0.7188 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 5 | 41 | Nhân viên được nghỉ bao nhiêu ngày phép năm? | adversarial | 0.7252 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 6 | 47 | Khi phát hiện malware trên máy tính công ty, nhân viên có nên tự xử lý không? | adversarial | 0.7259 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 7 | 21 | Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào? | multi_hop | 0.7360 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 8 | 44 | Bao lâu phải đổi mật khẩu một lần? | adversarial | 0.7370 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 9 | 45 | Có cần kích hoạt xác thực đa yếu tố (MFA) không? | adversarial | 0.7447 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |
| 10 | 28 | Nhân viên cấp Lead nhận tổng phụ cấp hàng tháng (ăn trưa + điện thoại) là bao nhiêu? | multi_hop | 0.7575 | context_recall | Missing relevant chunks | Improve chunking or add BM25 |

Đối chiếu và phân tích nhóm lỗi đại diện:
- Câu 33 (rank 1, multi_hop): Câu này hỏi gộp cả 2 ý: phụ cấp Manager (500k điện thoại + 1tr ăn trưa = 1.5tr) với ngày phép năm v2024 (15 ngày gốc + 4 ngày cho 12 năm thâm niên = 19 ngày). Khổ nỗi lúc retrieve thì chỉ vớt đc chunk phụ cấp, còn chunk thâm niên thì bị rớt mất tiêu, thành ra context_recall bị tụt thê thảm xuống còn 0.3889.
- Câu 50 (rank 2, adversarial): Bẫy ở chỗ hỏi dùng VPN cá nhân như NordVPN để tăng bảo mật thêm đc ko. Trong file cty có ghi cấm xài VPN ngoài. Nhưng retriever dạng dense lại bị hút vào mấy đoạn mô tả chung chung về VPN với WFH, lướt qua mất cái dòng cấm đoán cụ thể, nên context_recall chỉ lẹt đẹt 0.4545.
- Câu 41 (rank 5, adversarial): Dính bẫy version conflict giữa bản nghỉ phép năm 2023 (12 ngày) với bản 2024 (15 ngày). Retriever bốc cả 2 bản vào context luôn, model lúc trả lời tuy có nhắc v2024 nhưng ngữ cảnh bị loãng, làm context_recall tụt còn 0.5294.

## Matrix và nhóm yếu nhất

| Metric | factual | multi_hop | adversarial | Total |
|---|---|---|---|---|
| faithfulness | 2 | 1 | 0 | 3 |
| context_recall | 5 | 14 | 9 | 28 |
| context_precision | 3 | 4 | 0 | 7 |
| answer_relevancy | 10 | 1 | 1 | 12 |

Nhóm yếu theo mean thấp nhất: adversarial; mean: 0.7483.
Worst metric xuất hiện nhiều nhất: context_recall; số câu: 28.

Nhóm adversarial điểm trung bình lẹt đẹt nhất (0.7483) do toàn câu gài bẫy xung đột phiên bản (v2023 với v2024) với mấy câu phủ định. Mấy cái bẫy này làm cho dense retrieval bị lú, nó cứ thấy từ khóa na ná nhau là bốc vào chứ ko phân biệt đc bản nào cũ bản nào mới.
Metric context_recall là điểm yếu chủ đạo (chiếm tới 28/50 câu có điểm thấp nhất), đặc biệt nghiêm trọng ở multi_hop (14 câu) và adversarial (9 câu) do câu hỏi phân mảnh quá mà retriever ko gom đủ chunk rải rác.
Hướng sửa: Nhóm tính sẽ phối hợp Hybrid Search (kẹp BM25 để bắt dính mấy chữ version như v2024, v2.0 cùng với dense bge-m3) rồi tống qua Cross-Encoder Reranker lọc lại top 3-5 chunk xịn nhất. Sửa xong thì chạy lại lệnh `python scripts/run_experiments.py --phase a --live` để check xem context_recall có ngóc đầu lên ko.

## Bẫy adversarial và giới hạn

So sánh giữa các tập dữ liệu:
- Nhóm Factual điểm cao chót vót (avg_score 0.8889, context_recall 0.8842) nhờ câu hỏi ngắn, tra thẳng một tài liệu là ra ngay.
- Nhóm Multi-hop rơi tầm trung (avg_score 0.7914, context_recall 0.6661) vì phải ghép 2-3 điều khoản khác nhau nên dễ sót chunk.
- Nhóm Adversarial rớt đáy (avg_score 0.7483, context_recall 0.5338). Nhóm này phơi bày rõ mấy bẫy version conflict (Câu 41, 42, 44 về phép năm và chu kỳ đổi mật khẩu) với bẫy phủ định/hạn chế (Câu 46 thử việc ko có phép năm, Câu 47 cấm tự diệt malware, Câu 50 cấm VPN cá nhân). Đoạn phủ định này dense search bắt rất kém vì câu phủ định thường có cosine similarity thấp hơn câu khẳng định tương ứng. Điểm nhóm này thấp hơn chứng tỏ bộ câu hỏi phân hoá rất tốt chứ ko phải pipeline tự nhận ra bẫy đâu.
Giới hạn thực nghiệm: Test set này có 50 câu thôi nên chưa bao quát hết mọi ca ngoài đời. Model chạy là gemini-3.5-flash-lite qua API, thi thoảng LLM nó sinh câu từ ngẫu nhiên nhẹ nên điểm có thể lệch tí xíu giữa các lần chạy, cơ mà xu hướng chung thì chuẩn đét.
