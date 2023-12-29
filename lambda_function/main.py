import logging
import os
import json
import boto3
from collections import defaultdict
from datetime import datetime
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

# Load environment variables
load_dotenv()
IP_COUNT_TABLE = os.getenv("AWS_DYNAMO_IP_COUNT_TABLE")
DENIED_IP_TABLE = os.getenv("AWS_DYNAMO_DENIED_IP_TABLE")

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')

# Function to process CloudWatch log data
def lambda_handler(event, context):
    ip_count_table = dynamodb.Table(IP_COUNT_TABLE)  # Rolling list of IPs
    denied_ip_table = dynamodb.Table(DENIED_IP_TABLE)  # Permanent list of denied IPs

    ip_count = defaultdict(int)

    try:
        for record in event['Records']:
            log_data = json.loads(record['Sns']['Message'])
            ip_address = log_data['httpRequest']['clientIp']
            timestamp = log_data['timestamp']
            # Increment IP address counter and store timestamp
            update_ip_count(ip_address, timestamp, ip_count_table)
        # Check IP address counts and add to Denied IP list if they exceed the limit
        check_and_add_to_denied_list(ip_count_table, denied_ip_table)

    except Exception as e:
        logger.error(f"Error processing event record: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps('Error processing logs')
        }

    return {
        'statusCode': 200,
        'body': json.dumps('IP addresses processed')
    }

def update_ip_count(ip_address, timestamp, table):
    try:
        # Update or create the IP address record with new timestamp
        response = table.update_item(
            Key={'IPAddress': ip_address},
            UpdateExpression="SET Timestamp = :t ADD HitCount :incr",
            ExpressionAttributeValues={':t': timestamp, ':incr': 1},
            ReturnValues="UPDATED_NEW"
        )
        logger.info(f"IP count updated in DynamoDB: {response}")
    except Exception as e:
        logger.error(f"Error updating IP count in DynamoDB: {e}")

def check_and_add_to_denied_list(ip_count_table, denied_ip_table):
    try:
        # Scan the IP count table for IPs exceeding the limit
        response = ip_count_table.scan(
            FilterExpression="HitCount > :limit",
            ExpressionAttributeValues={':limit': 10}
        )
        for item in response.get('Items', []):
            add_ip_to_denied_list(item['IPAddress'], denied_ip_table)
            # Optionally, remove the IP from the count table
            # ip_count_table.delete_item(Key={'IPAddress': item['IPAddress']})
    except Exception as e:
        logger.error(f"Error scanning IP count table: {e}")

def add_ip_to_denied_list(ip_address, table):
    try:
        current_time = datetime.now().isoformat()
        response = table.put_item(Item={'IPAddress': ip_address, 'Timestamp': current_time})
        logger.info(f"Added {ip_address} to denied list in DynamoDB: {response}")
    except Exception as e:
        logger.error(f"Error adding {ip_address} to denied list in DynamoDB: {e}")