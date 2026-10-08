import pytest
from sqlalchemy import select
from app import create_app
from app.ai import AIError, Recommendation, Recommendations, validate_recommendations
from app.models import Base, Book, Loan, Member
from app.services import LibraryError, borrow_book, return_book


@pytest.fixture
def app(tmp_path):
    app = create_app({'TESTING': True, 'SECRET_KEY': 'test-only',
                      'DATABASE_URL': 'sqlite:///' + str(tmp_path / 'test.db')})
    Base.metadata.create_all(app.extensions['db_engine'])
    with app.extensions['db_session'].begin() as db:
        db.add(Book(title='Demo SQL', author='Demo Author', category='SQL',
            description='Practise SQL joins and grouping.', total_copies=1, available_copies=1))
        db.add_all([Member(name='Synthetic Reader One'), Member(name='Synthetic Reader Two')])
    yield app
    app.extensions['db_engine'].dispose()


def post(client, path='/', **data):
    client.get('/')
    with client.session_transaction() as s:
        data['csrf_token'] = s['csrf_token']
    data.setdefault('synthetic', 'yes')
    return client.post(path, data=data, follow_redirects=True)


def test_borrow_return_invariants(app):
    factory = app.extensions['db_session']
    with factory.begin() as db:
        loan_id = borrow_book(db, 1, 1)
    with pytest.raises(LibraryError):
        with factory.begin() as db:
            borrow_book(db, 1, 2)
    with pytest.raises(LibraryError):
        with factory.begin() as db:
            borrow_book(db, 1, 1)
    with factory.begin() as db:
        return_book(db, loan_id)
    with pytest.raises(LibraryError):
        with factory.begin() as db:
            return_book(db, loan_id)
    with factory() as db:
        assert db.get(Book, 1).available_copies == 1
        assert db.get(Loan, loan_id).returned_at is not None


def test_bad_member_does_not_change_inventory(app):
    with pytest.raises(LibraryError):
        with app.extensions['db_session'].begin() as db:
            borrow_book(db, 1, 999)
    with app.extensions['db_session']() as db:
        assert db.get(Book, 1).available_copies == 1


def test_ui_workflows(app):
    client = app.test_client()
    assert client.get('/').status_code == 200
    assert post(client, action='add_book', title='Demo Python', author='Fictional',
        category='Python', description='Python functions', copies='2').status_code == 200
    assert post(client, action='add_member', name='Demo C').status_code == 200
    assert post(client, action='borrow', book_id='1', member_id='1').status_code == 200
    assert b'Demo SQL' in client.get('/?search=SQL').data
    assert post(client, action='return', loan_id='1').status_code == 200
    assert b'already been returned' in post(client, action='return', loan_id='1').data
    assert client.post('/', data={}).status_code == 400
    assert post(client, action='add_book', copies='0').status_code == 400


def test_recommendations_exclude_member_information(app):
    captured = {}
    def recommender(interest, catalog):
        captured['catalog'] = catalog
        return Recommendations(recommendations=[Recommendation(book_id=1, reason='Useful for your SQL interest.',
            catalog_evidence='SQL joins')], message='Based on the supplied catalog.')
    app.config['RECOMMENDER'] = recommender
    response = post(app.test_client(), '/recommend', interest='SQL', ai_consent='yes')
    assert response.status_code == 200
    assert b'SQL joins' in response.data
    assert all(set(book) == {'id', 'title', 'author', 'category', 'description'} for book in captured['catalog'])
    assert 'Synthetic Reader One' not in str(captured['catalog'])


@pytest.mark.parametrize('book_id,evidence', [(999, 'SQL joins'), (1, 'invented passage'), (1, '')])
def test_unknown_or_ungrounded_recommendations(book_id, evidence):
    result = Recommendations(recommendations=[Recommendation(book_id=book_id, reason='Example',
        catalog_evidence=evidence)], message='')
    with pytest.raises(AIError):
        validate_recommendations(result, [{'id':1, 'description':'SQL joins', 'category':'SQL'}])


def test_ai_failure_preserves_catalog(app):
    def fail(*args):
        raise AIError('Model unavailable')
    app.config['RECOMMENDER'] = fail
    response = post(app.test_client(), '/recommend', interest='SQL', ai_consent='yes')
    assert b'Model unavailable' in response.data
    with app.extensions['db_session']() as db:
        assert db.get(Book, 1).available_copies == 1
        assert db.scalar(select(Loan.id)) is None


def test_no_consent_no_model(app):
    def fail(*args):
        raise AssertionError('Must not call Gemini')
    app.config['RECOMMENDER'] = fail
    assert post(app.test_client(), '/recommend', interest='SQL').status_code == 400


def test_seed_protects_existing_data(app):
    result = app.test_cli_runner().invoke(args=['seed-demo'])
    assert result.exit_code != 0
    assert 'existing data was preserved' in result.output


def test_mysql_configuration_required():
    with pytest.raises(RuntimeError):
        create_app({'DATABASE_URL': 'sqlite:///:memory:'})
