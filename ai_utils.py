"""
File: ai_utils.py
Purpose: DeepSeek AI integration utilities
Description: Provides helper functions for AI-powered features:
             - Report analysis (severity assessment for admins)
             - Senior chatbot (conversational AI assistant)
"""

import requests
import os

DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')
DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions'


def chat_completion(messages, max_tokens=500):
    """
    Call DeepSeek API with given messages.

    Args:
        messages: List of message dicts with 'role' and 'content'
        max_tokens: Maximum response length

    Returns:
        str: The AI response text
    """
    if not DEEPSEEK_API_KEY:
        print("[AI] WARNING: DEEPSEEK_API_KEY not set")
        return None

    try:
        print(f"[AI] Calling DeepSeek API...")
        resp = requests.post(
            DEEPSEEK_URL,
            headers={
                'Authorization': f'Bearer {DEEPSEEK_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': messages,
                'max_tokens': max_tokens,
                'temperature': 0.7
            },
            timeout=30
        )
        resp.raise_for_status()
        result = resp.json()['choices'][0]['message']['content']
        print(f"[AI] Response received ({len(result)} chars)")
        return result
    except Exception as e:
        print(f"[AI] ERROR: {type(e).__name__}: {e}")
        return None


def analyze_report(message_content, reason, description=None):
    """
    Generate AI analysis for a reported message.

    Args:
        message_content: The reported message text
        reason: The report reason (e.g. Harassment, Spam)
        description: Optional additional details from the reporter

    Returns:
        str: AI analysis text with severity and explanation
    """
    prompt = f"""You are a content moderation AI for a community app called GenCon SG that connects seniors with youth volunteers in Singapore.

A user has reported the following message. Analyze it and provide:
1. **Severity**: LOW, MEDIUM, HIGH, or CRITICAL
2. **Analysis**: A brief 1-2 sentence explanation of the content and why it may be problematic.
3. **Recommendation**: A brief suggested action for the admin.

Reported message: "{message_content}"
Report reason: {reason}"""

    if description:
        prompt += f"\nAdditional details from reporter: {description}"

    prompt += "\n\nRespond in this exact format:\nSeverity: [level]\nAnalysis: [explanation]\nRecommendation: [action]"

    messages = [
        {'role': 'system', 'content': 'You are a content moderation assistant. Be concise and objective.'},
        {'role': 'user', 'content': prompt}
    ]

    return chat_completion(messages, max_tokens=200)


SENIOR_CHATBOT_SYSTEM_PROMPT = """You are a friendly AI assistant for GenCon SG, a community app that connects seniors with youth volunteers in Singapore.

You are chatting with a senior citizen. Keep these guidelines in mind:
- Be warm, patient, and respectful
- Use simple, clear language
- Be helpful with questions about technology, health tips, daily life, or just friendly conversation
- If they seem lonely, be a good listener and engage warmly
- Keep responses concise (2-3 sentences usually) unless they ask for detail
- You can discuss Singapore culture, food, history, and local topics
- Never give medical diagnoses - suggest seeing a doctor for health concerns
- Do not discuss politics, religion, or controversial topics"""


def chatbot_reply(conversation_history):
    """
    Generate a chatbot reply for a senior user.

    Args:
        conversation_history: List of dicts with 'role' ('user'/'assistant') and 'content'

    Returns:
        str: The AI chatbot response
    """
    messages = [
        {'role': 'system', 'content': SENIOR_CHATBOT_SYSTEM_PROMPT}
    ] + conversation_history

    return chat_completion(messages, max_tokens=300)
