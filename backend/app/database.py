import boto3
from botocore.exceptions import ClientError
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt

# JWT Configuration
SECRET_KEY = "development_secret_key"  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# DynamoDB configuration for local development
dynamodb = boto3.resource(
    'dynamodb',
    endpoint_url='http://localhost:8000',
    region_name='local',
    aws_access_key_id='dummy',
    aws_secret_access_key='dummy'
)

def _create_table_if_not_exists():
    try:
        table = dynamodb.create_table(
            TableName='AspAIra_Users',
            KeySchema=[
                {'AttributeName': 'username', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'username', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
    except ClientError as e:
        if e.response['Error']['Code'] != 'ResourceInUseException':
            raise

_create_table_if_not_exists()
table = dynamodb.Table('AspAIra_Users')

def create_user(username: str, password: str):
    hashed_password = pwd_context.hash(password)
    try:
        table.put_item(
            Item={
                'username': username,
                'hashed_password': hashed_password,
                'is_active': True,
                'profile_completed': False
            },
            ConditionExpression='attribute_not_exists(username)'
        )
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return False
        raise

def get_user(username: str):
    try:
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
        response = table.update_item(
            Key={'username': username},
            UpdateExpression="set profile_part1 = :p",
            ExpressionAttributeValues={
                ':p': profile_data
            },
            ReturnValues="UPDATED_NEW"
        )
        return response
    except ClientError:
        return None

def update_profile_part2(username: str, profile_data: dict):
    try:
        response = table.update_item(
            Key={'username': username},
            UpdateExpression="set profile_part2 = :p, profile_completed = :t",
            ExpressionAttributeValues={
                ':p': profile_data,
                ':t': True
            },
            ReturnValues="UPDATED_NEW"
        )
        return response
    except ClientError:
        return None

def get_profile_status(username: str):
    user = get_user(username)
    if not user:
        return None
    return {
        'profile_completed': user.get('profile_completed', False)
    } 