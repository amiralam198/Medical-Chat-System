# Anti-Hallucination Design

This project does not generate medical answers from model weights. It retrieves evidence, ranks it, and copies short verbatim text from retrieved abstracts or user-provided PDF chunks.

## Guardrails

- No OpenAI, Gemini, Anthropic, or other generative LLM APIs.
- No model-memory answers.
- No paraphrasing in the default answer path.
- No invented citations.
- PubMed citations come only from parsed NCBI XML records.
- PDF evidence is labeled `[user PDF]` and is not treated as peer-reviewed by default.
- If no usable evidence sentence exists, the answer is exactly:

```text
I don't know based on the retrieved evidence.
```

## Extractive Answer Rules

The answer builder uses up to two PubMed sources and up to one uploaded PDF chunk. It chooses evidence sentences from abstract text or title fallback, appends `[pmid:...]`, and enforces a 100-word hard cap. PDF excerpts are prefixed with `From your uploaded PDF (verbatim):` and marked `[user PDF]`.

## Embeddings Are Ranking Only

Local `sentence-transformers/all-MiniLM-L6-v2` embeddings can rank evidence. They never produce answer text. If embeddings are unavailable, lexical overlap ranking is used and the chat endpoint still works.
