import pytest
from moto import mock_dynamodb
import boto3
from main import check_and_add_to_denied_list

# Constants for the test
IP_COUNT_TABLE = "IpCountTable"
DENIED_IP_TABLE = "DeniedIpTable"
HIT_COUNT_LIMIT = 10

def create_mock_tables():
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

    # Create IP Count Table
    dynamodb.create_table(
        TableName=IP_COUNT_TABLE,
        KeySchema=[{'AttributeName': 'IPAddress', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'IPAddress', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

    # Create Denied IP Table
    dynamodb.create_table(
        TableName=DENIED_IP_TABLE,
        KeySchema=[{'AttributeName': 'IPAddress', 'KeyType': 'HASH'}],
        AttributeDefinitions=[{'AttributeName': 'IPAddress', 'AttributeType': 'S'}],
        ProvisionedThroughput={'ReadCapacityUnits': 1, 'WriteCapacityUnits': 1}
    )

@mock_dynamodb
def test_check_and_add_to_denied_list():
    # Setup mock DynamoDB
    create_mock_tables()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    ip_count_table = dynamodb.Table(IP_COUNT_TABLE)
    denied_ip_table = dynamodb.Table(DENIED_IP_TABLE)

    # Populate the IP Count Table with test data
    ip_count_table.put_item(Item={'IPAddress': '192.168.1.1', 'HitCount': HIT_COUNT_LIMIT + 1})

    # Call the function under test
    check_and_add_to_denied_list(ip_count_table, denied_ip_table)

    # Validate that IP is added to the denied list
    response = denied_ip_table.get_item(Key={'IPAddress': '192.168.1.1'})
    assert 'Item' in response
    assert response['Item']['IPAddress'] == '192.168.1.1'

@mock_dynamodb
def test_check_and_add_to_denied_list_no_exceed():
    # Setup mock DynamoDB
    create_mock_tables()
    dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
    ip_count_table = dynamodb.Table(IP_COUNT_TABLE)
    denied_ip_table = dynamodb.Table(DENIED_IP_TABLE)

    # Populate the IP Count Table with test data below the limit
    ip_count_table.put_item(Item={'IPAddress': '192.168.1.2', 'HitCount': HIT_COUNT_LIMIT - 1})

    # Call the function under test
    check_and_add_to_denied_list(ip_count_table, denied_ip_table)

    # Validate that IP is not added to the denied list
    response = denied_ip_table.get_item(Key={'IPAddress': '192.168.1.2'})
    assert 'Item' not in response
