# PolicyGPT Enterprise: engineering case study

## Project overview

PolicyGPT Enterprise is a production-style evidence intelligence and policy RAG system. It accepts real PDFs, creates persistent evidence and metadata, and answers policy questions with page-level provenance, calibrated confidence, and controlled fallback behavior.

The intended audiences are HR and policy reviewers, compliance or governance teams, and engineers who need to understand why an answer was allowed or rejected. The project is a portfolio system rather than a commercial deployment.

## Problem and requirements

Generic document chat demos optimize for a fluent answer. Policy work needs a stronger contract: durable document identity, reviewable evidence, unsupported-question handling, and safe failure when optional generation is unavailable.

The product requirements were therefore:

- ingest and retain valid PDFs without exposing storage paths
- prevent duplicate indexing
- retrieve page-aware evidence across indexed documents
- block unsupported generation
- provide citations and interpretable confidence
- remain useful without Groq/OpenAI
- expose real evaluation results and dependency status
- survive a release-like stop/start without losing data

## Engineering constraints

The system uses local SentenceTransformer embeddings, embedded persistent Chroma, PostgreSQL metadata, synchronous ingestion, optional OpenAI-compatible providers, and a four-service Docker Compose deployment. Authentication, background workers, cloud infrastructure, and hosted observability were intentionally excluded so the evidence and operational contracts stayed the focus.

## Architecture and RAG pipeline

Next.js provides the Documents, Ask, Evaluation, and System products. Its server-only BFF owns upstream URLs, timeouts, validation, and safe error normalization. FastAPI routes delegate to services for storage, extraction, cleaning, chunking, embedding, retrieval, confidence, generation, and evaluation reads.

The ingestion pipeline hashes the full file, establishes PostgreSQL identity, stores the source atomically, extracts page text, cleans it, creates metadata-aware chunks, embeds locally, writes Chroma records, and marks the lifecycle ready only after indexing succeeds.

The Ask pipeline retrieves candidates, calculates evidence diagnostics, rejects scope or numeric contradictions, and permits generation only when the question has direct support. The output retains document, page, section, and excerpt provenance.

## Evidence and confidence design

Similarity alone is not called confidence. PolicyGPT calculates an answerability decision using retrieval score, candidate separation, query/evidence term coverage, numeric consistency, direct support, and external-authority risk. Unsupported responses show the rejection state instead of speculative prose.

This design makes confidence explainable and keeps page-level evidence as the primary review object. The generated text is helpful only after the evidence contract passes.

## Evaluation strategy

The repository contains 16 questions: 11 expected to be supported and 5 expected to be unsupported. The runner records readiness correctness, fallback correctness, expected-page hits, keyword matches, citation diagnostics, calibrated confidence inputs, provider attempts, and safe errors. The evaluation UI presents the real latest artifact; it does not invent analytics.

Dataset results are regression evidence for this controlled benchmark, not production accuracy or service-level claims.

## PostgreSQL metadata design

PostgreSQL is the source of truth for UUID identity, original and safe filenames, content type, byte size, SHA-256, storage key, processing state, counts, model/collection metadata, safe failure details, and timestamps. It does not store PDF bytes, extracted text, chunks, embeddings, prompts, or answers.

The SHA-256 uniqueness constraint makes duplicate prevention durable. Lifecycle updates make partially completed ingestion visible and let failures remain diagnosable without exposing raw exception text.

## Deployment and failure design

Compose starts PostgreSQL, gates on Alembic, then gates FastAPI and Next.js on readiness. Stable named volumes preserve the logical dataset. Both application images run non-root and the backend image caches a pinned embedding-model revision.

Liveness does not depend on PostgreSQL, Chroma, embeddings, or providers. Readiness checks PostgreSQL and Chroma read-only. Providers are optional: missing keys or temporary generation failures use citation-only fallback while evidence remains available.

Request IDs, safe HTTP completion logs, security headers, CORS validation, fail-fast settings, normalized errors, smoke tests, and a release verifier make failure states observable without claiming a full monitoring platform.

## Security boundaries

Operational endpoints exclude URLs, hosts, credentials, internal names, storage paths, stack traces, chunks, and embeddings. General request logging excludes bodies, prompts, answers, uploaded bytes, authorization headers, and cookies. The BFF keeps the backend address server-only.

The system does not implement authentication, authorization, tenant isolation, managed secrets, malware scanning, TLS, formal retention, or compliance certification. Those are explicit future requirements.

## Important decisions and tradeoffs

- **Evidence gate before generation:** lower answer coverage, stronger unsupported behavior.
- **PostgreSQL plus Chroma plus source storage:** clearer ownership and provenance, coordinated backup responsibility.
- **Synchronous ingestion:** simple truthful lifecycle, limited throughput and request duration.
- **Local embeddings:** provider-independent retrieval, larger image and model lifecycle responsibility.
- **Embedded Chroma:** straightforward single-instance persistence, no multi-replica coordination.
- **Provider-independent readiness:** availability reflects required evidence services, not an optional paid dependency.
- **Server-side BFF:** safer configuration and contracts, an additional runtime hop.

## Challenges and solutions

PDF extraction required cleaning without losing page provenance. Duplicate prevention required identity before expensive indexing and compensation after partial failure. Confidence required separating answerability from raw retrieval similarity. Provider errors required retries for transient failures but a controlled evidence-only result when generation still failed. Deployment required migration gating and consistent persistence across three data owners.

Each solution was tested at the boundary where it could fail rather than hidden inside a prompt.

## Validation evidence

- 229 backend tests and 112 frontend tests
- validated 16-question evaluation dataset
- frontend lint and production build
- Compose configuration with exactly PostgreSQL, migrate, backend, and frontend services
- non-root application containers and health-gated startup
- persistence verified across safe Compose down/up in the established baseline
- duplicate upload and provider-fallback behavior exercised in the established baseline

These counts and checks are repository validation facts, not customer or production claims.

## What makes it more than a PDF chatbot

Persistent document identity, duplicate prevention, metadata-aware retrieval, evidence gating, page-level provenance, calibrated confidence, unsupported-answer handling, provider resilience, evaluation datasets, operational logging, PostgreSQL lifecycle metadata, release-like Docker deployment, and explicit readiness/failure design.

## Limitations and roadmap

The current design is single-host and synchronous. It lacks authenticated tenant boundaries, asynchronous workers, managed stores and backups, distributed vector infrastructure, cloud deployment automation, and hosted telemetry.

A production roadmap would add identity and authorization first, then malware scanning/object storage, job-based ingestion, managed databases/backups, TLS and secret management, distributed observability, and reviewed cloud deployment.

## Skills demonstrated

- RAG architecture, retrieval, evidence gates, prompting, and provider resilience
- confidence calibration and evaluation design
- FastAPI/Pydantic service and error contracts
- PostgreSQL/SQLAlchemy/Alembic lifecycle modeling
- Next.js/React/TypeScript BFF and product states
- Docker image and Compose operational design
- testing, release verification, security boundaries, and technical communication

## Interview talking points

1. Why retrieval score is not confidence and how direct support changes the decision.
2. How the system behaves across unsupported evidence, missing provider keys, and dependency outages.
3. Why document identity belongs in PostgreSQL while chunks belong in Chroma.
4. How migration, readiness, and named volumes create a release-like startup contract.
5. Which missing controls prevent a cloud-production claim and what order to add them.
