# Protocol: Git Workflow

## Nhánh
- `main`: luôn chạy được. **Không push trực tiếp.** Protected (yêu cầu PR + 1 approve).
- `feature/<tên>-<mô-tả-ngắn>`: ví dụ `feature/tuyen-langgraph-agent`, `feature/an-hitl-api`, `feature/binh-doctor-dashboard`.
- `fix/<tên>-<mô-tả>` cho sửa lỗi; `docs/<mô-tả>` cho tài liệu; `contract/<mô-tả>` **riêng** cho thay đổi contract.

## Vòng lặp hàng ngày
```bash
git checkout main && git pull origin main          # 1. luôn cập nhật trước khi bắt đầu
git checkout -b feature/<ten>-<viec>                # 2. nhánh riêng
# ... code trong THƯ MỤC KHỐI CỦA MÌNH ...
git add <file cụ thể>                               # 3. không `git add .` bừa
git commit -m "feat(ai): thêm node red_flag"        # 4. commit nhỏ, message chuẩn
git push -u origin feature/<ten>-<viec>             # 5. push
# 6. mở Pull Request → điền template → tag reviewer → chờ CI xanh + approve → Squash & merge
```

## Conventional Commits
`<type>(<scope>): <mô tả ngắn, tiếng Việt hoặc Anh>`
- type: `feat` `fix` `docs` `refactor` `test` `chore` `contract`
- scope: `ai` `be` `fe` `docs` `infra`
- Ví dụ: `feat(be): endpoint POST /sessions/{id}/review`, `contract: thêm trường priority vào PlanItem`

## Pull Request
- Nhỏ (< 400 dòng thay đổi nếu được). 1 PR = 1 việc.
- Điền `.github/pull_request_template.md`.
- Reviewer: người khối kế bên (AI↔BE, BE↔FE). PR `contract/*` cần **cả 3** approve.
- Merge bằng **Squash and merge** để lịch sử `main` gọn.

## Tránh conflict
1. Chỉ sửa trong thư mục khối mình (xem `OWNERSHIP.md`). File dùng chung (`README.md`, `.env.example`, `docs/`) → sửa nhỏ, PR riêng.
2. Rebase thường xuyên: `git fetch origin && git rebase origin/main` (giải quyết conflict sớm khi còn nhỏ).
3. Không commit: `.env`, `node_modules`, `vector_store/`, `*.db`, file IDE.
4. Không format lại file của người khác (format cả file = conflict chắc chắn).
5. Đổi tên/di chuyển file dùng chung → báo nhóm trước.

## Khi có conflict
```bash
git fetch origin && git rebase origin/main
# sửa conflict trong editor → git add <file> → git rebase --continue
git push --force-with-lease      # CHỈ trên nhánh feature của mình, KHÔNG BAO GIỜ trên main
```
