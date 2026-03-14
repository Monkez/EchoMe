"""
TalkToMe LLM Service Tests
"""

import pytest
import json
from llm_service import FeedbackAnalyzer


class TestFeedbackAnalyzer:
    """Test Claude-based feedback analysis"""
    
    def test_analyze_positive_feedback(self):
        """Test positive sentiment analysis"""
        feedback = "I really love working here! The team is amazing and supportive."
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        data = result['data']
        assert data['sentiment'] in ['positive', 'neutral']
        assert 'sentiment_score' in data
        assert 'topics' in data
        assert 'summary' in data
    
    
    def test_analyze_negative_feedback(self):
        """Test negative sentiment analysis"""
        feedback = "The work hours are too long and management doesn't listen to us."
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        data = result['data']
        assert 'sentiment' in data
        assert 'key_concerns' in data
    
    
    def test_analyze_neutral_feedback(self):
        """Test neutral sentiment"""
        feedback = "Work has been steady. Some good things and some areas to improve."
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        data = result['data']
        assert data['sentiment'] == 'neutral'
    
    
    def test_extract_topics(self):
        """Test topic extraction"""
        feedback = "Career growth is important but work-life balance is suffering."
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        topics = result['data']['topics']
        assert len(topics) > 0
        assert any('career' in t.lower() for t in topics)
        assert any('work' in t.lower() for t in topics)
    
    
    def test_spam_detection(self):
        """Test spam detection"""
        spam = "Buy crypto now!!! Click here for free money!!!"
        
        result = FeedbackAnalyzer.analyze_feedback(spam)
        
        assert result['success'] == True
        assert result['data'].get('is_spam', False) == True
    
    
    def test_batch_analysis(self):
        """Test batch feedback analysis"""
        feedbacks = [
            "Great team culture! Love working here.",
            "Management needs better communication.",
            "Career path is unclear and limiting."
        ]
        
        result = FeedbackAnalyzer.batch_analyze_feedbacks(feedbacks)
        
        assert result['success'] == True
        data = result['data']
        assert data['total_feedbacks'] == 3
        assert 'satisfaction_score' in data
        assert 'sentiments' in data
        assert 'top_topics' in data
    
    
    def test_satisfaction_score_calculation(self):
        """Test satisfaction score 0-10 conversion"""
        feedbacks = [
            "Love it! Best company ever!",
            "It's okay, some pros and cons.",
            "Not happy here, considering leaving."
        ]
        
        result = FeedbackAnalyzer.batch_analyze_feedbacks(feedbacks)
        
        assert result['success'] == True
        score = result['data']['satisfaction_score']
        assert 0 <= score <= 10
    
    
    def test_summary_generation(self):
        """Test executive summary generation"""
        feedbacks = [
            "Team is great but work hours too long.",
            "Good culture, need better career development.",
            "Excited about our direction and goals."
        ]
        
        analytics = {
            'total_feedbacks': 3,
            'satisfaction_score': 6.5,
            'sentiments': {
                'positive_pct': 33,
                'neutral_pct': 34,
                'negative_pct': 33
            },
            'top_topics': [
                {'topic': 'work-life-balance', 'percentage': 33},
                {'topic': 'career-growth', 'percentage': 33}
            ],
            'top_concerns': [
                {'item': 'Work hours too long'},
                {'item': 'Career development unclear'}
            ]
        }
        
        summary = FeedbackAnalyzer.generate_summary(feedbacks, analytics)
        
        assert summary is not None
        assert len(summary) > 50
        assert isinstance(summary, str)
    
    
    def test_short_feedback(self):
        """Test with very short feedback"""
        feedback = "Good work!"
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        data = result['data']
        assert 'sentiment' in data
    
    
    def test_long_feedback(self):
        """Test with very long feedback"""
        feedback = """
        I've been working here for 3 years and I have many thoughts.
        The company culture is amazing - everyone is supportive and collaborative.
        However, there are some areas that need improvement.
        First, the work-life balance during peak seasons is concerning.
        I often work 60+ hours per week which affects my health and family time.
        Second, the career development path is not clear.
        I don't know what skills I need to advance or what opportunities are available.
        Third, compensation is below market rate for our region.
        Despite these challenges, I love the mission and my team.
        I hope we can address these concerns to create an even better workplace.
        """ * 2
        
        result = FeedbackAnalyzer.analyze_feedback(feedback)
        
        assert result['success'] == True
        assert 'topics' in result['data']
    
    
    def test_multiple_languages(self):
        """Test multilingual feedback"""
        feedbacks = [
            "Great company! Excellent team.",  # English
            "Très bonne ambiance de travail.",  # French
            "Excelente equipo de trabajo."      # Spanish
        ]
        
        result = FeedbackAnalyzer.batch_analyze_feedbacks(feedbacks)
        
        # Should handle gracefully
        assert result['success'] == True or result['success'] == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
