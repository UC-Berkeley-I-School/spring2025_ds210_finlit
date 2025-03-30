import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from .eval_database import EvaluationDatabase
from .eval_dify_service import DifyEvaluationService
from .eval_models import ConversationEvaluation, DifyEvaluationOutput

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationEvaluator:
    """Main class for evaluating conversations"""
    
    def __init__(self):
        """Initialize the evaluator with database and Dify service"""
        logger.info("Initializing ConversationEvaluator...")
        self.db = EvaluationDatabase()
        self.dify = DifyEvaluationService()
        logger.info("ConversationEvaluator initialized successfully")
    
    async def process_conversations(self, batch_size: int = 10):
        """Process all conversations that need evaluation"""
        logger.info("Starting conversation evaluation process...")
        
        try:
            # Get unevaluated conversations
            conversation_ids = self.db.get_unevaluated_conversations()
            
            if not conversation_ids:
                logger.info("No conversations found for evaluation")
                return
            
            logger.info(f"Found {len(conversation_ids)} conversations to evaluate")
            
            # Process conversations in batches
            for i in range(0, len(conversation_ids), batch_size):
                batch = conversation_ids[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} of {(len(conversation_ids) + batch_size - 1)//batch_size}")
                
                # Process each conversation in the batch
                tasks = [self._process_single_conversation(conv_id) for conv_id in batch]
                await asyncio.gather(*tasks)
                
                # Add a small delay between batches to avoid overwhelming the API
                if i + batch_size < len(conversation_ids):
                    await asyncio.sleep(1)
            
            logger.info("Completed conversation evaluation process")
            
        except Exception as e:
            logger.error(f"Error in process_conversations: {str(e)}", exc_info=True)
            raise
    
    async def _process_single_conversation(self, conversation_id: str) -> None:
        """Process a single conversation"""
        try:
            logger.info(f"Processing conversation {conversation_id}")
            
            # Get conversation details
            conversation = self.db.get_conversation(conversation_id)
            if not conversation:
                logger.error(f"Conversation {conversation_id} not found")
                return
            
            # Get conversation messages
            messages = self.db.get_conversation_messages(conversation_id)
            if not messages:
                logger.error(f"No messages found for conversation {conversation_id}")
                return
            
            # Get user profile
            user_profile = self.db.get_user_profile(conversation['username'])
            if not user_profile:
                logger.error(f"No user profile found for conversation {conversation_id}")
                return
            
            # Get agent_id from conversation
            agent_id = conversation.get('agent_id')
            if not agent_id:
                logger.error(f"No agent_id found for conversation {conversation_id}")
                return
            
            # Evaluate conversation
            evaluation = await self._evaluate_conversation(
                conversation_id=conversation_id,
                username=conversation['username'],
                messages=messages,
                user_profile=user_profile,
                agent_id=agent_id
            )
            
            if evaluation:
                # Store evaluation results
                if self.db.store_evaluation(evaluation.dict()):
                    logger.info(f"Successfully stored evaluation for conversation {conversation_id}")
                else:
                    logger.error(f"Failed to store evaluation for conversation {conversation_id}")
            else:
                logger.error(f"Failed to evaluate conversation {conversation_id}")
                
        except Exception as e:
            logger.error(f"Error processing conversation {conversation_id}: {str(e)}", exc_info=True)
    
    async def _evaluate_conversation(
        self,
        conversation_id: str,
        username: str,
        messages: List[Dict],
        user_profile: Dict,
        agent_id: str
    ) -> Optional[DifyEvaluationOutput]:
        """Evaluate a single conversation using Dify"""
        try:
            # Process with Dify agent
            evaluation_response = await self.dify.evaluate_conversation(
                conversation_id=conversation_id,
                username=username,
                messages=messages,
                user_profile=user_profile,
                agent_id=agent_id
            )
            
            if not evaluation_response:
                logger.error(f"No evaluation response received for conversation {conversation_id}")
                return None
            
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Error in _evaluate_conversation for {conversation_id}: {str(e)}", exc_info=True)
            return None

async def main():
    """Main entry point for the evaluation service"""
    try:
        logger.info("Starting evaluation service...")
        evaluator = ConversationEvaluator()
        await evaluator.process_conversations()
        logger.info("Evaluation service completed successfully")
    except Exception as e:
        logger.error(f"Error in main: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Evaluation service stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        exit(1) 