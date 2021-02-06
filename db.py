from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Date, Float, Integer
from constants import db_file, debug, validator_indexes

Base = declarative_base()


class Price(Base):
    __tablename__ = 'price'

    date = Column(Date, primary_key=True)
    start = Column(Float)
    high = Column(Float)
    low = Column(Float)
    end = Column(Float)

    def __init__(self, date, price):
        self.date = date
        self.start = price
        self.high = price
        self.low = price

    def update_prices(self, eth_price):
        self.end = eth_price

        if eth_price > self.high:
            self.high = eth_price

        elif eth_price < self.low:
            self.low = eth_price


class ValidatorMixin:
    date = Column(Date, primary_key=True)
    start = Column(Integer)
    end = Column(Integer)


def load_validators(validator_indexes):
    v = {}

    for val_idx in validator_indexes:
        v[val_idx] = type(val_idx, (ValidatorMixin, Base), dict(__tablename__=f'val_{val_idx}'))

    return v


sqlite_str = f'sqlite:///{str(db_file)}'
engine = create_engine(sqlite_str, echo=True if debug else False)
validators = load_validators(validator_indexes=validator_indexes)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
