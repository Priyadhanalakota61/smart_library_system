import click
from sqlalchemy import select
from .models import Base, Book, Member


def register_commands(app):
    @app.cli.command('init-db')
    def init_db():
        """Create missing tables in the configured database. Never drops tables."""
        Base.metadata.create_all(app.extensions['db_engine'])
        click.echo('Tables are ready.')

    @app.cli.command('seed-demo')
    def seed_demo():
        """Add a clearly fictional catalog and demo members to an empty database."""
        with app.extensions['db_session'].begin() as db:
            if db.scalar(select(Book.id).limit(1)) or db.scalar(select(Member.id).limit(1)):
                raise click.ClickException('Seed only an empty demo database; existing data was preserved.')
            samples = [
                ('SQL Trail Guide', 'Demo Author A', 'Databases', 'A fictional workbook covering SQL joins, grouping and relational database design.'),
                ('Python Workshop', 'Demo Author B', 'Programming', 'A fictional practical guide to Python functions, lists and small web applications.'),
                ('Garden Stories', 'Demo Author C', 'Fiction', 'A fictional collection of gentle stories about gardening and friendship.'),
                ('Web Interface Studio', 'Demo Author D', 'Frontend', 'A fictional guide to HTML, CSS, JavaScript and accessible web interfaces.')]
            for title, author, category, description in samples:
                db.add(Book(title=title, author=author, category=category, description=description,
                            total_copies=2, available_copies=2))
            db.add_all([Member(name='Demo Reader A'), Member(name='Demo Reader B')])
        click.echo('Fictional demo catalog and members added.')
