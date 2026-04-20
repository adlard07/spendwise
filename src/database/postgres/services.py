from typing import Any

from database.postgres.initialise import DatabaseInit
from utils.logger import logging
from database.postgres.models import (CreateUser,
							 CreateAccount,
							 CreateTransaction,
							 CreateExpence,
							 CreateCategory,)


class DatabaseServices:
	def __init__(self):
		self.dbs = DatabaseInit()

	# ========== Insert ========== 

	def insert_user(self, payload: CreateUser):
		try:
			pass
		except Exception as e:
			logging.error(f"Could not create user.\n{e}")


	def insert_accounts(self, payload: CreateAccount):
		try:
			pass
		except Exception as e:
			logging.error(f"Could not create account.\n{e}")


	def insert_transactions(self, payload: CreateTransaction):
		try:
			pass
		except Exception as e:
			logging.error(f"Could not create transaction.\n{e}")


	def insert_expenses(self, payload: CreateExpence):
		try:
			pass
		except Exception as e:
			logging.error(f"Could not create expense.\n{e}")


	def insert_categories(self, payload: CreateCategory):
		try:
			pass
		except Exception as e:
			logging.error(f"Could not create category.\n{e}")


	# ========== Get ========== 

	def get_all_users(self) -> list[dict[Any]]:
		try:
			query = """
				SELECT to_jsonb(u) AS row
				FROM users u;
			"""
			return self.dbs.execute_query(
				query=query, 
				fetch_mode='all'
				)

		except Exception as e:
			logging.error(f"Could not get users.\n{e}")

	
	def get_user_by_email(self, email_id: str) -> dict[Any]:
		try:
			query = """
				SELECT to_jsonb(u) AS row
				FROM users u
				WHERE email_id = %s;
			"""
			return self.dbs.execute_query(
				query=query, 
				params=(email_id), 
				fetch_mode='one'
				)

		except Exception as e:
			logging.error(f"Could not get user.\n{e}")


	# ========== Update ========== 



	# ========== Delete ========== 


if __name__=='__main__':
	dbs = DatabaseServices()
	print(dbs.get_all_users())