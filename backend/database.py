from sqlalchemy import create_engine, Column, String, Integer, Date, Boolean
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import date
import uuid

Base = declarative_base()

class UserRecord(Base):
    __tablename__ = 'user_records'
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_name = Column(String)
    years_of_experience = Column(Integer)
    current_designation = Column(String)
    address = Column(String)
    email = Column(String)
    date = Column(Date, default=date.today)
    deleted = Column(Boolean, default=False)

# SQLite database setup
engine = create_engine('sqlite:///user_registration.db')
Base.metadata.create_all(engine)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()

def create_record(data):
    session = get_session()
    try:
        # Convert years_of_experience to integer
        if 'years_of_experience' in data:
            data['years_of_experience'] = int(data['years_of_experience']) if data['years_of_experience'] else 0
        
        record = UserRecord(**data)
        session.add(record)
        session.commit()
        return record.id
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

def get_all_records():
    session = get_session()
    try:
        return [{
            'id': r.id,
            'candidate_name': r.candidate_name,
            'years_of_experience': r.years_of_experience,
            'current_designation': r.current_designation,
            'address': r.address,
            'email': r.email,
            'date': r.date.isoformat(),
            'deleted': r.deleted
        } for r in session.query(UserRecord)
          .filter_by(deleted=False)
          .order_by(UserRecord.date.desc()).all()]
    finally:
        session.close()


def get_record_by_id(record_id):
    session = get_session()
    try:
        record = session.query(UserRecord).filter_by(id=record_id).first()
        if record:
            return {
                'id': record.id,
                'candidate_name': record.candidate_name,
                'years_of_experience': record.years_of_experience,
                'current_designation': record.current_designation,
                'address': record.address,
                'email': record.email,
                'date': record.date.isoformat()
            }
        return None
    finally:
        session.close()

def update_record(record_id, data):
    session = get_session()
    try:
        record = session.query(UserRecord).filter_by(id=record_id).first()
        if not record:
            return False
            
        for key, value in data.items():
            if key == 'years_of_experience':
                value = int(value) if value else 0
            setattr(record, key, value)
            
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()

