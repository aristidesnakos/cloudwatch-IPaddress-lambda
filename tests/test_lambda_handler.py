import pytest
import json
from moto import mock_dynamodb
from lambda_function.main import lambda_handler
import boto3

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"

@pytest.fixture
def dynamodb(aws_credentials):
    with mock_dynamodb():
        yield boto3.resource('dynamodb', region_name="us-east-1")

def create_mock_tables(dynamodb):
    """Create mock DynamoDB tables."""
    ip_count_table = dynamodb.create_table(
        TableName="IpCountTable",
        KeySchema=[
            {'AttributeName': 'IPAddress', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'IPAddress', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    denied_ip_table = dynamodb.create_table(
        TableName="DeniedIpTable",
        KeySchema=[
            {'AttributeName': 'IPAddress', 'KeyType': 'HASH'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'IPAddress', 'AttributeType': 'S'}
        ],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    return ip_count_table, denied_ip_table

@pytest.fixture
def mock_env(monkeypatch, dynamodb):
    monkeypatch.setenv("AWS_DYNAMO_IP_COUNT_TABLE", "IpCountTable")
    monkeypatch.setenv("AWS_DYNAMO_DENIED_IP_TABLE", "DeniedIpTable")
    create_mock_tables(dynamodb)

def test_lambda_handler_success(mock_env):
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    dynamodb.create_table(
        TableName='YourTableNameHere',
        KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )
    
    event = {
        'Records': [
            {
                'Sns': {
                    'Message': json.dumps({
                        'httpRequest': {'clientIp': '123.123.123.123'},
                        'timestamp': '2023-01-01T00:00:00Z'
                    })
                }
            }
        ]
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 200
    assert json.loads(response['body']) == 'IP addresses processed'

def test_lambda_handler_failure(mock_env):
    event = {
        'Records': [
            {
                'Sns': {
                    'Message': 'Invalid JSON'
                }
            }
        ]
    }

    response = lambda_handler(event, None)

    assert response['statusCode'] == 500
    assert json.loads(response['body']) == 'Error processing logs'