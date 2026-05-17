# Trusted Sources And Paywall Policy

## PubMed Source Scope

The primary evidence source is PubMed through NCBI E-utilities:

- `esearch` for PMID discovery.
- `efetch` for metadata and abstracts.
- No publisher website scraping.
- No paywalled full text access.

## Journal Allowlist

The PubMed query is restricted to:

- BMJ
- Br Med J
- Lancet
- Nature
- JAMA
- JAMA Intern Med
- N Engl J Med
- Ann Intern Med
- Diabetes Care
- Diabetologia
- Circulation
- J Am Heart Assoc
- Eur Heart J
- Circ Res
- Stroke

After `efetch`, each record is checked again using `Journal/ISOAbbreviation`. Records outside the allowlist are discarded.

## Uploaded PDFs

Uploaded PDFs are optional. They are processed locally with PyMuPDF, chunked, and ranked against the doctor's question. They are cited as `[user PDF]` and listed as `User-provided PDF`.

User PDFs are not automatically trusted as peer-reviewed evidence. They are separate context supplied by the doctor.
