import uuid
import logging
from flask import Blueprint, request, jsonify, current_app
from typing import Dict, Any
from sqlalchemy.exc import IntegrityError
from app import db
from app.auth import api_read_required
from app.extensions import limiter
from app.models.feedback import FEATURE_CODE_MAX_LENGTH, Feedback, RequestedFeature
from app.services.feedback_analyzer import FeedbackAnalyzer
from app.services.feedback_service import FeedbackService
from app.llm import (
    ByokHeaderError,
    LLMNotConfiguredError,
    LLMRequestError,
    credential_from_headers,
)

api = Blueprint('api', __name__)
feedback_analyzer = FeedbackAnalyzer()
logger = logging.getLogger(__name__)


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

    # silent=True: JSON inválido vira None e cai no 400 JSON abaixo, em vez
    # do 400 em HTML do Werkzeug. null/lista/número também não são objetos.
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError('Request body must be a JSON object')

    if 'id' not in data or 'feedback' not in data:
        raise ValueError('Fields "id" and "feedback" are required')

    # Validate that the id is a well-formed UUID. Doing it here returns a
    # clean 400 instead of letting a malformed id blow up at commit time.
    try:
        uuid.UUID(str(data['id']))
    except (ValueError, AttributeError, TypeError):
        raise ValueError('Field "id" must be a valid UUID') from None

    feedback = data['feedback']
    if not isinstance(feedback, str):
        raise ValueError('Field "feedback" must be a string')

    if not feedback.strip():
        raise ValueError('Field "feedback" must not be empty')

    # Teto de tamanho: o texto vai inteiro para a LLM (custo por token).
    max_chars = current_app.config.get('MAX_FEEDBACK_CHARS', 5000)
    if len(feedback) > max_chars:
        raise ValueError(
            f'Field "feedback" must have at most {max_chars} characters')

    return data


@api.route('/feedbacks', methods=['POST'])
@limiter.limit(lambda: current_app.config.get('RATELIMIT_INGEST', '30 per minute'))
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

    # BYOK por requisição (opcional): X-LLM-Provider + X-LLM-Api-Key.
    try:
        credential = credential_from_headers(request.headers)
    except ByokHeaderError as e:
        return jsonify({'error': str(e), 'code': 'invalid_byok_headers'}), e.status_code

    # Check if feedback already exists
    if FeedbackService.get_feedback_by_id(feedback_id):
        return jsonify({'error': 'Feedback with this ID already exists'}), 409

    # Analyze feedback
    logger.info('Analyzing feedback id=%s', feedback_id)
    try:
        analysis_result = feedback_analyzer.analyze_feedback(
            feedback_text, credential=credential)
    except LLMNotConfiguredError:
        return jsonify({
            'error': 'Nenhum provedor de LLM configurado: defina uma chave no '
                     'servidor ou envie X-LLM-Provider e X-LLM-Api-Key.',
            'code': 'llm_not_configured',
        }), 503
    except LLMRequestError as e:
        # Só acontece com BYOK: a chave/modelo do próprio cliente falhou, então
        # nada é gravado e ele pode reenviar o mesmo id.
        if e.auth_failed:
            return jsonify({
                'error': 'O provedor recusou a chave enviada em X-LLM-Api-Key.',
                'code': 'llm_auth_failed',
            }), 422
        return jsonify({
            'error': 'O provedor de LLM falhou com a credencial enviada.',
            'code': 'llm_request_failed',
            'detail': e.attempts[-1].kind if e.attempts else None,
        }), 502
    sentiment = analysis_result.get('sentiment', 'INCONCLUSIVO')
    is_spam = analysis_result.get('is_spam', False)
    requested_features = analysis_result.get('requested_features', [])
    logger.info(
        'Feedback id=%s analyzed: sentiment=%s is_spam=%s features=%d',
        feedback_id, sentiment, is_spam, len(requested_features))

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
            # A coluna é VARCHAR(50): no Postgres um código maior derruba o
            # INSERT inteiro, então o limite é garantido aqui, na fronteira.
            code=str(feature['code'])[:FEATURE_CODE_MAX_LENGTH],
            reason=feature['reason'],
            feedback=feedback
        )
        db.session.add(requested_feature)

    # Save to database
    db.session.add(feedback)
    try:
        db.session.commit()
    except IntegrityError:
        # Duas requisições com o mesmo id passam juntas pela checagem acima;
        # a PK decide no commit, e o perdedor recebe o mesmo 409.
        db.session.rollback()
        return jsonify({'error': 'Feedback with this ID already exists'}), 409

    # Return result
    return jsonify({
        'id': str(feedback.id),
        'sentiment': feedback.sentiment,
        'is_spam': feedback.is_spam,
        'requested_features': [feature.to_dict() for feature in feedback.requested_features],
        # 'provedor/modelo' que fez a análise; null = resultado seguro padrão.
        'analyzed_by': analysis_result.get('analyzed_by'),
    }), 201


@api.route('/feedbacks', methods=['GET'])
@api_read_required
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
@api_read_required
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
