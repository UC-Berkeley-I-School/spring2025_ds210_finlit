"""
Service for handling Dify API integration.
Core functionality:
1. Send messages to Dify
2. Handle streaming responses
3. Save basic chat interactions
4. Return essential response data
"""
import os
import json
import requests
from sseclient import SSEClient
from typing import Dict, AsyncGenerator, Optional, Any, List
from datetime import datetime
from ..database import save_chat_message, get_chat_history
from ..config import AGENT_CONFIGS, ACTIVE_AGENT_VERSION

class DifyService:
    def __init__(self):
        """Initialize DifyService with configuration and headers"""
        self.conversation_id = None  # Initialize conversation_id as None
        self.config = AGENT_CONFIGS[ACTIVE_AGENT_VERSION]
        self.headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        print(f"Initialized DifyService with base_url: {self.config['base_url']}")

    def get_conversation_id(self):
        """Get current conversation ID"""
        return self.conversation_id

    def set_conversation_id(self, conversation_id):
        """Set conversation ID"""
        self.conversation_id = conversation_id
        print(f"Set conversation_id to: {conversation_id}")  # Debug log

    def process_message(
        self,
        username: str,
        message: str,
        profile_data: Dict,
        conversation_id: Optional[str] = None
    ) -> Dict:
        """Process a message through Dify"""
        try:
            # Extract profile data from the structured format
            profile1 = profile_data.get("profile1", {})
            profile2 = profile_data.get("profile2", {})
            
            # Dynamically build required inputs based on config
            required_inputs = {}
            for input_name, input_config in self.config['required_inputs'].items():
                source = input_config['source']
                profile_data = profile1 if source == "profile1" else profile2
                required_inputs[input_name] = str(profile_data.get(input_name, ""))
            
            print(f"Initializing Dify API request...")
            print(f"Base URL: {self.config['base_url']}")
            print(f"Headers: {self.headers}")
            print(f"Profile data received: {profile_data}")
            print(f"Mapped inputs for Dify: {required_inputs}")
            print(f"Conversation ID: {conversation_id}")

            # Prepare request data
            request_data = {
                "inputs": required_inputs,
                "query": message,
                "response_mode": "streaming",
                "user": username,
                "conversation_id": conversation_id  # Use the passed conversation_id directly
            }

            print(f"Sending request to Dify: {json.dumps(request_data, indent=2)}")

            # Make request to Dify
            response = requests.post(
                f"{self.config['base_url']}/v1/chat-messages",
                headers=self.headers,
                json=request_data,
                stream=True
            )

            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Response body: {response.text}")
                return None

            # Initialize response tracking variables
            message_id = None
            conversation_id = None
            full_response = ""
            dify_metadata = {
                "message_files": [],
                "feedback": None,
                "retriever_resources": [],
                "agent_thoughts": []
            }
            usage_metrics = None

            # Process streaming response
            for line in response.iter_lines():
                if line:
                    try:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            data = json.loads(line[6:])
                            event_type = data.get('event')
                            print(f"\nReceived event type: {event_type}")
                            print(f"Complete event data: {json.dumps(data, indent=2)}")
                            
                            if event_type == 'agent_message':
                                # Store message_id and conversation_id from any agent_message event
                                if not message_id and data.get('message_id'):
                                    message_id = data.get('message_id')
                                if not conversation_id and data.get('conversation_id'):
                                    conversation_id = data.get('conversation_id')
                                # Yield the chunk for streaming
                                yield {'event': 'agent_message', 'data': data}
                            
                            elif event_type == 'agent_thought':
                                # This contains the complete response
                                full_response = data.get('thought', '')
                                # Update metadata
                                dify_metadata['agent_thoughts'].append({
                                    'thought': data.get('thought', ''),
                                    'observation': data.get('observation', ''),
                                    'tool': data.get('tool', ''),
                                    'tool_labels': data.get('tool_labels', {})
                                })
                                # Yield the complete thought for streaming
                                yield {'event': 'agent_thought', 'data': data}
                            
                            elif event_type == 'message_end':
                                # Get usage metrics
                                usage_metrics = data.get('metadata', {}).get('usage', {})
                                if conversation_id:
                                    self.set_conversation_id(conversation_id)
                                yield {'event': 'message_end', 'data': data}
                            
                            elif event_type == 'error':
                                print(f"Received error event: {data.get('message')}")
                                yield {'error': data.get('message', 'Unknown error')}
                                return
                            
                    except json.JSONDecodeError as e:
                        print(f"Error decoding JSON: {str(e)}")
                        continue
                    except Exception as e:
                        print(f"Error processing line: {str(e)}")
                        continue

            print(f"\nFinal response data:")
            print(f"message_id: {message_id}")
            print(f"conversation_id: {conversation_id}")
            print(f"full_response: {full_response}")
            print(f"dify_metadata: {json.dumps(dify_metadata, indent=2)}")
            print(f"usage_metrics: {json.dumps(usage_metrics, indent=2)}")

            return {
                'message_id': message_id,
                'conversation_id': conversation_id,
                'response': full_response,
                'dify_metadata': dify_metadata,
                'usage_metrics': usage_metrics
            }

        except Exception as e:
            print(f"Error processing message: {str(e)}")
            return None

    def get_chat_history(self, username: str, conversation_id: Optional[str] = None) -> List[Dict]:
        """Get chat history for a user"""
        return get_chat_history(username, conversation_id) 