from typing import List, Optional, Dict
from app.models.feedback import Feedback
from sqlalchemy import desc


class FeedbackService:
    """Service class to handle feedback operations"""

    @staticmethod
    def get_feedback_by_id(feedback_id: str) -> Optional[Feedback]:
        """Get a feedback by its ID"""
        return Feedback.query.get(feedback_id)

    @staticmethod
    def get_recent_feedbacks(limit: int = 10) -> List[Feedback]:
        """Get most recent feedbacks"""
        # Forçar exclusão de spam sempre
        return Feedback.query.filter_by(is_spam=False).order_by(desc(Feedback.created_at)).limit(limit).all()

    @staticmethod
    def get_filtered_feedbacks(
        sentiment: Optional[str] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Dict:
        """Get paginated feedbacks with optional filters"""
        query = Feedback.query

        if sentiment:
            query = query.filter(Feedback.sentiment == sentiment.upper())

        # Forçar exclusão de spam sempre
        query = query.filter(Feedback.is_spam == False)

        pagination = query.order_by(
            desc(Feedback.created_at)
        ).paginate(page=page, per_page=per_page)

        return {
            'items': pagination.items,
            'pagination': pagination,
            'sentiment': sentiment
        }
