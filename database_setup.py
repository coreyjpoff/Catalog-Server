from psycopg2 import connect
from config import config

def create_tables():
    """create tables in database"""
    commands = (
    """
    CREATE TABLE Users (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE Category (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL
    )
    """,
    """
    CREATE TABLE CategoryItem (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255), NOT NULL,
        category_id INTEGER
        # XCJP here --figure out if i need cascade on forein keys
    )
    """
    )
    
def createCategory():
    columnNamesAndTypes = 'id serial PRIMARY KEY, name varchar'
    createTable('Category', columnNamesAndTypes)
    
def createCategoryItem():
    columnNamesAndTypes = 'id serial PRIMARY KEY, name varchar, description varchar, category_id
    
# class CategoryItem(Base):
#     __tablename__ = 'category_item'
#
#     id = Column(Integer, primary_key=True)
#     name = Column(String(255), nullable=False)
#     description = Column(String(1000))
#     category_id = Column(Integer, ForeignKey('category.id'))
#     category = relationship(Category)
#     user_id = Column(Integer, ForeignKey('user.id'))
#     user = relationship(User)
#
#     @property
#     def serialize(self):
#         """Return object data in easily serializeable format"""
#         return {
#             'id': self.id,
#             'name': self.name,
#             'description': self.description,
#             'category_id': self.category_id,
#         }


# engine = create_engine('sqlite:///catalog.db')
#
#
# Base.metadata.create_all(engine)
