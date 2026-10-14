import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from sqlalchemy import func

from app import db
from app.models.feedback import Feedback, RequestedFeature
from app.config import Config

logger = logging.getLogger(__name__)


def generate_weekly_summary():
    """
    Generates a summary of feedback from the last week

    Returns:
        dict: Dictionary with feedback statistics and summary
    """
    # Define the last week period
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)

    # Query feedback from last week that isn't spam
    weekly_feedbacks = Feedback.query.filter(
        Feedback.created_at.between(start_date, end_date),
        Feedback.is_spam == False
    ).all()

    # If no feedback, return empty summary
    if not weekly_feedbacks:
        return {
            'total_feedbacks': 0,
            'positive_percentage': 0,
            'negative_percentage': 0,
            'top_features': []
        }

    # Calculate statistics
    total_feedbacks = len(weekly_feedbacks)
    positive_feedbacks = sum(
        1 for f in weekly_feedbacks if f.sentiment == 'POSITIVO')
    negative_feedbacks = sum(
        1 for f in weekly_feedbacks if f.sentiment == 'NEGATIVO')

    # Calculate percentages
    positive_percentage = (positive_feedbacks /
                           total_feedbacks) * 100 if total_feedbacks > 0 else 0
    negative_percentage = (negative_feedbacks /
                           total_feedbacks) * 100 if total_feedbacks > 0 else 0

    # Find most requested features
    feature_query = db.session.query(
        RequestedFeature.code,
        func.count(RequestedFeature.code).label('count'),
        func.string_agg(RequestedFeature.reason, ' | ').label('reasons')
    ).join(Feedback).filter(
        Feedback.created_at.between(start_date, end_date),
        Feedback.is_spam == False
    ).group_by(RequestedFeature.code).order_by(func.count(RequestedFeature.code).desc()).limit(5)

    top_features = [
        {
            'code': feature.code,
            'count': feature.count,
            'reasons': feature.reasons.split(' | ')
        }
        for feature in feature_query
    ]

    # Return statistics
    return {
        'total_feedbacks': total_feedbacks,
        'positive_percentage': positive_percentage,
        'negative_percentage': negative_percentage,
        'top_features': top_features
    }


def generate_email_content(stats):
    """
    Generates email content without using LLM, using a predefined template

    Args:
        stats (dict): Feedback statistics

    Returns:
        str: HTML email content
    """
    # Return early if no feedback
    if stats['total_feedbacks'] == 0:
        return "<p>Nenhum feedback recebido essa semana.</p>"

    # Create features section
    features_html = ""
    if stats['top_features']:
        features_html = "<ul>"
        for feature in stats['top_features']:
            features_html += f"<li><strong>{feature['code']}</strong> (Mencionada {feature['count']} vezes)</li>"
        features_html += "</ul>"
    else:
        features_html = "<p>Nenhuma funcionalidade foi solicitada com frequência esta semana.</p>"

    # Prepare complete email
    email_content = f"""
    <html>
    <body>
        <h2>Resumo Semanal de Feedback - FeedLens</h2>
        
        <p>Prezada equipe,</p>
        
        <p>Este é o resumo automático dos feedbacks recebidos na última semana.</p>
        
        <h3>Estatísticas Gerais</h3>
        <p>Total de feedbacks: <strong>{stats['total_feedbacks']}</strong></p>
        <p>Feedbacks positivos: <strong>{stats['positive_percentage']:.1f}%</strong> ({stats['total_feedbacks'] * stats['positive_percentage'] / 100:.0f} feedbacks)</p>
        <p>Feedbacks negativos: <strong>{stats['negative_percentage']:.1f}%</strong> ({stats['total_feedbacks'] * stats['negative_percentage'] / 100:.0f} feedbacks)</p>
        
        <h3>Funcionalidades Mais Solicitadas</h3>
        {features_html}
        
        <hr>
        <p>Este e-mail foi gerado automaticamente pelo FeedLens.</p>
        <p>Para acessar o dashboard completo, visite <a href="#">o painel de administração</a>.</p>
    </body>
    </html>
    """

    return email_content


def send_weekly_summary_email():
    """
    Generates and sends weekly summary email

    Returns:
        bool: True if email sent successfully, False otherwise
    """
    # Check if email settings are defined
    if not all([Config.EMAIL_HOST, Config.EMAIL_PORT, Config.EMAIL_USER, Config.EMAIL_PASSWORD]):
        logger.warning("Incomplete email settings")
        return False

    # Check if there are configured recipients
    if not Config.EMAIL_RECIPIENTS:
        logger.warning("No recipients configured for weekly summary")
        return False

    # Generate week's statistics
    stats = generate_weekly_summary()

    # Generate email content
    email_content = generate_email_content(stats)

    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = f"Weekly Feedback Summary - FeedLens ({datetime.now().strftime('%Y-%m-%d')})"
    msg['From'] = Config.EMAIL_USER
    msg['To'] = ", ".join(Config.EMAIL_RECIPIENTS)

    # Add HTML content
    msg.attach(MIMEText(email_content, 'html'))

    try:
        # Connect to SMTP server
        server = smtplib.SMTP(Config.EMAIL_HOST, Config.EMAIL_PORT)
        if Config.EMAIL_USE_TLS:
            server.starttls()
        server.login(Config.EMAIL_USER, Config.EMAIL_PASSWORD)

        # Send email
        server.sendmail(Config.EMAIL_USER,
                        Config.EMAIL_RECIPIENTS, msg.as_string())
        server.quit()

        logger.info(
            f"Email sent successfully to {', '.join(Config.EMAIL_RECIPIENTS)}")
        return True
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        return False


def schedule_weekly_summary(scheduler):
    """
    Schedules weekly summary sending

    Args:
        scheduler: The task scheduler
    """
    # Schedule for every Monday at 8am
    scheduler.add_job(
        send_weekly_summary_email,
        'cron',
        day_of_week='mon',
        hour=8,
        minute=0,
        id='weekly_summary_email'
    )

    logger.info("Weekly summary sending scheduled for every Monday at 8am")
