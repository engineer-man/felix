import re
from typing import Optional, List

from sqlalchemy import update, delete
from sqlalchemy.future import select
from sqlalchemy.orm import Session

from db.models.spam import Spam, Spammer


class SpamDAL():
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_spam(self, member: str,regex: str):
        new_spam = Spam(member=member, regex=regex)
        self.db_session.add(new_spam)
        await self.db_session.flush()

    async def delete_spam(self, id: str):
        query = delete(Spam).where(Spam.id == id)
        await self.db_session.execute(query)

    async def get_all_spam(self):
        query = await self.db_session.execute(
            select(Spam).order_by(Spam.id)
        )
        return query.scalars().all()

    async def spam_by_id(self, id: str):
        query = await self.db_session.execute(
            select(Spam).where(Spam.id == id)
        )
        return query.scalars().one()

    async def update_spam_rule(self, id: str, member: str, regex: str):
        query = update(Spam).where(Spam.id == id)
        query = query.values(member=member, regex=regex)
        query.execution_options(synchronize_session='fetch')
        await self.db_session.execute(query)


##########
# Store previous rule breakers ?
class SpammerDAL():
    def __init__(self, db_session: Session):
        self.db_session = db_session

    async def add_spammer(self, member: str, regex: str):
        query = update(Spammer(member=member, regex=regex))
        self.db_session.execute(query)
