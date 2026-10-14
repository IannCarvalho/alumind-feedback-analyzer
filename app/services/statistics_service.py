from typing import Dict, List, TypedDict
from sqlalchemy import func
from app import db
from app.models.feedback import Feedback, RequestedFeature


class FeatureStats(TypedDict):
    code: str
    count: int
    percentage: float


class SentimentStats(TypedDict):
    POSITIVO: int
    NEGATIVO: int
    INCONCLUSIVO: int


class Statistics:
    """Service class to handle feedback statistics calculations"""

    @staticmethod
    def get_total_feedbacks(exclude_spam: bool = True) -> int:
        """Get total number of feedbacks, optionally excluding spam"""
        query = Feedback.query
        if exclude_spam:
            query = query.filter_by(is_spam=False)
        return query.count()

    @staticmethod
    def get_sentiment_counts(exclude_spam: bool = True) -> SentimentStats:
        """Get counts of feedbacks by sentiment"""
        sentiment_counts = db.session.query(
            Feedback.sentiment,
            func.count(Feedback.id).label('count')
        )

        if exclude_spam:
            sentiment_counts = sentiment_counts.filter_by(is_spam=False)

        sentiment_counts = sentiment_counts.group_by(
            Feedback.sentiment
        ).all()

        # Convert to dictionary with default values
        counts = {s.sentiment: s.count for s in sentiment_counts}
        return {
            'POSITIVO': counts.get('POSITIVO', 0),
            'NEGATIVO': counts.get('NEGATIVO', 0),
            'INCONCLUSIVO': counts.get('INCONCLUSIVO', 0)
        }

    @staticmethod
    def get_sentiment_percentages(total_feedbacks: int, sentiment_counts: SentimentStats) -> Dict[str, float]:
        """Calculate percentages for each sentiment"""
        if total_feedbacks == 0:
            return {
                'POSITIVO': 0.0,
                'NEGATIVO': 0.0,
                'INCONCLUSIVO': 0.0
            }

        return {
            sentiment: (count / total_feedbacks * 100)
            for sentiment, count in sentiment_counts.items()
        }

    @staticmethod
    def get_top_features(limit: int = 10, exclude_spam: bool = True) -> List[FeatureStats]:
        """Get most requested features"""
        total_feedbacks = Statistics.get_total_feedbacks(exclude_spam)

        query = db.session.query(
            RequestedFeature.code,
            func.count(RequestedFeature.code).label('count')
        ).join(Feedback)

        if exclude_spam:
            query = query.filter(Feedback.is_spam == False)

        features = query.group_by(
            RequestedFeature.code
        ).order_by(
            func.count(RequestedFeature.code).desc()
        ).limit(limit).all()

        return [
            {
                'code': feature.code,
                'count': feature.count,
                'percentage': (feature.count / total_feedbacks * 100) if total_feedbacks > 0 else 0
            }
            for feature in features
        ]

    @classmethod
    def get_dashboard_statistics(cls) -> Dict:
        """Get all statistics needed for the dashboard"""
        # Sempre excluir spam
        total_feedbacks = cls.get_total_feedbacks(exclude_spam=True)

        if total_feedbacks == 0:
            return {'has_data': False}

        sentiment_counts = cls.get_sentiment_counts(exclude_spam=True)

        return {
            'has_data': True,
            'total_feedbacks': total_feedbacks,
            'sentiment_counts': sentiment_counts,
            'sentiment_percentages': cls.get_sentiment_percentages(total_feedbacks, sentiment_counts),
            'top_features': cls.get_top_features(exclude_spam=True)
        }
