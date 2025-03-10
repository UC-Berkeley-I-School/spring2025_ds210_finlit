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
from typing import Optional, Dict, List
from .config import DATABASE_CONFIG

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
            self.tables['AspAIra_Chat'] = {}
        
        def Table(self, name):
            return InMemoryTable(self.tables[name])
    
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
    
    dynamodb = InMemoryDB()

USERS_TABLE = 'AspAIra_Users'
CHAT_TABLE = 'AspAIra_Chat'

def _create_tables_if_not_exists():
    try:
        # Check if users table exists
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

        # Check if chat table exists
        try:
            dynamodb.Table(CHAT_TABLE).table_status
            print(f"Table {CHAT_TABLE} exists")
        except (ClientError, AttributeError):
            print(f"Creating table {CHAT_TABLE}")
            try:
                table = dynamodb.create_table(
                    TableName=CHAT_TABLE,
                    KeySchema=[
                        {
                            'AttributeName': 'username',
                            'KeyType': 'HASH'
                        },
                        {
                            'AttributeName': 'timestamp',
                            'KeyType': 'RANGE'
                        }
                    ],
                    AttributeDefinitions=[
                        {
                            'AttributeName': 'username',
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
                    }
                )
                table.wait_until_exists()
                print(f"Table {CHAT_TABLE} created successfully")
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceInUseException':
                    print(f"Table {CHAT_TABLE} already exists")
                else:
                    raise
    except Exception as e:
        print(f"Warning: Error creating tables: {str(e)}")
        print("Using in-memory storage for development")

# Create tables on module import
_create_tables_if_not_exists()

def get_table():
    return dynamodb.Table(USERS_TABLE)

def create_user(username: str, password: str):
    print(f"Attempting to create user: {username}")  # Debug log
    hashed_password = pwd_context.hash(password)
    try:
        table = dynamodb.Table(USERS_TABLE)
        print(f"Got table reference: {USERS_TABLE}")  # Debug log
        
        # First check if user exists
        existing_user = table.get_item(Key={'username': username}).get('Item')
        if existing_user:
            print(f"User {username} already exists")  # Debug log
            return False
            
        # Create new user
        table.put_item(
            Item={
                'username': username,
                'hashed_password': hashed_password,
                'is_active': True,
                'profile_completed': False,
                'created_at': datetime.utcnow().isoformat()
            }
        )
        print(f"Successfully created user: {username}")  # Debug log
        return True
    except ClientError as e:
        print(f"Error creating user: {str(e)}")  # Debug log
        raise
    except Exception as e:
        print(f"Unexpected error creating user: {str(e)}")  # Debug log
        raise

def get_user(username: str):
    try:
        table = dynamodb.Table(USERS_TABLE)
        response = table.get_item(Key={'username': username})
        return response.get('Item')
    except ClientError:
        return None

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not pwd_context.verify(password, user['hashed_password']):
        return False
    return user

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

def save_chat_interaction(
    username: str,
    message: str,
    response: str,
    interaction_type: str,
    metadata: Optional[Dict] = None,
    quiz_data: Optional[Dict] = None,
    quiz_answers: Optional[List[str]] = None,
    quiz_feedback: Optional[str] = None
) -> bool:
    """Save chat interaction to DynamoDB with enhanced metadata"""
    try:
        table = dynamodb.Table(CHAT_TABLE)
        interaction = {
            'username': username,
            'timestamp': datetime.utcnow().isoformat(),
            'message': message,
            'response': response,
            'interaction_type': interaction_type,
            'metadata': metadata or {},
            'quiz_data': quiz_data,
            'quiz_answers': quiz_answers,
            'quiz_feedback': quiz_feedback
        }
        
        table.put_item(Item=interaction)
        return True
    except Exception as e:
        print(f"Error saving chat interaction: {str(e)}")
        return False

def get_chat_history(username: str) -> List[Dict]:
    """Get user's chat history with enhanced metadata"""
    try:
        table = dynamodb.Table(CHAT_TABLE)
        response = table.query(
            KeyConditionExpression='username = :username',
            ExpressionAttributeValues={':username': username},
            ScanIndexForward=False  # Most recent first
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting chat history: {str(e)}")
        return []

def get_user_quiz_history(username: str) -> List[Dict]:
    """Get user's quiz history"""
    try:
        table = dynamodb.Table(CHAT_TABLE)
        response = table.query(
            KeyConditionExpression='username = :username',
            FilterExpression='interaction_type = :type',
            ExpressionAttributeValues={
                ':username': username,
                ':type': 'quiz'
            },
            ScanIndexForward=False
        )
        return response.get('Items', [])
    except Exception as e:
        print(f"Error getting quiz history: {str(e)}")
        return []

# End of file - removing reset_database function 