import uuid
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

    # Validate that the id is a well-formed UUID. Doing it here returns a
    # clean 400 instead of letting a malformed id blow up at commit time.
    try:
        uuid.UUID(str(data['id']))
    except (ValueError, AttributeError, TypeError):
        raise ValueError('Field "id" must be a valid UUID') from None

    if not str(data['feedback']).strip():
        raise ValueError('Field "feedback" must not be empty')

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


@api.route('/feedbacks', methods=['GET'])
def list_feedbacks():
    """
    List analyzed feedbacks (spam excluded), newest first.

    Query params:
        page: page number (default 1)
        per_page: items per page (default 20, capped at 100)
        sentiment: optional filter (POSITIVO/NEGATIVO/INCONCLUSIVO)
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
    except (TypeError, ValueError):
        return jsonify({'error': 'page and per_page must be integers'}), 400

    if page < 1 or per_page < 1:
        return jsonify({'error': 'page and per_page must be positive'}), 400

    # Cap per_page to keep a single response bounded.
    per_page = min(per_page, 100)

    sentiment = request.args.get('sentiment')
    result = FeedbackService.get_filtered_feedbacks(
        sentiment=sentiment, page=page, per_page=per_page)
    pagination = result['pagination']

    return jsonify({
        'items': [item.to_dict() for item in result['items']],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev,
        },
        'sentiment': sentiment,
    }), 200


@api.route('/feedbacks/<feedback_id>', methods=['GET'])
def get_feedback(feedback_id):
    """
    Fetch a single feedback by its UUID.

    Returns 400 for a malformed id and 404 when it does not exist.
    """
    try:
        uuid.UUID(str(feedback_id))
    except (ValueError, AttributeError, TypeError):
        return jsonify({'error': 'Field "id" must be a valid UUID'}), 400

    feedback = FeedbackService.get_feedback_by_id(feedback_id)
    if feedback is None:
        return jsonify({'error': 'Feedback not found'}), 404

    return jsonify(feedback.to_dict()), 200
