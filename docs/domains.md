# Domains

`Vietnam Legal RAG` hỗ trợ **multi-domain** thông qua registry trong
`vietnam_legal_rag/domains/__init__.py`. Mỗi domain là một file riêng
đặt tên theo slug snake_case, export một hằng `DOMAIN` kiểu `DomainSpec`.

## Domain đã đăng ký

| Tên           | Hiển thị                  | Mô tả                                                                  |
|---------------|---------------------------|------------------------------------------------------------------------|
| `giao_thong`  | Luật Giao thông đường bộ   | Luật 23/2008/QH12, Nghị định 100/2019, 168/2024 về xử phạt VPHC.       |
| `dan_su`      | Bộ luật Dân sự 2015        | Hợp đồng, nghĩa vụ dân sự, quyền sở hữu, thừa kế.                      |
| `hinh_su`     | Bộ luật Hình sự 2015       | Tội danh, khung hình phạt, tình tiết tăng nặng / giảm nhẹ.            |
| `lao_dong`    | Bộ luật Lao động 2019      | Hợp đồng lao động, sa thải, BHXH, thời giờ làm việc, nghỉ phép.        |

## Cách thêm domain mới

1. Tạo file `src/vietnam_legal_rag/domains/<slug>.py`:

    ```python
    from vietnam_legal_rag.domains.base import DomainSpec

    DOMAIN = DomainSpec(
        name="dat_dai",
        display_name="Luật Đất đai 2024",
        description="Luật số 31/2024/QH15 — quyền sử dụng đất, giao dịch đất đai.",
        source_urls=[],
        keywords=["đất đai", "quyền sử dụng đất", "chuyển nhượng", "thửa đất"],
    )
    ```

2. Đăng ký trong `src/vietnam_legal_rag/domains/__init__.py`:

    ```python
    from vietnam_legal_rag.domains.dat_dai import DOMAIN as DAT_DAI

    DOMAIN_REGISTRY: dict[str, DomainSpec] = {
        spec.name: spec
        for spec in (GIAO_THONG, DAN_SU, HINH_SU, LAO_DONG, DAT_DAI)
    }
    ```

3. (Tuỳ chọn) Bổ sung URL nguồn vào `source_urls` sau khi đã crawl thử.

Không cần thay đổi bất kỳ file nào khác — CLI sẽ tự nhặt domain mới.

## Nguồn dữ liệu khuyến nghị

| Domain        | Nguồn chính thống                                |
|---------------|--------------------------------------------------|
| `giao_thong`  | thuvienphapluat.vn (mục Giao thông)              |
| `dan_su`      | thuvienphapluat.vn (mục Dân sự)                  |
| `hinh_su`     | thuvienphapluat.vn (mục Hình sự)                 |
| `lao_dong`    | thuvienphapluat.vn (mục Lao động)                |

> Ghi chú: một số văn bản còn hiệu lực có thể nằm trong **Nghị định** hoặc
> **Thông tư hướng dẫn**; cần scrape cả ba cấp (Luật → Nghị định → Thông tư)
> để truy hồi đầy đủ.

## Router Agent (phase tương lai)

Khi multi-agent được kích hoạt, `DomainSpec.keywords` sẽ là **tín hiệu chính**
để router phân loại câu hỏi. Vì vậy hãy giữ `keywords` ngắn gọn, đúng thuật ngữ
pháp lý, và ưu tiên các từ mà người dùng thật sự dùng (vd. "GPLX", "thửa đất").
