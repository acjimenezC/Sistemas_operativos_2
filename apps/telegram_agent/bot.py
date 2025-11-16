"""
Bot de Telegram simple con python-telegram-bot
Integración con Gemini AI y polling
"""
import os
import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

# Django setup
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment_bot.settings')
django.setup()

from django.utils import timezone
from apps.telegram_agent.models import (
    TelegramUser, TelegramMessage, AIResponse,
    Survey, SurveyQuestion, SurveyOption, SurveyResponse, SurveyAnswer
)
from apps.jobs.models import JobOffer
from services.gemini_client import GeminiClient

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /start - Bienvenida"""
    try:
        user = await get_or_create_user(update.effective_user)
        
        welcome_text = f"""Hola {user.first_name}! Bienvenido al Bot de Reclutamiento

Soy tu asistente de IA especializado en empleos. Puedo ayudarte a:
- Buscar ofertas de trabajo personalizadas
- Responder preguntas sobre procesos de selección
- Dar consejos sobre CV y entrevistas

Comandos disponibles:
/ofertas - Ver las ultimas ofertas
/ayuda - Mostrar ayuda
/perfil - Ver tu perfil

En que puedo ayudarte hoy?"""
        
        await update.message.reply_text(welcome_text)
    except Exception as e:
        logger.error(f"Error en start: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al procesar tu solicitud.")


async def ofertas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ofertas - Mostrar ofertas publicadas"""
    try:
        jobs = await sync_to_async(lambda: list(
            JobOffer.objects.filter(status='published').order_by('-created_at')[:5]
        ))()
        
        if not jobs:
            await update.message.reply_text("No hay ofertas disponibles actualmente.")
            return
        
        await update.message.reply_text("Ultimas Ofertas de Trabajo")
        
        for job in jobs:
            try:
                job_text = f"""Titulo: {job.title}
Empresa: {job.company}

Ubicacion: {job.location}
Salario: {job.salary_range()}

Descripcion:
{job.description[:150]}..."""
                
                await update.message.reply_text(job_text)
                
                # Registrar visualización
                await sync_to_async(update_job_views)(job)
            except Exception as e:
                logger.error(f"Error procesando oferta {job.id}: {str(e)}")
                continue
    
    except Exception as e:
        logger.error(f"Error en ofertas: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al obtener ofertas.")


async def ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /ayuda - Mostrar ayuda"""
    try:
        help_text = """AYUDA - Comandos Disponibles

Busqueda de Empleo:
/ofertas - Ver ultimas ofertas
/perfil - Ver tu perfil

Conversacion:
Escribe cualquier pregunta sobre empleos y te ayudare con IA.

