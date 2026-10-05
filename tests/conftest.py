# tests/conftest.py

import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from schema.db_schema import Base, Users


TEST_DATABASE_URL = "sqlite://"


engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={
        "check_same_thread": False
    },
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture
def db_session():

    # Create fresh test tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    try:
        yield db

    finally:
        db.close()

        # Destroy everything after the test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):

    user = Users(
        name='User',
        email="test@example.com",
        phone_number="+2348133881829"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user

@pytest.fixture
def test_userb(db_session):

    user = Users(
        name='User',
        email="test1@example.com",
        phone_number="+2349133881829"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user