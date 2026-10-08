from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from sqlalchemy import or_, select
from sqlalchemy.exc import SQLAlchemyError
from .ai import AIError, recommend_books, validate_recommendations
from .models import Book, Loan, Member
from .services import LibraryError, borrow_book, return_book

main = Blueprint('main', __name__)


def text_field(name, limit, required=True):
    value = request.form.get(name, '').strip()
    if (required and not value) or len(value) > limit:
        raise LibraryError(f'{name.replace("_", " ").capitalize()} is required and must be at most {limit} characters.')
    return value


@main.route('/', methods=['GET', 'POST'])
def home():
    error = None
    recommendations = None
    try:
        if request.method == 'POST':
            if request.form.get('synthetic') != 'yes':
                raise LibraryError('Use synthetic catalog and member data only for this demo.')
            action = request.form.get('action')
            with current_app.extensions['db_session'].begin() as db:
                if action == 'add_book':
                    copies = int(request.form.get('copies', '0'))
                    if not 1 <= copies <= 1000:
                        raise LibraryError('Copies must be between 1 and 1,000.')
                    db.add(Book(title=text_field('title', 200), author=text_field('author', 200),
                        category=text_field('category', 100), description=text_field('description', 2000),
                        total_copies=copies, available_copies=copies))
                elif action == 'add_member':
                    db.add(Member(name=text_field('name', 100)))
                elif action == 'borrow':
                    borrow_book(db, int(request.form.get('book_id', '0')), int(request.form.get('member_id', '0')))
                elif action == 'return':
                    return_book(db, int(request.form.get('loan_id', '0')))
                else:
                    raise LibraryError('Unknown action.')
            flash('Changes saved.')
            return redirect(url_for('main.home'))
    except (LibraryError, ValueError) as exc:
        error = str(exc) if isinstance(exc, LibraryError) else 'Choose valid numeric IDs and copy counts.'
    except SQLAlchemyError:
        error = 'Database operation failed. No transaction changes were saved. Check configuration and run init-db.'
    return dashboard(error=error, recommendations=recommendations)


def dashboard(error=None, recommendations=None, interest=''):
    try:
        with current_app.extensions['db_session']() as db:
            search = request.args.get('search', '').strip()[:200]
            query = select(Book).order_by(Book.title)
            if search:
                query = query.where(or_(Book.title.contains(search, autoescape=True),
                    Book.author.contains(search, autoescape=True), Book.category.contains(search, autoescape=True)))
            books = db.scalars(query).all()
            all_books = db.scalars(select(Book).order_by(Book.title)).all()
            members = db.scalars(select(Member).order_by(Member.name)).all()
            loans = db.execute(select(Loan, Book.title, Member.name).join(Book, Loan.book_id == Book.id)
                .join(Member, Loan.member_id == Member.id).where(Loan.returned_at.is_(None))
                .order_by(Loan.borrowed_at.desc())).all()
        return render_template('index.html', books=books, all_books=all_books, members=members,
            loans=loans, error=error, recommendations=recommendations, interest=interest, search=search), (400 if error else 200)
    except SQLAlchemyError:
        return render_template('unavailable.html'), 503


@main.post('/recommend')
def recommend():
    interest = request.form.get('interest', '').strip()
    try:
        if request.form.get('ai_consent') != 'yes':
            raise LibraryError('Confirm that your interest and catalog are synthetic before using Gemini.')
        if not interest or len(interest) > 1000:
            raise LibraryError('Enter a reading interest, up to 1,000 characters.')
        with current_app.extensions['db_session']() as db:
            books = db.scalars(select(Book).order_by(Book.id).limit(101)).all()
        if not books:
            raise LibraryError('Add books with descriptions before requesting recommendations.')
        if len(books) > 100:
            raise LibraryError('This prototype supports recommendations across up to 100 catalog books.')
        catalog = [dict(id=b.id, title=b.title, author=b.author, category=b.category, description=b.description) for b in books]
        recommender = current_app.config.get('RECOMMENDER', recommend_books)
        result = validate_recommendations(recommender(interest, catalog), catalog)
        lookup = {b.id: b for b in books}
        # Fetch current availability after the model response; never trust AI counts.
        with current_app.extensions['db_session']() as db:
            counts = {b.id: b.available_copies for b in db.scalars(select(Book)).all()}
        cards = [dict(book=lookup[r.book_id], reason=r.reason, evidence=r.catalog_evidence,
                      available=counts.get(r.book_id, 0)) for r in result.recommendations]
        return dashboard(recommendations={'cards': cards, 'message': result.message}, interest=interest)
    except (LibraryError, AIError) as exc:
        return dashboard(error=str(exc), interest=interest)
    except SQLAlchemyError:
        return dashboard(error='The catalog database is unavailable. No data was sent before catalog retrieval succeeded.')


@main.get('/health')
def health():
    return {'status': 'ok', 'product': 'smart_library_system'}
