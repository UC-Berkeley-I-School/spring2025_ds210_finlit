"""
Database operations for AspAIra application.
"""
import boto3
import os
from botocore.exceptions import ClientError
from botocore.config import Config
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
from typing import Optional, Dict, List, Any
from .config import DATABASE_CONFIG
import uuid
import json
from decimal import Decimal
from fastapi import Request

# JWT Configuration
SECRET_KEY = "development_secret_key"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DynamoDB configuration
try:
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='local',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy',
        config=Config(
            connect_timeout=5,
            retries={'max_attempts': 1}
        )
    )
    # Test the connection
    dynamodb.meta.client.list_tables()
    print("Successfully connected to DynamoDB local")
except Exception as e:
    print(f"Warning: Could not connect to DynamoDB local: {str(e)}")
    print("Using in-memory storage for development")
    # Create a simple in-memory storage for development
    class InMemoryDB:
        def __init__(self):
            self.tables = {}
            self._create_tables()
        
        def _create_tables(self):
            self.tables['AspAIra_Users'] = {}
            self.tables['AspAIra_Conversations'] = {}
            self.tables['AspAIra_Chats'] = {}
        
        def Table(self, name):
            return InMemoryTable(self.tables[name])
            
        def create_table(self, TableName, KeySchema, AttributeDefinitions, ProvisionedThroughput, GlobalSecondaryIndexes=None):
            # For in-memory storage, we just need to ensure the table exists
            if TableName not in self.tables:
                self.tables[TableName] = {}
            return InMemoryTable(self.tables[TableName])
    
    class InMemoryTable:
        def __init__(self, data):
            self.data = data
        
        def put_item(self, Item):
            if 'username' in Item:
                self.data[Item['username']] = Item
        
        def get_item(self, Key):
            return {'Item': self.data.get(Key.get('username'))}
        
        def query(self, **kwargs):
            return {'Items': list(self.data.values())}
        
        def scan(self):
            return {'Items': list(self.data.values())}
        
        def update_item(self, **kwargs):
            return {'Attributes': kwargs.get('ExpressionAttributeValues', {})}
            
        def wait_until_exists(self):
            # For in-memory storage, table exists immediately
            pass
            
        @property
        def table_status(self):
            return 'ACTIVE'
    
    dynamodb = InMemoryDB()

# Table names
USERS_TABLE = 'AspAIra_Users'
CHATS_TABLE = 'AspAIra_Chats'
EVALUATIONS_TABLE = 'AspAIra_ConversationEvaluations'

def _create_tables_if_not_exists():
    try:
        # Create Users table
        try:
            dynamodb.Table(USERS_TABLE).table_status
            print(f"Table {USERS_TABLE} exists")
        except (ClientError, AttributeError):
            print(f"Creating table {USERS_TABLE}")
            try:
                table = dynamodb.create_table(
                    TableName=USERS_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'username',
                            'KeyType': 'HASH'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'username',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                table.wait_until_exists()
                print(f"Table {USERS_TABLE} created successfully")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    print(f"Table {USERS_TABLE} already exists")
                else:
                    raise

        # Create Chats table
        try:
            dynamodb.Table(CHATS_TABLE).table_status
            print(f"Table {CHATS_TABLE} exists")
        except (ClientError, AttributeError):
            print(f"Creating table {CHATS_TABLE}")
            try:
                table = dynamodb.create_table(
                    TableName=CHATS_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'username',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'message_id',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'username',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'message_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'conversation_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    },
                    GlobalSecondaryIndexes=[
                        {
                            'IndexName': 'ConversationIndex',
                            'KeySchema': [
                                {
                                    'AttributeName': 'conversation_id',
                                    'KeyType': 'HASH'
                                },
                                {
                                    'AttributeName': 'timestamp',
                                    'KeyType': 'RANGE'
                                }
                            ],
                            'Projection': {
                                'ProjectionType': 'ALL'
                            },
                            'ProvisionedThroughput': {
                                'ReadCapacityUnits': 5,
                                'WriteCapacityUnits': 5
                            }
                        }
                    ]
                )
                table.wait_until_exists()
                print(f"Table {CHATS_TABLE} created successfully")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    print(f"Table {CHATS_TABLE} already exists")
                else:
                    raise

        # Create Evaluations table
        try:
            dynamodb.Table(EVALUATIONS_TABLE).table_status
            print(f"Table {EVALUATIONS_TABLE} exists")
        except (ClientError, AttributeError):
            print(f"Creating table {EVALUATIONS_TABLE}")
            try:
                table = dynamodb.create_table(
                    TableName=EVALUATIONS_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'conversation_id',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'evaluation_timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'conversation_id',
                            'AttributeType': 'S'
                        },
                        {
                            'AttributeName': 'evaluation_timestamp',
                            'AttributeType': 'S'
                        }
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                table.wait_until_exists()
                print(f"Table {EVALUATIONS_TABLE} created successfully")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    print(f"Table {EVALUATIONS_TABLE} already exists")
                else:
                    raise

    except Exception as e:
        print(f"Error creating tables: {str(e)}")
        raise

