# PolicyGPT Enterprise Smoke Test Checklist

Use this checklist before committing, recording a demo, or showing the project to someone.

The purpose of this checklist is to confirm that PolicyGPT Enterprise still behaves like a safe RAG system:

```text
retrieve evidence
→ score evidence
→ generate only if supported
→ return citations or fallback
```

---

## 1. Environment Check

* [ ] `.env` exists
* [ ] `.env` is not committed to Git
* [ ] `.env.example` exists
* [ ] `GROQ_API_KEY` is set if using Groq
* [ ] `LLM_PROVIDER=groq` for Groq demo
* [ ] `ENABLE_LLM_ANSWER=true` for real LLM answers
* [ ] `MIN_RETRIEVAL_SCORE=0.45`
* [ ] `CITATION_EXCERPT_MAX_CHARS=450`
* [ ] `LLM_EVIDENCE_MAX_CHARS=1200`
* [ ] `MAX_CITATION_CARDS=5`

Run:

```bash
cat .env | grep -E "LLM_PROVIDER|ENABLE_LLM_ANSWER|MIN_RETRIEVAL_SCORE|CITATION_EXCERPT_MAX_CHARS|LLM_EVIDENCE_MAX_CHARS"
```

Expected:

```text
ENABLE_LLM_ANSWER=true
LLM_PROVIDER=groq
MIN_RETRIEVAL_SCORE=0.45
CITATION_EXCERPT_MAX_CHARS=450
LLM_EVIDENCE_MAX_CHARS=1200
```

Do not print or share the real API key.

---

## 2. Backend Startup

Start backend:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Checklist:

* [ ] backend starts without import errors
* [ ] no Pydantic settings error
* [ ] no ChromaDB initialization error
* [ ] no missing package error
* [ ] no API key printed in logs

---

## 3. Backend Health

Run:

```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

Checklist:

* [ ] endpoint returns successfully
* [ ] backend status is healthy or ready
* [ ] no 500 error
* [ ] response is valid JSON

---

## 4. Clean Vector Store for Demo

For a clean test:

```bash
rm -rf data/chroma
```

Then restart backend.

Checklist:

* [ ] old vector data removed
* [ ] backend restarted after cleanup
* [ ] sample PDF uploaded once only
* [ ] duplicate citation cards do not appear

---

## 5. PDF Upload

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@examples/sample_hr_policy.pdf" \
  | python -m json.tool
```

Checklist:

* [ ] `success` is true
* [ ] filename is `sample_hr_policy.pdf`
* [ ] page count is 12
* [ ] total characters is greater than 0
* [ ] chunks are created
* [ ] chunks are stored in ChromaDB
* [ ] collection name is returned
* [ ] no duplicate upload issue during demo

Expected key fields:

```json
{
  "success": true,
  "filename": "sample_hr_policy.pdf",
  "page_count": 12,
  "chunk_count": 20,
  "stored_chunk_count": 20
}
```

---

## 6. Evidence Retrieval

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/evidence" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

Checklist:

* [ ] `answer_ready` is true
* [ ] `evidence_status` is moderate or strong
* [ ] `confidence_score` is greater than 0
* [ ] `citation_count` is greater than 0
* [ ] citation includes filename
* [ ] citation includes page number
* [ ] citation includes section title
* [ ] citation includes retrieval score
* [ ] `evidence_text` is not exposed in API response
* [ ] citation excerpt is short enough for UI
* [ ] citation points to the correct section

Expected citation section:

```text
3. Remote and Hybrid Work
```

---

## 7. Supported Question Answer

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

Checklist:

* [ ] `success` is true
* [ ] `answer_ready` is true
* [ ] `fallback_used` is false
* [ ] `llm_provider` is `groq` or `openai`
* [ ] `model_name` is returned
* [ ] citation count is greater than 0
* [ ] answer mentions CAD 300
* [ ] answer mentions receipts
* [ ] answer mentions approval before reimbursement

---

## 8. AI Tool Policy Question

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Can employees paste confidential data into public AI tools?","top_k":5}' \
  | python -m json.tool
