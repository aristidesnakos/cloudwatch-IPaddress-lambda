import pytest
import boto3
from moto import mock_dynamodb
from lambda_function.main import add_ip_to_denied_list

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'

@pytest.fixture
def dynamodb(aws_credentials):
    with mock_dynamodb():
        yield boto3.resource('dynamodb', region_name='us-east-1')

@pytest.fixture
def create_denied_ip_table(dynamodb):
    # Create DynamoDB tables for testing
    table = dynamodb.create_table(
        TableName="DeniedIpTable",
        KeySchema=[{'AttributeName': 'IPAddress', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'IPAddress', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    # Wait for the table to be created
    table.meta.client.get_waiter('table_exists').wait(TableName="DeniedIpTable")
    return table

def test_add_ip_to_denied_list(create_denied_ip_table):
    ip_address = "123.123.123.123"
    add_ip_to_denied_list(ip_address, create_denied_ip_table)

    # Verify if IP address is added to the denied list
    response = create_denied_ip_table.get_item(Key={'IPAddress': ip_address})
    assert 'Item' in response
    assert response['Item']['IPAddress'] == ip_address