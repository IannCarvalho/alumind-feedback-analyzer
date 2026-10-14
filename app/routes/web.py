from flask import Blueprint, render_template, request, redirect, url_for, abort
from app.services.statistics_service import Statistics
from app.services.feedback_service import FeedbackService

web = Blueprint('web', __name__)


@web.route('/')
def index():
    """Redirect to the dashboard page"""
    return redirect(url_for('web.dashboard'))


@web.route('/dashboard')
def dashboard():
    """
    Main dashboard page

    Displays feedback statistics and a list of most recent feedbacks
    """
    # Get statistics from the service
    stats = Statistics.get_dashboard_statistics()

    # Get recent feedbacks if we have data
    if stats['has_data']:
        stats['recent_feedbacks'] = FeedbackService.get_recent_feedbacks()

    return render_template('dashboard.html', **stats)


@web.route('/feedback/<feedback_id>')
def feedback_detail(feedback_id: str):
    """
    Feedback details page

    Args:
        feedback_id: UUID of the feedback to display
    """
    feedback = FeedbackService.get_feedback_by_id(feedback_id)
    if not feedback:
        abort(404)
    return render_template('feedback_detail.html', feedback=feedback)


@web.route('/feedbacks')
def feedback_list():
    """
    Feedback listing page with filters

    Query Parameters:
        sentiment: Filter by sentiment (POSITIVO, NEGATIVO, INCONCLUSIVO)
        page: Page number for pagination (default: 1)
    """
    # Get filter parameters
    sentiment = request.args.get('sentiment')
    page = request.args.get('page', 1, type=int)

    # Get filtered feedbacks
    feedback_data = FeedbackService.get_filtered_feedbacks(
        sentiment=sentiment,
        page=page
    )

    return render_template('feedback_list.html', **feedback_data)
