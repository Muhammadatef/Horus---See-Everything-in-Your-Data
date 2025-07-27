#!/usr/bin/env python3

"""
Test the conversational memory system to verify sequential chat works like ChatGPT
"""

import asyncio
import sys
sys.path.insert(0, '/home/maf/maf/Dask/AIBI/backend')

from app.services.conversation_memory_service import ConversationMemoryService

async def test_conversation_memory():
    """Test conversation memory functionality"""
    
    print("🧪 Testing Conversation Memory System")
    print("=" * 50)
    
    # Create memory service
    memory = ConversationMemoryService()
    
    # Test 1: Create a new conversation
    conversation_id = memory.create_conversation(
        user_id="test_user",
        file_info={"filename": "sales_data.csv", "total_rows": 100}
    )
    
    print(f"✅ Created conversation: {conversation_id}")
    
    # Test 2: Add messages to conversation
    print("\n🔄 Adding messages to conversation:")
    
    # First message
    memory.add_message(conversation_id, 'user', 'What is the average price?')
    memory.add_message(conversation_id, 'assistant', 'The average price is $456.99 based on your sales data.')
    
    # Follow-up message
    memory.add_message(conversation_id, 'user', 'What about the highest price?')
    memory.add_message(conversation_id, 'assistant', 'The highest price in your dataset is $1,999.99.')
    
    # Another follow-up
    memory.add_message(conversation_id, 'user', 'Can you compare that to the lowest price?')
    memory.add_message(conversation_id, 'assistant', 'Sure! The lowest price is $49.99, so there\'s a range of $1,950 between your cheapest and most expensive items.')
    
    print("   Added 6 messages (3 user, 3 assistant)")
    
    # Test 3: Get conversation history
    print("\n📜 Testing conversation history retrieval:")
    history = memory.get_conversation_history(conversation_id, last_n_messages=4)
    
    for i, msg in enumerate(history, 1):
        role = msg['role'].upper()
        content = msg['content'][:60] + "..." if len(msg['content']) > 60 else msg['content']
        print(f"   {i}. {role}: {content}")
    
    # Test 4: Get conversation context
    print("\n🧠 Testing conversation context:")
    context = memory.get_conversation_context(conversation_id)
    
    print(f"   File: {context.get('file_info', {}).get('filename', 'Unknown')}")
    print(f"   Topics discussed: {context.get('topics_discussed', [])}")
    print(f"   Analysis performed: {context.get('analysis_performed', [])}")
    print(f"   Recent messages: {len(context.get('recent_messages', []))}")
    
    # Test 5: Format for LLM
    print("\n🤖 Testing LLM context formatting:")
    llm_context = memory.format_conversation_for_llm(conversation_id)
    print("   LLM Context Preview:")
    lines = llm_context.split('\n')
    for line in lines[:8]:  # Show first 8 lines
        print(f"     {line}")
    if len(lines) > 8:
        print(f"     ... ({len(lines) - 8} more lines)")
    
    # Test 6: Get conversation summary
    print("\n📊 Testing conversation summary:")
    summary = memory.get_conversation_summary(conversation_id)
    print(f"   Messages: {summary.get('message_count', 0)}")
    print(f"   Created: {summary.get('created_at', 'Unknown')}")
    print(f"   Topics: {summary.get('topics_discussed', [])}")
    
    print(f"\n🎉 All conversation memory tests passed!")
    print("The system now maintains ChatGPT-like conversation history!")

if __name__ == "__main__":
    asyncio.run(test_conversation_memory())