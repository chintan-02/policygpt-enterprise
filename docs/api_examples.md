# PolicyGPT Enterprise API Examples

This file contains common API commands for testing PolicyGPT Enterprise from the terminal.

Make sure the backend is running:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Backend documentation:

```text
http://localhost:8000/docs
```

---

## 1. Health Check

```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

Expected shape:

```json
{
  "status": "healthy"
}
```

The exact response fields may differ depending on the current health implementation, but the request should return successfully.

---

## 2. Upload Sample PDF

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@examples/sample_hr_policy.pdf" \
  | python -m json.tool
```

Expected shape:

```json
{
  "success": true,
  "filename": "sample_hr_policy.pdf",
  "page_count": 12,
  "chunk_count": 20,
  "stored_chunk_count": 20,
  "collection_name": "policygpt_documents"
}
```

Important fields:

| Field                | Meaning                                   |
| -------------------- | ----------------------------------------- |
| `page_count`         | Number of pages extracted from the PDF    |
| `total_characters`   | Total extracted characters after cleaning |
| `chunk_count`        | Number of chunks created                  |
| `stored_chunk_count` | Number of chunks stored in ChromaDB       |
| `collection_name`    | Active ChromaDB collection                |

---

## 3. Retrieve Evidence

Use this endpoint when you want to inspect retrieval before answer generation.

```bash
curl -X POST "http://localhost:8000/api/v1/documents/evidence" \
  -H "Content-Type: application/json" \
  -d '{"query":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

Expected shape:

```json
{
  "success": true,
  "query": "What is the remote work equipment allowance?",
  "top_k": 5,
  "answer_ready": true,
  "evidence_status": "moderate",
  "confidence_score": 0.6217,
  "min_retrieval_score": 0.45,
  "citation_count": 1,
  "citations": [
    {
      "filename": "sample_hr_policy.pdf",
      "page_number": 5,
      "section_title": "3. Remote and Hybrid Work",
      "retrieval_score": 0.6217
    }
  ]
}
```

Expected behavior:

* citation card points to page 5
* section title should be Remote and Hybrid Work
* `evidence_text` should not appear in the API response
* `excerpt` should be short enough for UI display

---

## 4. Ask Supported Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

Expected shape:

```json
{
  "success": true,
  "question": "What is the remote work equipment allowance?",
  "answer_ready": true,
  "evidence_status": "moderate",
  "confidence_score": 0.6217,
  "citation_count": 1,
  "llm_provider": "groq",
  "model_name": "llama-3.3-70b-versatile",
  "fallback_used": false
}
```

Expected answer should mention:

* one-time equipment allowance
* up to CAD 300
* approved ergonomic or productivity items
* receipts required
* approval before reimbursement

This confirms:

* evidence retrieval worked
* answer generation was allowed
* Groq or OpenAI generated an answer
* the answer was grounded in citation evidence

---

## 5. Ask AI Tool Policy Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Can employees paste confidential data into public AI tools?","top_k":5}' \
  | python -m json.tool
```

Expected answer should mention:

* employees must not paste confidential data into public AI tools
* personal data
* customer data
* proprietary code
* internal documents
* security details
* Security and Legal approval

Expected behavior:

```json
{
  "answer_ready": true,
  "evidence_status": "strong",
  "fallback_used": false
}
```

The answer should be grounded in the Confidentiality, Data Privacy, and AI Tool Use section.

---

## 6. Ask Vacation Notice Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"How many days in advance should employees request planned vacation?","top_k":5}' \
  | python -m json.tool
```

Expected answer should mention the required advance notice from the uploaded policy document.

Use this question to test:

* leave policy retrieval
* page citation quality
* section title extraction

---

## 7. Ask Harassment / Retaliation Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What should employees do if they see harassment or retaliation?","top_k":5}' \
  | python -m json.tool
```

Expected answer should mention reporting concerns through the proper channel described in the policy.

Use this question to test:

* conduct policy retrieval
* compliance-style answer generation
* citation grounding

---

## 8. Ask Expense Receipt Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What does the policy say about expense receipts?","top_k":5}' \
  | python -m json.tool
```

Expected answer should mention receipt requirements from the expense/travel policy section.

Use this question to test:

* policy-specific retrieval
* answer completeness
* citation quality

---

## 9. Ask Unsupported Question

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the CEO home address?","top_k":5}' \
  | python -m json.tool
```

Expected response:

```json
{
  "success": true,
  "question": "What is the CEO home address?",
  "answer": "I could not find enough supporting evidence in the uploaded documents to answer this question reliably.",
  "answer_ready": false,
  "evidence_status": "insufficient",
  "confidence_score": 0.0,
  "citation_count": 0,
  "citations": [],
  "llm_provider": "none",
  "model_name": null,
  "fallback_used": true
}
```

This proves unsupported answers are not hallucinated.

Important expected behavior:

* LLM should not be called
* citation count should be 0
* confidence should be 0.0
* fallback should be true
* provider should be none

---

## 10. Test No-LLM Mode

In `.env`, temporarily set:

```env
ENABLE_LLM_ANSWER=false
LLM_PROVIDER=none
```

Restart backend:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Ask a supported question:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

Expected shape:

```json
{
  "answer_ready": true,
  "fallback_used": true,
  "llm_provider": "none",
  "citation_count": 1
}
```

This proves the system can return citation evidence even when LLM generation is disabled.

After testing, switch back:

```env
ENABLE_LLM_ANSWER=true
LLM_PROVIDER=groq
```

Restart backend again.

---

## 11. Test Provider Failure Fallback

Temporarily set an invalid Groq key:

```env
GROQ_API_KEY=wrong_key_test
```

Restart backend and ask a supported question:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"Can employees paste confidential data into public AI tools?","top_k":5}' \
  | python -m json.tool
```

Expected behavior:

* API should not crash
* raw provider error should not be exposed
* citation evidence should still be returned
* fallback should be true
* answer should say LLM generation is not available right now

After testing, restore the real key.

---

## 12. Clean Vector Store for Fresh Demo

For a clean demo, stop the backend and remove local ChromaDB data:

```bash
rm -rf data/chroma
```

Restart backend:

```bash
uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000
```

Upload the sample PDF again:

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@examples/sample_hr_policy.pdf" \
  | python -m json.tool
```

This prevents duplicate indexed documents during local testing.

---

## 13. Recommended Demo Order

Run these in order:

```bash
curl http://localhost:8000/api/v1/health | python -m json.tool
```

```bash
curl -X POST "http://localhost:8000/api/v1/documents/upload" \
  -F "file=@examples/sample_hr_policy.pdf" \
  | python -m json.tool
```

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the remote work equipment allowance?","top_k":5}' \
  | python -m json.tool
```

```bash
curl -X POST "http://localhost:8000/api/v1/documents/ask" \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the CEO home address?","top_k":5}' \
  | python -m json.tool
```
