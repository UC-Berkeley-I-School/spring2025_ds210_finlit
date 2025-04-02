import asyncio
import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from .eval_database import EvaluationDatabase
from .eval_dify_service import DifyEvaluationService
from .eval_models import DifyEvaluationOutput, UsageMetrics

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
    
    async def process_conversations(self):
        """Process all conversations that need evaluation sequentially"""
        logger.info("Starting conversation evaluation process...")
        
        try:
            # Get unevaluated conversations
            conversation_ids = self.db.get_unevaluated_conversations()
            
            if not conversation_ids:
                logger.info("No conversations found for evaluation")
                return
            
            logger.info(f"Found {len(conversation_ids)} conversations to evaluate")
            
            # Process each conversation sequentially
            for i, conv_id in enumerate(conversation_ids, 1):
                logger.info(f"Processing conversation {i} of {len(conversation_ids)}")
                await self._process_single_conversation(conv_id)
                
                # Add delay between conversations to avoid rate limits
                if i < len(conversation_ids):  # Don't delay after the last conversation
                    logger.info("Waiting 2 seconds before next conversation...")
                    await asyncio.sleep(2)
            
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
            
            # Compute usage metrics
            usage_metrics = self._compute_usage_metrics(messages)
            
            # Add usage metrics to evaluation response
            evaluation_response.usage_metrics = usage_metrics
            
            return evaluation_response
            
        except Exception as e:
            logger.error(f"Error in _evaluate_conversation for {conversation_id}: {str(e)}", exc_info=True)
            return None
            
    def _compute_usage_metrics(self, messages: List[Dict]) -> Optional[UsageMetrics]:
        """Compute usage metrics from conversation messages"""
        try:
            if not messages:
                logger.warning("No messages provided for usage metrics computation")
                return None
                
            # Initialize metrics
            total_tokens = Decimal('0')
            total_completion_tokens = Decimal('0')
            total_cost = Decimal('0')
            total_latency = Decimal('0')
            max_latency = Decimal('0')
            
            # Process each message
            for msg in messages:
                usage = msg.get('usage_metrics', {})
                
                # Sum up tokens - properly handle prompt and completion tokens
                prompt_tokens = Decimal(str(usage.get('prompt_tokens', 0)))
                completion_tokens = Decimal(str(usage.get('completion_tokens', 0)))
                total_tokens += prompt_tokens + completion_tokens
                total_completion_tokens += completion_tokens
                
                # Sum up costs - using total_price which already includes both prompt and completion costs
                cost = Decimal(str(usage.get('total_price', '0')))
                total_cost += cost
                
                # Track latency
                latency = Decimal(str(usage.get('latency', 0)))
                total_latency += latency
                max_latency = max(max_latency, latency)
            
            # Calculate averages
            num_turns = len(messages)
            if num_turns > 0:
                avg_tokens_per_turn = total_tokens / Decimal(str(num_turns))
                avg_completion_tokens = total_completion_tokens / Decimal(str(num_turns))
                avg_cost_per_turn = total_cost / Decimal(str(num_turns))
                avg_latency = total_latency / Decimal(str(num_turns))
            else:
                avg_tokens_per_turn = Decimal('0')
                avg_completion_tokens = Decimal('0')
                avg_cost_per_turn = Decimal('0')
                avg_latency = Decimal('0')
            
            # Create UsageMetrics object
            return UsageMetrics(
                num_turns=num_turns,
                avg_tokens_per_turn=avg_tokens_per_turn,
                avg_completion_tokens=avg_completion_tokens,
                avg_cost_per_turn=avg_cost_per_turn,
                total_price=total_cost,
                avg_latency=avg_latency,
                max_latency=max_latency,
                currency="USD"
            )
            
        except Exception as e:
            logger.error(f"Error computing usage metrics: {str(e)}", exc_info=True)
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