Soporte:
Si necesitas ayuda, contacta al administrador."""
        
        await update.message.reply_text(help_text, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Error en ayuda: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al procesar tu solicitud.")


async def perfil(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /perfil - Ver perfil"""
    try:
        user = await get_or_create_user(update.effective_user)
        msg_count = await sync_to_async(lambda: TelegramMessage.objects.filter(user=user).count())()
        
        profile_text = f"""Tu Perfil

Informacion:
Usuario: @{user.username}
Nombre: {user.first_name}

Estadisticas:
Mensajes: {msg_count}
Miembro desde: {user.created_at.strftime('%d/%m/%Y')}"""
        
        await update.message.reply_text(profile_text)
    except Exception as e:
        logger.error(f"Error en perfil: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al obtener tu perfil.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handler para mensajes generales"""
    
    try:
        logger.info(f"=== Nueva peticion recibida de {update.effective_user.username}")
        
        # Obtener o crear usuario (en thread sincrónico)
        user = await sync_to_async(get_or_create_user_sync)(update.effective_user)
        logger.info(f"Usuario: {user.username} (ID: {user.telegram_id})")
        
        # Verificar si está respondiendo encuesta
        if context.user_data.get('survey_mode'):
            # Seleccionar encuesta
            survey_id_str = update.message.text.strip()
            survey_mapping = context.user_data.get('available_surveys', {})
            
            if survey_id_str in survey_mapping:
                survey_id = survey_mapping[survey_id_str]
                survey = await sync_to_async(Survey.objects.get)(id=survey_id)
                tg_user = update.effective_user
                
                context.user_data['survey_mode'] = False
                await iniciar_encuesta(update, context, survey, user)
            else:
                await update.message.reply_text("Opción inválida. Intenta de nuevo con el número de la encuesta.")
            return
        
        if context.user_data.get('current_survey'):
            # Procesar respuesta de encuesta
            await procesar_respuesta_encuesta(update, context, update.message.text)
            return
        
        # Crear mensaje en BD (en thread sincrónico)
        msg = await sync_to_async(create_message_sync)(user, update.message)
        logger.info(f"Mensaje registrado en DB (ID: {msg.id})")
        
        # Obtener contexto (en thread sincrónico)
        available_jobs = await sync_to_async(get_available_jobs)()
        logger.info(f"Ofertas disponibles: {len(available_jobs)}")
        
        context_data = {'available_jobs': available_jobs}
        
        # Mostrar accion de "escribiendo"
        await update.message.chat.send_action("typing")
        logger.info("Enviando accion 'typing' a Telegram")
        
        # Obtener respuesta de Gemini (operación I/O, puede ser async)
        logger.info(f"Llamando a Gemini con: {update.message.text[:50]}...")
        gemini = GeminiClient()
        ai_result = gemini.get_response(
            update.message.text,
            str(user.telegram_id),
            context_data
        )
        logger.info(f"Respuesta Gemini obtenida. Error: {ai_result.get('error')}, Longitud: {len(ai_result['response'])}")
        
        # Guardar respuesta de IA (en thread sincrónico)
        ai_response = await sync_to_async(create_ai_response_sync)(msg, ai_result)
        logger.info(f"AIResponse guardada en DB (ID: {ai_response.id}, Status: {ai_response.status})")
        
        # Enviar respuesta
        response_text = ai_result['response']
        if not response_text or len(response_text.strip()) == 0:
            logger.warning("Respuesta vacia de Gemini")
            response_text = "No pude generar una respuesta. Por favor intenta de nuevo."
        
        logger.info(f"Enviando respuesta a Telegram ({len(response_text)} caracteres)...")
        
        if len(response_text) > 4000:
            chunks = [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]
            logger.info(f"Dividiendo en {len(chunks)} mensajes")
            for i, chunk in enumerate(chunks):
                await update.message.reply_text(chunk, parse_mode="HTML")
                logger.info(f"Chunk {i+1}/{len(chunks)} enviado")
        else:
            await update.message.reply_text(response_text, parse_mode="HTML")
            logger.info("Respuesta enviada exitosamente")
        
        logger.info(f"OK - Mensaje procesado completamente de {user.username}")
    
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"ERROR en handle_message: {str(e)}")
        logger.error(f"Traceback: {error_detail}")
        
        try:
            if update and update.message:
                await update.message.reply_text(f"ERROR: {str(e)[:100]}")
        except Exception as reply_error:
            logger.error(f"No se pudo enviar mensaje de error: {str(reply_error)}")


# Funciones síncronas para operaciones de BD
def get_or_create_user_sync(tg_user):
    """Obtener o crear usuario de Telegram (sincrónico)"""
    user, _ = TelegramUser.objects.get_or_create(
        telegram_id=str(tg_user.id),
        defaults={
            'username': tg_user.username or 'sin_usuario',
            'first_name': tg_user.first_name or 'Usuario',
            'last_name': tg_user.last_name or '',
        }
    )
    
    # Actualizar información si cambió
    if user.username != (tg_user.username or 'sin_usuario') or user.first_name != (tg_user.first_name or 'Usuario'):
        user.username = tg_user.username or 'sin_usuario'
        user.first_name = tg_user.first_name or 'Usuario'
        user.last_name = tg_user.last_name or ''
        user.save()
    
    return user


def create_message_sync(user, message):
    """Crear registro de mensaje (sincrónico)"""
    return TelegramMessage.objects.create(
        user=user,
        message_type='text',
        direction='incoming',
        content=message.text,
        telegram_message_id=message.message_id
    )


def get_available_jobs():
    """Obtener ofertas disponibles (sincrónico)"""
    return list(
        JobOffer.objects.filter(status='published').values(
            'title', 'company', 'location'
        )[:5]
    )


def create_ai_response_sync(msg, ai_result):
    """Crear respuesta de IA (sincrónico)"""
    return AIResponse.objects.create(
        message=msg,
        response_text=ai_result['response'],
        confidence_score=ai_result['confidence_score'],
        model_used=ai_result['model'],
        status='sent' if not ai_result.get('error') else 'failed'
    )


def update_job_views(job):
    """Actualizar vistas de oferta (sincrónico)"""
    job.views_count += 1
    job.save(update_fields=['views_count'])


