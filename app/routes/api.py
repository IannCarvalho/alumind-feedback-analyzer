from flask import Blueprint, request, jsonify
from typing import Dict, Any
from app import db
from app.models.feedback import Feedback, RequestedFeature
from app.services.feedback_analyzer import FeedbackAnalyzer
from app.services.feedback_service import FeedbackService

api = Blueprint('api', __name__)
feedback_analyzer = FeedbackAnalyzer()


def validate_feedback_request() -> Dict[str, Any]:
    """
    Validate feedback request data

    Returns:
        Dict containing the validated data

    Raises:
        ValueError if validation fails
    """
    if not request.is_json:
        raise ValueError('Request must be valid JSON')

    data = request.get_json()

    if 'id' not in data or 'feedback' not in data:
        raise ValueError('Fields "id" and "feedback" are required')

    return data


@api.route('/feedbacks', methods=['POST'])
def analyze_feedback():
    """
    Endpoint to receive and analyze feedback

    Receives a JSON with feedback ID and text, analyzes sentiment,
    spam status and identifies requested features.
    """
    try:
        data = validate_feedback_request()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    feedback_id = data['id']
    feedback_text = data['feedback']

    # Check if feedback already exists
    if FeedbackService.get_feedback_by_id(feedback_id):
        return jsonify({'error': 'Feedback with this ID already exists'}), 409

    # Analyze feedback
    analysis_result = feedback_analyzer.analyze_feedback(feedback_text)
    sentiment = analysis_result.get('sentiment', 'INCONCLUSIVO')
    is_spam = analysis_result.get('is_spam', False)
    requested_features = analysis_result.get('requested_features', [])

    # Create feedback in database
    feedback = Feedback(
        id=feedback_id,
        feedback_text=feedback_text,
        sentiment=sentiment,
        is_spam=is_spam
    )

    # Add requested features
    for feature in requested_features:
        requested_feature = RequestedFeature(
            code=feature['code'],
            reason=feature['reason'],
            feedback=feedback
        )
        db.session.add(requested_feature)

    # Save to database
    db.session.add(feedback)
    db.session.commit()

    # Return result
    return jsonify({
        'id': str(feedback.id),
        'sentiment': feedback.sentiment,
        'is_spam': feedback.is_spam,
        'requested_features': [feature.to_dict() for feature in feedback.requested_features]
    }), 201
