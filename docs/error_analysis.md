# Error Analysis Report (bm25, Top-5)

**Date**: 2026-07-10 | **Testset**: data/eval/questions.v2.jsonl (200 queries)

## Summary

| Metric | Value |
|---|---|
| Total | 200 |
| Correct | 140 |
| Failed | 60 |
| Recall@5 | 70.00% |

## Recall by Domain

| Domain | Total | Correct | Recall |
|---|---|---|---|
| dan_su | 18 | 14 | 78% |
| dat_dai | 20 | 12 | 60% |
| doanh_nghiep | 43 | 29 | 67% |
| giao_duc | 17 | 11 | 65% |
| giao_thong | 19 | 11 | 58% |
| hanh_chinh | 20 | 13 | 65% |
| hinh_su | 4 | 4 | 100% |
| lao_dong | 9 | 7 | 78% |
| moi_truong | 7 | 5 | 71% |
| thue | 24 | 19 | 79% |
| unknown | 16 | 13 | 81% |
| y_te | 3 | 2 | 67% |

## Failed Queries (60)

- **#1** `492/2000/QĐ-BTM` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 492/2000/QĐ-BTM là gì?_
- **#5** `34/2000/QĐ-BCN` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 492/2000/QĐ-NHNN5` — _Nội dung quy định tại Điều 4 của 34/2000/QĐ-BCN là gì?_
- **#6** `111/2000/QĐ-BNN-TTCB` → Retrieved: `825/2000/TT-BKHCNMT, 18/2000/QĐ-BGDĐT, 1117/1998/QĐ-UB` — _Theo văn bản 111/2000/QĐ-BNN-TTCB, quy định về trường có nhiệm vụ chủ yếu sau đâ_
- **#7** `54/2000/NĐ-CP` → Retrieved: `792/1997/QĐ-UB, 5-LCT/HĐNN7, 16/2000/NĐ-CP` — _Văn bản 54/2000/NĐ-CP quy định thế nào về việc: khiếu nại, tố cáo và giải quyết _
- **#11** `139-HĐBT` → Retrieved: `71-HĐBT, 44/2000/NĐ-CP, 12/2000/TT-BKH` — _Nội dung quy định tại Điều 73 của 139-HĐBT là gì?_
- **#13** `147/2000/QĐ-TTg` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 147/2000/QĐ-TTg là gì?_
- **#17** `43/2000/NĐ-CP` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 17/2000/QĐ-BXD` — _Nội dung quy định tại Điều 7 của 43/2000/NĐ-CP là gì?_
- **#23** `34/2000/QĐ-UB` → Retrieved: `99/1998/NĐ-CP, 30/2000/PL-UBTVQH10, 44/2000/NĐ-CP` — _Nội dung quy định tại Điều 16 của 34/2000/QĐ-UB là gì?_
- **#24** `863/QĐ-UB/TC` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 863/QĐ-UB/TC là gì?_
- **#29** `3540/QĐ-UB` → Retrieved: `102/NĐ-LB, 218/CP, 351-HĐBT` — _Chi tiết Điều 22 trong 3540/QĐ-UB về thu, chi lệ phí?_
- **#32** `03/2000/NĐ-CP` → Retrieved: `93/2000/QĐ-BNN/TCCB, 18/NH-QĐ, 92/2000/QĐ-BNN/TCCB` — _Trong lĩnh vực doanh_nghiep, 03/2000/NĐ-CP hướng dẫn về điều lệ công ty ra sao?_
- **#35** `53/1998/QĐ-UB/NC2` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 53/1998/QĐ-UB/NC2 là gì?_
- **#38** `16/SL` → Retrieved: `130/SL, 135, 77C` — _Văn bản 16/SL quy định thế nào về việc: bộ trưởng bộ nội vụ chiểu sắc lệnh thi h_
- **#40** `02/2000/QĐ-BGD` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 02/2000/QĐ-BGD là gì?_
- **#43** `874/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 874/QĐ-UB là gì?_
- **#44** `886/1997/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của 886/1997/QĐ-UB là gì?_
- **#46** `179/1999/NĐ-CP` → Retrieved: `Không số, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 21 của 179/1999/NĐ-CP là gì?_
- **#51** `88/2000/QĐ-BTM` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 88/2000/QĐ-BTM là gì?_
- **#54** `54/SL` → Retrieved: `88/SL, 87, 73` — _Trong lĩnh vực moi_truong, 54/SL hướng dẫn về bộ trưởng bộ canh nông chiểu sắc l_
- **#56** `49/SL` → Retrieved: `14/2000/NĐ-CP, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 51 của 49/SL là gì?_
- **#59** `112-HĐBT` → Retrieved: `56/HĐBT, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 112-HĐBT là gì?_
- **#61** `1121/1997/QĐ-UB` → Retrieved: `18/1999/PL-UBTVQH10, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 34 của 1121/1997/QĐ-UB là gì?_
- **#64** `23/2000/QH10` → Retrieved: `44/2000/NĐ-CP, 43/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 36 của 23/2000/QH10 là gì?_
- **#65** `2/HĐBT` → Retrieved: `14/2000/NĐ-CP, 69/2000/QĐ-TTg, 44/2000/NĐ-CP` — _Nội dung quy định tại Điều 9 của 2/HĐBT là gì?_
- **#66** `02/2000/NĐ-CP` → Retrieved: `217/2000/QĐ-TCBĐ, 48/1999/NĐ-CP, 55/1999/NĐ-CP` — _Theo văn bản 02/2000/NĐ-CP, quy định về phạm vi điều chỉnh được nêu ở đâu và như_
- **#67** `176-QĐ/LBGTVT-NV` → Retrieved: `2/BT, 74/2000/QĐ-UB, 1588/QĐ-UB` — _Văn bản 176-QĐ/LBGTVT-NV quy định thế nào về việc: xe tránh nhau?_
- **#69** `553-BYT/QĐ` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 553-BYT/QĐ là gì?_
- **#71** `983/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 983/QĐ-UB là gì?_
- **#74** `254-TC/QĐ-BH` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 18/2000/QĐ-BGDĐT` — _Nội dung quy định tại Điều 14 của 254-TC/QĐ-BH là gì?_
- **#75** `257/SL` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của 257/SL là gì?_
- **#81** `37/2000/QĐ-NHNN1` → Retrieved: `249/2000/QĐ-NHNN9, 224/2000/QĐ-NHNN2, 448/2000/QĐ-NHNN2` — _Văn bản 37/2000/QĐ-NHNN1 quy định thế nào về việc: việc bổ sung, sửa đổi quy chế_
- **#84** `197-HĐBT` → Retrieved: `171/1999/NĐ-CP, 48/HĐBT, 23/2000/QĐ-CHK` — _Chi tiết Điều 4 trong 197-HĐBT về - bãi bỏ những quy định trước đây trái với quy_
- **#85** `182 QĐ/UB-TC` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của 182 QĐ/UB-TC là gì?_
- **#89** `24/2000/NĐ-CP` → Retrieved: `12/2000/TT-BKH, 44/2000/NĐ-CP, Không số` — _Nội dung quy định tại Điều 54 của 24/2000/NĐ-CP là gì?_
- **#103** `38/2000/QĐ-BCN` → Retrieved: `48/TBXH, 40/1998/QĐ-UB, 1592/TCHQ-PC` — _Theo văn bản 38/2000/QĐ-BCN, quy định về nhiệm vụ chủ yếu củavụ được nêu ở đâu v_
- **#104** `174/HĐBT` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 174/HĐBT là gì?_
- **#108** `06/QĐ-TTg` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của 06/QĐ-TTg là gì?_
- **#111** `28/2000/PL-UBTVQH10` → Retrieved: `18/1999/PL-UBTVQH10, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 34 của 28/2000/PL-UBTVQH10 là gì?_
- **#118** `2779/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 2779/QĐ-UB là gì?_
- **#126** `801/QĐ` → Retrieved: `437/QĐ-KT, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 4 của 801/QĐ là gì?_
- **#132** `358-CT` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 358-CT là gì?_
- **#152** `Không số` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 76/2000/NĐ-CP` — _Nội dung quy định tại Điều 33 của Không số là gì?_
- **#154** `19-LĐTBXH/TT` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 17/2000/QĐ-BXD` — _Nội dung quy định tại Điều 7 của 19-LĐTBXH/TT là gì?_
- **#156** `44/SL` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 44/SL là gì?_
- **#157** `13/HĐBT` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 13/HĐBT là gì?_
- **#158** `41/1999/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 41/1999/QĐ-UB là gì?_
- **#162** `101/2000/QĐ-UB` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của 101/2000/QĐ-UB là gì?_
- **#166** `Không số` → Retrieved: `44/2000/NĐ-CP, 17/1999/PL-UBTVQH10, 17/1999/PL-UBTVQH10` — _Nội dung quy định tại Điều 1 của Không số là gì?_
- **#167** `126/SL` → Retrieved: `44/2000/NĐ-CP, 14/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 3 của 126/SL là gì?_
- **#168** `305-TC/BH` → Retrieved: `44/2000/NĐ-CP, 353-HĐBT, 69/2000/QĐ-TTg` — _Nội dung quy định tại Điều 8 của 305-TC/BH là gì?_
- **#174** `171/1999/NĐ-CP` → Retrieved: `120-CP, 147/TT-GTVT, 19-GT-CA` — _Theo văn bản 171/1999/NĐ-CP, quy định về bộ giao thông vận tải có trách nhiệm đư_
- **#176** `659/QĐ-UB` → Retrieved: `55/1999/NĐ-CP, 353-HĐBT, 124/SL` — _Chi tiết Điều 5 trong 659/QĐ-UB về chế độ của đội?_
- **#177** `30/HĐBT` → Retrieved: `233/1999/QĐ-TTg, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 17 của 30/HĐBT là gì?_
- **#180** `313-CT` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 313-CT là gì?_
- **#192** `87/SL` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 1341/QĐ-UB` — _Nội dung quy định tại Điều 2 của 87/SL là gì?_
- **#193** `44/2000/NĐ-CP` → Retrieved: `825/2000/TT-BKHCNMT, 825/2000/TT-BKHCNMT, 176/1999/NĐ-CP` — _Theo văn bản 44/2000/NĐ-CP, quy định về thủ tục xử phạt được nêu ở đâu và như th_
- **#196** `764/TTg` → Retrieved: `44/2000/NĐ-CP, 4/CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 10 của 764/TTg là gì?_
- **#197** `64-HĐBT` → Retrieved: `16/1997/NĐ-CP, 44/2000/NĐ-CP, 1341/QĐ-UB` — _Nội dung quy định tại Điều 20 của 64-HĐBT là gì?_
- **#198** `50/HĐBT` → Retrieved: `01/QĐ-UB, 802-BYT/QĐ, 01/QĐ-UB` — _Trong lĩnh vực dat_dai, 50/HĐBT hướng dẫn về - tổ chức bộ máy giúp bộ trưởng thự_
- **#199** `39/1995/NĐ-CP` → Retrieved: `44/2000/NĐ-CP, 1341/QĐ-UB, 17/2000/QĐ-BXD` — _Nội dung quy định tại Điều 7 của 39/1995/NĐ-CP là gì?_
