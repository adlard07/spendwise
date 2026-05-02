import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv

from src.models.users import CreateUser

load_dotenv(override=True)


class DatabaseServices:
    def __init__(self):
        self._dynamodb = boto3.resource(
            "dynamodb",
            region_name=os.getenv("AWS_REGION", "ap-south-1"),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        )
        self.users = self._dynamodb.Table(os.getenv("USERS_TABLE_NAME", "users"))  # type: ignore
        self.sessions = self._dynamodb.Table(  # type: ignore
            os.getenv("SESSIONS_TABLE_NAME", "sessions")
        )
        self.api_keys = self._dynamodb.Table(  # type: ignore
            os.getenv("API_KEYS_TABLE_NAME", "api_keys")
        )

    def _get_database_all_tables(self) -> List[str]:
        return [table.name for table in self._dynamodb.tables.all()]  # type: ignore

    # =========================================================================
    # Users
    # =========================================================================

    def create_user(self, payload: CreateUser) -> Dict[str, Any]:
        item = {
            "user_id": payload.user_id,
            "first_name": payload.first_name,
            "last_name": payload.last_name,
            "username": payload.username,
            "email": str(payload.email),
            "password": payload.password,
            "role": payload.role,
            "currency": payload.currency,
            "disabled": payload.disabled,
            "created_at": payload.created_at.isoformat()
            if payload.created_at
            else None,
            "updated_at": payload.updated_at.isoformat()
            if payload.updated_at
            else None,
        }
        self.users.put_item(Item=item)
        return item

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        resp = self.users.get_item(Key={"user_id": user_id})
        return resp.get("Item")

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        resp = self.users.query(
            IndexName="email-index",
            KeyConditionExpression=Key("email").eq(email),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    def update_user(self, user_id: str, updates: Dict[str, Any]) -> None:
        updates["updated_at"] = datetime.now(timezone.utc).isoformat()
        expr_parts = [f"#{k} = :{k}" for k in updates]
        self.users.update_item(
            Key={"user_id": user_id},
            UpdateExpression="SET " + ", ".join(expr_parts),
            ExpressionAttributeNames={f"#{k}": k for k in updates},
            ExpressionAttributeValues={f":{k}": v for k, v in updates.items()},
        )

    # =========================================================================
    # Sessions (refresh tokens)
    # =========================================================================

    def create_session(self, session: Dict[str, Any]) -> None:
        self.sessions.put_item(Item=session)

    def get_session_by_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        resp = self.sessions.query(
            IndexName="token_hash-index",
            KeyConditionExpression=Key("token_hash").eq(token_hash),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        resp = self.sessions.get_item(Key={"session_id": session_id})
        return resp.get("Item")

    def revoke_session(self, session_id: str) -> None:
        self.sessions.update_item(
            Key={"session_id": session_id},
            UpdateExpression="SET revoked = :t, revoked_at = :ts",
            ExpressionAttributeValues={
                ":t": True,
                ":ts": datetime.now(timezone.utc).isoformat(),
            },
        )

    def revoke_all_user_sessions(self, user_id: str) -> None:
        resp = self.sessions.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id),
            FilterExpression="revoked = :f",
            ExpressionAttributeValues={":f": False},
        )
        for item in resp.get("Items", []):
            self.revoke_session(item["session_id"])

    def list_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        resp = self.sessions.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        return resp.get("Items", [])

    # =========================================================================
    # API Keys
    # =========================================================================

    def create_api_key(self, record: Dict[str, Any]) -> None:
        self.api_keys.put_item(Item=record)

    def get_api_key(self, key_id: str) -> Optional[Dict[str, Any]]:
        resp = self.api_keys.get_item(Key={"key_id": key_id})
        return resp.get("Item")

    def get_api_key_by_prefix(self, prefix: str) -> Optional[Dict[str, Any]]:
        resp = self.api_keys.query(
            IndexName="prefix-index",
            KeyConditionExpression=Key("prefix").eq(prefix),
            Limit=1,
        )
        items = resp.get("Items", [])
        return items[0] if items else None

    def update_api_key_last_used(self, key_id: str) -> None:
        self.api_keys.update_item(
            Key={"key_id": key_id},
            UpdateExpression="SET last_used_at = :ts",
            ExpressionAttributeValues={
                ":ts": datetime.now(timezone.utc).isoformat(),
            },
        )

    def revoke_api_key(self, key_id: str) -> None:
        self.api_keys.update_item(
            Key={"key_id": key_id},
            UpdateExpression="SET revoked = :t, revoked_at = :ts",
            ExpressionAttributeValues={
                ":t": True,
                ":ts": datetime.now(timezone.utc).isoformat(),
            },
        )

    def list_api_keys_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        resp = self.api_keys.query(
            IndexName="user_id-index",
            KeyConditionExpression=Key("user_id").eq(user_id),
        )
        return resp.get("Items", [])


if __name__ == "__main__":
    services = DatabaseServices()
    print(services._get_database_all_tables())
