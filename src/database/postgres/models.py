from pydantic import BaseModel
import datetime


# ============= Create =============

class CreateUser(BaseModel):
	firstname: str
	lastname: str
	email_id: str
	password: str
	refresh_token: str

class CreateAccount(BaseModel):
	user_id: str
	balance: float
	income: float = None
	debt: float = None
	tax_perc: float = None
	saving_perc: float = None
	invest_perc: float = None

class CreateTransaction(BaseModel):
	account_id: str
	amount: float
	name: str
	description: str
	categories: list[str]
	paymt_mode_id: str
	transaction_date: datetime.datetime
	receipt_url: str = None

class CreateExpence(BaseModel):
	account_id: str
	amount: float
	name: str
	description: str
	categories: list[str]
	paymt_mode_id: str
	transaction_date: datetime.datetime
	receipt_url: str = None

class CreateCategory(BaseModel):
	name: str
	description: str
	budge: float
	icon_url: str


# ============= Update =============
