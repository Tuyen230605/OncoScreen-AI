# data/guidelines — nguồn sự thật cho RAG

Mỗi file `.md` = 1 guideline (hoặc 1 phần), tên `<cancer_type>_<source>_<year>.md`. Bắt buộc có frontmatter:

```yaml
---
cancer_type: breast          # breast | cervical | colorectal | liver | lung | prostate | other
source: "USPSTF 2024"        # tên hiển thị
url: https://...
gender: female               # male | female | any
min_age: 40
max_age: 74
risk_level: average          # average | elevated | high | any
language: vi                 # vi | en
---
```

Nội dung: chia theo heading `## ` (mỗi heading = 1 chunk). Nên có các mục: `## Khuyến nghị`, `## Đối tượng`, `## Phương pháp & khoảng cách`, `## Dấu hiệu cảnh báo`.

Ưu tiên nguồn mở: USPSTF, ACS, WHO, Bộ Y tế VN, Bệnh viện K. Ghi rõ URL để trích dẫn. Tóm tắt bằng tiếng Việt, giữ số liệu chính xác.
