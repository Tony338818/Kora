from schema.db_schema import Users
from sqlalchemy.orm import Session
from schema.user_schema import UserCreate
from sqlalchemy.exc import IntegrityError


# Create User
async def createUser(db: Session, user: UserCreate):
    try:
        new_user = Users(
            **user.model_dump()
        )
        
        db.add(new_user)
        db.commit()
        return {
            'success': True,
            'message': f'User created successfully! {new_user.id}, {new_user.phone_number}'
        }
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
        
# Read user
def readUser(db: Session, phone_number: str):
    try:
        user =  db.query(Users).filter_by(phone_number=phone_number).all()
        if not user:
            return {
                'exists': False,
                'message': 'User not Found!'
            }   
        
        return {
            'exists': True,
            'message': f'Hi {user.name if user.name else 'User'}'
        }  
    except Exception as e:
        return {
            'success': False,
            'message': str(e)
        }