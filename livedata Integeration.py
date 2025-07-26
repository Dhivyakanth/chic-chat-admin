import base64
import google.generativeai as genai
# from google.generativeai import types  # No longer needed
from config import Config
import os
import sys
import re
import difflib
import requests
import io
import csv
from datetime import datetime, timedelta
import calendar
from collections import defaultdict


def fetch_sales_data_from_api():
    """Fetch sales data from the provided API endpoint and return as a list of records."""
    url = "http://54.234.201.60:5000/chat/getFormData"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == 200 and "formData" in data:
            return data["formData"]
        else:
            raise ValueError(f"API returned unexpected response: {data}")
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return []

def is_sales_related_question(question):
    """Check if the question is related to sales data analysis, allowing for fuzzy keyword matches AND checking against live API data."""
    sales_keywords = [
        'record','dress','sales', 'trend', 'predict', 'forecast', 'quantity', 'rate', 'revenue',
        'agent', 'customer', 'weave', 'linen', 'satin', 'denim', 'crepe', 'twill',
        'premium', 'standard', 'economy', 'cotton', 'polyester', 'spandex',
        'order', 'status', 'confirmed', 'pending', 'cancelled', 'growth',
        'performance', 'top', 'best', 'most', 'sold', 'item', 'product',
        'month', 'year', 'quarter', 'period', 'analysis', 'data','id','date',
        # Add common misspellings and variations
        'quality', 'kolity', 'qualety', 'qaulity', 'qulaity',
        'composition', 'komposition', 'kumposison', 'composision',
        # Agent names from the CSV data
        'priya', 'sowmiya', 'mukilan', 'karthik',
        # Customer names from the CSV data
        'alice', 'smith', 'ravi', 'qilyze', 'jhon'
    ]
    question_lower = question.lower()
    words = question_lower.split()
    
    # First check: keyword matching with more lenient fuzzy matching
    for word in words:
        # Fuzzy match with lower cutoff for better misspelling detection
        matches = difflib.get_close_matches(word, sales_keywords, n=1, cutoff=0.6)
        if matches:
            return True
    # Substring match (for multi-word keywords or partials)
    for keyword in sales_keywords:
        if keyword in question_lower:
            return True
    
    # Second check: check against live API data
    try:
        sales_data = fetch_sales_data_from_api()
        if sales_data:
            # Extract all unique values from the API data
            api_keywords = set()
            for record in sales_data:
                # Add agent names
                if 'agentName' in record and record['agentName']:
                    api_keywords.add(record['agentName'].lower().strip())
                # Add customer names
                if 'customerName' in record and record['customerName']:
                    api_keywords.add(record['customerName'].lower().strip())
                # Add weave types
                if 'weave' in record and record['weave']:
                    api_keywords.add(record['weave'].lower().strip())
                # Add quality types
                if 'quality' in record and record['quality']:
                    api_keywords.add(record['quality'].lower().strip())
                # Add composition data
                if 'composition' in record and record['composition']:
                    api_keywords.add(record['composition'].lower().strip())
                # Add status data
                if 'status' in record and record['status']:
                    api_keywords.add(record['status'].lower().strip())
            
            # Check if any word in the question matches API data
            for word in words:
                # Direct match
                if word in api_keywords:
                    return True
                # Fuzzy match with API data
                matches = difflib.get_close_matches(word, list(api_keywords), n=1, cutoff=0.75)
                if matches:
                    return True
    except Exception as e:
        # If API fails, fall back to keyword-only checking
        print(f"API check failed, using keyword-only: {e}")
        pass
    
    return False

def correct_misspellings(text):
    """Correct common misspellings in the text"""
    corrections = {
        'kolity': 'quality',
        'qualety': 'quality',
        'qaulity': 'quality',
        'qulaity': 'quality',
        'kumposison': 'composition',
        'komposition': 'composition',
        'composision': 'composition',
        'weav': 'weave',
        'weev': 'weave',
        'agnet': 'agent',
        'cusomer': 'customer',
        'custmer': 'customer',
        'salse': 'sales',
        'seles': 'sales',
        'preium': 'premium',
        'standrd': 'standard',
        'econmy': 'economy'
    }
    
    corrected_text = text.lower()
    for misspelling, correction in corrections.items():
        corrected_text = corrected_text.replace(misspelling, correction)
    
    return corrected_text

def analyze_historical_trends(sales_data):
    """Analyze historical trends from sales data for prediction"""
    if not sales_data:
        return {}
    
    monthly_data = defaultdict(lambda: {
        'total_quantity': 0,
        'total_revenue': 0,
        'order_count': 0,
        'weave_types': defaultdict(int),
        'compositions': defaultdict(int),
        'qualities': defaultdict(int)
    })
    
    # Group data by month
    for record in sales_data:
        try:
            # Parse date
            date_str = record.get('date', '')
            if date_str:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                month_key = f"{date_obj.year}-{date_obj.month:02d}"
                
                # Aggregate data
                quantity = float(record.get('quantity', 0))
                rate = float(record.get('rate', 0))
                revenue = quantity * rate
                
                monthly_data[month_key]['total_quantity'] += quantity
                monthly_data[month_key]['total_revenue'] += revenue
                monthly_data[month_key]['order_count'] += 1
                
                # Track categories
                weave = record.get('weave', '').lower().strip()
                composition = record.get('composition', '').lower().strip()
                quality = record.get('quality', '').lower().strip()
                
                if weave:
                    monthly_data[month_key]['weave_types'][weave] += quantity
                if composition:
                    monthly_data[month_key]['compositions'][composition] += quantity
                if quality:
                    monthly_data[month_key]['qualities'][quality] += quantity
                    
        except (ValueError, TypeError):
            continue
    
    return monthly_data

def calculate_growth_rates(monthly_data):
    """Calculate month-over-month growth rates"""
    sorted_months = sorted(monthly_data.keys())
    growth_rates = {}
    
    for i in range(1, len(sorted_months)):
        prev_month = sorted_months[i-1]
        curr_month = sorted_months[i]
        
        prev_qty = monthly_data[prev_month]['total_quantity']
        curr_qty = monthly_data[curr_month]['total_quantity']
        
        if prev_qty > 0:
            growth_rate = ((curr_qty - prev_qty) / prev_qty) * 100
            growth_rates[curr_month] = growth_rate
        else:
            growth_rates[curr_month] = 0
    
    return growth_rates

def predict_future_sales(target_date_str, sales_data):
    """Predict sales for a future date based on historical trends"""
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        target_month = f"{target_date.year}-{target_date.month:02d}"
        
        # Analyze historical data
        monthly_data = analyze_historical_trends(sales_data)
        growth_rates = calculate_growth_rates(monthly_data)
        
        if not monthly_data:
            return {
                'error': 'Insufficient historical data for prediction',
                'prediction': 0,
                'confidence': 'Low'
            }
        
        # Calculate average monthly metrics
        total_months = len(monthly_data)
        avg_quantity = sum(data['total_quantity'] for data in monthly_data.values()) / total_months
        avg_revenue = sum(data['total_revenue'] for data in monthly_data.values()) / total_months
        avg_orders = sum(data['order_count'] for data in monthly_data.values()) / total_months
        
        # Calculate average growth rate
        if growth_rates:
            avg_growth_rate = sum(growth_rates.values()) / len(growth_rates)
        else:
            avg_growth_rate = 5.0  # Default 5% growth assumption
        
        # Seasonal adjustment based on historical same-month data
        target_month_num = target_date.month
        historical_same_months = []
        
        for month_key, data in monthly_data.items():
            year, month = month_key.split('-')
            if int(month) == target_month_num:
                historical_same_months.append(data['total_quantity'])
        
        seasonal_factor = 1.0
        if historical_same_months:
            seasonal_avg = sum(historical_same_months) / len(historical_same_months)
            seasonal_factor = seasonal_avg / avg_quantity if avg_quantity > 0 else 1.0
        
        # Calculate months into future
        latest_month = max(monthly_data.keys())
        latest_date = datetime.strptime(latest_month + '-01', '%Y-%m-%d')
        months_ahead = (target_date.year - latest_date.year) * 12 + (target_date.month - latest_date.month)
        
        # Apply compound growth
        growth_multiplier = (1 + avg_growth_rate/100) ** months_ahead
        
        # Calculate predictions
        predicted_quantity = avg_quantity * seasonal_factor * growth_multiplier
        predicted_revenue = avg_revenue * seasonal_factor * growth_multiplier
        predicted_orders = avg_orders * seasonal_factor * growth_multiplier
        
        # Determine confidence level
        confidence = 'High' if months_ahead <= 6 else 'Medium' if months_ahead <= 12 else 'Low'
        
        return {
            'target_date': target_date_str,
            'predicted_quantity': round(predicted_quantity, 2),
            'predicted_revenue': round(predicted_revenue, 2),
            'predicted_orders': round(predicted_orders),
            'avg_growth_rate': round(avg_growth_rate, 2),
            'seasonal_factor': round(seasonal_factor, 2),
            'confidence': confidence,
            'months_ahead': months_ahead,
            'historical_months': total_months
        }
        
    except Exception as e:
        return {
            'error': f'Prediction error: {str(e)}',
            'prediction': 0,
            'confidence': 'Low'
        }

def is_prediction_question(question):
    """Check if the question is asking for future predictions"""
    prediction_keywords = [
        'predict', 'forecast', 'future', 'will be', 'next year', 'next month',
        '2026', '2027', '2028', 'upcoming', 'expected', 'projection'
    ]
    q_lower = question.lower()
    return any(keyword in q_lower for keyword in prediction_keywords)

def extract_prediction_date(question):
    """Extract target date from prediction question"""
    # Look for year patterns
    year_pattern = r'(202[6-9]|20[3-9]\d)'
    year_match = re.search(year_pattern, question)
    
    # Look for month patterns
    month_patterns = {
        'january': 1, 'jan': 1, 'february': 2, 'feb': 2, 'march': 3, 'mar': 3,
        'april': 4, 'apr': 4, 'may': 5, 'june': 6, 'jun': 6,
        'july': 7, 'jul': 7, 'august': 8, 'aug': 8, 'september': 9, 'sep': 9,
        'october': 10, 'oct': 10, 'november': 11, 'nov': 11, 'december': 12, 'dec': 12
    }
    
    q_lower = question.lower()
    month_num = None
    for month_name, num in month_patterns.items():
        if month_name in q_lower:
            month_num = num
            break
    
    # Default values
    target_year = year_match.group(1) if year_match else '2026'
    target_month = month_num if month_num else 6  # Default to June
    
    return f"{target_year}-{target_month:02d}-15"  # Use 15th of the month

def generate_response(user_question, chat_history=None, followup_flag=False):
    try:
        # --- Smart Context Analysis ---
        def is_followup_question(q):
            """Check if question is a follow-up to the immediate previous question"""
            followup_phrases = [
                'only in', 'what about', 'how about', 'and for', 'show me', 'can you', 'do it', 
                'yes', 'change it', 'ok', 'go ahead', 'then', 'next', 'now', 'also', 
                'give me', 'tell me', 'show', 'list', 'details', 'breakdown', 'again', 'repeat'
            ]
            temporal_phrases = ['only in', 'in ', 'for ', 'during', 'within']
            ql = q.lower().strip()
            
            # Check if it's a temporal filter (like "only in June month")
            if any(phrase in ql for phrase in temporal_phrases):
                return True
            
            # Check other follow-up patterns
            return any(ql.startswith(phrase) or phrase in ql for phrase in followup_phrases) or len(ql.split()) <= 5

        def are_questions_related(current_q, last_q):
            """Check if two questions are about the same topic/analysis"""
            if not last_q or not current_q:
                return False
            
            # Define topic keywords for different analysis areas
            topic_groups = {
                'weave': ['weave', 'weev', 'plain', 'satin', 'linen', 'denim', 'crepe', 'twill', 'spandex'],
                'composition': ['composition', 'komposition', 'kumposison', 'composision', 'cotton', 'polyester'],
                'quality': ['quality', 'kolity', 'qualety', 'premium', 'standard', 'economy'],
                'agent': ['agent', 'agnet', 'priya', 'sowmiya', 'mukilan', 'karthik', 'boobalan', 'boopalan'],
                'customer': ['customer', 'cusomer', 'alice', 'smith', 'ravi', 'qilyze', 'jhon'],
                'sales': ['sales', 'revenue', 'quantity', 'rate', 'growth', 'trend', 'sold', 'most'],
                'status': ['status', 'confirmed', 'pending', 'cancelled']
            }
            
            def get_question_topics(question):
                """Get the topics/categories a question belongs to"""
                q_lower = question.lower()
                topics = []
                for topic, keywords in topic_groups.items():
                    if any(keyword in q_lower for keyword in keywords):
                        topics.append(topic)
                return topics
            
            current_topics = get_question_topics(current_q)
            last_topics = get_question_topics(last_q)
            
            # Questions are related if they share at least one topic
            return bool(set(current_topics) & set(last_topics))

        def get_last_user_question(chat_history):
            """Get the most recent user question from chat history"""
            if not chat_history:
                return None
            
            for msg in reversed(chat_history[:-1]):  # Exclude current question
                if msg.get("role") == "user":
                    return msg["parts"][0]["text"]
            return None

        def is_temporal_filter(q):
            """Check if the question is asking for a time-based filter"""
            temporal_patterns = [
                r'only in (\w+)',
                r'in (\w+) month',
                r'for (\w+)',
                r'during (\w+)'
            ]
            return any(re.search(pattern, q.lower()) for pattern in temporal_patterns)

        # Smart context handling for follow-up questions
        if (followup_flag or (chat_history and is_followup_question(user_question))):
            last_question = get_last_user_question(chat_history)
            
            # Handle misspelling corrections with "yes" responses
            if user_question.lower().strip() in ['yes', 'yeah', 'yep', 'sure', 'please do', 'go ahead', 'correct']:
                if last_question:
                    # Try to correct common misspellings in the last question
                    corrected_question = correct_misspellings(last_question)
                    if corrected_question != last_question:
                        # Use the corrected question
                        user_question = corrected_question
                        # Use only the last 2 messages for context
                        limited_history = chat_history[-2:] if len(chat_history) >= 2 else chat_history
                        chat_history = limited_history
                    else:
                        # No correction found, ask for clarification
                        api_key = os.getenv("GEMINI_API_KEY")
                        if not api_key:
                            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the script.")
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("models/gemini-2.0-flash")
                        context_response = f"""You are a Dress Sales Monitoring Chatbot. The user's previous question was: "{last_question}" and they responded "yes".

Please provide a helpful response that:
1. Acknowledges their confirmation
2. Asks them to rephrase their original question more clearly
3. Provides 2-3 example questions they could ask about sales data
4. Mentions you can help with sales analysis, trends, and predictions

Keep the response friendly and encouraging."""
                        response = model.generate_content(context_response)
                        response_text = response.text
                        print(response_text, end="")
                        return response_text
            
            # Check if questions are actually related before combining
            if last_question and are_questions_related(user_question, last_question):
                if is_temporal_filter(user_question):
                    # This is a temporal filter - apply it to the last question only
                    combined_question = f"{last_question.strip()} {user_question.strip()}"
                    
                    # Check if the combined context is sales-related
                    if not is_sales_related_question(combined_question):
                        api_key = os.getenv("GEMINI_API_KEY")
                        if not api_key:
                            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the script.")
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("models/gemini-2.0-flash")
                        context_response = f"""You are a Dress Sales Monitoring Chatbot. A user asked: \"{user_question}\"

This question appears to be outside my domain of expertise. I am specifically designed to analyze fabric sales data, provide sales insights, and make predictions about sales performance.

Please provide a helpful, polite response that:
1. Acknowledges their question
2. Explains that this is outside your scope as a sales analytics chatbot
3. Suggests they ask about sales data, trends, predictions, or fabric performance instead
4. Provides 2-3 example questions they could ask

Keep the response friendly and helpful, not dismissive."""
                        response = model.generate_content(context_response)
                        response_text = response.text
                        print(response_text, end="")
                        return response_text
                    
                    # Process with limited context - only the last question + current filter
                    user_question = combined_question
                    # Use only the last 2 messages for context to avoid mixing old contexts
                    limited_history = chat_history[-2:] if len(chat_history) >= 2 else chat_history
                    chat_history = limited_history
                    
                else:
                    # Regular follow-up - only combine with immediate previous question if related
                    combined_question = f"{last_question.strip()} {user_question.strip()}"
                    
                    if not is_sales_related_question(combined_question):
                        api_key = os.getenv("GEMINI_API_KEY")
                        if not api_key:
                            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the script.")
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel("models/gemini-2.0-flash")
                        context_response = f"""You are a Dress Sales Monitoring Chatbot. A user asked: \"{user_question}\"

This question appears to be outside my domain of expertise. I am specifically designed to analyze fabric sales data, provide sales insights, and make predictions about sales performance.

Please provide a helpful, polite response that:
1. Acknowledges their question
2. Explains that this is outside your scope as a sales analytics chatbot
3. Suggests they ask about sales data, trends, predictions, or fabric performance instead
4. Provides 2-3 example questions they could ask

Keep the response friendly and helpful, not dismissive."""
                        response = model.generate_content(context_response)
                        response_text = response.text
                        print(response_text, end="")
                        return response_text
                    
                    # Process with limited context
                    user_question = combined_question
                    limited_history = chat_history[-2:] if len(chat_history) >= 2 else chat_history
                    chat_history = limited_history
            # If questions are not related, treat as a new independent question - no context combination

        # If the current question is NOT related to the dataset, return the default refusal
        # BUT allow prediction questions even if not strictly matching keywords
        if not is_sales_related_question(user_question) and not is_prediction_question(user_question):
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the script.")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("models/gemini-2.0-flash")
            context_response = f"""You are a Dress Sales Monitoring Chatbot. A user asked: \"{user_question}\"

This question appears to be outside my domain of expertise. I am specifically designed to analyze fabric sales data, provide sales insights, and make predictions about sales performance.

Please provide a helpful, polite response that:
1. Acknowledges their question
2. Explains that this is outside your scope as a sales analytics chatbot
3. Suggests they ask about sales data, trends, predictions, or fabric performance instead
4. Provides 2-3 example questions they could ask

Keep the response friendly and helpful, not dismissive."""
            response = model.generate_content(context_response)
            response_text = response.text
            print(response_text, end="")
            return response_text

        # Check if this is a prediction question and handle it specially
        if is_prediction_question(user_question):
            # Fetch sales data for prediction
            sales_data = fetch_sales_data_from_api()
            if not sales_data:
                return "I apologize, but I cannot access the sales data needed for predictions at the moment. Please try again later."
            
            # Extract target date from question
            target_date = extract_prediction_date(user_question)
            
            # Generate prediction
            prediction_result = predict_future_sales(target_date, sales_data)
            
            if 'error' in prediction_result:
                return f"**Prediction Error:** {prediction_result['error']}"
            
            # Format prediction response
            target_datetime = datetime.strptime(target_date, '%Y-%m-%d')
            month_name = calendar.month_name[target_datetime.month]
            year = target_datetime.year
            
            prediction_response = f"""**📈 Sales Prediction for {month_name} {year}**

**Summary:** Based on historical trends analysis, I predict the following sales metrics for {month_name} {year}:

**Detailed Forecast:**
- **Predicted Quantity:** {prediction_result['predicted_quantity']:,} units
- **Predicted Revenue:** ₹{prediction_result['predicted_revenue']:,.2f}
- **Predicted Orders:** {prediction_result['predicted_orders']:,} orders
- **Average Growth Rate:** {prediction_result['avg_growth_rate']}% per month
- **Seasonal Factor:** {prediction_result['seasonal_factor']}x (based on historical {month_name} data)

**Prediction Details:**
- **Confidence Level:** {prediction_result['confidence']}
- **Months Ahead:** {prediction_result['months_ahead']} months from latest data
- **Historical Data:** Based on {prediction_result['historical_months']} months of sales data

**Key Insights:**
- This prediction uses historical sales patterns, seasonal trends, and growth rates
- {prediction_result['confidence']} confidence due to {prediction_result['months_ahead']} months projection horizon
- Seasonal adjustment applied based on historical {month_name} performance
- Growth projection assumes continuation of current market trends

**Disclaimer:** This prediction is based on historical data patterns and assumes continuation of current trends. Actual results may vary due to market conditions, economic factors, seasonal variations, and external events."""
            
            print(prediction_response, end="")
            return prediction_response

        # Get API key from environment variable
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set. Please set it before running the script.")
        genai.configure(api_key=api_key)
        model_name = "models/gemini-2.0-flash"  # or 'gemini-pro' if you want
        model = genai.GenerativeModel(model_name)
        # Fetch sales data from API
        sales_data = fetch_sales_data_from_api()
        # Convert sales_data (list of dicts) to CSV string for Gemini context
        csv_buffer = io.StringIO()
        if sales_data:
            writer = csv.DictWriter(csv_buffer, fieldnames=sales_data[0].keys())
            writer.writeheader()
            writer.writerows(sales_data)
            csv_string = csv_buffer.getvalue()
        else:
            csv_string = ""

        # Build contents with chat history
        contents = []

        # Add system context about the Dress Sales Monitoring Chatbot
        system_context = """You are the Dress Sales Monitoring Chatbot, an advanced AI-powered analytics system designed for dress and fabric sales companies. Your job is to help business administrators gain insights from their sales data in a professional, friendly, and interactive way.

**SMART CONTEXT HANDLING:**
- When a user asks a follow-up question with temporal filters (like "only in June month"), apply the filter ONLY to the immediately previous question, not all previous questions
- If the previous question was about "composition" and user asks "only in June month", analyze composition data for June only
- If the previous question was about "weave type" and user asks "only in June month", analyze weave type data for June only
- Do NOT combine multiple different previous questions unless they are directly related

**CRITICAL ANALYSIS RULES:**
- When analyzing "most sold" items, ALWAYS check if there are ties (equal counts)
- If ALL items have the same count (e.g., all have count of 1), state "There is a TIE - all items have equal sales" 
- NEVER claim one item is "most sold" when multiple items have the same highest count
- Be mathematically accurate and honest about ties and equal distributions
- SUMMARY MUST MATCH THE DATA: If there's a tie, the summary must say "There is a tie" NOT "X is the most sold"
- **FOR REVENUE CALCULATIONS: Calculate once, show final result clearly, NO multiple corrections or "however" statements**

**ALWAYS structure your responses as follows:**
1. **Summary:** Start with a clear, concise summary of the answer in plain language. IF THERE IS A TIE, THE SUMMARY MUST STATE "There is a tie" NOT claim one item is most sold.
2. **Detailed Breakdown:** Follow with a detailed statistical breakdown, including numbers, calculations, or markdown tables where appropriate. Show your reasoning and how you arrived at the answer.
3. **Professional Communication Style:** Use a clear, informative, and business-focused approach. Provide accurate data analysis with proper context. Use markdown formatting (bold, bullet points, tables) for clarity and professional presentation. Always conclude with relevant insights or recommendations based on the data.

**Example Context Handling:**

Conversation:
User: What is the most sold weave type?
AI: [Analyzes all weave types] Plain is the most sold weave type.

User: What is the most sold composition?
AI: [Analyzes all compositions] 20% is the most sold composition.

User: Only in June month?
AI: [Analyzes ONLY composition data for June, not weave types] Based on June data, 100pct cotton is the most sold composition in June.

**Example of Handling Ties:**
If all items have equal counts (e.g., Satin: 1, Linen: 1, Cotton: 1), respond:

**Summary:** There is a TIE - all weave types have equal sales with 1 record each in June.

**Detailed Breakdown:** 
- Satin: 1
- Linen: 1  
- Cotton: 1

**Insights:** No single weave type is dominant in this period. All weave types performed equally.

The system operates on a dataset containing over 1,000 sales records with detailed information including dates, product qualities (premium, standard, economy), weave types (spandex, linen, denim, satin, crepe, plain, twill), quantities, compositions, order statuses, rates, agent names, and customer information.

The chatbot employs a Random Forest Regressor machine learning model that continuously learns from historical sales patterns to predict future sales quantities based on product characteristics, seasonal factors, and market trends. It processes natural language queries through keyword extraction and pattern matching, then generates conversational responses enhanced by Google's Gemini AI to provide professional, context-aware answers. The system features an adaptive learning mechanism that tracks user preferences and question patterns, allowing it to personalize responses and improve accuracy over time.

Special Features & Advanced Capabilities:
- **Sophisticated Trend Analysis:** Identify revenue growth or decline patterns over custom time periods, such as "past 6 months" or "January to August," providing detailed month-over-month comparisons with percentage changes and trend directions
- **Field-Specific Analysis:** Comprehensive analysis across different time dimensions (daily, weekly, monthly, yearly) for weave types, compositions, qualities, and customer/agent performance
- **Range Analysis:** Compare performance between specific month ranges
- **Leading Analysis:** Identify top performers in various categories over different time periods
- **Continuous Trend Analysis:** When analyzing trends between months (e.g., "January to August"), analyze ALL months in between, not just start and end points

Future Prediction Capabilities:
The chatbot excels in predictive analytics with multiple forecasting approaches:
- **Advanced Time Series Analysis:** Analyze historical monthly trends, seasonal patterns, and growth rates to predict future sales
- **Specific Date Predictions:** Predict sales for specific future dates (e.g., "June 2026", "March 15, 2027") by analyzing historical patterns and applying growth trends
- **Year-Based Predictions:** For year-based predictions (e.g., "2027 sales forecast"), use historical yearly data to calculate growth rates and project future values with monthly breakdowns
- **Growth Projections:** Incorporate trend analysis and growth projections, considering factors like seasonal patterns, historical growth rates, and market evolution
- **Detailed Projections:** Provide detailed monthly projections for future years, including quantity predictions, revenue estimates, and confidence levels based on historical data patterns
- **Seasonal Adjustments:** Apply seasonal factors based on historical performance of the same month in previous years
- **Confidence Scoring:** Provide confidence levels (High/Medium/Low) based on prediction horizon and data availability

**Prediction Examples:**
- "What will be the sales in June 2026?" → Analyzes June historical data + growth trends
- "Predict sales for 2027" → Year-long forecast with monthly breakdown
- "Future sales forecast for premium cotton dresses" → Category-specific predictions
- "Expected revenue next year" → Revenue projections with confidence intervals

Response Intelligence:
The system responds to queries through a multi-layered approach:
- **Keyword Analysis:** First analyze the question for keywords and patterns
- **Data Extraction:** Extract relevant data based on time periods, product categories, or specific entities mentioned
- **Dual Response Format:** Provide both summary and detailed responses, with the ability to expand information on demand
- **Complex Query Handling:** Handle complex queries like "trend over past 6 months," "most sold weave type in January 2024," or "predict sales for premium cotton dresses"
- **Context Awareness:** Maintain context awareness, learning from previous interactions to provide more relevant and personalized responses
- **Disclaimers:** Ensure all predictions include appropriate disclaimers about market uncertainties and external factors that may affect accuracy

For prediction questions (like "What will be the most sold item in 2026?"), analyze the historical data for:
1. Top-selling items by weave, quality, and composition
2. Year-over-year growth rates
3. Seasonal patterns and trends
4. Project future sales using these patterns

For trend analysis requests (like "Show me the trend from January to August 2024"):
1. Identify the full range of months requested
2. Process each month sequentially (Jan, Feb, Mar, Apr, May, Jun, Jul, Aug)
3. Calculate month-over-month percentage changes
4. Provide detailed breakdown with trend indicators (🔻 Down, 🔼 Up)
5. Include summary of the overall trend pattern

Always provide data-driven insights and predictions based on the provided CSV data."""

        # Add CSV data as context (as a text part)
        contents.append({
            "role": "user",
            "parts": [
                {"text": csv_string},
                {"text": f"{system_context}\n\nThis is the fabric sales data from 2024-2025. Use this data to answer questions and make predictions."},
            ],
        })

        # Add chat history if provided (with smart context limiting)
        if chat_history:
            # Only add the relevant context based on the type of question
            for message in chat_history:
                contents.append(message)

        # Add the current user question
        contents.append({
            "role": "user",
            "parts": [
                {"text": user_question},
            ],
        })

        response = model.generate_content(
            contents=contents,
        )
        response_text = response.text
        print(response_text, end="")

        return response_text

    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(error_msg)
        return error_msg

def main():
    print("Welcome to the Dress Sales Monitoring Chatbot!")
    print("I can help you analyze sales trends, predict future performance, and provide insights from your fabric sales data.")
    print("Ask me questions about sales trends, product performance, or request predictions (e.g., 'What will be the most sold item in 2026?')")
    print("Type 'exit' or 'quit' to end the chat.\n")

    # Validate API key
    if not Config.validate_api_key():
        print("❌ Please configure your Gemini API key in the config file.")
        print("Get your free API key from: https://makersuite.google.com/app/apikey")
        return

    chat_history = []
    last_actionable_question = None

    while True:
        user_input = input("\nYou: ").strip().lower()

        if user_input in ['exit', 'quit']:
            print("Goodbye!")
            break

        if not user_input:
            continue

        # Detect if the user is saying "yes" or similar - let generate_response handle this
        # No special handling here, pass it through to generate_response

        # Add user message to history
        user_message = {
            "role": "user",
            "parts": [{"text": user_input}]
        }
        chat_history.append(user_message)

        # Store the last actionable question (refine logic as needed)
        last_actionable_question = user_input

        # Get AI response
        print("AI: ", end="")
        ai_response = generate_response(user_input, chat_history)

        # Add AI response to history
        ai_message = {
            "role": "model",
            "parts": [{"text": ai_response}]
        }
        chat_history.append(ai_message)

        print()  # Add newline after response

if __name__ == "__main__":
    main()
