import os
import logging
from telegram import Bot
from telegram.error import TelegramError
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHANNEL_ID = os.getenv('TELEGRAM_CHANNEL_ID')

def publish_job_offer(job):
    """Publica una oferta de trabajo en el canal de Telegram"""
    if not TOKEN or not CHANNEL_ID:
        logger.warning('TELEGRAM_TOKEN or TELEGRAM_CHANNEL_ID not configured')
        return False
    
    try:
        bot = Bot(token=TOKEN)
        
        message = (
            f"💼 <b>{job.title}</b>\n"
            f"🏢 {job.company}\n"
            f"📍 {job.location}\n"
            f"💰 {job.salary_range()}\n\n"
            f"{job.description}\n\n"
            f"👉 <a href='{job.apply_link}'>APLICAR AQUÍ</a>"
        )
        
        bot.send_message(chat_id=CHANNEL_ID, text=message, parse_mode='HTML')
        logger.info(f"Offer published: {job.title}")
        return True
    except TelegramError as e:
        logger.error(f"Error publishing offer: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return False


def publish_generated_image(image_base64: str, theme: str, description: str):
    """Publica una imagen generada a todos los usuarios activos del bot"""
    if not TOKEN:
        logger.warning('TELEGRAM_TOKEN not configured')
        return False
    
    try:
        import io
        import base64
        import requests
        from apps.telegram_agent.models import TelegramUser
        
        # Obtener todos los usuarios activos
        active_users = TelegramUser.objects.filter(is_active=True)
        
        if not active_users.exists():
            logger.warning('[publish_generated_image] No hay usuarios activos para enviar imagen')
            return False
        
        logger.info(f'[publish_generated_image] Enviando imagen a {active_users.count()} usuarios')
        
        # Decodificar base64 una sola vez
        if ',' in image_base64:
            image_data = image_base64.split(',')[1]
        else:
            image_data = image_base64
        
        try:
            image_bytes = base64.b64decode(image_data)
        except Exception as e:
            logger.error(f'[publish_generated_image] Error decodificando base64: {str(e)}')
            return False
        
        # Crear mensaje
        caption = f"<b>{theme.title()}</b>\n\n{description}\n\n📱 Generado con IA - Magneto Empleos"
        
        # Usar API REST de Telegram
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        
        # Enviar a cada usuario
        success_count = 0
        error_count = 0
        
        for user in active_users:
            try:
                # Crear BytesIO fresh para cada usuario
                image_io = io.BytesIO(image_bytes)
                
                files = {'photo': ('image.png', image_io, 'image/png')}
                data = {
                    'chat_id': user.telegram_id,
                    'caption': caption,
                    'parse_mode': 'HTML'
                }
                
                logger.info(f'[publish_generated_image] Enviando a usuario {user.telegram_id}...')
                
                response = requests.post(url, files=files, data=data, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f'[publish_generated_image] ✅ Enviada a usuario {user.username or user.telegram_id}')
                    success_count += 1
                else:
                    logger.error(f'[publish_generated_image] ❌ Error enviando a {user.telegram_id}: {response.status_code}')
                    logger.error(f'[publish_generated_image] Response: {response.text[:200]}')
                    error_count += 1
            
            except Exception as e:
                logger.error(f'[publish_generated_image] Error enviando a usuario {user.telegram_id}: {str(e)}')
                error_count += 1
        
        logger.info(f'[publish_generated_image] Resumen: {success_count} exitosas, {error_count} fallidas')
        
        # Retornar True si al menos una fue exitosa
        return success_count > 0
    
    except Exception as e:
        logger.error(f'[publish_generated_image] Error inesperado: {str(e)}')
        import traceback
        logger.error(traceback.format_exc())
        return False