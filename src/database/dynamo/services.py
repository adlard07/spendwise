import os
from decimal import Decimal
from typing import Any, Dict, List, Optional

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.config import Config
from dotenv import load_dotenv
from fastapi import HTTPException

from src.database.dynamo.initialize import DynamoClient
from src.models.users import CreateUser

load_dotenv(override=True)


class DatabaseServices:
    def __init__(self):
        self.users_table = os.getenv("USERS_TABLE_NAME", "users")
        self.dynamo_client = DynamoClient()

    def _table(self, table_name: str):
        """Get a DynamoDB Table resource."""
        try:
            return self.dynamo_client.dynamodb.Table(table_name)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Crud Operatiosn
    def put_item(self, item: Dict[str, Any], table_name: str) -> Dict[str, Any]:
        """Insert single item."""
        try:
            table = self._table(table_name)
            cleaned_item = self._convert_floats_to_decimal(item)
            table.put_item(Item=cleaned_item)
            return item
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def batch_write(self, items: List[Dict[str, Any]], table_name: str) -> None:
        """Batch insert up to 25 items."""
        try:
            table = self._table(table_name)
            with table.batch_writer() as batch:
                for item in items:
                    cleaned_item = self._convert_floats_to_decimal(item)
                    batch.put_item(Item=cleaned_item)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_item(
        self, key: Dict[str, Any], table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Get single item by key."""
        try:
            table = self._table(table_name)
            response = table.get_item(Key=key)
            return self._convert_decimal_to_float(response.get("Item"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def find_one(
        self, filter_dict: Dict[str, Any], table_name: str
    ) -> Optional[Dict[str, Any]]:
        """Find first item matching filter."""
        try:
            items = self.query_by_filter(filter_dict, table_name=table_name, limit=1)
            return items[0] if items else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def query_by_filter(
        self,
        filter_dict: Dict[str, Any],
        table_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query items with filter expression (scan-based)."""
        try:
            table = self._table(table_name)

            filter_expression = None
            for key, value in filter_dict.items():
                condition = Attr(key).eq(value)
                filter_expression = (
                    condition
                    if filter_expression is None
                    else filter_expression & condition
                )

            kwargs = {"FilterExpression": filter_expression}
            if limit:
                kwargs["Limit"] = limit

            response = table.scan(**kwargs)
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response and (not limit or len(items) < limit):
                response = table.scan(
                    FilterExpression=filter_expression,
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            items = items[:limit] if limit else items
            return [self._convert_decimal_to_float(item) for item in items]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def query_by_key(
        self,
        key_name: str,
        key_value: Any,
        table_name: str,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query items by partition/sort key."""
        try:
            table = self._table(table_name)

            kwargs = {"KeyConditionExpression": Key(key_name).eq(key_value)}
            if limit:
                kwargs["Limit"] = limit

            response = table.query(**kwargs)
            items = response.get("Items", [])

            while "LastEvaluatedKey" in response and (not limit or len(items) < limit):
                response = table.query(
                    KeyConditionExpression=Key(key_name).eq(key_value),
                    ExclusiveStartKey=response["LastEvaluatedKey"],
                )
                items.extend(response.get("Items", []))

            items = items[:limit] if limit else items
            return [self._convert_decimal_to_float(item) for item in items]
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def update_one(
        self, key: Dict[str, Any], update_data: Dict[str, Any], table_name: str
    ) -> Dict[str, Any]:
        """Update single item with $set style syntax."""
        try:
            table = self._table(table_name)
            set_data = update_data.get("$set", update_data)
            cleaned_data = self._convert_floats_to_decimal(set_data)

            update_expression = "SET " + ", ".join(
                [f"#{k} = :{k}" for k in cleaned_data.keys()]
            )
            expression_attribute_names = {f"#{k}": k for k in cleaned_data.keys()}
            expression_attribute_values = {f":{k}": v for k, v in cleaned_data.items()}

            response = table.update_item(
                Key=key,
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values,
                ReturnValues="ALL_NEW",
            )
            return self._convert_decimal_to_float(response.get("Attributes"))
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def delete_one(self, key: Dict[str, Any], table_name: str) -> None:
        """Delete single item."""
        try:
            table = self._table(table_name)
            table.delete_item(Key=key)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Authenticate users
    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Fetch a user by username (partition key)."""
        try:
            table = self._table(self.users_table)
            response = table.query(
                KeyConditionExpression=Key("username").eq(username),
                Limit=1,
            )
            items = response.get("Items", [])
            return self._convert_decimal_to_float(items[0]) if items else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def create_user(self, user_data: CreateUser) -> Dict[str, Any]:
        try:
            """Persist a new user record."""
            item = user_data.model_dump()
            return self.put_item(item=item, table_name=self.users_table)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Look up user by email using GSI."""
        try:
            results = self.dynamo_client.query_by_key(
                table_name="expense-tracker-users",
                pk_name="email",
                pk_value=email,
                index_name="email-index",
                limit=1,
            )
            return results[0] if results else None
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Helper functions

    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """Convert floats to Decimal for DynamoDB compatibility."""
        if isinstance(obj, float):
            return Decimal(str(obj))
        elif isinstance(obj, dict):
            return {k: self._convert_floats_to_decimal(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        return obj

    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """Convert Decimal back to float for application use."""
        if obj is None:
            return None
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, dict):
            return {k: self._convert_decimal_to_float(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        return obj


if __name__ == "__main__":
    dbs = DatabaseServices()
    # dbs.create_user(username="adelard",
    #                 email="adelarddcunha@gmail.com",
    #                 hashed_password="Adelard@123")
