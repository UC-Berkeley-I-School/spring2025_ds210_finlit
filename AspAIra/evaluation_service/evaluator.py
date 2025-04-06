import asyncio
import logging
import json
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal
from .eval_database import EvaluationDatabase
from .eval_dify_service import DifyEvaluationService
from .eval_models import DifyEvaluationOutput, UsageMetrics, QuizMetrics, JudgeEvaluation, JudgeMetrics, ScoreMetrics, EvaluationNotes
from .eval_config import AGENT_CONFIGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConversationEvaluator:
    """Main class for evaluating conversations"""
    
    def __init__(self):
        """Initialize the evaluator with database and judge services"""
        logger.info("Initializing ConversationEvaluator...")
        self.db = EvaluationDatabase()
        # Create a map of judge services
        self.judge_services = {
            judge_id: DifyEvaluationService(config)
            for judge_id, config in AGENT_CONFIGS.items()
        }
        logger.info(f"Initialized {len(self.judge_services)} judge services")
    
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
        """Evaluate a single conversation using multiple judges"""
        try:
            judge_evaluations = []
            
            # Run evaluation for each judge
            for judge_id, judge_service in self.judge_services.items():
                try:
                    logger.info(f"Starting evaluation with judge {judge_id} for conversation {conversation_id}")
                    
                    # Get evaluation from judge
                    evaluation = await judge_service.evaluate_conversation(
                        conversation_id=conversation_id,
                        username=username,
                        messages=messages,
                        user_profile=user_profile,
                        agent_id=agent_id
                    )
                    
                    if evaluation:
                        # Log and store raw evaluation response
                        raw_response = json.dumps(evaluation, default=str)
                        logger.info(f"Raw evaluation from {judge_id}: {raw_response}")
                        
                        try:
                            # Check for error messages in the response
                            if any(error_indicator in raw_response.lower() for error_indicator in ["sorry", "error", "unable", "failed"]):
                                logger.warning(f"Error response detected from {judge_id}")
                                judge_eval = JudgeEvaluation(
                                    judge_id=judge_id,
                                    scores=ScoreMetrics(
                                        Personalization=Decimal('0'),
                                        Language_Simplicity=Decimal('0'),
                                        Response_Length=Decimal('0'),
                                        Content_Relevance=Decimal('0'),
                                        Content_Difficulty=Decimal('0')
                                    ),
                                    evaluation_notes={
                                        "summary": "",
                                        "key_insights": "",
                                        "areas_for_improvement": "",
                                        "recommendations": ""
                                    },
                                    judge_metrics=None,
                                    process_status="error",
                                    raw_response=raw_response
                                )
                                logger.info(f"Created error evaluation with stored response: {judge_eval.dict()}")
                                judge_evaluations.append(judge_eval)
                                continue
                            
                            # Create judge evaluation with simplified validation
                            judge_eval = JudgeEvaluation(
                                judge_id=judge_id,
                                scores=ScoreMetrics(
                                    Personalization=evaluation.get("Personalization", Decimal('0')),
                                    Language_Simplicity=evaluation.get("Language_Simplicity", Decimal('0')),
                                    Response_Length=evaluation.get("Response_Length", Decimal('0')),
                                    Content_Relevance=evaluation.get("Content_Relevance", Decimal('0')),
                                    Content_Difficulty=evaluation.get("Content_Difficulty", Decimal('0'))
                                ),
                                evaluation_notes=evaluation.get("evaluation_notes", {}),
                                judge_metrics=None,
                                process_status="success",
                                raw_response=None
                            )
                            logger.info(f"Created successful evaluation for {judge_id}: {judge_eval.dict()}")
                            judge_evaluations.append(judge_eval)
                            
                        except Exception as e:
                            logger.error(f"Error creating evaluation for {judge_id}: {str(e)}")
                            # Create error evaluation but keep multi-agent flow
                            judge_eval = JudgeEvaluation(
                                judge_id=judge_id,
                                scores=ScoreMetrics(
                                    Personalization=Decimal('0'),
                                    Language_Simplicity=Decimal('0'),
                                    Response_Length=Decimal('0'),
                                    Content_Relevance=Decimal('0'),
                                    Content_Difficulty=Decimal('0')
                                ),
                                evaluation_notes={
                                    "summary": "",
                                    "key_insights": "",
                                    "areas_for_improvement": "",
                                    "recommendations": ""
                                },
                                judge_metrics=None,
                                process_status="error",
                                raw_response=raw_response
                            )
                            logger.info(f"Created error evaluation for {judge_id}: {judge_eval.dict()}")
                            judge_evaluations.append(judge_eval)
                            continue
                            
                    else:
                        logger.error(f"No evaluation response from judge {judge_id}")
                        # Create error evaluation but keep multi-agent flow
                        judge_eval = JudgeEvaluation(
                            judge_id=judge_id,
                            scores=ScoreMetrics(
                                Personalization=Decimal('0'),
                                Language_Simplicity=Decimal('0'),
                                Response_Length=Decimal('0'),
                                Content_Relevance=Decimal('0'),
                                Content_Difficulty=Decimal('0')
                            ),
                            evaluation_notes={
                                "summary": "",
                                "key_insights": "",
                                "areas_for_improvement": "",
                                "recommendations": ""
                            },
                            judge_metrics=None,
                            process_status="error",
                            raw_response=None
                        )
                        logger.info(f"Created error evaluation for no response: {judge_eval.dict()}")
                        judge_evaluations.append(judge_eval)
                        
                except Exception as e:
                    logger.error(f"Error with judge {judge_id}: {str(e)}", exc_info=True)
                    # Create error evaluation but keep multi-agent flow
                    judge_eval = JudgeEvaluation(
                        judge_id=judge_id,
                        scores=ScoreMetrics(
                            Personalization=Decimal('0'),
                            Language_Simplicity=Decimal('0'),
                            Response_Length=Decimal('0'),
                            Content_Relevance=Decimal('0'),
                            Content_Difficulty=Decimal('0')
                        ),
                        evaluation_notes={
                            "summary": "",
                            "key_insights": "",
                            "areas_for_improvement": "",
                            "recommendations": ""
                        },
                        judge_metrics=None,
                        process_status="error",
                        raw_response=None
                    )
                    logger.info(f"Created error evaluation for judge error: {judge_eval.dict()}")
                    judge_evaluations.append(judge_eval)
                    continue
            
            if not judge_evaluations:
                logger.error(f"No successful judge evaluations for conversation {conversation_id}")
                return None
            
            # Log successful evaluations summary
            success_count = sum(1 for e in judge_evaluations if e.process_status == "success")
            logger.info(f"Successfully collected evaluations from {success_count} judges")
            
            # Compute usage metrics
            usage_metrics = self._compute_usage_metrics(messages)
            logger.info(f"Computed usage metrics: {usage_metrics.dict() if usage_metrics else None}")
            
            # Compute quiz metrics
            quiz_metrics = self._compute_quiz_metrics(messages)
            logger.info(f"Computed quiz metrics: {quiz_metrics.dict() if quiz_metrics else None}")
            
            # Create final evaluation output
            evaluation_output = DifyEvaluationOutput(
                conversation_id=conversation_id,
                username=username,
                agent_id=agent_id,
                evaluation_timestamp=datetime.utcnow(),
                judge_evaluations=judge_evaluations,
                usage_metrics=usage_metrics,
                quiz_metrics=quiz_metrics
            )
            
            return evaluation_output
            
        except Exception as e:
            logger.error(f"Error in _evaluate_conversation: {str(e)}", exc_info=True)
            return None
            
    def _validate_evaluation_response(self, response: Dict) -> bool:
        """Validate the structure of an evaluation response"""
        try:
            # Required fields for scores
            required_score_fields = [
                "Personalization", "Language_Simplicity", "Response_Length",
                "Content_Relevance", "Content_Difficulty"
            ]
            
            # Check all required score fields are present
            if not all(field in response for field in required_score_fields):
                logger.warning("Missing required score fields in response")
                return False
                
            # Check evaluation_notes structure
            notes = response.get("evaluation_notes", {})
            if not isinstance(notes, dict):
                logger.warning("Evaluation notes is not a dictionary")
                return False
                
            # Verify that all score fields are numeric (can be converted to Decimal)
            for field in required_score_fields:
                try:
                    value = response.get(field)
                    if value is not None:
                        Decimal(str(value))
                except (TypeError, ValueError):
                    logger.warning(f"Invalid numeric value for field {field}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            return False
            
    def _create_error_evaluation(self, judge_id: str, error_message: str, raw_response: Optional[str] = None):
        """Create an error evaluation with proper error handling"""
        return JudgeEvaluation(
            judge_id=judge_id,
            scores=ScoreMetrics(
                Personalization=Decimal('0'),
                Language_Simplicity=Decimal('0'),
                Response_Length=Decimal('0'),
                Content_Relevance=Decimal('0'),
                Content_Difficulty=Decimal('0')
            ),
            evaluation_notes=EvaluationNotes(
                summary="",  # Keep empty, error details go in raw_response
                key_insights="",
                areas_for_improvement="",
                recommendations=""
            ),
            judge_metrics=None,
            process_status="error",
            raw_response=raw_response or error_message  # Store error message in raw_response if no raw_response provided
        )
            
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

    def _compute_quiz_metrics(self, messages: List[Dict]) -> QuizMetrics:
        """Compute quiz metrics from conversation messages"""
        logger.info("Computing quiz metrics from messages")
        if not messages:
            logger.warning("No messages provided for quiz metrics computation")
            return QuizMetrics(quiz_taken=False, quiz_score=Decimal('0'))
            
        try:
            # Find the last message that contains quiz results
            quiz_result = None
            for message in reversed(messages):
                if "quiz_result" in message.get("content", ""):
                    quiz_result = message
                    break
            
            if quiz_result:
                logger.info(f"Found quiz result message: {quiz_result.get('content')}")
                # Extract the quiz score from the message
                quiz_score = quiz_result.get("quiz_score", 0)
                logger.info(f"Extracted quiz score: {quiz_score} (type: {type(quiz_score)})")
                
                # Convert quiz score to Decimal
                try:
                    if isinstance(quiz_score, (int, float)):
                        quiz_score = Decimal(str(quiz_score))
                    elif isinstance(quiz_score, str):
                        quiz_score = Decimal(quiz_score)
                    else:
                        logger.warning(f"Unexpected quiz score type: {type(quiz_score)}, defaulting to 0")
                        quiz_score = Decimal('0')
                except Exception as e:
                    logger.error(f"Error converting quiz score to Decimal: {str(e)}")
                    quiz_score = Decimal('0')
                
                logger.info(f"Converted quiz score to Decimal: {quiz_score}")
                return QuizMetrics(quiz_taken=True, quiz_score=quiz_score)
            else:
                logger.info("No quiz result found in messages")
                return QuizMetrics(quiz_taken=False, quiz_score=Decimal('0'))
        except Exception as e:
            logger.error(f"Error computing quiz metrics: {str(e)}")
            return QuizMetrics(quiz_taken=False, quiz_score=Decimal('0'))

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