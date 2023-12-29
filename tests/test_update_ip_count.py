import pytest
from moto import mock_dynamodb
import boto3
from lambda_function.main import update_ip_count

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

def create_ip_count_table(dynamodb):
    table = dynamodb.create_table(
        TableName="IpCountTable",
        KeySchema=[
            {
                'AttributeName': 'IPAddress',
                'KeyType': 'HASH'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'IPAddress',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 10,
            'WriteCapacityUnits': 10
        }
    )
    return table

@pytest.fixture
def ip_count_table(dynamodb):
    return create_ip_count_table(dynamodb)

def test_update_ip_count(ip_count_table):
    ip_address = '192.168.1.1'
    timestamp = '2023-12-29T12:00:00'

    # Call the function under test
    update_ip_count(ip_address, timestamp, ip_count_table)

    # Fetch the updated item
    response = ip_count_table.get_item(Key={'IPAddress': ip_address})
    item = response['Item']

    # Assert that the IP count was updated correctly
    assert item['IPAddress'] == ip_address
    assert item['Timestamp'] == timestamp
    assert item['HitCount'] == 1  # assuming a new entry starts with a count of 1