async def get_or_create_user(tg_user):
    """Obtener o crear usuario de Telegram (async wrapper)"""
    return await sync_to_async(get_or_create_user_sync)(tg_user)


# ============ HANDLERS PARA ENCUESTAS ============

async def encuesta_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /encuesta - Iniciar encuesta disponible"""
    try:
        user = await get_or_create_user(update.effective_user)
        
        # Obtener encuestas activas
        surveys = await sync_to_async(lambda: list(
            Survey.objects.filter(status='active').order_by('-created_at')[:5]
        ))()
        
        if not surveys:
            await update.message.reply_text(
                "No hay encuestas disponibles en este momento.\n"
                "Vuelve pronto para participar en nuestras encuestas."
            )
            return
        
        if len(surveys) == 1:
            # Si hay una sola, iniciarla directamente
            await iniciar_encuesta(update, context, surveys[0], user)
        else:
            # Si hay varias, mostrar opciones
            text = "Encuestas Disponibles:\n\n"
            keyboard = []
            
            for idx, survey in enumerate(surveys, 1):
                text += f"{idx}. {survey.title}\n"
                text += f"   {survey.description[:50]}...\n\n"
                keyboard.append([f"{idx}. {survey.title}"])
            
            text += "\nEscribe el número de la encuesta que deseas responder."
            
            # Guardar en context para recuperar después
            context.user_data['available_surveys'] = {
                str(i): s.id for i, s in enumerate(surveys, 1)
            }
            context.user_data['survey_mode'] = True
            
            await update.message.reply_text(text)
    
    except Exception as e:
        logger.error(f"Error en encuesta_start: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al cargar encuestas.")


async def iniciar_encuesta(update: Update, context: ContextTypes.DEFAULT_TYPE, survey, user):
    """Iniciar la respuesta de una encuesta específica"""
    try:
        # Verificar si ya respondió
        existing_response = await sync_to_async(lambda: SurveyResponse.objects.filter(
            survey=survey,
            user=user
        ).first())()
        
        if existing_response and existing_response.is_completed:
            await update.message.reply_text(
                f"Ya respondiste la encuesta '{survey.title}' el "
                f"{existing_response.completed_at.strftime('%d/%m/%Y %H:%M')}."
            )
            return
        
        # Crear o recuperar respuesta
        survey_response, created = await sync_to_async(lambda: SurveyResponse.objects.get_or_create(
            survey=survey,
            user=user,
            defaults={'started_at': timezone.now()}
        ))()
        
        # Obtener primera pregunta
        first_question = await sync_to_async(lambda: survey.questions.filter(
            order__isnull=False
        ).order_by('order').first())()
        
        if not first_question:
            await update.message.reply_text(
                "Esta encuesta no tiene preguntas configuradas."
            )
            return
        
        # Guardar estado en context
        context.user_data['current_survey'] = survey.id
        context.user_data['survey_response'] = survey_response.id
        context.user_data['current_question_order'] = 0
        
        await enviar_pregunta(update, context, survey, first_question, 0)
    
    except Exception as e:
        logger.error(f"Error iniciar_encuesta: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al iniciar la encuesta.")


async def enviar_pregunta(update: Update, context: ContextTypes.DEFAULT_TYPE, survey, question, question_number):
    """Enviar una pregunta de la encuesta"""
    try:
        total_questions = await sync_to_async(lambda: survey.questions.count())()
        
        # Construir mensaje
        question_text = f"Pregunta {question_number + 1}/{total_questions}\n\n{question.question_text}"
        
        if question.is_required:
            question_text += " *"
        
        # Según tipo de pregunta
        if question.question_type == 'multiple':
            # Opciones múltiples
            options = await sync_to_async(lambda: list(
                question.options.all().order_by('order')
            ))()
            
            question_text += "\n\n"
            keyboard = []
            for idx, option in enumerate(options, 1):
                question_text += f"{idx}. {option.option_text}\n"
                keyboard.append([f"{idx}. {option.option_text}"])
            
            question_text += f"\nEscribe el número de tu opción:"
            
            context.user_data['question_type'] = 'multiple'
            context.user_data['question_options'] = {
                str(i): o.id for i, o in enumerate(options, 1)
            }
        
        elif question.question_type == 'yes_no':
            question_text += "\n\n1. Sí\n2. No"
            context.user_data['question_type'] = 'yes_no'
        
        elif question.question_type == 'rating':
            question_text += "\n\n1 ⭐ 2 ⭐ 3 ⭐ 4 ⭐ 5 ⭐\n\nEscribe un número del 1 al 5:"
            context.user_data['question_type'] = 'rating'
        
        elif question.question_type == 'text':
            question_text += "\n\nEscribe tu respuesta:"
            context.user_data['question_type'] = 'text'
        
        context.user_data['current_question_id'] = question.id
        context.user_data['current_question_order'] = question_number
        
        await update.message.reply_text(question_text)
    
    except Exception as e:
        logger.error(f"Error enviar_pregunta: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al procesar la pregunta.")


async def procesar_respuesta_encuesta(update: Update, context: ContextTypes.DEFAULT_TYPE, user_answer: str):
    """Procesar respuesta de usuario a pregunta de encuesta"""
    try:
        if not context.user_data.get('current_survey'):
            return
        
        survey_id = context.user_data['current_survey']
        survey_response_id = context.user_data['survey_response']
        question_id = context.user_data['current_question_id']
        question_type = context.user_data.get('question_type')
        
        # Obtener objetos
        survey = await sync_to_async(Survey.objects.get)(id=survey_id)
        survey_response = await sync_to_async(SurveyResponse.objects.get)(id=survey_response_id)
        question = await sync_to_async(SurveyQuestion.objects.get)(id=question_id)
        
        # Procesar según tipo
        answer_data = {
            'response': survey_response,
            'question': question,
            'answered_at': timezone.now()
        }
        
        if question_type == 'multiple':
            option_id_str = user_answer.strip()
            option_mapping = context.user_data.get('question_options', {})
            
            if option_id_str not in option_mapping:
                await update.message.reply_text("Opción inválida. Intenta de nuevo.")
                return
            
            option = await sync_to_async(SurveyOption.objects.get)(
                id=option_mapping[option_id_str]
            )
            answer_data['selected_option'] = option
        
        elif question_type == 'yes_no':
            if user_answer.strip() == '1':
                answer_data['answer_text'] = 'yes'
            elif user_answer.strip() == '2':
                answer_data['answer_text'] = 'no'
            else:
                await update.message.reply_text("Escribe 1 para Sí o 2 para No.")
                return
        
        elif question_type == 'rating':
            try:
                rating = int(user_answer.strip())
                if rating < 1 or rating > 5:
                    raise ValueError
                answer_data['rating'] = rating
            except ValueError:
                await update.message.reply_text("Escribe un número del 1 al 5.")
                return
        
        elif question_type == 'text':
            answer_data['answer_text'] = user_answer
        
        # Guardar respuesta
        await sync_to_async(SurveyAnswer.objects.create)(**answer_data)
        
        # Obtener siguiente pregunta
        current_order = context.user_data.get('current_question_order', 0)
        next_question = await sync_to_async(lambda: survey.questions.filter(
            order__gt=current_order
        ).order_by('order').first())()
        
        if not next_question:
            # Encuesta completada
            survey_response.is_completed = True
            survey_response.completed_at = timezone.now()
            await sync_to_async(survey_response.save)()
            
            context.user_data.pop('current_survey', None)
            
            await update.message.reply_text(
                f"¡Gracias por responder la encuesta '{survey.title}'!\n\n"
                "Tus respuestas han sido registradas exitosamente."
            )
        else:
            # Enviar siguiente pregunta
            next_order = next_question.order if next_question.order else current_order + 1
            await enviar_pregunta(update, context, survey, next_question, next_order)
    
    except Exception as e:
        logger.error(f"Error procesar_respuesta_encuesta: {str(e)}", exc_info=True)
        await update.message.reply_text("Error al procesar tu respuesta.")


def run_bot():
    """Ejecutar el bot en polling mode"""
    if not TELEGRAM_TOKEN:
        logger.error('TELEGRAM_TOKEN no está configurado en .env')
        return
    
    logger.info("Bot iniciando en modo polling...")
    
    # Crear aplicación del bot
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    
    # Agregar handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ofertas", ofertas))
    application.add_handler(CommandHandler("ayuda", ayuda))
    application.add_handler(CommandHandler("perfil", perfil))
    application.add_handler(CommandHandler("encuesta", encuesta_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    logger.info("Bot iniciado exitosamente. Esperando mensajes...")
    logger.info("Presiona Ctrl+C para detener el bot")
    
    # Iniciar polling
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    run_bot()
