#!/usr/bin/env python3
"""
Manual test of the enhanced response system to verify specific data answers
"""

import pandas as pd
import asyncio
import json

# Simulate the data processing that happens in the conversational endpoint
def test_response_system():
    """Test the response system with our test data"""
    
    # Load the test data
    df = pd.read_csv('/home/maf/maf/Dask/AIBI/test_data.csv')
    
    print("🧪 Testing Enhanced Analysis System Response Logic")
    print("=" * 60)
    print(f"📊 Test Data: {len(df)} rows, columns: {list(df.columns)}")
    print()
    
    # Calculate expected values from our test data
    expected_values = {
        'average_price': df['price'].mean(),
        'max_price': df['price'].max(),
        'min_price': df['price'].min(),
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'total_quantity': df['quantity'].sum(),
        'highest_rating_product': df.loc[df['rating'].idxmax()]['product_name'],
        'highest_rating_value': df['rating'].max(),
        'electronics_count': len(df[df['category'] == 'Electronics'])
    }
    
    print("📈 Expected Values from Test Data:")
    print(f"   • Average Price: ${expected_values['average_price']:.2f}")
    print(f"   • Max Price: ${expected_values['max_price']:.2f}")
    print(f"   • Min Price: ${expected_values['min_price']:.2f}")
    print(f"   • Total Products: {expected_values['total_rows']}")
    print(f"   • Total Quantity: {expected_values['total_quantity']}")
    print(f"   • Highest Rated Product: {expected_values['highest_rating_product']} ({expected_values['highest_rating_value']})")
    print(f"   • Electronics Products: {expected_values['electronics_count']}")
    print()
    
    # Simulate the advanced analysis results structure
    mock_analysis_results = {
        'statistical_overview': {
            'descriptive_stats': {
                'summary': {
                    'price': {
                        'mean': expected_values['average_price'],
                        'min': expected_values['min_price'],
                        'max': expected_values['max_price'],
                        'std': df['price'].std()
                    },
                    'quantity': {
                        'mean': df['quantity'].mean(),
                        'min': df['quantity'].min(),
                        'max': df['quantity'].max(),
                        'sum': expected_values['total_quantity']
                    },
                    'rating': {
                        'mean': df['rating'].mean(),
                        'min': df['rating'].min(),
                        'max': expected_values['highest_rating_value']
                    }
                }
            },
            'categorical_analysis': {
                'category': {
                    'unique_values': df['category'].nunique(),
                    'most_common': df['category'].value_counts().to_dict()
                }
            }
        }
    }
    
    file_info = {
        'filename': 'test_data.csv',
        'total_rows': expected_values['total_rows'],
        'columns': expected_values['total_columns']
    }
    
    # Test different question patterns
    test_questions = [
        "What is the average price?",
        "What is the highest price?", 
        "What is the lowest price?",
        "How many products do we have?",
        "What's the total quantity of all products?",
        "Which product has the highest rating?",
        "Show me a histogram",
        "What correlations exist?",
        "Show me products in Electronics category"
    ]
    
    print("🔍 Testing Question Response Logic:")
    print("=" * 60)
    
    for question in test_questions:
        print(f"\n❓ Question: '{question}'")
        
        # Simulate the fallback logic from enhanced_llm_service.py
        response = generate_fallback_response(question, mock_analysis_results, file_info)
        print(f"📝 Response: {response}")
        
        # Verify the response contains expected data
        verify_response(question, response, expected_values)
        print("-" * 40)

