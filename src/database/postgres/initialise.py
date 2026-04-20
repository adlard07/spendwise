import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Sequence, Literal, Optional
from dotenv import load_dotenv

from utils.logger import logging

load_dotenv()

FetchMode = Literal["all", "one", "none"]
ConnMode = Literal["keep", "close"]
DatabaseType = Literal["postgres", "sqlite3"]


@dataclass
class Postgres:
    db_host: str = os.getenv("DATABASE_HOST") or "localhost"
    db_port: int = int(os.getenv("DATABASE_PORT") or "5432")
    db_name: str = os.getenv("DATABASE_NAME") or ""
    db_user: str = os.getenv("DATABASE_USER") or ""
    db_password: str = os.getenv("DATABASE_PASSWORD") or ""

    def __post_init__(self) -> None:
        if not all([self.db_name, self.db_user, self.db_password]):
            raise ValueError("Missing one of DATABASE_NAME / DATABASE_USER / DATABASE_PASSWORD in .env")

    def connect(self):
        import psycopg2  # lazy import so sqlite-only setups don't fail
        return psycopg2.connect(
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
            port=self.db_port,
            host=self.db_host,
        )

@dataclass
class SQLite:
    path: str

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn


class DatabaseInit:
    def __init__(self, db_type: DatabaseType = "postgres"):
        self.db_type: DatabaseType = db_type

        if db_type == "sqlite3":
            sqlite_path = os.getenv("SQLITE_DATABASE_PATH")
            if not sqlite_path:
                raise ValueError("Missing SQLITE_DATABASE_PATH in .env")
            os.makedirs(os.path.dirname(sqlite_path) or ".", exist_ok=True)
            self.db_connection = SQLite(sqlite_path).connect()

        elif db_type == "postgres":
            self.db_connection = Postgres().connect()

        else:
            raise ValueError(f"Unsupported db_type: {db_type}")

    def execute_query(self, query: str, params: Sequence[Any] = (), fetch_mode: FetchMode = "all", conn_mode: ConnMode = "close") -> Optional[Any]:
        timestamp = datetime.now()
        curr = None
        try:
            curr = self.db_connection.cursor()
            curr.execute(query, params)

            if fetch_mode == "one":
                result = curr.fetchone()
            elif fetch_mode == "all":
                result = curr.fetchall()
            else:
                result = None

            self.db_connection.commit()
            return result
        except Exception:
            try:
                self.db_connection.rollback()
            except Exception:
                pass
            raise
        finally:
            if curr is not None:
                try:
                    curr.close()
                except Exception:
                    pass

            delta = datetime.now() - timestamp
            logging.info(f"Query executed in {delta.total_seconds()} seconds")

            if conn_mode == "close":
                self.close()

    def close(self) -> None:
        try:
            self.db_connection.close()
        except Exception:
            pass


