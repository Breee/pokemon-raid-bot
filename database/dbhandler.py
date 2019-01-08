"""
MIT License
Copyright (c) 2018 Breee@github
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import sqlalchemy
from sqlalchemy import or_
from globals.globals import LOGGER
from sqlalchemy.orm import sessionmaker
from poll.Poll import Poll
from poll.MultiPoll import MultiPoll
from poll.SinglePoll import SinglePoll
import database.dbmodels as models
import datetime
from typing import List


def transaction_wrapper(func):
    def _wrap_func(*args, **kwargs):
        self = args[0]
        Session = sessionmaker(bind=self.engine, expire_on_commit = False)

        # new session.   no connections are in use.
        self.session = Session()
        try:
            # execute transaction statements.
            res = func(*args, **kwargs)
            # commit.  The pending changes above
            # are flushed via flush(), the Transaction
            # is committed, the Connection object closed
            # and discarded, the underlying DBAPI connection
            # returned to the connection pool.
            self.session.commit()
        except Exception as err:
            LOGGER.critical(err)
            # on rollback, the same closure of state
            # as that of commit proceeds.
            self.session.rollback()
            raise
        finally:
            # close the Session.  This will expunge any remaining
            # objects as well as reset any existing SessionTransaction
            # state.  Neither of these steps are usually essential.
            # However, if the commit() or rollback() itself experienced
            # an unanticipated internal failure (such as due to a mis-behaved
            # user-defined event handler), .close() will ensure that
            # invalid state is removed.
            self.session.close()
        return res

    return _wrap_func

class DbHandler(object):

    def __init__(self, host, database, port, user, password, dialect, driver):
        self.host = host
        self.database = database
        self.port = port
        self.user = user
        self.password = password
        self.dialect = dialect
        self.driver = driver
        self.conn = None
        self.cursor = None
        self.engine = sqlalchemy.create_engine('%s+%s://%s:%s@%s:%s/%s' % (dialect, driver, user, password, host,port,database), pool_pre_ping=True)
        self.session = None
        self.metadata = sqlalchemy.MetaData()
        self.base = models.Base
        self.base.metadata.create_all(self.engine)

    @transaction_wrapper
    def add_poll(self, poll : Poll, trigger_message, poll_message) -> None:
        new_poll = None
        if isinstance(poll, MultiPoll):
            new_poll = models.Poll(name=poll.poll_title,
                                   external_id=poll.poll_id,
                                   creation_time=datetime.datetime.now(),
                                   last_update=datetime.datetime.now(),
                                   vote_options=poll.vote_options,
                                   reaction_to_user=poll.reaction_to_user,
                                   user_to_amount=poll.user_to_amount,
                                   enabled=True,
                                   poll_message=poll_message.id,
                                   trigger_message=trigger_message.id,
                                   server=trigger_message.guild.id,
                                   channel=trigger_message.channel.id,
                                   is_multipoll=True)
        elif isinstance(poll, SinglePoll):
            new_poll = models.Poll(name=poll.poll_title,
                                   external_id=poll.poll_id,
                                   creation_time=datetime.datetime.now(),
                                   last_update=datetime.datetime.now(),
                                   enabled=True,
                                   poll_message=poll_message.id,
                                   trigger_message=trigger_message.id,
                                   server=trigger_message.guild.id,
                                   channel=trigger_message.channel.id,
                                   is_multipoll=False)

        if new_poll:
            self.session.add(new_poll)

    @transaction_wrapper
    def get_poll(self, external_id:str) -> models.Poll:
        try:
            poll = self.session.query(models.Poll).filter(models.Poll.external_id == external_id).one()
        except sqlalchemy.orm.exc.NoResultFound:
            LOGGER.warning("Poll with ID %d does not exist" % external_id)
            return None
        return poll

    @transaction_wrapper
    def get_poll_with_message_id(self, message_id:int) -> models.Poll:
        try:
            poll = self.session.query(models.Poll).filter(or_(models.Poll.poll_message == str(message_id), models.Poll.trigger_message == str(message_id))).one()
            return poll
        except sqlalchemy.orm.exc.NoResultFound:
            LOGGER.warning("Poll with poll_message or trigger_message ID %d does not exist" % message_id)
        return None

    @transaction_wrapper
    def get_polls(self, age=None) -> List[models.Poll]:
        if age:
            since = datetime.datetime.now() - datetime.timedelta(days=age)
            polls = self.session.query(models.Poll).filter(models.Poll.creation_time >= since)
        else:
            polls = self.session.query(models.Poll).filter()
        return polls

    @transaction_wrapper
    def update_poll(self, poll: Poll) -> None:
        old_poll = self.get_poll(poll.poll_id)
        if old_poll:
            if isinstance(poll, MultiPoll):
                old_poll.user_to_amount = poll.user_to_amount
                old_poll.reaction_to_user = poll.reaction_to_user
            old_poll.last_update = datetime.datetime.now()

    @transaction_wrapper
    def disable_poll(self, poll:Poll) -> models.Poll:
        old_poll = self.get_poll(poll.poll_id)
        if old_poll:
            old_poll.last_update = datetime.datetime.now()
            old_poll.enabled = False
            return old_poll

    @transaction_wrapper
    def disable_poll_via_id(self, message_id) -> models.Poll:
        poll = self.get_poll_with_message_id(message_id=message_id)
        if poll:
            poll.last_update = datetime.datetime.now()
            poll.enabled = False
            return poll



if __name__ == '__main__':
    db = DbHandler(host="localhost", user="polldb", password="testitest123", port="3307", database="poll-db", dialect="mysql", driver="mysqlconnector")






