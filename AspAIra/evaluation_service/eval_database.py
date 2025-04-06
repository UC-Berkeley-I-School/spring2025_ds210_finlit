from typing import List, Dict, Optional
import os
from dotenv import load_dotenv
from datetime import datetime
from decimal import Decimal
from botocore.exceptions import ClientError
from backend.app.database import (
    dynamodb,
    CHATS_TABLE,
    USERS_TABLE,
    EVALUATIONS_TABLE
)
from .eval_models import UserProfile, DifyEvaluationOutput, PROFILE1_FIELDS, PROFILE2_FIELDS

load_dotenv()

class EvaluationDatabase:
    """Handles all DynamoDB interactions for evaluation service"""
    
    def __init__(self):
        """Initialize database tables"""
        self.chats_table = dynamodb.Table(CHATS_TABLE)
        self.evaluations_table = dynamodb.Table(EVALUATIONS_TABLE)
        self.users_table = dynamodb.Table(USERS_TABLE)
    
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
    
    def _convert_to_dynamodb_format(self, data: Dict) -> Dict:
        """Recursively convert numeric values to Decimal for DynamoDB"""
        try:
            converted = {}
            for key, value in data.items():
                try:
                    if isinstance(value, (int, float)):
                        converted[key] = Decimal(str(value))
                    elif isinstance(value, dict):
                        converted[key] = self._convert_to_dynamodb_format(value)
                    elif isinstance(value, list):
                        converted[key] = [
                            self._convert_to_dynamodb_format(item) if isinstance(item, dict) else item
                            for item in value
                        ]
                    else:
                        converted[key] = value
                except Exception as e:
                    print(f"Error converting key {key}: {str(e)}")
                    converted[key] = value  # Keep original value if conversion fails
            return converted
        except Exception as e:
            print(f"Error in _convert_to_dynamodb_format: {str(e)}")
            return data  # Return original data if conversion fails

    def store_evaluation(self, evaluation_data: Dict) -> bool:
        """Store evaluation results in AspAIra_ConversationEvaluations"""
        try:
            print(f"Starting to store evaluation data: {evaluation_data}")
            
            # Validate data against DifyEvaluationOutput model
            validated_data = DifyEvaluationOutput(**evaluation_data)
            print("Data validated successfully")
            
            # Convert to dict and ensure timestamp is in ISO format
            data_to_store = validated_data.dict()
            data_to_store['evaluation_timestamp'] = data_to_store['evaluation_timestamp'].isoformat()
            print("Timestamp converted to ISO format")
            
            # Log judge metrics before conversion
            for judge_eval in data_to_store.get('judge_evaluations', []):
                print(f"Judge metrics before conversion for {judge_eval['judge_id']}: {judge_eval.get('judge_metrics')}")
            
            # Convert all numeric values to Decimal recursively
            converted_data = self._convert_to_dynamodb_format(data_to_store)
            
            # Log judge metrics after conversion
            for judge_eval in converted_data.get('judge_evaluations', []):
                print(f"Judge metrics after conversion for {judge_eval['judge_id']}: {judge_eval.get('judge_metrics')}")
            
            # Store in DynamoDB
            print(f"Attempting to store converted data: {converted_data}")
            self.evaluations_table.put_item(Item=converted_data)
            print(f"Successfully stored evaluation for conversation {converted_data['conversation_id']}")
            return True
            
        except Exception as e:
            print(f"Error storing evaluation: {str(e)}")
            import traceback
            print(f"Full traceback: {traceback.format_exc()}")
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