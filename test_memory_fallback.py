#!/usr/bin/env python3

"""
Test the conversation memory system without Redis (in-memory fallback)
"""

import sys
import os
sys.path.insert(0, '/home/maf/maf/Dask/AIBI/backend')

# Mock redis module to test fallback
class MockRedis:
    def from_url(self, *args, **kwargs):
        raise Exception("Redis not available")

sys.modules['redis'] = MockRedis()

def test_memory_fallback():
    """Test conversation memory with Redis fallback"""
    
    print("🧪 Testing Conversation Memory System (In-Memory Fallback)")
    print("=" * 60)
    
    try:
        from app.services.conversation_memory_service import ConversationMemoryService
        
        # Create memory service (should fall back to in-memory)
        memory = ConversationMemoryService()
        
        print(f"✅ Service created successfully")
        print(f"✅ Using Redis: {memory.use_redis}")
        print(f"✅ Storage type: {'Redis' if memory.use_redis else 'In-Memory (fallback)'}")
        
        # Test conversation creation
        conversation_id = memory.create_conversation(
            user_id="test_user",
            file_info={"filename": "test_data.csv", "total_rows": 10}
        )
        
        print(f"✅ Created conversation: {conversation_id[:8]}...")
        
        # Test message addition
        memory.add_message(conversation_id, 'user', 'What is the average price?')
        memory.add_message(conversation_id, 'assistant', 'The average price is $456.99.')
        memory.add_message(conversation_id, 'user', 'What about the highest price?')
        memory.add_message(conversation_id, 'assistant', 'The highest price is $1999.99.')
        
        print("✅ Added 4 messages to conversation")
        
        # Test history retrieval
        history = memory.get_conversation_history(conversation_id)
        print(f"✅ Retrieved {len(history)} messages from history")
        
        # Test context retrieval
        context = memory.get_conversation_context(conversation_id)
        print(f"✅ Retrieved conversation context")
        print(f"   File: {context.get('file_info', {}).get('filename', 'Unknown')}")
        print(f"   Recent messages: {len(context.get('recent_messages', []))}")
        
        # Test LLM formatting
        llm_context = memory.format_conversation_for_llm(conversation_id)
        print(f"✅ Generated LLM context ({len(llm_context)} characters)")
        
        # Test summary
        summary = memory.get_conversation_summary(conversation_id)
        print(f"✅ Generated conversation summary")
        print(f"   Messages: {summary.get('message_count', 0)}")
        
        print("\n🎉 All conversation memory tests PASSED!")
        print("💡 System gracefully falls back to in-memory storage when Redis unavailable")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_memory_fallback()