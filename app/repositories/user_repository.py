from sqlmodel import Session, select
from app.db.models import User

class UserRepo:
    def __init__(self, session: Session):
        self.session = session

    def get_all_users(self):
        statement = select(User)
        return self.session.exec(statement).all()

    def get_user_by_id(self, user_id: int):
        return self.session.get(User, user_id)

    def create_user(self, user: User):
        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)
        return user
