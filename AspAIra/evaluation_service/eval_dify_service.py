"""
Service for handling Dify API integration for evaluation.
Core functionality:
1. Format conversation data for evaluation
2. Send evaluation requests to Dify
3. Process and validate responses
4. Return evaluation results
"""
import os
import json
import aiohttp
from typing import Dict, List, Optional, AsyncGenerator
from datetime import datetime
from dotenv import load_dotenv
from .eval_models import DifyEvaluationOutput, EvaluationNotes
from decimal import Decimal
import logging

load_dotenv()

logger = logging.getLogger(__name__)

class DifyEvaluationService:
    """Service for handling Dify API integration for evaluation"""
    
    def __init__(self, config: Dict):
        """Initialize DifyEvaluationService with configuration and headers"""
        self.config = config
        self.headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        print(f"Initialized DifyEvaluationService with base_url: {self.config['base_url']}")
    
    def format_conversation_data(self, evaluation_input: Dict) -> Dict:
        """Format conversation data for evaluation"""
        # Create evaluation inputs with correct field names
        evaluation_inputs = {
            "convo_id": evaluation_input["convo_id"],
            "username": evaluation_input["username"],
            "conversation_log": evaluation_input["conversation_history"],
            "country_of_origin": evaluation_input["country_of_origin"],
            "time_in_uae": evaluation_input["time_in_uae"],
            "job_title": evaluation_input["job_title"],
            "housing": evaluation_input["housing"],
            "education_level": evaluation_input["education_level"],
            "number_of_kids": evaluation_input["number_of_kids"],
            "bank_account": evaluation_input["bank_account"],
            "debt_information": evaluation_input["debt_information"],
            "remittance_information": evaluation_input["remittance_information"],
            "financial_dependents": evaluation_input["financial_dependents"]
        }
        
        # Create the final request data
        request_data = {
            "inputs": evaluation_inputs,
            "query": "Evaluate this conversation",
            "response_mode": "streaming",
            "user": "evaluation_agent",
            "conversation_id": ""  # Empty for new conversations
        }
        
        return request_data
    
    def _convert_to_decimal(self, value) -> Decimal:
        """Convert a value to Decimal, handling both string and numeric inputs"""
        logger.info(f"Converting value to Decimal: {value} (type: {type(value)})")
        if value is None:
            logger.info("Value is None, returning Decimal('0')")
            return Decimal('0')
        if isinstance(value, str):
            try:
                decimal_value = Decimal(value)
                logger.info(f"Successfully converted string to Decimal: {decimal_value}")
                return decimal_value
            except Exception as e:
                logger.warning(f"Failed to convert string to Decimal: {str(e)}")
                return Decimal('0')
        decimal_value = Decimal(str(value))
        logger.info(f"Converted numeric value to Decimal: {decimal_value}")
        return decimal_value
    
    def _parse_evaluation_notes(self, notes_str: str) -> Dict:
        """Parse evaluation notes string into a structured dictionary"""
        try:
            # Default structure
            notes_dict = {
                "summary": "",
                "key_insights": "",
                "areas_for_improvement": "",
                "recommendations": ""
            }
            
            # Handle empty or None input
            if not notes_str:
                return notes_dict
            
            # First try to parse as JSON if it's already in that format
            try:
                if isinstance(notes_str, str) and notes_str.strip().startswith('{'):
                    parsed = json.loads(notes_str)
                    if isinstance(parsed, dict):
                        return {k: str(v) for k, v in parsed.items() if k in notes_dict}
            except json.JSONDecodeError:
                pass
            
            # Split the string into key-value pairs using multiple delimiters
            # Handle both single and double quotes, and escaped quotes
            pairs = []
            current_pos = 0
            while current_pos < len(notes_str):
                # Find the next key
                key_start = notes_str.find(' ', current_pos)
                if key_start == -1:
                    break
                
                # Find the value delimiter
                value_start = notes_str.find('=', key_start)
                if value_start == -1:
                    break
                
                # Get the key
                key = notes_str[key_start:value_start].strip()
                
                # Find the value
                value_start += 1
                quote_char = notes_str[value_start]
                if quote_char not in ['"', "'"]:
                    current_pos = value_start
                    continue
                
                # Find the end of the value
                value_end = notes_str.find(quote_char, value_start + 1)
                while value_end != -1 and notes_str[value_end - 1] == '\\':
                    value_end = notes_str.find(quote_char, value_end + 1)
                
                if value_end == -1:
                    break
                
                # Extract the value
                value = notes_str[value_start + 1:value_end]
                # Remove escape characters
                value = value.replace('\\"', '"').replace("\\'", "'")
                
                if key in notes_dict:
                    notes_dict[key] = value.strip()
                
                current_pos = value_end + 1
            
            return notes_dict
        except Exception as e:
            logger.error(f"Error parsing evaluation notes: {str(e)}")
            return notes_dict

    def _extract_json_from_response(self, thought: str, raw_thought: str) -> Optional[Dict]:
        """Extract JSON from response, handling both direct JSON and markdown-embedded JSON"""
        try:
            # First try to parse the entire response as JSON
            try:
                evaluation_data = json.loads(thought)
            except json.JSONDecodeError:
                try:
                    # Try to extract JSON from the text
                    start_idx = thought.find('{')
                    end_idx = thought.rfind('}') + 1
                    if start_idx != -1 and end_idx != 0:
                        json_str = thought[start_idx:end_idx]
                        evaluation_data = json.loads(json_str)
                    else:
                        # If no JSON found, create default structure
                        evaluation_data = {
                            "Personalization": 0,
                            "Language_Simplicity": 0,
                            "Response_Length": 0,
                            "Content_Relevance": 0,
                            "Content_Difficulty": 0,
                            "evaluation_notes": {
                                "summary": "",
                                "key_insights": "",
                                "areas_for_improvement": "",
                                "recommendations": ""
                            }
                        }
                except json.JSONDecodeError:
                    # If JSON extraction fails, create default structure
                    evaluation_data = {
                        "Personalization": 0,
                        "Language_Simplicity": 0,
                        "Response_Length": 0,
                        "Content_Relevance": 0,
                        "Content_Difficulty": 0,
                        "evaluation_notes": {
                            "summary": "",
                            "key_insights": "",
                            "areas_for_improvement": "",
                            "recommendations": ""
                        }
                    }

            # Convert scores to Decimal and handle evaluation notes like the old code
            result = {
                "Personalization": self._convert_to_decimal(evaluation_data.get("Personalization")),
                "Language_Simplicity": self._convert_to_decimal(evaluation_data.get("Language_Simplicity")),
                "Response_Length": self._convert_to_decimal(evaluation_data.get("Response_Length")),
                "Content_Relevance": self._convert_to_decimal(evaluation_data.get("Content_Relevance")),
                "Content_Difficulty": self._convert_to_decimal(evaluation_data.get("Content_Difficulty")),
                "evaluation_notes": {
                    "summary": evaluation_data.get("evaluation_notes", {}).get("summary", ""),
                    "key_insights": evaluation_data.get("evaluation_notes", {}).get("key_insights", ""),
                    "areas_for_improvement": evaluation_data.get("evaluation_notes", {}).get("areas_for_improvement", ""),
                    "recommendations": evaluation_data.get("evaluation_notes", {}).get("recommendations", "")
                },
                "process_status": "success",
                "raw_response": raw_thought
            }
            return result

        except Exception as e:
            logger.error(f"Error extracting JSON from response: {str(e)}")
            return None

    async def send_to_dify(self, data: Dict) -> Optional[Dict]:
        """Send data to Dify API using streaming mode"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/v1/chat-messages",
                    headers=self.headers,
                    json=data
                ) as response:
                    if response.status == 200:
                        last_thought_event = None
                        raw_thought = None
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line = line.decode('utf-8')
                                    
                                    if line.startswith('data: '):
                                        data = json.loads(line[6:])
                                        event_type = data.get('event')
                                        
                                        if event_type == 'agent_thought':
                                            last_thought_event = data
                                            raw_thought = data.get('thought')
                                            logger.info(f"Received agent thought: {raw_thought}")
                                        
                                        elif event_type == 'error':
                                            logger.error(f"Error from Dify: {data.get('message', 'Unknown error')}")
                                            return {
                                                "Personalization": Decimal('0'),
                                                "Language_Simplicity": Decimal('0'),
                                                "Response_Length": Decimal('0'),
                                                "Content_Relevance": Decimal('0'),
                                                "Content_Difficulty": Decimal('0'),
                                                "evaluation_notes": {
                                                    "summary": "",
                                                    "key_insights": "",
                                                    "areas_for_improvement": "",
                                                    "recommendations": ""
                                                },
                                                "process_status": "error",
                                                "raw_response": data.get('message', 'Unknown error')
                                            }

                                except json.JSONDecodeError as e:
                                    logger.error(f"Error decoding JSON line: {str(e)}")
                                    continue
                                except Exception as e:
                                    logger.error(f"Error processing line: {str(e)}")
                                    continue
                        
                        if last_thought_event:
                            thought = last_thought_event.get('thought', '')
                            logger.info(f"Processing final thought: {thought}")
                            
                            evaluation_data = self._extract_json_from_response(thought, raw_thought)
                            if evaluation_data:
                                return evaluation_data
                            else:
                                return {
                                    "Personalization": Decimal('0'),
                                    "Language_Simplicity": Decimal('0'),
                                    "Response_Length": Decimal('0'),
                                    "Content_Relevance": Decimal('0'),
                                    "Content_Difficulty": Decimal('0'),
                                    "evaluation_notes": {
                                        "summary": "",
                                        "key_insights": "",
                                        "areas_for_improvement": "",
                                        "recommendations": ""
                                    },
                                    "process_status": "error",
                                    "raw_response": raw_thought
                                }
                        else:
                            logger.error("No agent_thought events received")
                            return None
                            
                    else:
                        error_data = await response.json()
                        error_message = error_data.get('message', 'Unknown error')
                        logger.error(f"Error from Dify: {error_message}")
                        return {
                            "Personalization": Decimal('0'),
                            "Language_Simplicity": Decimal('0'),
                            "Response_Length": Decimal('0'),
                            "Content_Relevance": Decimal('0'),
                            "Content_Difficulty": Decimal('0'),
                            "evaluation_notes": {
                                "summary": "",
                                "key_insights": "",
                                "areas_for_improvement": "",
                                "recommendations": ""
                            },
                            "process_status": "error",
                            "raw_response": error_message
                        }
                        
        except Exception as e:
            logger.error(f"Error sending data to Dify: {str(e)}")
            return {
                "Personalization": Decimal('0'),
                "Language_Simplicity": Decimal('0'),
                "Response_Length": Decimal('0'),
                "Content_Relevance": Decimal('0'),
                "Content_Difficulty": Decimal('0'),
                "evaluation_notes": {
                    "summary": "",
                    "key_insights": "",
                    "areas_for_improvement": "",
                    "recommendations": ""
                },
                "process_status": "error",
                "raw_response": str(e)
            }

    async def evaluate_conversation(self, conversation_id: str, username: str, messages: List[Dict], user_profile: Dict, agent_id: str) -> Optional[Dict]:
        """Evaluate a conversation using Dify"""
        try:
            # Format conversation history as plain text
            conversation_text = []
            for msg in messages:
                interaction = [
                    f"[{msg.get('timestamp', '')}]",
                    f"User: {msg.get('response', '')}",
                    f"Assistant: {msg.get('message', '')}",
                    ""
                ]
                conversation_text.extend(interaction)
            
            conversation_history = "\n".join(conversation_text)
            
            # Store original values for later use
            original_conversation_id = conversation_id
            original_username = username
            original_agent_id = agent_id
            
            # Prepare evaluation input data
            evaluation_input = {
                "convo_id": original_conversation_id,
                "username": original_username,
                "conversation_history": conversation_history,
                "country_of_origin": user_profile.get('country_of_origin', ''),
                "time_in_uae": user_profile.get('time_in_uae', ''),
                "job_title": user_profile.get('job_title', ''),
                "housing": user_profile.get('housing', ''),
                "education_level": user_profile.get('education_level', ''),
                "number_of_kids": user_profile.get('number_of_kids', ''),
                "bank_account": user_profile.get('bank_account', ''),
                "debt_information": user_profile.get('debt_information', ''),
                "remittance_information": user_profile.get('remittance_information', ''),
                "financial_dependents": user_profile.get('financial_dependents', '')
            }
            
            request_data = self.format_conversation_data(evaluation_input)
            response = await self.send_to_dify(request_data)
            
            if response:
                # Store the raw response
                raw_response = json.dumps(response, default=str)
                
                # For error responses, preserve the raw_response
                if response.get("process_status") == "error":
                    return response
                
                # For successful responses, create EvaluationNotes
                evaluation_notes = EvaluationNotes(
                    summary=response.get('evaluation_notes', {}).get('summary', ''),
                    key_insights=response.get('evaluation_notes', {}).get('key_insights', ''),
                    areas_for_improvement=response.get('evaluation_notes', {}).get('areas_for_improvement', ''),
                    recommendations=response.get('evaluation_notes', {}).get('recommendations', '')
                )
                
                # Return the evaluation data in the expected format
                return {
                    "Personalization": response.get('Personalization', Decimal('0')),
                    "Language_Simplicity": response.get('Language_Simplicity', Decimal('0')),
                    "Response_Length": response.get('Response_Length', Decimal('0')),
                    "Content_Relevance": response.get('Content_Relevance', Decimal('0')),
                    "Content_Difficulty": response.get('Content_Difficulty', Decimal('0')),
                    "evaluation_notes": evaluation_notes,
                    "process_status": "success",
                    "raw_response": raw_response  # Always store the raw response
                }
            
            return None
            
        except Exception as e:
            print(f"Error evaluating conversation: {str(e)}")
            return None 