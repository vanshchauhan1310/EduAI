# PDF store — TEST ONLY

Drop NCERT (or any) PDFs here to feed the RAG knowledge base during local
testing. You can either:

- **Upload via the app** — the Streamlit sidebar saves the PDF here and ingests it, or
- **Drop a file here manually** and pick it in the app's "Knowledge base" panel to ingest.

Ingestion parses the PDF → text chunks → stores them in SQLite (`db.KBChunk`),
and the retriever (`rag.py`) indexes them so the tutor is grounded in the content.

> ⚠️ **This local folder is for prototyping only.** In production a future
> developer should replace it with object storage (e.g. S3 / Supabase Storage)
> and move the chunks + embeddings into the production DB (Postgres + pgvector).
> The PDFs themselves are git-ignored.
