from app import create_app
from app.services.email_service import generate_weekly_summary, generate_email_content, send_weekly_summary_email

# Crie uma instância da aplicação
app = create_app()

# Use o contexto da aplicação
with app.app_context():
    # Gere as estatísticas
    stats = generate_weekly_summary()
    
    # Gere o conteúdo do e-mail
    email_content = generate_email_content(stats)
    
    # Exiba o conteúdo do e-mail
    print(email_content)
    
    # Opcionalmente, teste o envio
    success = send_weekly_summary_email()
    print(f"E-mail enviado com sucesso: {success}")
