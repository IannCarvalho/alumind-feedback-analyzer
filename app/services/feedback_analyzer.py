import json
import logging
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from app.config import Config

logger = logging.getLogger(__name__)


class FeedbackAnalyzer:
    """Service for analyzing feedback using LLM"""

    def __init__(self):
        """Initialize the feedback analyzer"""
        api_key = Config.OPENAI_API_KEY
        model_name = Config.OPENAI_MODEL

        if not api_key:
            raise ValueError("OpenAI API Key not configured")

        self.llm = ChatOpenAI(
            model_name=model_name,
            temperature=0.0,
            openai_api_key=api_key
        )

    def analyze_feedback(self, feedback_text):
        """
        Analyzes feedback to determine sentiment and extract requested features

        Args:
            feedback_text (str): Feedback text

        Returns:
            dict: Dictionary with sentiment and requested features
        """
        prompt = ChatPromptTemplate.from_template("""
        Você é um assistente especializado em analisar feedbacks de usuários de um
        aplicativo. Seu objetivo é classificar o sentimento do feedback, detectar spam
        e identificar funcionalidades solicitadas.

        Analise o seguinte feedback e forneça:
        1. Classificação de sentimento: "POSITIVO", "NEGATIVO" ou "INCONCLUSIVO"
        2. Identificação se é spam ou não (feedback é spam se não for relacionado ao aplicativo, contiver links suspeitos, for ofensivo sem ser construtivo ou parecer gerado automaticamente)
        3. Identificação das funcionalidades solicitadas pelo usuário, se houver

        Para cada funcionalidade identificada, forneça:
        - Um código único para a funcionalidade (use letras maiúsculas e sublinhado, como EDITAR_PERFIL)
        - Uma razão explicando por que o usuário quer essa funcionalidade

        Retorne o resultado no formato JSON com as seguintes chaves:
        - sentiment: string (POSITIVO, NEGATIVO ou INCONCLUSIVO)
        - is_spam: booleano (true/false)
        - requested_features: array de objetos com as chaves 'code' e 'reason'

        Feedback: {feedback}
        """)

        chain = prompt | self.llm
        response = chain.invoke({"feedback": feedback_text})

        # Extract JSON from response
        try:
            # Try to find JSON in response
            content = response.content
            # Find start and end of JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1

            if start_idx != -1 and end_idx != -1:
                json_str = content[start_idx:end_idx]
                result = json.loads(json_str)
            else:
                # If specific JSON format not found, try to parse complete text
                result = json.loads(content)

            # Ensure result has expected structure
            if 'sentiment' not in result:
                result['sentiment'] = 'INCONCLUSIVO'
            if 'is_spam' not in result:
                result['is_spam'] = False
            if 'requested_features' not in result:
                result['requested_features'] = []

            return result

        except (json.JSONDecodeError, ValueError) as e:
            # In case of error in analysis, return default result
            logger.error(f"Error analyzing LLM response: {e}")
            return {
                'sentiment': 'INCONCLUSIVO',
                'is_spam': False,
                'requested_features': []
            }
