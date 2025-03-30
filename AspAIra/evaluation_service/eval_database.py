from typing import List, Dict, Optional
import boto3
import os
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError
from botocore.config import Config
from .eval_models import UserProfile, DifyEvaluationOutput, PROFILE1_FIELDS, PROFILE2_FIELDS

load_dotenv()

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
            self.tables['AspAIra_ConversationEvaluations'] = {}
        
        def Table(self, name):
            return InMemoryTable(self.tables[name])
    
    class InMemoryTable:
        def __init__(self, data):
            self.data = data
        
        def put_item(self, Item):
            if 'conversation_id' in Item:
                self.data[Item['conversation_id']] = Item
        
        def get_item(self, Key):
            return {'Item': self.data.get(Key.get('conversation_id'))}
        
        def query(self, **kwargs):
            return {'Items': list(self.data.values())}
        
        def scan(self):
            return {'Items': list(self.data.values())}
        
        def update_item(self, **kwargs):
            return {'Attributes': kwargs.get('ExpressionAttributeValues', {})}
        
        def table_status(self):
            return 'ACTIVE'
    
    dynamodb = InMemoryDB()

class EvaluationDatabase:
    """Handles all DynamoDB interactions for evaluation service"""
    
    def __init__(self):
        """Initialize DynamoDB connection"""
        self.dynamodb = boto3.resource(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='local',  # Required for local DynamoDB
            aws_access_key_id='dummy',  # Required for local DynamoDB
            aws_secret_access_key='dummy'  # Required for local DynamoDB
        )
        self.chats_table = self.dynamodb.Table('AspAIra_Chats')
        self.evaluations_table = self.dynamodb.Table('AspAIra_ConversationEvaluations')
        self.users_table = self.dynamodb.Table('AspAIra_Users')
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure all required tables exist, create if they don't"""
        try:
            # Check if evaluations table exists
            self.evaluations_table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create evaluations table
                self.dynamodb.create_table(
                    TableName='AspAIra_ConversationEvaluations',
                    KeySchema=[
                        {'AttributeName': 'conversation_id', 'KeyType': 'HASH'},
                        {'AttributeName': 'evaluation_timestamp', 'KeyType': 'RANGE'}
                    ],
                    AttributeDefinitions=[
                        {'AttributeName': 'conversation_id', 'AttributeType': 'S'},
                        {'AttributeName': 'evaluation_timestamp', 'AttributeType': 'S'}
                    ],
                    ProvisionedThroughput={
                        'ReadCapacityUnits': 5,
                        'WriteCapacityUnits': 5
                    }
                )
                # Wait for table to be created
                self.evaluations_table.wait_until_exists()
                print("Created AspAIra_ConversationEvaluations table")
        
        # Verify other tables exist
        try:
            self.chats_table.table_status
            self.users_table.table_status
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                raise Exception("Required tables 'AspAIra_Chats' or 'AspAIra_Users' not found. Please ensure they exist.")
    
    def get_unevaluated_conversations(self) -> List[str]:
        """Get conversation IDs that exist in chats but not in evaluations"""
        try:
            # Get all conversations from chats table using GSI
            chats_response = self.chats_table.scan(
                ProjectionExpression='conversation_id'
            )
            chat_conversations = {item['conversation_id'] for item in chats_response.get('Items', [])}
            
            # Get all evaluated conversations
            eval_response = self.evaluations_table.scan(
                ProjectionExpression='conversation_id'
            )
            evaluated_conversations = {item['conversation_id'] for item in eval_response.get('Items', [])}
            
            # Return conversations that haven't been evaluated
            return list(chat_conversations - evaluated_conversations)
        except Exception as e:
            print(f"Error getting unevaluated conversations: {str(e)}")
            return []
    
    def get_conversation_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation using the ConversationIndex GSI"""
        try:
            response = self.chats_table.query(
                IndexName='ConversationIndex',
                KeyConditionExpression='conversation_id = :conv_id',
                ExpressionAttributeValues={
                    ':conv_id': conversation_id
                },
                ScanIndexForward=True  # Get messages in chronological order
            )
            return response.get('Items', [])
        except Exception as e:
            print(f"Error getting conversation messages: {str(e)}")
            return []
    
    def get_user_profile(self, username: str) -> Dict:
        """Get user profile data from AspAIra_Users table"""
        try:
            response = self.users_table.get_item(
                Key={'username': username},
                ProjectionExpression='profile1, profile2'
            )
            user_data = response.get('Item', {})
            
            # Get profile data using field mappings
            profile_data = {}
            
            # Add profile1 fields
            profile1 = user_data.get('profile1', {})
            for field in PROFILE1_FIELDS:
                if field in profile1:
                    profile_data[field] = profile1[field]
            
            # Add profile2 fields
            profile2 = user_data.get('profile2', {})
            for field in PROFILE2_FIELDS:
                if field in profile2:
                    profile_data[field] = profile2[field]
            
            return profile_data
        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return {}
    
    def store_evaluation(self, evaluation_data: Dict) -> bool:
        """Store evaluation results in AspAIra_ConversationEvaluations"""
        try:
            # Validate data against DifyEvaluationOutput model
            validated_data = DifyEvaluationOutput(**evaluation_data)
            
            # Convert to dict and ensure timestamp is in ISO format
            data_to_store = validated_data.dict()
            data_to_store['evaluation_timestamp'] = data_to_store['evaluation_timestamp'].isoformat()
            
            # Convert numeric values to Decimal for DynamoDB
            converted_data = {}
            for key, value in data_to_store.items():
                if isinstance(value, (int, float)):
                    converted_data[key] = Decimal(str(value))
                else:
                    converted_data[key] = value
            
            # Store in DynamoDB
            self.evaluations_table.put_item(Item=converted_data)
            print(f"Successfully stored evaluation for conversation {converted_data['conversation_id']}")
            return True
            
        except Exception as e:
            print(f"Error storing evaluation: {str(e)}")
            return False
    
    def get_evaluation(self, conversation_id: str) -> Dict:
        """Get evaluation results for a conversation"""
        try:
            response = self.evaluations_table.get_item(
                Key={'conversation_id': conversation_id}
            )
            return response.get('Item', {})
        except Exception as e:
            print(f"Error getting evaluation: {str(e)}")
            return {}
    
    def mark_conversation_evaluated(self, conversation_id: str) -> bool:
        """Mark a conversation as evaluated"""
        try:
            self.chats_table.update_item(
                Key={'conversation_id': conversation_id},
                UpdateExpression='SET evaluation_status = :status, evaluated_at = :timestamp',
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':timestamp': datetime.utcnow().isoformat()
                }
            )
            return True
        except Exception as e:
            print(f"Error marking conversation as evaluated: {str(e)}")
            return False
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get a single conversation by ID using the ConversationIndex GSI"""
        try:
            response = self.chats_table.query(
                IndexName='ConversationIndex',
                KeyConditionExpression='conversation_id = :conv_id',
                ExpressionAttributeValues={
                    ':conv_id': conversation_id
                },
                Limit=1,
                ScanIndexForward=True  # Get the first message in chronological order
            )
            items = response.get('Items', [])
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting conversation: {str(e)}")
            return None 