from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker

# We have a command in cogs/management.py that needs just the database
# filename, which dumps the db
DATABASE_FILENAME = 'felix.sqlite'

engine = create_async_engine('sqlite+aiosqlite:///' + DATABASE_FILENAME, future=True, echo=False)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()
