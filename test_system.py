#!/usr/bin/env python3

"""
Test script to verify the enhanced analysis system responds correctly to user questions
"""

import os
import sys
import tempfile
import pandas as pd

# Add the backend directory to the path
sys.path.insert(0, '/home/maf/maf/Dask/AIBI/backend')

from app.services.enhanced_data_ingestion import EnhancedDataIngestionService
from app.services.enhanced_llm_service import EnhancedLLMService
from app.services.advanced_analysis_service import AdvancedAnalysisService

async def test_question_response():
    """Test if the system provides specific answers to user questions"""
    
    # Load test data
    test_file = '/home/maf/maf/Dask/AIBI/test_data.csv'
    
    # Initialize services
    ingestion_service = EnhancedDataIngestionService()
    llm_service = EnhancedLLMService()
    advanced_analysis = AdvancedAnalysisService()
    
    # Test questions to verify specific responses
    test_questions = [
        "What is the average price?",
        "How many products do we have?",
        "Which product has the highest rating?",
        "What's the total quantity of all products?",
        "Show me products in the Electronics category",
        "What is the correlation between price and rating?"
    ]
    
    print("🧪 Testing Enhanced Analysis System")
    print("=" * 50)
    
    # Process the test file
    source_config = {
        'source_type': 'file',
        'source': test_file,
        'options': {'format': 'csv'}
    }
    
    try:
        df = await ingestion_service._process_file_source(source_config)
        schema = await ingestion_service._generate_enhanced_schema(df, source_config)
        all_data = df.to_dict('records')
        
        print(f"📊 Loaded {len(df)} rows with columns: {list(df.columns)}")
        print()
        
        # Test each question
        for i, question in enumerate(test_questions, 1):
            print(f"🔍 Test {i}: {question}")
            print("-" * 30)
            
            # Perform advanced analysis
            advanced_results = await advanced_analysis.analyze_with_sophistication(
                data=all_data,
                question=question,
                schema=schema
            )
            
            # Generate response
            answer = await llm_service._generate_advanced_conversational_response(
                question=question,
                advanced_analysis_results=advanced_results,
                schema=schema,
                file_info={
                    'filename': 'test_data.csv',
                    'total_rows': len(df),
                    'columns': len(df.columns)
                }
            )
            
            print(f"📝 Answer: {answer}")
            print()
            
            # Verify the answer contains specific data
            if "average price" in question.lower():
                avg_price = df['price'].mean()
                print(f"✅ Expected average price: ${avg_price:.2f}")
                
            elif "how many products" in question.lower():
                total_products = len(df)
                print(f"✅ Expected count: {total_products} products")
                
            elif "highest rating" in question.lower():
                max_rating_product = df.loc[df['rating'].idxmax()]
                print(f"✅ Expected: {max_rating_product['product_name']} with rating {max_rating_product['rating']}")
                
            elif "total quantity" in question.lower():
                total_qty = df['quantity'].sum()
                print(f"✅ Expected total quantity: {total_qty}")
                
            print("=" * 50)
            
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import asyncio
    asyncio.run(test_question_response())