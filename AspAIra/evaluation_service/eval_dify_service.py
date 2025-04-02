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
from .eval_models import DifyEvaluationOutput
from decimal import Decimal

load_dotenv()

# Evaluation agent configuration
EVAL_AGENT_CONFIG = {
    "api_key": os.getenv("DIFY_API_KEY", "app-vrvVKNIRXX8W0E8mBmAj3m17"),
    "base_url": os.getenv("DIFY_BASE_URL", "http://localhost"),
    "model": "claude-3-opus-20240229",
    "agent_mode": "evaluation"
}

class DifyEvaluationService:
    """Service for handling Dify API integration for evaluation"""
    
    def __init__(self):
        """Initialize DifyEvaluationService with configuration and headers"""
        self.config = EVAL_AGENT_CONFIG
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
    
    async def send_to_dify(self, data: Dict) -> Optional[Dict]:
        """Send data to Dify API using streaming mode"""
        try:
            # Log the request data for debugging
            # print("\nSending request to Dify:")
            # print(f"URL: {self.config['base_url']}/v1/chat-messages")
            # print(f"Headers: {self.headers}")
            # print(f"Request data: {json.dumps(data, indent=2)}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.config['base_url']}/v1/chat-messages",
                    headers=self.headers,
                    json=data
                ) as response:
                    # print(f"\nDify Response Status: {response.status}")
                    # print(f"Response Headers: {response.headers}")
                    
                    if response.status == 200:
                        # print("\nStarting to process streaming response...")
                        
                        # Store the last agent_thought event
                        last_thought_event = None
                        
                        async for line in response.content:
                            if line:
                                try:
                                    line = line.decode('utf-8')
                                    # print(f"\nRaw line received: {line}")
                                    
                                    if line.startswith('data: '):
                                        data = json.loads(line[6:])
                                        event_type = data.get('event')
                                        # print(f"Event type: {event_type}")
                                        # print(f"Event data: {json.dumps(data, indent=2)}")
                                        
                                        if event_type == 'agent_thought':
                                            # Store this thought event
                                            last_thought_event = data
                                            # print(f"Stored thought event: {data.get('thought', '')}")
                                        
                                        elif event_type == 'error':
                                            print(f"Error from Dify: {data.get('message', 'Unknown error')}")
                                            return None
                                            
                                except json.JSONDecodeError as e:
                                    print(f"Error decoding JSON line: {str(e)}")
                                    print(f"Problematic line: {line}")
                                    continue
                                except Exception as e:
                                    print(f"Error processing line: {str(e)}")
                                    print(f"Problematic line: {line}")
                                    continue
                        
                        # After processing all events, handle the last thought event
                        if last_thought_event:
                            thought = last_thought_event.get('thought', '')
                            # print(f"\nProcessing final thought: {thought}")
                            
                            try:
                                # Try to parse the thought as JSON
                                evaluation_data = json.loads(thought)
                                # print(f"Successfully parsed evaluation data: {json.dumps(evaluation_data, indent=2)}")
                                return evaluation_data
                            except json.JSONDecodeError as e:
                                print(f"Error parsing thought as JSON: {str(e)}")
                                print(f"Thought content: {thought}")
                                
                                # Try to extract JSON from the text
                                try:
                                    # Look for JSON-like structure in the text
                                    start_idx = thought.find('{')
                                    end_idx = thought.rfind('}') + 1
                                    
                                    if start_idx == -1:
                                        # print("No opening curly brace found in text")
                                        pass
                                    if end_idx == 0:
                                        # print("No closing curly brace found in text")
                                        pass
                                        
                                    if start_idx != -1 and end_idx != 0:
                                        json_str = thought[start_idx:end_idx]
                                        # print(f"Extracted JSON string: {json_str}")
                                        
                                        evaluation_data = json.loads(json_str)
                                        
                                        # Validate required fields
                                        required_fields = [
                                            "Personalization", "Language_Simplicity",
                                            "Response_Length", "Content_Relevance",
                                            "Content_Difficulty"
                                        ]
                                        missing_fields = [field for field in required_fields if field not in evaluation_data]
                                        
                                        if missing_fields:
                                            # print(f"Missing required fields in extracted JSON: {missing_fields}")
                                            # Create default values for missing fields
                                            for field in missing_fields:
                                                evaluation_data[field] = 0
                                        
                                        # Ensure Notes field exists
                                        if "Notes" not in evaluation_data:
                                            evaluation_data["Notes"] = thought
                                            
                                        # print(f"Successfully extracted and parsed JSON from text: {json.dumps(evaluation_data, indent=2)}")
                                        return evaluation_data
                                    else:
                                        # print("Could not find valid JSON structure in text")
                                        pass
                                except json.JSONDecodeError as e2:
                                    print(f"Error extracting JSON from text: {str(e2)}")
                                    print(f"Attempted to parse: {json_str}")
                                except Exception as e3:
                                    print(f"Unexpected error while processing text: {str(e3)}")
                                
                                # If no valid JSON found, create default evaluation data
                                # print("Creating default evaluation data with original thought in Notes")
                                return {
                                    "Personalization": 0,
                                    "Language_Simplicity": 0,
                                    "Response_Length": 0,
                                    "Content_Relevance": 0,
                                    "Content_Difficulty": 0,
                                    "Notes": thought  # Store the agent's message in Notes
                                }
                        else:
                            print("No agent_thought events received")
                            return None
                            
                    else:
                        error_data = await response.json()
                        error_code = error_data.get('code', 'unknown')
                        error_message = error_data.get('message', 'Unknown error')
                        
                        # Handle specific error cases
                        if error_code == 'invalid_param':
                            print(f"Invalid parameter error: {error_message}")
                        elif error_code == 'app_unavailable':
                            print(f"App configuration unavailable: {error_message}")
                        elif error_code == 'provider_not_initialize':
                            print(f"No available model credential configuration: {error_message}")
                        elif error_code == 'provider_quota_exceeded':
                            print(f"Model invocation quota insufficient: {error_message}")
                        elif error_code == 'model_currently_not_support':
                            print(f"Current model unavailable: {error_message}")
                        elif error_code == 'completion_request_error':
                            print(f"Text generation failed: {error_message}")
                        else:
                            print(f"Error sending data to Dify: {response.status}")
                            print(f"Error response: {error_message}")
                        return None
                        
        except Exception as e:
            print(f"Error sending data to Dify: {str(e)}")
            return None
    
    async def evaluate_conversation(self, conversation_id: str, username: str, messages: List[Dict], user_profile: Dict, agent_id: str) -> Optional[Dict]:
        """Evaluate a conversation using Dify"""
        try:
            # Format conversation history as plain text
            conversation_text = []
            for msg in messages:
                # Format each message interaction
                interaction = [
                    f"[{msg.get('timestamp', '')}]",
                    f"User: {msg.get('response', '')}",
                    f"Assistant: {msg.get('message', '')}",
                    ""  # Add blank line between interactions
                ]
                conversation_text.extend(interaction)
            
            # Join all lines with newlines
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
            
            # Format data for Dify
            request_data = self.format_conversation_data(evaluation_input)
            
            # Send to Dify
            response = await self.send_to_dify(request_data)
            
            if response:
                # Convert response to DifyEvaluationOutput using original values
                return DifyEvaluationOutput(
                    conversation_id=original_conversation_id,
                    username=original_username,
                    agent_id=original_agent_id,  # Include agent_id
                    Personalization=response['Personalization'],
                    Language_Simplicity=response['Language_Simplicity'],
                    Response_Length=response['Response_Length'],
                    Content_Relevance=response['Content_Relevance'],
                    Content_Difficulty=response['Content_Difficulty'],
                    Notes=response['Notes']
                )
            return None
            
        except Exception as e:
            print(f"Error evaluating conversation: {str(e)}")
            return None 