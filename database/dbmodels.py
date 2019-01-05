from sqlalchemy import Column, Integer, String, TypeDecorator, TIMESTAMP, Boolean, UnicodeText
from sqlalchemy.ext.declarative import declarative_base
import json

Base = declarative_base()

class Json(TypeDecorator):

    impl = UnicodeText

    def process_bind_param(self, value, dialect):
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        return json.loads(value)

class Poll(Base):
    __tablename__ = 'poll'
    id = Column(Integer, primary_key=True)
    external_id = Column(String(255), unique=True)
    name = Column(UnicodeText(255))
    creation_time = Column(TIMESTAMP)
    last_update = Column(TIMESTAMP)
    # list
    vote_options = Column(Json)
    # dict
    reaction_to_user = Column(Json)
    # dict
    user_to_amount = Column(Json)
    enabled = Column(Boolean, default=True)
    poll_message = Column(String(20), unique=True)
    trigger_message = Column(String(20), unique=True)
    server = Column(String(20))
    channel = Column(String(20))
    is_multipoll = Column(Boolean)


