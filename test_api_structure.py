#!/usr/bin/env python3

"""
Test the API endpoint structure and imports
"""

import sys
sys.path.insert(0, '/home/maf/maf/Dask/AIBI/backend')

def test_api_imports():
    """Test that all API components import correctly"""
    
    print("🧪 Testing API Endpoint Structure")
    print("=" * 50)
    
    try:
        # Test conversation memory import
        from app.services.conversation_memory_service import conversation_memory
        print("✅ ConversationMemoryService imported successfully")
        
        # Test other required services
        from app.services.enhanced_data_ingestion import EnhancedDataIngestionService
        print("✅ EnhancedDataIngestionService imported successfully")
        
        from app.services.enhanced_llm_service import EnhancedLLMService
        print("✅ EnhancedLLMService imported successfully")
        
        from app.services.advanced_analysis_service import AdvancedAnalysisService
        print("✅ AdvancedAnalysisService imported successfully")
        
        # Test API endpoint imports
        print("\n📡 Testing API endpoint structure...")
        
        # Read the conversational endpoint to check structure
        with open('/home/maf/maf/Dask/AIBI/backend/app/api/v1/endpoints/conversational.py', 'r') as f:
            content = f.read()
        
        # Check for key components
        checks = [
            ('conversation_memory import', 'from app.services.conversation_memory_service import conversation_memory'),
            ('/analyze endpoint', '@router.post("/analyze")'),
            ('/continue endpoint', '@router.post("/continue")'),
            ('conversation creation', 'conversation_memory.create_conversation'),
            ('message addition', 'conversation_memory.add_message'),
            ('context retrieval', 'conversation_memory.get_conversation_context'),
            ('conversation context param', 'conversation_context=conversation_context')
        ]
        
        for check_name, check_text in checks:
            if check_text in content:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
        
        print("\n🎉 API structure verification complete!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_api_imports()