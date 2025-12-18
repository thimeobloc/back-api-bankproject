"""
User repository module.

This module defines the UserRepo class responsible for
handling database operations related to users.
"""

from sqlmodel import Session, select
from app.db.models import User


class UserRepo:
    """
    User repository.

    Encapsulates all database operations related to the User entity.
    """

    def __init__(self, session: Session):
        """
        Initialize the user repository.

        :param session: Active database session
        """
        self.session = session

    def get_all_users(self):
        """
        Retrieve all users from the database.

        :return: List of all User records
        """
        statement = select(User)
        return self.session.exec(statement).all()

    def get_user_by_id(self, user_id: int):
        """
        Retrieve a user by its identifier.

        :param user_id: User unique identifier
        :return: User instance or None if not found
        """
        return self.session.get(User, user_id)

    def create_user(self, user: User):
        """
        Create a new user in the database.

        :param user: User instance to persist
        :return: Persisted User with generated fields
        """
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
