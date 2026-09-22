# Protocol: AI Core ↔ Backend Contract

**Nguồn sự thật:** `ai_core/ai_core/schemas.py` (Pydantic v2). File này là bản mô tả người-đọc; nếu lệch nhau, `schemas.py` thắng.
**Chủ sở hữu:** AI Core (Tuyền). Backend chỉ *tiêu thụ*. Muốn đổi → PR tag cả team.

## 1. Interface

Backend chỉ được import từ `ai_core.api` và `ai_core.schemas`. Không import sâu vào `graph/`, `rag/`, `tools/`.

```python
from ai_core.api import get_agent          # trả ScreeningAgent hoặc MockAgent tuỳ USE_MOCK_AGENT
from ai_core.schemas import PatientContext, ScreeningResult, ...

agent = get_agent()
agent.get_questionnaire(profile: PatientProfile) -> Questionnaire
agent.check_red_flags(answers: list[Answer]) -> RedFlagResult
agent.run_screening(ctx: PatientContext) -> ScreeningResult
agent.get_education(cancer_type: CancerType) -> EducationContent
```

Tất cả hàm **đồng bộ (sync)**, có thể chạy vài giây → backend gọi trong threadpool (`fastapi.concurrency.run_in_threadpool`).
Mọi lỗi nội bộ AI raise `ai_core.api.AgentError` (subclass `Exception`) — backend map thành HTTP 502.

## 2. Schemas (tóm tắt — xem `schemas.py` để biết đầy đủ)

### Enum
| Enum | Giá trị |
|---|---|
| `Gender` | `male`, `female`, `other` |
| `CancerType` | `breast`, `cervical`, `colorectal`, `liver`, `lung`, `prostate`, `other` |
| `RiskLevel` | `average`, `elevated`, `high` |
| `SessionStatus` | `collecting`, `red_flag`, `pending_review`, `approved`, `rejected`, `completed` |
| `QuestionType` | `single_choice`, `multi_choice`, `number`, `boolean`, `text` |
| `RedFlagSeverity` | `urgent` (đi khám ngay), `soon` (khám trong vài tuần) |

### Input
```
PatientProfile   { age:int, gender:Gender, genetics_history:list[str], lifestyle:dict[str,Any], lifestyle_score:float|None }
Answer           { question_id:str, value:Any }
PatientContext   { session_id:str, profile:PatientProfile, answers:list[Answer], prior_sessions_summary:str|None }
```

### Output
```
Question         { id, text, type:QuestionType, options:list[str]|None, required:bool, depends_on:str|None }
Questionnaire    { version:str, questions:list[Question] }

RedFlag          { code:str, symptom:str, severity:RedFlagSeverity, advice:str }
RedFlagResult    { detected:bool, flags:list[RedFlag], message:str|None }

Source           { doc_id:str, title:str, section:str|None, excerpt:str, url:str|None }
RiskFactor       { cancer_type:CancerType, level:RiskLevel, reasons:list[str] }
RiskAssessment   { overall_summary:str, factors:list[RiskFactor] }
PlanItem         { cancer_type:CancerType, method:str, start_age:int|None, interval_months:int,
                   next_due:date, rationale:str, sources:list[Source] (>=1), priority:int }
ScreeningPlan    { items:list[PlanItem], general_advice:str, generated_at:datetime, model:str }
ScreeningResult  { status:Literal["pending_review","red_flag"], risk_assessment:RiskAssessment|None,
                   draft_plan:ScreeningPlan|None, red_flag:RedFlagResult|None, disclaimer:str, trace_id:str }
EducationContent { cancer_type, title, warning_signs:list[str], prevention_tips:list[str], body_md:str, sources:list[Source] }
```

## 3. Bất biến (invariants) backend có thể tin tưởng
1. `run_screening` **không bao giờ** trả `draft_plan` khi `status == "red_flag"`.
2. Mọi `PlanItem.sources` có ≥ 1 phần tử (guardrail của AI Core đảm bảo).
3. `disclaimer` luôn non-empty, tiếng Việt.
4. `draft_plan` serialise bằng `.model_dump(mode="json")` → lưu thẳng vào cột JSON, đọc lại bằng `ScreeningPlan.model_validate`.
5. `MockAgent` và `ScreeningAgent` cùng interface, cùng schema → backend test với mock là đủ tin cậy về hình dạng dữ liệu.

### 3.1 Payload theo trạng thái

Đây là quy tắc bắt buộc cho mọi implementation của agent:

| `status` | Bắt buộc | Phải rỗng |
|---|---|---|
| `red_flag` | `red_flag.detected=true`, `red_flag.flags`, `red_flag.message`, `disclaimer`, `trace_id` | `risk_assessment`, `draft_plan` |
| `pending_review` | `risk_assessment`, `draft_plan.items[]`, `disclaimer`, `trace_id` | `red_flag` |

`ScreeningResult` tự kiểm tra các quy tắc này bằng Pydantic. Backend không cần tự đoán
payload có hợp lệ hay không; nếu agent trả dữ liệu sai, lỗi phải được map thành HTTP 502.

### 3.2 Hợp đồng MockAgent

`MockAgent` là implementation thay thế cho `ScreeningAgent`, không phải một schema khác.
Nó phải:

- trả questionnaire từ `data/questionnaire.json` và tôn trọng `depends_on`;
- chạy detector red-flag rule-based trước khi tạo kế hoạch;
- trả đủ ba trạng thái để tích hợp: `collecting` được thể hiện qua `missing_questions`,
  `red_flag` khi phát hiện triệu chứng và `pending_review` khi đủ dữ liệu;
- luôn trả `PlanItem.sources` không rỗng và disclaimer tiếng Việt;
- hỗ trợ truyền `today` khi khởi tạo trong test để `next_due` tái lập được.

Các ca chuẩn để BE/FE dùng khi tích hợp:

1. Nữ 45 tuổi, có tiền sử gia đình ung thư vú, không có triệu chứng → `pending_review`.
2. Nam 55 tuổi, hút thuốc từ 20 gói-năm trở lên → `pending_review`, có item phổi.
3. Bất kỳ hồ sơ nào trả lời một red-flag symptom là `true` → `red_flag`, không có plan.

## 4. Cấu hình AI Core đọc từ env
`LLM_PROVIDER`, `LLM_MODEL`, `LLM_API_KEY`, `EMBEDDING_PROVIDER`, `EMBEDDING_MODEL`, `VECTOR_STORE_DIR`, `USE_MOCK_AGENT`.
Backend không cần biết chi tiết — chỉ đảm bảo `.env` ở root được load (`ai_core.config` tự đọc).

## 5. Quy trình đổi contract
1. Mở PR sửa `schemas.py` + file này + `frontend/src/types/api.ts` (nếu ảnh hưởng đến FE).
2. Cập nhật `mock.py` để mock trả dữ liệu hợp lệ theo schema mới.
3. Cả 3 thành viên approve. Merge → thông báo trong nhóm.
