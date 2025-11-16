"""
Servicio de integración con Google Gemini AI
Maneja la generación de respuestas inteligentes para usuarios de Telegram
"""
import os
import json
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# Configuración de Gemini
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
MODEL_NAME = 'gemini-2.5-flash'  # Usar modelo más nuevo y disponible

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)


class GeminiClient:
    """Cliente para interactuar con Google Gemini API"""
    
    def __init__(self):
        self.model = genai.GenerativeModel(MODEL_NAME) if GEMINI_API_KEY else None
        self.chat_history = {}  # Store chat history by user_id
        self.system_prompt = self._get_system_prompt()
    
    def _get_system_prompt(self) -> str:
        """Obtiene el prompt del sistema para el bot de reclutamiento"""
        return """Eres el asistente virtual oficial de Magneto te llamas Loomy, una plataforma que conecta talentos con oportunidades laborales a través de tecnología e inteligencia artificial.

Tu función principal es operar como un agente automatizado de Telegram que:
- Responde comentarios y mensajes directos de forma cordial y útil y corta, para no aburrir a las personas.
- Recopila información relevante del usuario para orientar procesos de reclutamiento.
- Fortalece la marca empleadora manteniendo un tono humano, amigable y motivador.

Tu propósito:
Ayudar a personas mayores de 18 años a encontrar empleo según sus habilidades, aspiraciones y perfil; y apoyar a las empresas ofreciéndoles un camino más fácil y eficiente para encontrar talento. 

Instrucciones de estilo:
- Habla siempre en español.
- Utiliza emojis de forma moderada para hacer la conversación más amena.
- Sé claro, cercano y profesional.
- Da respuestas breves pero informativas.
- Mantén coherencia con la voz de Magneto (amabilidad, orientación, apoyo).
- Cuando corresponda, sugiere explorar nuestras redes oficiales: Magneto Empleos en Instagram, Facebook, LinkedIn, YouTube y TikTok.

Eres un agente diseñado para mejorar la experiencia de los usuarios, fortalecer la marca empleadora y facilitar el proceso de reclutamiento.
"""
    
    def get_response(self, user_message: str, user_id: str = None, context: dict = None) -> dict:
        """
        Obtiene una respuesta de Gemini para un mensaje de usuario
        
        Args:
            user_message: Mensaje del usuario
            user_id: ID del usuario para mantener contexto
            context: Contexto adicional (ofertas disponibles, historial, etc.)
        
        Returns:
            Dict con respuesta, confianza y metadata
        """
        logger.info(f"[GeminiClient] Iniciando get_response para usuario {user_id}")
        logger.info(f"[GeminiClient] Mensaje: {user_message[:100]}")
        logger.info(f"[GeminiClient] Modelo disponible: {self.model is not None}")
        
        if not self.model:
            logger.error("[GeminiClient] Gemini API no está configurada - GEMINI_API_KEY no encontrado")
            return {
                'response': 'Lo siento, el servicio de IA no está disponible en este momento.',
                'confidence_score': 0.0,
                'model': 'gemini-2.5-flash',
                'error': True
            }
        
        try:
            # Construir contexto de conversación
            logger.info("[GeminiClient] Construyendo prompt...")
            full_prompt = self._build_prompt(user_message, user_id, context)
            logger.info(f"[GeminiClient] Prompt preparado ({len(full_prompt)} caracteres)")
            
            # Generar respuesta
            logger.info("[GeminiClient] Llamando a Gemini API...")
            response = self.model.generate_content(full_prompt)
            response_text = response.text
            
            logger.info(f"[GeminiClient] Respuesta recibida ({len(response_text)} caracteres)")
            
            # Calcular confianza
            confidence = self._calculate_confidence(response)
            logger.info(f"[GeminiClient] Confianza calculada: {confidence}")
            
            logger.info(f"[GeminiClient] OK - Respuesta generada exitosamente para usuario {user_id}")
            
            return {
                'response': response_text,
                'confidence_score': confidence,
                'model': MODEL_NAME,
                'error': False
            }
        
        except Exception as e:
            logger.error(f"[GeminiClient] ERROR en Gemini: {str(e)}")
            import traceback
            logger.error(f"[GeminiClient] Traceback: {traceback.format_exc()}")
            
            return {
                'response': 'Lo siento, ocurrió un error procesando tu mensaje. Por favor intenta de nuevo.',
                'confidence_score': 0.0,
                'model': MODEL_NAME,
                'error': True,
                'error_detail': str(e)
            }
    
    def _build_prompt(self, user_message: str, user_id: str = None, context: dict = None) -> str:
        """Construye el prompt completo con contexto"""
        prompt = self.system_prompt
        prompt += "\n\n--- CONVERSACIÓN ---\n"
        
        # Agregar contexto si está disponible
        if context:
            if context.get('recent_messages'):
                prompt += "\n--- HISTORIAL RECIENTE ---\n"
                for msg in context['recent_messages'][-5:]:  # Últimas 5 mensajes
                    prompt += f"Usuario: {msg['content']}\n"
            
            if context.get('available_jobs'):
                prompt += "\n--- OFERTAS DISPONIBLES ---\n"
                for job in context['available_jobs'][:3]:  # Top 3 ofertas
                    prompt += f"• {job['title']} en {job['company']} - {job['location']}\n"
        
        prompt += f"\nUsuario: {user_message}\nAsistente:"
        return prompt
    
    def _calculate_confidence(self, response) -> float:
        """Calcula la puntuación de confianza de la respuesta"""
        try:
            # Verificar si hay finish_reason válido
            if hasattr(response, 'prompt_feedback'):
                if response.prompt_feedback.block_reason:
                    return 0.3  # Baja confianza si fue bloqueada
            
            # Respuestas más largas generalmente son más confiables
            if response.text and len(response.text) > 50:
                return min(0.95, len(response.text) / 500)
            
            return 0.7
        except:
            return 0.5


def get_ai_response(prompt: str, user_id: str = None, context: dict = None) -> dict:
    """
    Función helper para obtener respuesta de IA
    
    Args:
        prompt: Mensaje del usuario
        user_id: ID del usuario
        context: Contexto adicional
    
    Returns:
        Dict con la respuesta
    """
    client = GeminiClient()
    return client.get_response(prompt, user_id, context)
