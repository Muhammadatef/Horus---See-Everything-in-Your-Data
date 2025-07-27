"""
Conversation Memory Service for maintaining chat history like ChatGPT
Stores messages, context, and data analysis results for sequential conversations
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import redis
import os

logger = logging.getLogger(__name__)

class ConversationMemoryService:
    """
    Manages conversation history and context for sequential chat sessions
    Like ChatGPT, maintains memory of previous questions and answers
    Uses Redis for persistent storage across service restarts
    """
    
    def __init__(self):
        # Connect to Redis for persistent conversation storage
        self.redis_client = None
        self.use_redis = True
        
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            logger.info("Connected to Redis for conversation memory")
        except Exception as e:
            logger.warning(f"Redis not available, using in-memory storage: {e}")
            self.use_redis = False
            self.conversations: Dict[str, Dict] = {}  # Fallback to in-memory
        
        self.max_history_length = 20  # Keep last 20 messages
        self.max_conversation_age_hours = 24  # Auto-cleanup after 24 hours
        self.redis_prefix = "horus:conversation:"
    
    def create_conversation(self, user_id: str, file_info: Dict[str, Any] = None) -> str:
        """Create a new conversation session"""
        conversation_id = str(uuid.uuid4())
        
        conversation_data = {
            'id': conversation_id,
            'user_id': user_id,
            'created_at': datetime.now().isoformat(),
            'last_activity': datetime.now().isoformat(),
            'file_info': file_info,  # Info about uploaded file
            'data_schema': None,     # Schema of the uploaded data
            'data_summary': None,    # Statistical summary of data
            'messages': [],          # Conversation history
            'context': {
                'topics_discussed': [],
                'analysis_performed': [],
                'insights_found': []
            }
        }
        
        self._store_conversation(conversation_id, conversation_data)
        
        logger.info(f"Created new conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    def add_message(self, conversation_id: str, role: str, content: str, 
                   analysis_results: Dict = None, visualization: Dict = None) -> bool:
        """Add a message to the conversation history"""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return False
        
        message = {
            'id': str(uuid.uuid4()),
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'analysis_results': analysis_results,
            'visualization': visualization
        }
        
        conversation['messages'].append(message)
        conversation['last_activity'] = datetime.now().isoformat()
        
        # Update conversation context
        if role == 'user':
            self._update_context_from_user_message(conversation, content)
        elif role == 'assistant' and analysis_results:
            self._update_context_from_analysis(conversation, analysis_results)
        
        # Keep only recent messages to avoid memory bloat
        if len(conversation['messages']) > self.max_history_length:
            conversation['messages'] = conversation['messages'][-self.max_history_length:]
        
        # Store updated conversation
        self._store_conversation(conversation_id, conversation)
        
        logger.info(f"Added {role} message to conversation {conversation_id}")
        return True
    
    def get_conversation_history(self, conversation_id: str, last_n_messages: int = 10) -> List[Dict]:
        """Get recent conversation history for context"""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation['messages']
        return messages[-last_n_messages:] if messages else []
    
    def get_conversation_context(self, conversation_id: str) -> Dict[str, Any]:
        """Get conversation context for LLM prompting"""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return {}
        
        # Build context summary
        recent_messages = self.get_conversation_history(conversation_id, 5)
        
        context = {
            'conversation_id': conversation_id,
            'file_info': conversation.get('file_info', {}),
            'data_schema': conversation.get('data_schema'),
            'data_summary': conversation.get('data_summary'),
            'recent_messages': recent_messages,
            'topics_discussed': conversation['context']['topics_discussed'],
            'analysis_performed': conversation['context']['analysis_performed'],
            'insights_found': conversation['context']['insights_found']
        }
        
        return context
    
    def update_data_context(self, conversation_id: str, schema: Dict, data_summary: Dict) -> bool:
        """Update the data context for the conversation"""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation['data_schema'] = schema
        conversation['data_summary'] = data_summary
        
        # Store updated conversation
        self._store_conversation(conversation_id, conversation)
        
        logger.info(f"Updated data context for conversation {conversation_id}")
        return True
    
    def format_conversation_for_llm(self, conversation_id: str) -> str:
        """Format conversation history for LLM context"""
        context = self.get_conversation_context(conversation_id)
        
        if not context:
            return ""
        
        # Build formatted conversation history
        history_parts = []
        
        # Add file context if available
        if context.get('file_info'):
            file_info = context['file_info']
            history_parts.append(f"[DATA FILE: {file_info.get('filename', 'unknown')} with {file_info.get('total_rows', 0)} rows]")
        
        # Add recent conversation
        recent_messages = context.get('recent_messages', [])
        for msg in recent_messages:
            role = msg['role'].upper()
            content = msg['content']
            history_parts.append(f"{role}: {content}")
        
        # Add context about what's been discussed
        if context.get('topics_discussed'):
            topics = ', '.join(context['topics_discussed'][-5:])  # Last 5 topics
            history_parts.append(f"[TOPICS DISCUSSED: {topics}]")
        
        return "\n".join(history_parts)
    
    def _update_context_from_user_message(self, conversation: Dict, message: str) -> None:
        """Extract topics and context from user messages"""
        message_lower = message.lower()
        
        # Identify topics being discussed
        topics = []
        if any(word in message_lower for word in ['price', 'cost', 'money']):
            topics.append('pricing')
        if any(word in message_lower for word in ['quantity', 'amount', 'count']):
            topics.append('quantities')
        if any(word in message_lower for word in ['rating', 'score', 'review']):
            topics.append('ratings')
        if any(word in message_lower for word in ['category', 'type', 'group']):
            topics.append('categories')
        if any(word in message_lower for word in ['correlation', 'relationship']):
            topics.append('correlations')
        if any(word in message_lower for word in ['trend', 'time', 'over time']):
            topics.append('trends')
        
        # Add unique topics
        for topic in topics:
            if topic not in conversation['context']['topics_discussed']:
                conversation['context']['topics_discussed'].append(topic)
    
    def _update_context_from_analysis(self, conversation: Dict, analysis_results: Dict) -> None:
        """Extract insights from analysis results"""
        
        # Track what analysis was performed
        if 'statistical_overview' in analysis_results:
            if 'statistical_analysis' not in conversation['context']['analysis_performed']:
                conversation['context']['analysis_performed'].append('statistical_analysis')
        
        if 'correlation' in analysis_results:
            if 'correlation_analysis' not in conversation['context']['analysis_performed']:
                conversation['context']['analysis_performed'].append('correlation_analysis')
        
        if 'clustering' in analysis_results:
            if 'clustering_analysis' not in conversation['context']['analysis_performed']:
                conversation['context']['analysis_performed'].append('clustering_analysis')
        
        # Extract key insights
        if 'correlation' in analysis_results:
            strong_corrs = analysis_results['correlation'].get('strong_correlations', [])
            for corr in strong_corrs[:2]:  # Top 2 correlations
                insight = f"{corr['variable1']} and {corr['variable2']} are {corr['strength']} correlated"
                if insight not in conversation['context']['insights_found']:
                    conversation['context']['insights_found'].append(insight)
    
    def cleanup_old_conversations(self) -> int:
        """Remove old conversations to free memory"""
        cutoff_time = datetime.now().timestamp() - (self.max_conversation_age_hours * 3600)
        
        to_remove = []
        for conv_id, conversation in self.conversations.items():
            created_at = datetime.fromisoformat(conversation['created_at']).timestamp()
            if created_at < cutoff_time:
                to_remove.append(conv_id)
        
        for conv_id in to_remove:
            del self.conversations[conv_id]
        
        logger.info(f"Cleaned up {len(to_remove)} old conversations")
        return len(to_remove)
    
    def _store_conversation(self, conversation_id: str, conversation_data: Dict) -> None:
        """Store conversation data (Redis or in-memory)"""
        if self.use_redis and self.redis_client:
            try:
                key = f"{self.redis_prefix}{conversation_id}"
                self.redis_client.set(key, json.dumps(conversation_data))
                # Set expiration
                self.redis_client.expire(key, self.max_conversation_age_hours * 3600)
            except Exception as e:
                logger.error(f"Failed to store conversation in Redis: {e}")
                # Fallback to in-memory
                self.conversations[conversation_id] = conversation_data
        else:
            self.conversations[conversation_id] = conversation_data
    
    def _load_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Load conversation data (Redis or in-memory)"""
        if self.use_redis and self.redis_client:
            try:
                key = f"{self.redis_prefix}{conversation_id}"
                data = self.redis_client.get(key)
                if data:
                    return json.loads(data)
            except Exception as e:
                logger.error(f"Failed to load conversation from Redis: {e}")
        
        # Fallback to in-memory or if Redis fails
        return self.conversations.get(conversation_id)
    
    def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get a summary of the conversation for debugging"""
        conversation = self._load_conversation(conversation_id)
        if not conversation:
            return {}
        
        return {
            'id': conversation_id,
            'message_count': len(conversation['messages']),
            'created_at': conversation['created_at'],
            'last_activity': conversation['last_activity'],
            'file_name': conversation.get('file_info', {}).get('filename'),
            'topics_discussed': conversation['context']['topics_discussed'],
            'analysis_performed': conversation['context']['analysis_performed']
        }

# Global instance
conversation_memory = ConversationMemoryService()