class SchemeInit:
    def __init__(self, db_type: DatabaseType = "postgres"):
        self.dbs = DatabaseInit(db_type)

    def execute_query(self, query: str, params: Sequence[Any] = (), fetch_mode: FetchMode = "all", conn_mode: ConnMode = "close") -> Optional[Any]:
        return self.dbs.execute_query(
            query=query,
            params=params,
            fetch_mode=fetch_mode,
            conn_mode=conn_mode,
        )

    def _get_table_schema(self, table_name: str, schema_name: str = "public", conn_mode: ConnMode = "keep"):
        try:
            schema = self.execute_query(
                query="""
                    SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = %s
                    ORDER BY
                        ordinal_position;
                """,
                params=(table_name, schema_name),
                fetch_mode="one",
                conn_mode=conn_mode,
            )
            columns = self.execute_query(
                query="""
                SELECT column_name, data_type, character_maximum_length
                FROM information_schema.columns
                WHERE table_name = %s
                  AND table_schema = %s
                ORDER BY ordinal_position;
                """,
                params=(table_name, schema_name),
                fetch_mode='all',
                conn_mode=conn_mode
                )

            return {
                "schema": schema,
                "columns": columns,
            }
        except Exception as e:
            logging.error(f"Could not fetch table schema.")
            raise

    # ================ Database architecture ===============

    def create_users(self, conn_mode: ConnMode = "close"):
        try:
            query = """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;

                CREATE TABLE IF NOT EXISTS users (
                  user_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                  firstname       VARCHAR(20) NOT NULL,
                  lastname        VARCHAR(20) NOT NULL,
                  email_id        TEXT NOT NULL UNIQUE,
                  password        TEXT NOT NULL,
                  refresh_token   TEXT NOT NULL,
                  api_key         TEXT[],
                  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
                  updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
                );
            """
            self.execute_query(query=query, fetch_mode="none", conn_mode="keep")
            schema = self._get_table_schema("users", conn_mode=conn_mode)
            return {"success": True, "schema": schema}
        except Exception as e:
            logging.error(f"Failed to create users table.\n{e}")
            return {"success": False, "error": str(e)}

    def create_transaction(self, conn_mode: ConnMode = "close"):
        try:
            query = """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;

                CREATE TABLE IF NOT EXISTS transactions (
                    transc_id       UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
                    account_id      UUID NOT NULL,
                    amount          FLOAT NOT NULL,
                    name            VARCHAR(100) NOT NULL,
                    description     TEXT,
                    categories      TEXT[] NOT NULL,
                    paymt_mode_id   UUID,
                    transc_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    receipt_url     VARCHAR(100),
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT transc_fk
                        FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                );
            """
            self.execute_query(query=query, fetch_mode="none", conn_mode="keep")
            schema = self._get_table_schema("transactions", conn_mode=conn_mode)
            return {"success": True, "schema": schema}
        except Exception as e:
            logging.error(f"Failed to create transactions table.\n{e}")
            return {"success": False, "error": str(e)}

    def create_expenses(self, conn_mode: ConnMode = "close"):
        try:
            query = """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;

                CREATE TABLE IF NOT EXISTS expenses (
                    expense_id      UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
                    account_id      UUID NOT NULL,
                    amount          FLOAT NOT NULL,
                    name            VARCHAR(100) NOT NULL,
                    description     TEXT,
                    categories      TEXT[] NOT NULL,
                    paymt_mode_id   UUID,
                    transc_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    paymt_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    receipt_url     VARCHAR(100),
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                    CONSTRAINT expense_fk
                        FOREIGN KEY (account_id) REFERENCES accounts(account_id) ON DELETE CASCADE
                );
            """
            self.execute_query(query=query, fetch_mode="none", conn_mode="keep")
            schema = self._get_table_schema("expenses", conn_mode=conn_mode)
            return {"success": True, "schema": schema}
        except Exception as e:
            logging.error(f"Failed to create expenses table.\n{e}")
            return {"success": False, "error": str(e)}

    def create_accounts(self, conn_mode: ConnMode = "close"):
        try:
            query = """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;

                CREATE TABLE IF NOT EXISTS accounts (
                    account_id    UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
                    user_id       UUID NOT NULL,
                    balance       FLOAT NOT NULL,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    income        FLOAT DEFAULT 0.0,
                    debt          FLOAT DEFAULT 0.0,
                    tax_perc      FLOAT DEFAULT 0.0,
                    saving_perc   FLOAT DEFAULT 0.0,
                    invest_perc   FLOAT DEFAULT 0.0,

                    CONSTRAINT accounts_fk
                        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
            """
            self.execute_query(query=query, fetch_mode="none", conn_mode="keep")
            schema = self._get_table_schema("accounts", conn_mode=conn_mode)
            return {"success": True, "schema": schema}
        except Exception as e:
            logging.error(f"Failed to create accounts table.\n{e}")
            return {"success": False, "error": str(e)}

    def create_categories(self, conn_mode: ConnMode = "close"):
        try:
            query = """
                CREATE EXTENSION IF NOT EXISTS pgcrypto;

                CREATE TABLE IF NOT EXISTS categories (
                    category_id   UUID PRIMARY KEY DEFAULT GEN_RANDOM_UUID(),
                    name          VARCHAR(40) NOT NULL,
                    description   TEXT,
                    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    budget        FLOAT,
                    icon          VARCHAR(100)
                );
            """
            self.execute_query(query=query, fetch_mode="none", conn_mode="keep")
            schema = self._get_table_schema("categories", conn_mode=conn_mode)
            return {"success": True, "schema": schema}
        except Exception as e:
            logging.error(f"Failed to create categories table.\n{e}")
            return {"success": False, "error": str(e)}


def initialise_database_schema():
    try:
        dbs_init = SchemeInit("postgres")

        tables = [
            dbs_init.create_users,
            dbs_init.create_transaction,
            dbs_init.create_expenses,
            dbs_init.create_accounts,
            dbs_init.create_categories,
        ]

        for table in tables:
            result = table(conn_mode="keep")

            fn_name = getattr(table, "__name__", str(table))
            if isinstance(result, dict) and result.get("success") is True:
                logging.info(f"{fn_name} schema:\n{result.get('schema')}")
            else:
                logging.error(f"{fn_name} failed:\n{result}")

    except Exception as e:
        logging.error(f"Something went wrong.\n{e}")


if __name__ == "__main__":
    initialise_database_schema()

    # query = "select * from users;"
    # dbs = DatabaseInit()
    # rows = dbs.execute_query(query=query)
    # print(rows)

