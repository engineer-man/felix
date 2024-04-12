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
        query = await self.db_session.execute(
            select(Spam).order_by(Spam.id)
        )
        return query.scalars().all()

    async def check_duplicate(self, regex: str):
        """Check for duplicate spam rule, return ID of existing entry if found"""
        query = await self.db_session.execute(
            select(Spam.id).filter(Spam.regex == regex)
        )
        
        duplicate_entry = query.scalar()
        return duplicate_entry

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


class SpammerDAL():
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_spammer(self, member: str, regex: str):
        """Add member and spam rule broken to history"""
        add_spammer = Spammer(member=member, regex=regex)
        self.db_session.add(add_spammer)
        await self.db_session.flush()

    async def get_all_spammers(self):
        """Return all spammers in database"""
        query = await self.db_session.execute(
            select(Spammer).order_by(Spammer.id.desc()).limit(10)
        )
        return query.scalars().all()

    async def get_spammer_count(self):
        """Return count of rule breakers"""
        query = await self.db_session.execute(
            'SELECT count(id) from Spammer'
        )
        return query.scalar()

    async def spammer_by_id(self, id: str):
        """Return spammer by its ID"""
        query = await self.db_session.execute(
            select(Spammer).where(Spammer.id == id)
        )
        return query.scalars().first()

    async def delete_spammer(self, id: str):
        """Remove spammer item by its id"""
        query = delete(Spammer).where(Spammer.id == id)
        await self.db_session.execute(query)
