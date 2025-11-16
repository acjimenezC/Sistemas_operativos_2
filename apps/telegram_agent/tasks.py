"""
Tareas Celery para procesamiento asincrónico
"""
import logging
from celery import shared_task
from django.utils import timezone
from django.contrib.auth.models import User
import asyncio
from aiogram import Bot
from dotenv import load_dotenv
import os

from apps.telegram_agent.models import TelegramUser, Broadcast, AIResponse, TelegramMessage
from services.gemini_client import GeminiClient

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
bot = Bot(token=TELEGRAM_TOKEN)


@shared_task
def send_scheduled_broadcasts():
    """Envía broadcasts programados que han llegado su hora"""
    try:
        now = timezone.now()
        broadcasts = Broadcast.objects.filter(
            status='scheduled',
            scheduled_at__lte=now
        )
        
        for broadcast in broadcasts:
            send_broadcast.delay(broadcast.id)
            
        logger.info(f"Se encontraron {broadcasts.count()} broadcasts para enviar")
        return f"Procesados {broadcasts.count()} broadcasts"
    
    except Exception as e:
        logger.error(f"Error en send_scheduled_broadcasts: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def send_broadcast(broadcast_id):
    """Envía un broadcast a todos los usuarios activos"""
    try:
        broadcast = Broadcast.objects.get(id=broadcast_id)
        broadcast.status = 'sending'
        broadcast.save()
        
        users = TelegramUser.objects.filter(is_active=True)
        sent_count = 0
        failed_count = 0
        
        for user in users:
            try:
                asyncio.run(send_broadcast_message(user.telegram_id, broadcast.content))
                sent_count += 1
            except Exception as e:
                logger.error(f"Error enviando broadcast a {user.telegram_id}: {str(e)}")
                failed_count += 1
        
        broadcast.sent_count = sent_count
        broadcast.failed_count = failed_count
        broadcast.status = 'sent' if failed_count == 0 else 'failed'
        broadcast.save()
        
        logger.info(f"Broadcast {broadcast_id} enviado: {sent_count} éxitos, {failed_count} fallos")
        return f"Broadcast enviado: {sent_count} éxitos, {failed_count} fallos"
    
    except Exception as e:
        logger.error(f"Error en send_broadcast: {str(e)}")
        return f"Error: {str(e)}"


async def send_broadcast_message(chat_id: str, text: str):
    """Envía mensaje de broadcast a Telegram"""
    try:
        if len(text) > 4000:
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            for chunk in chunks:
                await bot.send_message(chat_id=chat_id, text=chunk, parse_mode="HTML")
        else:
            await bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error enviando a {chat_id}: {str(e)}")
        raise


@shared_task
def analyze_feedback():
    """Analiza el feedback recibido y mejora el modelo"""
    try:
        # Obtener respuestas con feedback reciente
        responses = AIResponse.objects.filter(
            status='rated',
            feedback_score__isnull=False
        ).order_by('-updated_at')[:20]
        
        gemini = GeminiClient()
        
        analysis_results = []
        for response in responses:
            feedback_analysis = gemini.analyze_feedback(response.feedback or "")
            analysis_results.append({
                'response_id': response.id,
                'analysis': feedback_analysis
            })
        
        logger.info(f"Análisis completado para {len(analysis_results)} respuestas")
        return f"Analizadas {len(analysis_results)} respuestas con feedback"
    
    except Exception as e:
        logger.error(f"Error en analyze_feedback: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def cleanup_old_data():
    """Limpia datos antiguos de la base de datos"""
    try:
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=90)
        
        # Limpiar mensajes antiguos
        old_messages_count, _ = TelegramMessage.objects.filter(
            created_at__lt=cutoff_date
        ).delete()
        
        # Limpiar respuestas antiguas
        old_responses_count, _ = AIResponse.objects.filter(
            created_at__lt=cutoff_date,
            status__in=['pending', 'failed']
        ).delete()
        
        logger.info(f"Limpieza completada: {old_messages_count} mensajes, {old_responses_count} respuestas")
        return f"Eliminados {old_messages_count} mensajes y {old_responses_count} respuestas antiguas"
    
    except Exception as e:
        logger.error(f"Error en cleanup_old_data: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def process_ai_response_batch(user_ids: list):
    """Procesa respuestas de IA para un lote de usuarios"""
    try:
        gemini = GeminiClient()
        processed = 0
        
        for user_id in user_ids:
            try:
                user = TelegramUser.objects.get(telegram_id=user_id)
                recent_message = TelegramMessage.objects.filter(user=user).latest('created_at')
                
                if recent_message and not AIResponse.objects.filter(message=recent_message).exists():
                    ai_result = gemini.get_response(recent_message.content, user_id)
                    
                    AIResponse.objects.create(
                        message=recent_message,
                        response_text=ai_result['response'],
                        confidence_score=ai_result['confidence_score'],
                        model_used=ai_result['model'],
                        status='sent'
                    )
                    processed += 1
            except Exception as e:
                logger.error(f"Error procesando usuario {user_id}: {str(e)}")
        
        logger.info(f"Procesadas {processed} respuestas de IA")
        return f"Procesadas {processed} respuestas"
    
    except Exception as e:
        logger.error(f"Error en process_ai_response_batch: {str(e)}")
        return f"Error: {str(e)}"


@shared_task
def generate_statistics():
    """Genera estadísticas del sistema"""
    try:
        stats = {
            'total_users': TelegramUser.objects.count(),
            'active_users': TelegramUser.objects.filter(is_active=True).count(),
            'total_messages': TelegramMessage.objects.count(),
            'total_ai_responses': AIResponse.objects.count(),
            'average_confidence': AIResponse.objects.values('confidence_score').average() or 0,
            'broadcasts_sent': Broadcast.objects.filter(status='sent').count(),
        }
        
        logger.info(f"Estadísticas generadas: {stats}")
        return stats
    
    except Exception as e:
        logger.error(f"Error en generate_statistics: {str(e)}")
        return f"Error: {str(e)}"
