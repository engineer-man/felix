from sqlalchemy import update, delete
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.models.spam import Spam, Spammer


class SpamDAL():
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_spam(self, member: str, regex: str):
        """Add new spam rule to database"""
        new_spam = Spam(member=member, regex=regex)
        self.db_session.add(new_spam)
        await self.db_session.flush()


    async def check_duplicate(self, regex: str):
        """Check for duplicate spam rule, return Bool"""
        query = await self.db_session.execute(
            select(Spam).filter(Spam.regex == regex)
        )
        return len(query.scalars().all()) > 0


    async def delete_spam(self, id: str):
        """Remove spam item by its id"""
        query = delete(Spam).where(Spam.id == id)
        await self.db_session.execute(query)


    async def get_all_spam(self):
        """Return all spam in database"""
        query = await self.db_session.execute(
            select(Spam).order_by(Spam.id)
        )
        return query.scalars().all()


    async def spam_by_id(self, id: str):
        """Return spam rule by its ID"""
        query = await self.db_session.execute(
            select(Spam).where(Spam.id == id)
        )
        return query.scalars().first()


    async def update_spam_rule(self, id: str, member: str, regex: str):
        """Update existing spam rule by ID"""
        query = update(Spam).where(Spam.id == id)
        query = query.values(member=member, regex=regex)
        query.execution_options(synchronize_session='fetch')
        await self.db_session.execute(query)


##########
# Store record of previous rule breakers ?
class SpammerDAL():
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_spammer(self, member: str, regex: str):
        query = update(Spammer(member=member, regex=regex))
        self.db_session.execute(query)
