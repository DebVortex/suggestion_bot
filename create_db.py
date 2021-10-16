from database import db
from database.models import Suggestion

def create_tables():
    with db:
        db.create_tables([Suggestion])


if __name__ == '__main__':
    print("Creating Database...")
    create_tables()
    print("... done!")