# Create tables on module import
_create_tables_if_not_exists()

def get_table():
    return dynamodb.Table(USERS_TABLE)

class UserExistsError(Exception):
    pass

def create_user(username: str, password: str):
    print(f"Attempting to create user: {username}")
    hashed_password = pwd_context.hash(password)
    try:
        table = dynamodb.Table(USERS_TABLE)
        print(f"Got table reference: {USERS_TABLE}")
        
        # First check if user exists
        existing_user = table.get_item(Key={'username': username}).get('Item')
        if existing_user:
            print(f"User {username} already exists")
            raise UserExistsError(f"Username '{username}' already exists")
            
        # Create new user
        table.put_item(
            Item={
                'username': username,
                'password': hashed_password,
                'profile1': {},
                'profile2': {},
                'is_active': True,
                'profile1_complete': False,
                'profile2_complete': False,
                'created_at': datetime.utcnow().isoformat(),
                'last_login': datetime.utcnow().isoformat()
            }
        )
        print(f"Successfully created user: {username}")
        return True
    except UserExistsError:
        raise
    except ClientError as e:
        print(f"Error creating user: {str(e)}")
        raise
    except Exception as e:
        print(f"Unexpected error creating user: {str(e)}")
        raise

def get_user(username: str):
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'username': username})
        return response.get('Item')
    except ClientError:
        return None

def authenticate_user(username: str, password: str):
    """Authenticate user with username and password"""
    try:
        user = get_user(username)
        if not user:
            return None
        if not pwd_context.verify(password, user['password']):
            return None
        return user
    except Exception as e:
        print(f"Error authenticating user: {str(e)}")
        return None

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user_from_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        return get_user(username)
    except JWTError:
        return None