```

Checklist:

* [ ] answer is generated
* [ ] fallback is false
* [ ] evidence status is strong or moderate
* [ ] answer says confidential data should not be pasted into public AI tools
* [ ] answer mentions Security and Legal approval
* [ ] citation points to data privacy / AI tool section

Expected section:

```text
5. Confidentiality, Data Privacy, and AI Tool Use
```

---

## 9. Unsupported Question Fallback

Run:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the CEO home address?","top_k":5}' \
  | python -m json.tool
```

Checklist:

* [ ] `success` is true
* [ ] `answer_ready` is false
* [ ] `evidence_status` is insufficient
* [ ] `confidence_score` is 0.0
* [ ] `citation_count` is 0
* [ ] citations list is empty
* [ ] `llm_provider` is none
* [ ] `model_name` is null
* [ ] `fallback_used` is true
* [ ] answer does not invent a CEO address

Expected behavior:

```text
The system should not call Groq/OpenAI when evidence is insufficient.
```

---

## 10. Provider Failure Fallback

Temporarily set an invalid key in `.env`:

```env
GROQ_API_KEY=wrong_key_test
```

Restart backend and ask a supported question.

Checklist:

* [ ] API does not crash
* [ ] raw provider error is not exposed to the user
* [ ] fallback_used is true
* [ ] citation evidence is still returned
* [ ] answer says LLM generation is not available right now

After test, restore the real key:

```env
GROQ_API_KEY=your_real_key
```

Restart backend again.

---

## 11. No-LLM Mode

Temporarily set:

```env
ENABLE_LLM_ANSWER=false
LLM_PROVIDER=none
```

Restart backend and ask a supported question.

Checklist:

* [ ] answer_ready is true
* [ ] citation evidence is returned
* [ ] fallback_used is true
* [ ] llm_provider is none
* [ ] API does not crash

Then restore:

```env
ENABLE_LLM_ANSWER=true
LLM_PROVIDER=groq
```

---

## 12. Streamlit UI

Run:

```bash
streamlit run ui/app.py
```

Checklist:

* [ ] UI opens at `http://localhost:8501`
* [ ] sidebar loads
* [ ] backend status says connected
* [ ] upload section appears
* [ ] sample PDF uploads successfully
* [ ] document indexed summary appears
* [ ] Ask PolicyGPT page works
* [ ] answer card appears
* [ ] evidence badge appears
* [ ] confidence badge appears
* [ ] provider badge appears
* [ ] model badge appears
* [ ] fallback badge appears
* [ ] citation cards render cleanly
* [ ] no raw HTML appears in citation cards
* [ ] unsupported question shows fallback UI
* [ ] Evidence Explorer page works
* [ ] Architecture page works

---

## 13. UI Demo Questions

Test these in the Streamlit UI:

```text
What is the remote work equipment allowance?
Can employees paste confidential data into public AI tools?
How many days in advance should employees request planned vacation?
What should employees do if they see harassment or retaliation?
What does the policy say about expense receipts?
What is the CEO home address?
```

Checklist:

* [ ] supported questions generate answers
* [ ] unsupported question falls back
* [ ] citations appear for supported questions
* [ ] no citations appear for unsupported question
* [ ] provider badge is shown
* [ ] confidence score is shown

---

## 14. Git Check

Run:

```bash
git status
```

Checklist:

* [ ] `.env` is not staged
* [ ] `data/` is not staged
* [ ] `.DS_Store` is not staged
* [ ] README is staged
* [ ] docs are staged
* [ ] screenshots `.gitkeep` is staged

Commit:

```bash
git add README.md docs/demo_script.md docs/api_examples.md docs/smoke_test_checklist.md screenshots/.gitkeep
git commit -m "Add README and demo documentation"
git push
```

---

## 15. Final Demo Readiness

Before showing the project:

* [ ] backend running
* [ ] Streamlit running
* [ ] sample PDF uploaded once
* [ ] supported question tested
* [ ] unsupported question tested
* [ ] Evidence Explorer tested
* [ ] Architecture page tested
* [ ] GitHub repository updated
* [ ] README looks complete on GitHub
* [ ] screenshots are ready for Step 8.6
