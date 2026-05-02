import os
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Key
from botocore.config import Config
from dotenv import load_dotenv

load_dotenv(override=True)


class DynamoInit:
    def __init__(self):
        self.aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
        self.aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
        self.region_name = os.getenv("AWS_REGION_NAME")
        self.config = Config(
            max_pool_connections=int(os.getenv("MAX_POOL_CONNECTIONS", 50)),
            connect_timeout=int(os.getenv("CONNECTION_TIMEOUT", 5)),
            read_timeout=int(os.getenv("READ_TIMEOUT", 60)),
            retries={
                "max_attempts": int(os.getenv("MAX_ATTEMPT", 3)),
                "mode": "adaptive",
            },
        )
        self.dynamodb = boto3.resource(
            "dynamodb",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            region_name=self.region_name,
            config=self.config,
        )


class DynamoClient:
    def __init__(self):
        self.init = DynamoInit()
        self.dynamodb = self.init.dynamodb

    def _get_table(self, table_name: str):
        return self.dynamodb.Table(table_name)  # type: ignore

    @staticmethod
    def _sanitize(obj):
        if isinstance(obj, float):
            return Decimal(str(obj))
        if isinstance(obj, dict):
            return {k: DynamoClient._sanitize(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [DynamoClient._sanitize(v) for v in obj]
        return obj

    def put_item(
        self, table_name: str, item: dict, condition: str | None = None
    ) -> dict:
        table = self._get_table(table_name)
        params = {"Item": self._sanitize(item)}
        if condition:
            params["ConditionExpression"] = condition
        return table.put_item(**params)

    def get_item(
        self, table_name: str, key: dict, consistent: bool = False
    ) -> dict | None:
        table = self._get_table(table_name)
        resp = table.get_item(Key=key, ConsistentRead=consistent)
        return resp.get("Item")

    def query_by_key(
        self,
        table_name: str,
        pk_name: str,
        pk_value,
        sk_condition=None,
        index_name: str | None = None,
        scan_forward: bool = True,
        limit: int | None = None,
    ) -> list[dict]:
        table = self._get_table(table_name)
        key_expr = Key(pk_name).eq(pk_value)
        if sk_condition is not None:
            key_expr = key_expr & sk_condition

        params = {
            "KeyConditionExpression": key_expr,
            "ScanIndexForward": scan_forward,
        }
        if index_name:
            params["IndexName"] = index_name
        if limit:
            params["Limit"] = limit

        items = []
        while True:
            resp = table.query(**params)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        return items

    def update_one(
        self,
        table_name: str,
        key: dict,
        updates: dict,
        condition: str | None = None,
    ) -> dict:
        table = self._get_table(table_name)

        expr_parts, attr_names, attr_values = [], {}, {}
        for i, (field, value) in enumerate(updates.items()):
            placeholder_name = f"#f{i}"
            placeholder_val = f":v{i}"
            expr_parts.append(f"{placeholder_name} = {placeholder_val}")
            attr_names[placeholder_name] = field
            attr_values[placeholder_val] = self._sanitize(value)

        params = {
            "Key": key,
            "UpdateExpression": "SET " + ", ".join(expr_parts),
            "ExpressionAttributeNames": attr_names,
            "ExpressionAttributeValues": attr_values,
            "ReturnValues": "ALL_NEW",
        }
        if condition:
            params["ConditionExpression"] = condition

        resp = table.update_item(**params)
        return resp.get("Attributes")

    # ── DELETE ──

    def delete_one(
        self, table_name: str, key: dict, condition: str | None = None
    ) -> dict:
        table = self._get_table(table_name)
        params = {
            "Key": key,
            "ReturnValues": "ALL_OLD",
        }
        if condition:
            params["ConditionExpression"] = condition
        resp = table.delete_item(**params)
        return resp.get("Attributes")

    def query_by_filter(
        self,
        table_name: str,
        pk_name: str,
        pk_value,
        sk_condition=None,
        filter_expression=None,
        index_name: str | None = None,
        scan_forward: bool = True,
        limit: int | None = None,
    ) -> list[dict]:
        table = self._get_table(table_name)
        key_expr = Key(pk_name).eq(pk_value)
        if sk_condition is not None:
            key_expr = key_expr & sk_condition

        params = {
            "KeyConditionExpression": key_expr,
            "ScanIndexForward": scan_forward,
        }
        if index_name:
            params["IndexName"] = index_name
        if filter_expression is not None:
            params["FilterExpression"] = filter_expression
        if limit:
            params["Limit"] = limit

        items = []
        while True:
            resp = table.query(**params)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" not in resp:
                break
            params["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
        return items


if __name__ == "__main__":
    client = DynamoClient()
    tables = list(client.dynamodb.tables.all())  # type: ignore
    print("Tables:", tables)
    print("DynamoDB client initialized successfully.")