def generate_fallback_response(question: str, analysis_results: dict, file_info: dict) -> str:
    """Simulate the _generate_question_specific_fallback method"""
    question_lower = question.lower()
    
    # Extract statistical data for specific answers
    stats = analysis_results.get('statistical_overview', {}).get('descriptive_stats', {}).get('summary', {})
    
    if any(word in question_lower for word in ['average', 'mean']) and 'price' in question_lower:
        if 'price' in stats:
            price_mean = stats['price']['mean']
            return f"The **average price** of products in your dataset is **${price_mean:.2f}**. The prices range from ${stats['price']['min']:.2f} to ${stats['price']['max']:.2f}, showing a good spread across different price points."
    
    elif any(word in question_lower for word in ['highest', 'maximum', 'max', 'most expensive']):
        if 'price' in stats:
            max_price = stats['price']['max']
            return f"The **highest price** in your dataset is **${max_price:.2f}**. This represents the premium end of your product range."
    
    elif any(word in question_lower for word in ['lowest', 'minimum', 'min', 'cheapest']):
        if 'price' in stats:
            min_price = stats['price']['min']
            return f"The **lowest price** in your dataset is **${min_price:.2f}**. This represents the most affordable option in your product range."
    
    elif any(word in question_lower for word in ['how many', 'count', 'total']) and not 'quantity' in question_lower:
        return f"Your dataset contains **{file_info['total_rows']} records** across **{file_info['columns']} columns**. This gives you a comprehensive view of your data volume."
    
    elif 'quantity' in question_lower and any(word in question_lower for word in ['total', 'sum']):
        if 'quantity' in stats:
            total_qty = stats['quantity']['sum']
            return f"The **total quantity** of all products in your dataset is **{total_qty} units**. This represents your complete inventory count."
    
    elif any(word in question_lower for word in ['highest', 'best']) and 'rating' in question_lower:
        if 'rating' in stats:
            max_rating = stats['rating']['max']
            return f"The **highest rating** in your dataset is **{max_rating}**. This represents your top-rated product."
    
    elif any(word in question_lower for word in ['histogram', 'distribution']):
        return f"I've created a histogram showing the distribution of your data. This visualization reveals the frequency patterns and helps identify common value ranges in your dataset."
    
    elif any(word in question_lower for word in ['correlation', 'relationship']):
        return f"I can analyze correlations between numerical variables in your data. This helps identify relationships between price, quantity, ratings, and other metrics."
    
    elif 'electronics' in question_lower:
        return f"I found products in the Electronics category in your dataset. Let me show you the breakdown and analysis for this category."
    
    else:
        return f"I've analyzed your **{file_info.get('filename', 'data')}** file. Let me provide specific insights about: {question}"

def verify_response(question: str, response: str, expected_values: dict):
    """Verify if the response contains the expected data values"""
    question_lower = question.lower()
    
    if 'average price' in question_lower:
        expected_price = f"${expected_values['average_price']:.2f}"
        if expected_price in response:
            print(f"✅ PASS: Contains expected average price {expected_price}")
        else:
            print(f"❌ FAIL: Expected {expected_price}, not found in response")
    
    elif 'highest price' in question_lower:
        expected_price = f"${expected_values['max_price']:.2f}"
        if expected_price in response:
            print(f"✅ PASS: Contains expected max price {expected_price}")
        else:
            print(f"❌ FAIL: Expected {expected_price}, not found in response")
    
    elif 'lowest price' in question_lower:
        expected_price = f"${expected_values['min_price']:.2f}"
        if expected_price in response:
            print(f"✅ PASS: Contains expected min price {expected_price}")
        else:
            print(f"❌ FAIL: Expected {expected_price}, not found in response")
    
    elif 'how many' in question_lower or 'count' in question_lower:
        expected_count = str(expected_values['total_rows'])
        if expected_count in response:
            print(f"✅ PASS: Contains expected count {expected_count}")
        else:
            print(f"❌ FAIL: Expected {expected_count}, not found in response")
    
    elif 'total quantity' in question_lower:
        expected_qty = str(expected_values['total_quantity'])
        if expected_qty in response:
            print(f"✅ PASS: Contains expected total quantity {expected_qty}")
        else:
            print(f"❌ FAIL: Expected {expected_qty}, not found in response")
    
    else:
        print(f"ℹ️  INFO: Response generated for question type")

if __name__ == "__main__":
    test_response_system()