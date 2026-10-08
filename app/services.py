from sqlalchemy import select, update
from .models import Book, Loan, Member, utc_now


class LibraryError(ValueError):
    pass


def borrow_book(session, book_id, member_id):
    # Lock the book before inspecting loans: serializes borrowing of its copies.
    book = session.scalar(select(Book).where(Book.id == book_id).with_for_update())
    if not book or not session.get(Member, member_id):
        raise LibraryError('Choose an existing book and demo member.')
    if session.scalar(select(Loan.id).where(Loan.book_id == book_id,
        Loan.member_id == member_id, Loan.returned_at.is_(None))):
        raise LibraryError('This member already has an active loan for this book.')
    changed = session.execute(update(Book).where(Book.id == book_id,
        Book.available_copies > 0).values(available_copies=Book.available_copies - 1))
    if changed.rowcount != 1:
        raise LibraryError('No copy is currently available.')
    loan = Loan(book_id=book_id, member_id=member_id)
    session.add(loan)
    session.flush()
    return loan.id


def return_book(session, loan_id):
    loan = session.get(Loan, loan_id)
    if not loan:
        raise LibraryError('Loan not found.')
    session.scalar(select(Book).where(Book.id == loan.book_id).with_for_update())
    changed = session.execute(update(Loan).where(Loan.id == loan_id,
        Loan.returned_at.is_(None)).values(returned_at=utc_now()))
    if changed.rowcount != 1:
        raise LibraryError('This loan has already been returned.')
    changed = session.execute(update(Book).where(Book.id == loan.book_id,
        Book.available_copies < Book.total_copies).values(available_copies=Book.available_copies + 1))
    if changed.rowcount != 1:
        raise LibraryError('Copy counts are inconsistent; no changes were saved.')