def update_profile_part1(username: str, profile_data: dict):
    try:
        print(f"Attempting to update profile1 for user {username}")
        print(f"Profile data to save: {profile_data}")
        table = dynamodb.Table(USERS_TABLE)
        
        # First check if user exists
        existing_user = table.get_item(Key={'username': username})
        print(f"Existing user data: {existing_user}")
        
        response = table.update_item(
            Key={
                'username': username
            },
            UpdateExpression='SET profile1 = :profile_data, profile1_complete = :complete',
            ExpressionAttributeValues={
                ':profile_data': profile_data,
                ':complete': True
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"DynamoDB response: {response}")
        return True
    except Exception as e:
        print(f"Error updating profile1 for user {username}")
        print(f"Error type: {type(e)}")
        print(f"Error message: {str(e)}")
        print(f"Error details: {e.__dict__}")
        return False

def update_profile_part2(username: str, profile_data: dict):
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.update_item(
            Key={
                'username': username
            },
            UpdateExpression='SET profile2 = :profile_data, profile2_complete = :complete',
            ExpressionAttributeValues={
                ':profile_data': profile_data,
                ':complete': True
            },
            ReturnValues="UPDATED_NEW"
        )
        print(f"Updated profile2 for user {username}: {response}")
        return True
    except Exception as e:
        print(f"Error updating profile2 for user {username}: {str(e)}")
        return False

def get_profile_status(username: str):
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(
            Key={
                'username': username
            },
            ProjectionExpression='profile1_complete, profile2_complete'
        )
        if 'Item' in response:
            return {
                'profile1_complete': response['Item'].get('profile1_complete', False),
                'profile2_complete': response['Item'].get('profile2_complete', False)
            }
        return {
            'profile1_complete': False,
            'profile2_complete': False
        }
    except Exception as e:
        print(f"Error getting profile status for user {username}: {str(e)}")
        return {
            'profile1_complete': False,
            'profile2_complete': False
        }

def scan_all_users():
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.scan()
        return response.get('Items', [])
    except Exception as e:
        print(f"Error scanning users: {str(e)}")
        return []

def save_chat_message(
    message_id: str,
    conversation_id: str,
    username: str,
    agent_id: str,
    timestamp: datetime,
    message: str,
    response: str,
    interaction_type: str,
    dify_metadata: dict,
    quiz_data: Optional[dict] = None,
    usage_metrics: Optional[dict] = None
) -> bool:
    """Save a chat message to DynamoDB"""
    try:
        print("\n=== Starting save_chat_message ===")
        print(f"Input parameters:")
        print(f"message_id: {message_id}")
        print(f"conversation_id: {conversation_id}")
        print(f"username: {username}")
        print(f"agent_id: {agent_id}")
        print(f"timestamp: {timestamp}")
        print(f"message length: {len(message)}")
        print(f"response length: {len(response)}")
        print(f"interaction_type: {interaction_type}")
        print(f"dify_metadata: {dify_metadata}")
        print(f"quiz_data: {quiz_data}")
        print(f"usage_metrics: {usage_metrics}")

        # Validate required fields
        if not message_id or not conversation_id or not username or not agent_id or not timestamp or not message or not response or not interaction_type:
            print("Missing required fields:")
            print(f"message_id: {bool(message_id)}")
            print(f"conversation_id: {bool(conversation_id)}")
            print(f"username: {bool(username)}")
            print(f"agent_id: {bool(agent_id)}")
            print(f"timestamp: {bool(timestamp)}")
            print(f"message: {bool(message)}")
            print(f"response: {bool(response)}")
            print(f"interaction_type: {bool(interaction_type)}")
            return False

        # Validate response content
        if not response or not response.strip():
            print("Empty response content")
            return False

        # Convert timestamp to ISO format string
        timestamp_str = timestamp.isoformat()
        
        # Convert numeric values in usage_metrics to Decimal
        if usage_metrics:
            converted_metrics = {}
            for key, value in usage_metrics.items():
                if isinstance(value, (int, float)):
                    converted_metrics[key] = Decimal(str(value))
                elif isinstance(value, dict):
                    converted_metrics[key] = {
                        k: Decimal(str(v)) if isinstance(v, (int, float)) else v
                        for k, v in value.items()
                    }
                else:
                    converted_metrics[key] = value
            usage_metrics = converted_metrics
        
        # Prepare the item for DynamoDB
        item = {
            'username': username,
            'message_id': message_id,
            'conversation_id': conversation_id,
            'agent_id': agent_id,
            'timestamp': timestamp_str,
            'message': message,
            'response': response,
            'interaction_type': interaction_type,
            'dify_metadata': dify_metadata or {}
        }
        
        # Add optional fields if present
        if quiz_data:
            item['quiz_data'] = quiz_data
        if usage_metrics:
            item['usage_metrics'] = usage_metrics
        
        print("\nPrepared DynamoDB item:")
        print(f"username: {item['username']}")
        print(f"message_id: {item['message_id']}")
        print(f"conversation_id: {item['conversation_id']}")
        print(f"agent_id: {item['agent_id']}")
        print(f"timestamp: {item['timestamp']}")
        print(f"message length: {len(item['message'])}")
        print(f"response length: {len(item['response'])}")
        print(f"interaction_type: {item['interaction_type']}")
        print(f"dify_metadata keys: {list(item['dify_metadata'].keys())}")
        if 'quiz_data' in item:
            print(f"quiz_data present: {bool(item['quiz_data'])}")
        if 'usage_metrics' in item:
            print(f"usage_metrics present: {bool(item['usage_metrics'])}")
        
        print("\nAttempting to save to DynamoDB...")
        # Save to DynamoDB
        table = dynamodb.Table(CHATS_TABLE)
        response = table.put_item(Item=item)
        
        print(f"DynamoDB response: {response}")
        print("=== Save completed successfully ===")
        return True
        
    except Exception as e:
        print(f"Error saving chat message: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

def get_chat_history(username: str, conversation_id: Optional[str] = None) -> List[dict]:
    """Get chat history for a user, optionally filtered by conversation_id"""
    try:
        table = dynamodb.Table('chat_messages')
        
        if conversation_id:
            # Get messages for specific conversation
            response = table.query(
                KeyConditionExpression='username = :username AND conversation_id = :conversation_id',
                ExpressionAttributeValues={
                    ':username': username,
                    ':conversation_id': conversation_id
                },
                ScanIndexForward=True  # Get messages in chronological order
            )
        else:
            # Get all messages for user
            response = table.query(
                KeyConditionExpression='username = :username',
                ExpressionAttributeValues={
                    ':username': username
                },
                ScanIndexForward=True
            )
        
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []

def get_conversations(username: str) -> List[dict]:
    """Get all unique conversations for a user"""
    try:
        table = dynamodb.Table('chat_messages')
        
        # Get all messages for user
        response = table.query(
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={
                ':username': username
            }
        )
        
        # Extract unique conversations
        conversations = {}
        for item in response.get('Items', []):
            conv_id = item['conversation_id']
            if conv_id not in conversations:
                conversations[conv_id] = {
                    'conversation_id': conv_id,
                    'last_message': item['message'],
                    'last_timestamp': item['timestamp'],
                    'message_count': 0
                }
            conversations[conv_id]['message_count'] += 1
        
        # Convert to list and sort by last timestamp
        return sorted(
            list(conversations.values()),
            key=lambda x: x['last_timestamp'],
            reverse=True
        )
    except Exception as e:
        print(f"Error getting conversations: {str(e)}")
        return []

def get_user_quiz_history(username: str) -> List[Dict]:
    """Get user's quiz history"""
    try:
        table = dynamodb.Table(CHATS_TABLE)
        response = table.scan(
            FilterExpression='username = :username AND interaction_type = :type',
            ExpressionAttributeValues={
                ':username': username,
                ':type': 'quiz'
            }
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting quiz history: {str(e)}")
        return []

def update_conversation_activity(conversation_id: str) -> bool:
    """Update conversation's last activity timestamp"""
    try:
        table = dynamodb.Table(CONVERSATIONS_TABLE)
        table.update_item(
            Key={'conversation_id': conversation_id},
            UpdateExpression='SET last_activity = :now',
            ExpressionAttributeValues={
                ':now': datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating conversation activity: {str(e)}")
        return False

def update_conversation_id(username: str, dify_conversation_id: str) -> bool:
    """Update conversation with Dify's conversation ID"""
    try:
        table = dynamodb.Table(CONVERSATIONS_TABLE)
        table.update_item(
            Key={'username': username},
            UpdateExpression='SET conversation_id = :conv_id, created_at = :now, last_activity = :now',
            ExpressionAttributeValues={
                ':conv_id': dify_conversation_id,
                ':now': datetime.utcnow().isoformat()
            }
        )
        return True
    except Exception as e:
        print(f"Error updating conversation ID: {str(e)}")
        return False

def verify_token(request: Request) -> Optional[str]:
    """Verify JWT token from request header"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
            
        # Get token part after 'Bearer '
        token = auth_header.split(' ', 1)[1] if ' ' in auth_header else auth_header
        
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            return payload.get('username')
        except jwt.InvalidTokenError:
            return None
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None

# End of file - removing reset_database function 