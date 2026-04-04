from schema.db_schema import Users
from sqlalchemy.orm import Session
from schema.user_schema import UserCreate
from sqlalchemy.exc import IntegrityError


# Create User
def createUser(db: Session, user: UserCreate):
    try:
        new_user = Users(
            **user.model_dump()
        )
        
        db.add(new_user)
        db.commit()
    except IntegrityError as e:
        return {
            'success': False,
            'message': e._message
        }
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }