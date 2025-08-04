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
import json


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

def filter_confirmed_orders(sales_data):
    """Filter sales data to include only confirmed orders."""
    if not sales_data:
        return []
    
    confirmed_orders = []
    status_debug = {}  # Debug: track all statuses
    
    for record in sales_data:
        status = record.get('status', '').lower().strip()
        
        # Debug: count all statuses
        status_debug[status] = status_debug.get(status, 0) + 1
        
        if status == 'confirmed':
            confirmed_orders.append(record)
    
    # Debug logging
    print(f"🔍 Status breakdown: {status_debug}")
    print(f"✅ Confirmed orders found: {len(confirmed_orders)} out of {len(sales_data)} total")
    
    return confirmed_orders

def analyze_discount_strategy():
    """Analyze live sales data and provide intelligent discount recommendations using Gemini AI."""
    try:
        # Fetch live sales data
        all_sales_data = fetch_sales_data_from_api()
        if not all_sales_data:
            return "❌ Unable to fetch live sales data for discount analysis."
        
        # Filter for confirmed orders only
        sales_data = filter_confirmed_orders(all_sales_data)
        if not sales_data:
            return "❌ No confirmed orders found for discount analysis."
        
        # Perform data analysis
        total_orders = len(sales_data)
        current_date = datetime.now()
        
        # Category performance analysis
        categories = {}
        status_breakdown = {}
        agent_performance = {}
        customer_segments = {}
        price_analysis = {}
        monthly_trends = {}
        
        for record in sales_data:
            # Extract key metrics
            weave = record.get('weave', 'Unknown')
            quality = record.get('quality', 'Unknown')
            composition = record.get('composition', 'Unknown')
            status = record.get('status', 'Unknown')
            agent = record.get('agentName', 'Unknown')
            customer = record.get('customerName', 'Unknown')
            quantity = float(record.get('quantity', 0))
            rate = float(record.get('rate', 0))
            total_value = quantity * rate
            
            # Order date analysis - fix date parsing
            order_date = record.get('date', '')
            try:
                # Handle ISO format like "2025-05-27T17:09:18.536Z"
                if 'T' in order_date:
                    order_datetime = datetime.strptime(order_date.split('T')[0], '%Y-%m-%d')
                else:
                    order_datetime = datetime.strptime(order_date, '%Y-%m-%d')
                month_key = order_datetime.strftime('%Y-%m')
                if month_key not in monthly_trends:
                    monthly_trends[month_key] = {'orders': 0, 'value': 0, 'quantity': 0}
                monthly_trends[month_key]['orders'] += 1
                monthly_trends[month_key]['value'] += total_value
                monthly_trends[month_key]['quantity'] += quantity
            except:
                pass
            
            # Category analysis
            category_key = f"{weave}_{quality}_{composition}"
            if category_key not in categories:
                categories[category_key] = {'orders': 0, 'total_value': 0, 'total_quantity': 0}
            categories[category_key]['orders'] += 1
            categories[category_key]['total_value'] += total_value
            categories[category_key]['total_quantity'] += quantity
            
            # Status analysis
            status_breakdown[status] = status_breakdown.get(status, 0) + 1
            
            # Agent performance
            if agent not in agent_performance:
                agent_performance[agent] = {'orders': 0, 'value': 0}
            agent_performance[agent]['orders'] += 1
            agent_performance[agent]['value'] += total_value
            
            # Price analysis
            if rate > 0:
                if quality not in price_analysis:
                    price_analysis[quality] = {'rates': [], 'orders': 0}
                price_analysis[quality]['rates'].append(rate)
                price_analysis[quality]['orders'] += 1
        
        # Generate AI-powered discount recommendations
        analysis_data = {
            'total_confirmed_orders': total_orders,
            'categories': categories,
            'agent_performance': agent_performance,
            'price_analysis': price_analysis,
            'monthly_trends': monthly_trends,
            'analysis_date': current_date.strftime('%Y-%m-%d')
        }
        
        # Create comprehensive prompt for Gemini AI
        discount_prompt = f"""
        As a sales analytics expert, analyze the following live dress sales data (CONFIRMED ORDERS ONLY) and provide strategic discount recommendations:

        CONFIRMED SALES OVERVIEW:
        - Total Confirmed Orders: {total_orders}
        
        CATEGORY PERFORMANCE (CONFIRMED ORDERS):
        {json.dumps(categories, indent=2)}
        
        AGENT PERFORMANCE (CONFIRMED ORDERS):
        {json.dumps(agent_performance, indent=2)}
        
        PRICE ANALYSIS (CONFIRMED ORDERS):
        {json.dumps(price_analysis, indent=2)}
        
        MONTHLY TRENDS (CONFIRMED ORDERS):
        {json.dumps(monthly_trends, indent=2)}

        Please provide:
        1. **DISCOUNT RECOMMENDATIONS** (with specific percentages and reasoning)
        2. **CATEGORY-WISE STRATEGY** (which products need discounts)
        3. **TIMING RECOMMENDATIONS** (when to apply discounts)
        4. **PERFORMANCE INSIGHTS** (what's working/not working)
        5. **ACTION ITEMS** (immediate steps to take)

        Format your response clearly with specific discount percentages and short, actionable reasons.
        """
        
        # Configure Gemini AI
        genai.configure(api_key=Config.GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Generate AI response
        response = model.generate_content(discount_prompt)
        
        if response and response.text:
            return f"🎯 **LIVE CONFIRMED SALES DISCOUNT ANALYSIS** 📊\n\n{response.text}"
        else:
            return "❌ Unable to generate discount recommendations at this time."
            
    except Exception as e:
        return f"❌ Error in discount analysis: {str(e)}"

def is_sales_related_question(question):
    """Check if the question is related to sales data analysis, allowing for fuzzy keyword matches AND checking against live API data."""
    sales_keywords = [
        'record','dress','sales', 'trend', 'predict', 'forecast', 'quantity', 'rate', 'revenue',
        'agent', 'customer', 'weave', 'linen', 'satin', 'denim', 'crepe', 'twill',
        'premium', 'standard', 'economy', 'cotton', 'polyester', 'spandex',
        'order', 'status', 'confirmed', 'pending', 'cancelled', 'growth',
        'performance', 'top', 'best', 'most', 'sold', 'item', 'product',
        'month', 'year', 'quarter', 'period', 'analysis', 'data','id','date',
        # Add discount related keywords
        'discount', 'offer', 'sale', 'promotion', 'price', 'strategy', 'recommendation',
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
    """Analyze historical trends from confirmed sales data for prediction"""
    if not sales_data:
        return {}
    
    # Filter for confirmed orders only
    confirmed_sales = filter_confirmed_orders(sales_data)
    if not confirmed_sales:
        return {}
    
    monthly_data = defaultdict(lambda: {
        'total_quantity': 0,
        'total_revenue': 0,
        'order_count': 0,
        'weave_types': defaultdict(int),
        'compositions': defaultdict(int),
        'qualities': defaultdict(int)
    })
    
    # Group data by month (confirmed orders only)
    for record in confirmed_sales:
        try:
            # Parse date - handle ISO format with timezone
            date_str = record.get('date', '')
            if date_str:
                # Handle ISO format like "2025-05-27T17:09:18.536Z"
                if 'T' in date_str:
                    date_obj = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                else:
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
    """Predict sales for a future date based on confirmed historical trends"""
    try:
        target_date = datetime.strptime(target_date_str, '%Y-%m-%d')
        target_month = f"{target_date.year}-{target_date.month:02d}"
        
        # Filter for confirmed orders only
        confirmed_sales = filter_confirmed_orders(sales_data)
        if not confirmed_sales:
            return {
                'error': 'No confirmed orders found for prediction',
                'prediction': 0,
                'confidence': 'Low'
            }
        
        # Analyze historical data (confirmed orders only)
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
            'historical_months': total_months,
            'note': 'Predictions based on confirmed orders only'
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

def get_confirmed_orders_by_month(sales_data, month_name):
    """Return confirmed orders for a given month name (e.g., 'june')."""
    month_map = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
        'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12
    }
    month_num = month_map.get(month_name.lower())
    if not month_num:
        return []

    confirmed_orders = filter_confirmed_orders(sales_data)
    filtered = []
    for record in confirmed_orders:
        date_str = record.get('date', '')
        try:
            if date_str:
                # Handle ISO format like "2025-05-27T17:09:18.536Z"
                if 'T' in date_str:
                    date_obj = datetime.strptime(date_str.split('T')[0], '%Y-%m-%d')
                else:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                if date_obj.month == month_num:
                    filtered.append(record)
        except Exception as e:
            continue
    return filtered

def validate_count_accuracy(summary_count, detailed_items, item_type="items"):
    """Validate that summary count matches detailed breakdown count"""
    actual_count = len(detailed_items) if isinstance(detailed_items, list) else detailed_items
    
    if summary_count != actual_count:
        print(f"🚨 COUNT MISMATCH DETECTED:")
        print(f"   Summary claims: {summary_count} {item_type}")
        print(f"   Actual count: {actual_count} {item_type}")
        print(f"   This is a validation error that needs correction.")
        return False
    return True

def generate_response(user_question, chat_history=None, followup_flag=False):
    try:
        # Debug: Check for month-based queries FIRST
        month_keywords = [
            'january', 'february', 'march', 'april', 'may', 'june', 'july',
            'august', 'september', 'october', 'november', 'december'
        ]
        found_month = None
        for mk in month_keywords:
            if mk in user_question.lower():
                found_month = mk
                break

        # Handle month-based queries with debug info
        if found_month and ('sales' in user_question.lower() or 'happened' in user_question.lower()):
            print(f"🔍 DEBUG: Month-based query detected: {found_month}")
            all_sales_data = fetch_sales_data_from_api()
            print(f"🔍 DEBUG: Total records fetched: {len(all_sales_data) if all_sales_data else 0}")
            
            month_orders = get_confirmed_orders_by_month(all_sales_data, found_month)
            print(f"🔍 Confirmed orders found for {found_month.title()}: {len(month_orders)}")
            
            if not month_orders:
                return f"**Summary:** No confirmed sales found for {found_month.title()}.\n\n**Detailed Breakdown:** After analyzing all sales records, there are 0 confirmed orders in {found_month.title()}."
            
            # Show weave counts for the month
            weave_counts = {}
            for record in month_orders:
                weave = record.get('weave', 'Unknown').strip()
                if weave:
                    weave_counts[weave] = weave_counts.get(weave, 0) + 1
            print(f"🔍 Weave counts for {found_month.title()}: {weave_counts}")
            
            # Create detailed breakdown
            breakdown_lines = []
            for i, record in enumerate(month_orders, 1):
                date = record.get('date', 'N/A')
                weave = record.get('weave', 'N/A')
                quality = record.get('quality', 'N/A')
                quantity = record.get('quantity', 'N/A')
                agent = record.get('agentName', 'N/A')
                customer = record.get('customerName', 'N/A')
                breakdown_lines.append(f"{i}. **Date:** {date}, **Weave:** {weave}, **Quality:** {quality}, **Quantity:** {quantity}, **Agent:** {agent}, **Customer:** {customer}")
            
            breakdown = "\n".join(breakdown_lines)
            weave_summary = ", ".join([f"{weave}: {count}" for weave, count in weave_counts.items()])
            
            return f"""**Summary:** {len(month_orders)} confirmed sales found for {found_month.title()}.

**Detailed Breakdown:**
{breakdown}

**Weave Type Summary:** {weave_summary}

**Insights:** The confirmed sales data for {found_month.title()} shows activity across {len(weave_counts)} different weave types."""

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

        # --- DISCOUNT ANALYSIS HANDLING ---
        discount_keywords = ['discount', 'offer', 'sale', 'promotion', 'price', 'strategy', 'recommendation', 'suggest']
        if any(keyword in user_question.lower() for keyword in discount_keywords):
            # Return comprehensive discount analysis
            return analyze_discount_strategy()

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
        all_sales_data = fetch_sales_data_from_api()
        
        # Filter for confirmed orders only for analysis
        confirmed_sales_data = filter_confirmed_orders(all_sales_data)
        
        # Convert confirmed sales_data (list of dicts) to CSV string for Gemini context
        csv_buffer = io.StringIO()
        if confirmed_sales_data:
            writer = csv.DictWriter(csv_buffer, fieldnames=confirmed_sales_data[0].keys())
            writer.writeheader()
            writer.writerows(confirmed_sales_data)
            confirmed_csv_string = csv_buffer.getvalue()
        else:
            confirmed_csv_string = ""

        # Also prepare full data CSV for context (to show all statuses available)
        full_csv_buffer = io.StringIO()
        if all_sales_data:
            writer = csv.DictWriter(full_csv_buffer, fieldnames=all_sales_data[0].keys())
            writer.writeheader()
            writer.writerows(all_sales_data)
            full_csv_string = full_csv_buffer.getvalue()
        else:
            full_csv_string = ""

        # Build contents with chat history
        contents = []

        # Add system context about the Dress Sales Monitoring Chatbot
        system_context = """You are the Dress Sales Monitoring Chatbot, an advanced AI-powered analytics system designed for dress and fabric sales companies. Your job is to help business administrators gain insights from their sales data in a professional, friendly, and interactive way.

**CRITICAL STATUS FILTERING RULES:**
- **CONFIRMED ORDERS ONLY:** When analyzing "most sold", "total sales", "revenue", "trends", or any sales performance metrics, ONLY use records with status = "confirmed"
- **NEVER GROUP STATUSES:** Do NOT combine or group "confirmed" and "processed" orders together - they are completely separate categories
- **Status Categories:** Orders have distinct statuses: confirmed, processed, pending, cancelled, etc. - treat each separately
- **Sales Analysis:** "Most sold" = most sold among CONFIRMED orders ONLY (exclude processed, pending, cancelled)

**CRITICAL COUNTING AND VALIDATION RULES - MANDATORY:**
- **STEP 1:** ALWAYS count the ACTUAL records you are analyzing BEFORE writing your response
- **STEP 2:** VERIFY your count by manually going through each record one by one
- **STEP 3:** The number in your summary MUST EXACTLY MATCH the number of items in your detailed breakdown
- **STEP 4:** Before finalizing response, double-check: Summary count = Detailed breakdown count
- **ZERO TOLERANCE:** There must be NO discrepancies between summary and detailed counts
- **EXAMPLE:** If you display 2 Twill orders, your summary must say "2 Twill orders" NOT "3 Twill orders"

**COUNTING METHODOLOGY:**
1. Filter the data for the exact criteria (e.g., confirmed status, specific weave type, specific month)
2. Count the filtered records manually: 1, 2, 3, etc.
3. Verify your count by listing each record
4. Use the VERIFIED count in your summary
5. Display the EXACT SAME number of records in your detailed breakdown

**CRITICAL ANALYSIS RULES:**
- When analyzing "most sold" items, ALWAYS check if there are ties (equal counts) among CONFIRMED orders
- If ALL confirmed items have the same count (e.g., all have count of 1), state "There is a TIE - all items have equal sales" 
- NEVER claim one item is "most sold" when multiple items have the same highest count among confirmed orders
- Be mathematically accurate and honest about ties and equal distributions
- SUMMARY MUST MATCH THE DATA: If there's a tie among confirmed orders, the summary must say "There is a tie" NOT "X is the most sold"

**MANDATORY RESPONSE VALIDATION CHECKLIST:**
Before providing your final response, you MUST verify:
✓ Count in summary = Count in detailed breakdown (EXACT MATCH REQUIRED)
✓ All displayed records match the filtering criteria
✓ Mathematical calculations are accurate
✓ No contradictions between summary and details
✓ If you say "3 orders" in summary, you show exactly 3 orders in breakdown

**RESPONSE STRUCTURE:**
1. **Summary:** Clear, concise summary with VERIFIED ACCURATE COUNT
2. **Detailed Breakdown:** Show EXACT SAME COUNT as mentioned in summary
3. **Insights:** Professional analysis based on accurate data

**EXAMPLE OF CORRECT COUNTING:**
If you find 2 Twill confirmed orders:
- Summary: "Twill has 2 confirmed orders"
- Detailed Breakdown: [Display exactly 2 Twill orders]
- Count Verification: ✓ Summary (2) = Breakdown (2)

**EXAMPLE OF INCORRECT COUNTING (DO NOT DO THIS):**
- Summary: "Twill has 3 confirmed orders" 
- Detailed Breakdown: [Display only 2 Twill orders]
- Count Verification: ✗ Summary (3) ≠ Breakdown (2) - THIS IS WRONG

Remember: ACCURACY IS PARAMOUNT. Count carefully, verify your count, and ensure perfect alignment between summary and detailed breakdown."""

        # Add CSV data as context (confirmed orders for analysis)
        contents.append({
            "role": "user",
            "parts": [
                {"text": f"CONFIRMED ORDERS DATA (for sales analysis):\n{confirmed_csv_string}"},
                {"text": f"FULL DATA (all statuses - for reference):\n{full_csv_string}"},
                {"text": f"{system_context}\n\nUse the CONFIRMED orders data for sales analysis (most sold, revenue, trends). Use FULL data only when user specifically asks about other statuses like 'pending' or 'cancelled'."},
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

def debug_weave_counts():
    """Debug function to check actual weave counts in confirmed orders"""
    all_sales_data = fetch_sales_data_from_api()
    confirmed_sales_data = filter_confirmed_orders(all_sales_data)
    
    print(f"📊 Total records: {len(all_sales_data)}")
    print(f"📊 Confirmed records: {len(confirmed_sales_data)}")
    
    # Count weaves in confirmed orders
    weave_counts = {}
    for record in confirmed_sales_data:
        weave = record.get('weave', 'Unknown').strip()
        if weave:
            weave_counts[weave] = weave_counts.get(weave, 0) + 1
    
    print(f"🔍 ACTUAL confirmed weave counts: {weave_counts}")
    
    # Show individual confirmed records for verification
    print("\n📋 Individual confirmed records:")
    for i, record in enumerate(confirmed_sales_data, 1):
        print(f"{i}. Weave: {record.get('weave', 'N/A')}, Status: {record.get('status', 'N/A')}, ID: {record.get('_id', 'N/A')}")
    
    return weave_counts

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
