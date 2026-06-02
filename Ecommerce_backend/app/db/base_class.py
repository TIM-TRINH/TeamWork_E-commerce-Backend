from sqlalchemy.orm import declarative_base

Base = declarative_base()


def get_declarative_base():
	return Base
