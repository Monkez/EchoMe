"""
TalkToMe LLM Service - AI-powered feedback analysis
Uses Claude API for sentiment analysis, topic extraction, filtering
"""

import anthropic
import json
from datetime import datetime
from typing import Dict, List, Any

client = anthropic.Anthropic()

class FeedbackAnalyzer:
    """Analyze feedback using Claude LLM"""
    
    @staticmethod
    def analyze_feedback(content: str) -> Dict[str, Any]:
        """
        Analyze single feedback
        
        Returns:
        {
            'sentiment': 'positive|neutral|negative',
            'sentiment_score': -1 to 1,
            'is_filtered': bool,
            'filter_reason': str,
            'topics': ['topic1', 'topic2'],
            'summary': 'concise summary',
            'key_concerns': ['concern1', 'concern2']
        }
        """
        
        prompt = f"""
Analyze this employee feedback and provide structured output as JSON:

FEEDBACK:
{content}

Analyze and respond ONLY with valid JSON (no markdown, no extra text):
{{
    "sentiment": "positive|neutral|negative",
    "sentiment_score": -1 to 1 (float),
    "topics": ["topic1", "topic2"],
    "summary": "1-2 sentence concise summary",
    "is_spam": false,
    "is_inappropriate": false,
    "key_concerns": ["concern1", "concern2"],
    "suggestions": ["suggestion1", "suggestion2"]
}}

Rules:
- sentiment_score: -1 (very negative), 0 (neutral), 1 (very positive)
- topics: extract main themes (e.g., "work-life-balance", "career-growth", "management", "compensation", "communication")
- is_spam: true if not genuine feedback
- is_inappropriate: true if offensive/discriminatory
- summary: capture essence in 1-2 sentences
- Extract 2-3 key concerns
- Extract 2-3 constructive suggestions if present
"""
        
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=500,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Parse JSON response
            response_text = message.content[0].text
            analysis = json.loads(response_text)
            
            return {
                'success': True,
                'data': analysis
            }
            
        except json.JSONDecodeError:
            return {
                'success': False,
                'error': 'Failed to parse LLM response'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def batch_analyze_feedbacks(feedbacks: List[str]) -> Dict[str, Any]:
        """Analyze multiple feedbacks and aggregate results"""
        
        results = []
        for feedback in feedbacks:
            result = FeedbackAnalyzer.analyze_feedback(feedback)
            if result['success']:
                results.append(result['data'])
        
        if not results:
            return {'success': False, 'error': 'No valid feedback to analyze'}
        
        # Aggregate results
        aggregated = FeedbackAnalyzer._aggregate_results(results)
        
        return {
            'success': True,
            'data': aggregated
        }
    
    @staticmethod
    def _aggregate_results(results: List[Dict]) -> Dict[str, Any]:
        """Aggregate multiple feedback analyses"""
        
        # Count sentiments
        sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
        sentiment_scores = []
        all_topics = {}
        all_concerns = []
        all_suggestions = []
        
        for result in results:
            # Sentiment
            sentiment = result.get('sentiment', 'neutral')
            sentiments[sentiment] += 1
            if 'sentiment_score' in result:
                sentiment_scores.append(result['sentiment_score'])
            
            # Topics
            for topic in result.get('topics', []):
                all_topics[topic] = all_topics.get(topic, 0) + 1
            
            # Concerns and suggestions
            all_concerns.extend(result.get('key_concerns', []))
            all_suggestions.extend(result.get('suggestions', []))
        
        # Calculate percentages
        total = len(results)
        sentiments_pct = {
            k: round(v / total * 100, 1) for k, v in sentiments.items()
        }
        
        # Average satisfaction (0-10 scale)
        avg_sentiment_score = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
        satisfaction_score = round((avg_sentiment_score + 1) / 2 * 10, 1)
        
        # Top topics
        top_topics = sorted(all_topics.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            'total_feedbacks': total,
            'satisfaction_score': satisfaction_score,
            'sentiments': {
                'positive_pct': sentiments_pct['positive'],
                'neutral_pct': sentiments_pct['neutral'],
                'negative_pct': sentiments_pct['negative']
            },
            'top_topics': [
                {'topic': topic, 'count': count, 'percentage': round(count/total*100, 1)}
                for topic, count in top_topics
            ],
            'top_concerns': FeedbackAnalyzer._aggregate_items(all_concerns, 5),
            'top_suggestions': FeedbackAnalyzer._aggregate_items(all_suggestions, 5)
        }
    
    @staticmethod
    def _aggregate_items(items: List[str], top_n: int) -> List[Dict]:
        """Aggregate and deduplicate items"""
        
        from collections import Counter
        
        # Simple deduplication (TODO: use embeddings for better clustering)
        item_counts = Counter(items)
        top_items = item_counts.most_common(top_n)
        
        return [
            {'item': item, 'count': count}
            for item, count in top_items
        ]
    
    @staticmethod
    def generate_summary(feedbacks: List[str], analytics: Dict) -> str:
        """Generate executive summary of all feedbacks"""
        
        # Create summary prompt
        prompt = f"""
Based on these feedback analytics, write a brief executive summary (3-4 sentences):

Total Feedbacks: {analytics['total_feedbacks']}
Satisfaction Score: {analytics['satisfaction_score']}/10

Sentiments:
- Positive: {analytics['sentiments']['positive_pct']}%
- Neutral: {analytics['sentiments']['neutral_pct']}%
- Negative: {analytics['sentiments']['negative_pct']}%

Top Topics: {', '.join([t['topic'] for t in analytics['top_topics'][:3]])}

Top Concerns:
{chr(10).join([f"- {c['item']}" for c in analytics['top_concerns'][:3]])}

Write a 3-4 sentence summary that a leader could quickly read to understand team sentiment and main issues.
"""
        
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=300,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return message.content[0].text
            
        except Exception as e:
            return f"Error generating summary: {str(e)}"


# Example usage
if __name__ == '__main__':
    # Test single feedback
    test_feedback = """
    I really enjoy working with the team, but I think we need better communication 
    about project timelines. Sometimes I feel like priorities change without clear explanation. 
    Also, work-life balance could be better during peak seasons.
    """
    
    result = FeedbackAnalyzer.analyze_feedback(test_feedback)
    print("Single Feedback Analysis:")
    print(json.dumps(result, indent=2))
    
    # Test batch
    test_feedbacks = [
        test_feedback,
        "Management doesn't listen to our ideas. We need more autonomy in decision-making.",
        "Great company culture! Love the team. Could use more career development opportunities though."
    ]
    
    batch_result = FeedbackAnalyzer.batch_analyze_feedbacks(test_feedbacks)
    print("\nBatch Analysis:")
    print(json.dumps(batch_result, indent=2))
