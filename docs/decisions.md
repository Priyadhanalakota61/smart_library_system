# Confirmed scope and implementation decisions

The user asked to build both remaining products in separate repositories after the MVP proposal.

- Flask, SQLAlchemy, MySQL through PyMySQL, Gemini.
- Add/search books, add/list demo members, borrow/return, check available copies.
- Book fields: title, author, category, short description, total/available copies. These support the proposed catalog-based recommendation workflow.
- One active loan per member/book. No due dates, fines, reservations, eligibility decisions or user roles in this prototype.
- Conventional library records persist in MySQL with no auto-expiry or deletion screen. Recommendations and reading interests are not persisted.
- Recommendations use only supplied catalog descriptions/categories and reading interests, with book IDs and exact supporting excerpts checked server-side.
- Member identities and loan history are never included in AI context. Use fictional catalog and member data throughout the demo.
- Transactional inventory updates prevent negative counts and repeated returns. MySQL book row locking serializes borrowing and returning of the same book.
- SQLite exists only for isolated tests, never as a silently substituted production database.
- Local single-operator demo with CSRF and escaped HTML. No authentication or multi-user authorization. Public deployment requires an access-control design.
- No reuse of the user's earlier library code: this is a standalone implementation.
