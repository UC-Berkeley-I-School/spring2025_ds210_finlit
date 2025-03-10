"""
Service for handling Dify API integration.
Core functionality:
1. Send messages to Dify
2. Handle streaming responses
3. Save basic chat interactions
4. Return essential response data
"""
import httpx
from typing import Dict
from datetime import datetime
from ..database import save_chat_interaction
from ..config import AGENT_CONFIGS
import json

class DifyService:
    def __init__(self, agent_type: str = "dify", version: str = "v1"):
        """Initialize DifyService with configuration and headers"""
        self.config = AGENT_CONFIGS[agent_type][version]
        self.headers = {
            "Authorization": f"Bearer {self.config['api_key']}",
            "Content-Type": "application/json"
        }
        print(f"Initialized DifyService with base_url: {self.config['base_url']}")

    async def process_message(
        self,
        username: str,
        message: str,
        profile_data: Dict
    ) -> Dict:
        """Process message and get response from Dify"""
        try:
            # Extract only required profile fields
            required_inputs = {
                k: profile_data.get(k, "") for k in self.config["required_inputs"]
            }
            
            # Handle initial topic selection
            if message in ["1", "2", "3"]:
                topic_map = {
                    "1": "Creating a budget",
                    "2": "Saving strategies",
                    "3": "Tips for sending money home"
                }
                message = f"I want to learn about {topic_map[message]}"
            
            # Prepare request with required inputs
            request_data = {
                "inputs": required_inputs,
                "query": message,
                "response_mode": "streaming",
                "conversation_id": profile_data.get("conversation_id", ""),  # Use existing conversation if available
                "user": username
            }
            
            print(f"Initializing Dify API request...")
            print(f"Base URL: {self.config['base_url']}")
            print(f"Headers: {self.headers}")
            print(f"Request data: {request_data}")
            
            # Call Dify API
            async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
                try:
                    print(f"Sending request to Dify API endpoint: {self.config['base_url']}/v1/chat-messages")
                    response = await client.post(
                        f"{self.config['base_url']}/v1/chat-messages",
                        headers=self.headers,
                        json=request_data
                    )
                    
                    print(f"Response status code: {response.status_code}")
                    print(f"Response headers: {response.headers}")
                    
                    if response.status_code != 200:
                        print(f"Dify API error response: {response.text}")
                        raise Exception(f"Dify API error (status {response.status_code}): {response.text}")
                    
                    # Handle streaming response
                    full_response = ""
                    message_id = None
                    conversation_id = None
                    last_data = None
                    
                    print("Starting to process streaming response...")
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            try:
                                data = json.loads(line[6:])
                                print(f"Received streaming data event: {data.get('event')}")
                                
                                if data.get("event") in ["agent_message", "agent_thought", "message"]:
                                    # Update message_id and conversation_id from any valid event
                                    if not message_id and data.get("message_id"):
                                        message_id = data.get("message_id")
                                        print(f"Captured message_id: {message_id}")
                                    if not conversation_id and data.get("conversation_id"):
                                        conversation_id = data.get("conversation_id")
                                        print(f"Captured conversation_id: {conversation_id}")
                                    # Append answer content if present for agent_message events
                                    if data.get("event") == "agent_message" and "answer" in data:
                                        current_answer = data["answer"]
                                        print(f"Adding to response: {current_answer}")
                                        full_response += current_answer
                                elif data.get("event") == "error":
                                    print(f"Received error event: {data.get('message')}")
                                    raise Exception(f"Dify API streaming error: {data.get('message')}")
                                elif data.get("event") == "done":
                                    print("Received done event - stream complete")
                                    break
                                
                                # Store the last data received
                                last_data = data
                                
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse streaming JSON: {str(e)}")
                                continue
                    
                    print(f"Stream processing complete")
                    print(f"Final complete response: {full_response}")
                    print(f"Final Message ID: {message_id}")
                    print(f"Final Conversation ID: {conversation_id}")
                    
                    if not message_id or not conversation_id:
                        if last_data:
                            print(f"Last received data: {last_data}")
                        raise Exception("Failed to receive valid message_id or conversation_id")
                    
                    # Save basic chat interaction with metadata
                    save_chat_interaction(
                        username=username,
                        message=message,
                        response=full_response,
                        interaction_type="content",
                        metadata={
                            "profile_data": required_inputs,
                            "message_id": message_id,
                            "conversation_id": conversation_id,
                            "created_at": datetime.utcnow().isoformat()
                        }
                    )
                    
                    # Return essential response data
                    return {
                        "message": full_response,
                        "timestamp": datetime.utcnow(),
                        "message_id": message_id,
                        "conversation_id": conversation_id
                    }
                    
                except httpx.RequestError as e:
                    print(f"Request error: {str(e)}")
                    raise Exception(f"Failed to connect to Dify API: {str(e)}")
                
        except Exception as e:
            print(f"Error in process_message: {str(e)}")
            raise Exception(f"Error in process_message: {str(e)}") 