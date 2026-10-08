# Smart Library Management System — AI Enhanced

A standalone Flask/MySQL library prototype with borrowing transactions and Gemini recommendations grounded in the supplied catalog.

## Features

- Add/search books and check available/total copies.
- Add/list fictional demo members; borrow and return books.
- One active loan per member/book; reject unavailable copies and repeated returns.
- Recommend up to three catalog books from a reading interest with exact supporting excerpts. Unknown book IDs and unsupported excerpts are rejected.
- Library operations work even when Gemini is unavailable. AI receives catalog descriptions and the interest, never member names or loans.

## Windows setup (Python 3.12)

From this project folder in PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup.ps1
notepad .env
```

In MySQL Workbench, run:

```sql
CREATE DATABASE smart_library_system CHARACTER SET utf8mb4;
```

In your private .env, set DATABASE_URL in this shape:

```text
DATABASE_URL=mysql+pymysql://YOUR_USER:URL_ENCODED_PASSWORD@127.0.0.1:3306/smart_library_system?charset=utf8mb4
```

URL-encode reserved password characters. Never paste credentials into chat. Configure GEMINI_API_KEY and the exact GEMINI_MODEL currently working with your key. Set a private SECRET_KEY for stable sessions. The database must already exist; Workbench is a client and the MySQL server must be running.

```powershell
.\.venv\Scripts\python.exe -m flask --app run init-db
.\.venv\Scripts\python.exe -m flask --app run seed-demo
.\.venv\Scripts\python.exe run.py
```

Open http://127.0.0.1:5002. The seed command adds fictional books and members only to an empty database. It preserves existing data by refusing to seed it. init-db creates missing tables and never drops existing ones; it is not a schema migration tool.

## Demo

Borrow SQL Trail Guide as Demo Reader A. Borrow its second copy as Demo Reader B. The available count becomes zero. Return one loan and the count becomes one. Try recommending books for “I want to practise SQL joins.” Verify the exact catalog excerpt and current availability shown.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Tests exercise Flask workflows, real transactions in isolated SQLite, inventory invariants, rejected IDs/evidence, consent and mocked AI failures. They do not prove live MySQL locking or Gemini availability; verify those with your local credentials before presenting. SQLite is rejected outside TESTING.

## Architecture and limits

`models.py`: books, members and loans. `services.py`: atomic borrowing/returning. `routes.py`: form validation and escaped HTML. `ai.py`: structured recommendations validated against supplied catalog IDs and excerpts.

MySQL tables use InnoDB; book row locks and conditional inventory updates run inside one transaction. Failures roll back. No due dates, fines, reservations, edits/deletion screens, patron accounts or borrowing eligibility decisions. Records persist until removed by the operator. The model's reason is still advisory even when its quoted evidence is verified.

This is a local single-operator demo. Use fictional catalog and member records. Interests/recommendations are not saved; provider retention is separate. Recommendations support a catalog of up to 100 books. Credentials are ignored by Git. Add authentication, authorization, quota controls and retention management before public hosting.

## Repository workflow

Target: Priyadhanalakota61/smart_library_system, product branch smart_library_system. The code is maintained on the product branch; main contains the initial repository README. CI runs tests on pushes/PRs.
