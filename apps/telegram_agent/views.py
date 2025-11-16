"""
Vistas para Telegram Webhook y Panel Web
"""
import json
import logging
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import Count, Q, Avg
from dotenv import load_dotenv
import os
from datetime import timedelta
from django.contrib.auth.models import User

from apps.telegram_agent.models import (
    TelegramUser, TelegramMessage, AIResponse, Broadcast, TelegramConfig,
    Survey, SurveyQuestion, SurveyOption, SurveyResponse, SurveyAnswer
)
from apps.jobs.models import JobOffer
from services.gemini_client import GeminiClient
from services.gemini_2_cliente import Gemini2Client
from services.telegram_api import publish_generated_image

load_dotenv()
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')


@login_required(login_url='/admin/login/')
def dashboard(request):
    """Dashboard con estadisticas generales"""
    context = {
        'total_users': TelegramUser.objects.count(),
        'total_messages': TelegramMessage.objects.count(),
        'total_responses': AIResponse.objects.count(),
        'total_jobs': JobOffer.objects.filter(status='published').count(),
        'recent_messages': TelegramMessage.objects.select_related('user', 'ai_response').order_by('-created_at')[:10],
    }
    return render(request, 'telegram_agent/dashboard.html', context)


@login_required(login_url='/admin/login/')
def conversations(request):
    """Historial de conversaciones con opcion de feedback"""
    messages = TelegramMessage.objects.select_related('user', 'ai_response').order_by('-created_at')
    
    context = {
        'messages': messages,
    }
    return render(request, 'telegram_agent/conversations.html', context)


@login_required(login_url='/admin/login/')
def analytics(request):
    """Pagina de analítica con estadisticas detalladas"""
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    # Estadisticas basicas
    active_users = TelegramUser.objects.filter(
        messages__created_at__gte=timezone.now() - timedelta(days=30)
    ).distinct().count()
    
    messages_today = TelegramMessage.objects.filter(
        created_at__date=today
    ).count()
    
    avg_confidence = AIResponse.objects.aggregate(Avg('confidence_score'))['confidence_score__avg'] or 0
    avg_feedback = AIResponse.objects.aggregate(Avg('feedback_score'))['feedback_score__avg'] or 0
    
    # Empleos mas solicitados (por menciones en mensajes)
    top_jobs = []
    for job in JobOffer.objects.filter(status='published'):
        count = TelegramMessage.objects.filter(
            content__icontains=job.title
        ).count()
        if count > 0:
            top_jobs.append({
                'title': job.title,
                'search_count': count,
            })
    
    # Agregar porcentajes
    if top_jobs:
        max_count = max([j['search_count'] for j in top_jobs])
        for job in top_jobs:
            job['search_percentage'] = (job['search_count'] / max_count * 100) if max_count > 0 else 0
    else:
        top_jobs = []
    
    # Actividad ultimos 7 dias
    activity_last_7_days = []
    max_activity = 1
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        count = TelegramMessage.objects.filter(created_at__date=day).count()
        activity_last_7_days.append({
            'date': day,
            'count': count,
        })
        if count > max_activity:
            max_activity = count
    
    for item in activity_last_7_days:
        item['percentage'] = (item['count'] / max_activity * 100) if max_activity > 0 else 0
    
    # Calidad de respuestas
    excellent = AIResponse.objects.filter(feedback_score__gte=5).count()
    good = AIResponse.objects.filter(feedback_score=4).count()
    ok = AIResponse.objects.filter(feedback_score=3).count()
    bad = AIResponse.objects.filter(feedback_score__lte=2).count()
    total = excellent + good + ok + bad
    
    context = {
        'active_users': active_users,
        'messages_today': messages_today,
        'avg_confidence': avg_confidence,
        'avg_feedback': avg_feedback,
        'top_jobs': top_jobs[:5],
        'activity_last_7_days': activity_last_7_days,
        'excellent_count': excellent,
        'good_count': good,
        'ok_count': ok,
        'bad_count': bad,
        'quality_excellent': (excellent / total * 100) if total > 0 else 0,
        'quality_good': (good / total * 100) if total > 0 else 0,
        'quality_ok': (ok / total * 100) if total > 0 else 0,
        'quality_bad': (bad / total * 100) if total > 0 else 0,
        'user_statistics': [
            {
                'user': user,
                'message_count': TelegramMessage.objects.filter(user=user).count(),
                'response_count': AIResponse.objects.filter(message__user=user).count(),
                'avg_feedback': AIResponse.objects.filter(message__user=user).aggregate(Avg('feedback_score'))['feedback_score__avg'] or 0,
            }
            for user in TelegramUser.objects.all()[:10]
        ],
    }
    
    return render(request, 'telegram_agent/analytics.html', context)


@login_required(login_url='/admin/login/')
def image_generator(request):
    """Pagina para generar imagenes con Gemini"""
    context = {
        'generated_images': [],  # TODO: Crear modelo de imagenes
    }
    return render(request, 'telegram_agent/image_generator.html', context)


@login_required(login_url='/admin/login/')
def generate_image(request):
    """API para generar imagenes, carruseles y videos con Stable Diffusion"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Metodo no permitido'})
    
    try:
        data = json.loads(request.body)
        content_type = data.get('content_type', 'image')
        theme = data.get('theme', '')
        description = data.get('description', '')
        
        logger.info(f"[generate_image] Datos recibidos: {data}")
        
        if not theme or not description:
            return JsonResponse({'success': False, 'error': 'Tema y descripción son requeridos'})
        
        logger.info(f"[generate_image] Generando {content_type} - tema={theme}")
        
        # Generar imagen con Gemini 2
        gemini2_client = Gemini2Client()
        
        if not gemini2_client.is_configured():
            logger.error("[generate_image] Gemini 2 no está configurado")
            return JsonResponse({
                'success': False,
                'error': 'Gemini 2 no está configurado',
                'details': 'Asegúrate de tener GEMINI_API_KEY_2 en el archivo .env'
            })
        
        result = gemini2_client.generate_image(description, content_type, theme=theme)
        
        if not result or not result.get('success'):
            logger.error(f"[generate_image] Error generando imagen: {result}")
            return JsonResponse({
                'success': False,
                'error': result.get('error') if result else 'Error desconocido',
                'details': result.get('details') if result else None
            })
        
        # Convertir imagen a base64 para transmitir en JSON
        import base64
        image_base64 = base64.b64encode(result['image_data']).decode('utf-8')
        
        logger.info(f"[generate_image] Imagen generada exitosamente ({result['size_bytes']} bytes)")
        
        # Preparar respuesta
        response_data = {
            'success': True,
            'image_base64': f"data:image/png;base64,{image_base64}",
            'content_type': content_type,
            'theme': theme,
            'description': description,
            'model': result.get('model', 'gemini-2.0-flash-exp'),
            'size_bytes': result['size_bytes']
        }
        
        # Si la imagen viene del caché, solo loguear sin enviar aviso al cliente
        if result.get('from_cache'):
            logger.info(f"[generate_image] Imagen del caché utilizada: {result.get('message', 'Usando imagen predefinida')}")
        
        return JsonResponse(response_data)
    
    except json.JSONDecodeError as e:
        logger.error(f"[generate_image] Error en JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': 'JSON inválido'})
    except Exception as e:
        logger.error(f"[generate_image] Error: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': str(e)})


def publish_image(request):
    """API para publicar imagen generada en Telegram"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Metodo no permitido'})
    
    try:
        data = json.loads(request.body)
        theme = data.get('theme', '').strip()
        description = data.get('description', '').strip()
        image_base64 = data.get('image_base64', '').strip()
        
        logger.info(f"[publish_image] Publicando imagen - tema={theme}")
        logger.info(f"[publish_image] image_base64 tamaño: {len(image_base64)} caracteres")
        
        # Validación más detallada
        if not image_base64 or len(image_base64) < 100:
            logger.error(f"[publish_image] image_base64 inválido o muy corto")
            return JsonResponse({'success': False, 'error': 'No hay imagen para publicar o está incompleta'})
        
        if not theme or not description:
            return JsonResponse({'success': False, 'error': 'Tema y descripción son requeridos'})
        
        logger.info(f"[publish_image] Iniciando publicación en Telegram...")
        
        # Publicar imagen en Telegram
        success = publish_generated_image(image_base64, theme, description)
        
        if not success:
            logger.error(f"[publish_image] Fallo al publicar en Telegram")
            return JsonResponse({
                'success': False,
                'error': 'No se pudo publicar en Telegram. Verifica logs y TELEGRAM_CHANNEL_ID'
            })
        
        logger.info(f"[publish_image] ✅ Imagen publicada exitosamente en Telegram")
        
        return JsonResponse({
            'success': True, 
            'message': 'Imagen publicada en el canal de Telegram',
            'theme': theme,
            'description': description
        })
    
    except json.JSONDecodeError as e:
        logger.error(f"[publish_image] Error decodificando JSON: {str(e)}")
        return JsonResponse({'success': False, 'error': 'JSON inválido en la solicitud'})
    
    except Exception as e:
        logger.error(f"[publish_image] Error publicando imagen: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return JsonResponse({'success': False, 'error': f'Error del servidor: {str(e)}'})
        return JsonResponse({'success': False, 'error': str(e)})


@login_required(login_url='/admin/login/')
def feedback_response(request, response_id):
    """API para enviar feedback de respuestas IA"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Metodo no permitido'})
    
    try:
        data = json.loads(request.body)
        response_obj = get_object_or_404(AIResponse, id=response_id)
        
        response_obj.feedback_score = int(data.get('rating', 3))
        response_obj.feedback_text = data.get('feedback', '')
        response_obj.save()
        
        return JsonResponse({'success': True, 'message': 'Feedback registrado'})
    
    except Exception as e:
        logger.error(f"Error en feedback: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})


@csrf_exempt
def webhook(request):
    """
    Webhook para recibir actualizaciones de Telegram
    POST /telegram/webhook/
    """
    if request.method == 'POST':
        try:
            update_data = json.loads(request.body)
            
            # Procesar actualización
            process_telegram_update(update_data)
            
            return JsonResponse({'ok': True})
        except Exception as e:
            logger.error(f"Error en webhook: {str(e)}")
            return JsonResponse({'ok': False, 'error': str(e)}, status=400)
    
    return JsonResponse({'ok': True, 'message': 'Webhook ready'})


def process_telegram_update(update_data: dict):
    """
    Procesa una actualización de Telegram
    Crea mensajes, genera respuestas con Gemini y envía respuestas
    """
    try:
        if 'message' not in update_data:
            return
        
        message_data = update_data['message']
        user_data = message_data.get('from', {})
        
        # Obtener o crear usuario
        telegram_id = str(user_data.get('id'))
        user, created = TelegramUser.objects.get_or_create(
            telegram_id=telegram_id,
            defaults={
                'username': user_data.get('username', ''),
                'first_name': user_data.get('first_name', ''),
                'last_name': user_data.get('last_name', ''),
            }
        )
        
        # Determinar tipo de mensaje
        message_type = 'text'
        content = message_data.get('text', '')
        
        if message_data.get('photo'):
            message_type = 'photo'
            content = '[Foto enviada]'
        elif message_data.get('document'):
            message_type = 'document'
            content = '[Documento enviado]'
        elif message_data.get('voice'):
            message_type = 'voice'
            content = '[Mensaje de voz]'
        
        # Crear registro de mensaje
        msg = TelegramMessage.objects.create(
            user=user,
            message_type=message_type,
            direction='incoming',
            content=content,
            telegram_message_id=message_data.get('message_id'),
            metadata=message_data
        )
        
        # No responder a mensajes que no sean texto
        if message_type != 'text':
            return
        
        # Obtener contexto
        available_jobs = list(
            JobOffer.objects.filter(status='published').values(
                'title', 'company', 'location'
            )[:5]
        )
        
        context = {
            'available_jobs': available_jobs
        }
        
        # Generar respuesta con Gemini
        gemini = GeminiClient()
        ai_result = gemini.get_response(content, telegram_id, context)
        
        # Guardar respuesta de IA
        ai_response = AIResponse.objects.create(
            message=msg,
            response_text=ai_result['response'],
            confidence_score=ai_result['confidence_score'],
            model_used=ai_result['model'],
            status='pending'
        )
        
        logger.info(f"Mensaje procesado de {user.username}: {content[:50]}")
    
    except Exception as e:
        logger.error(f"Error procesando actualización: {str(e)}")


# ============ VISTAS DEL PANEL WEB ============

@login_required
def dashboard(request):
    """Dashboard principal del panel de administración"""
    context = {
        'total_users': TelegramUser.objects.count(),
        'total_messages': TelegramMessage.objects.count(),
        'total_jobs': JobOffer.objects.count(),
        'published_jobs': JobOffer.objects.filter(status='published').count(),
        'pending_responses': AIResponse.objects.filter(status='pending').count(),
        'recent_messages': TelegramMessage.objects.order_by('-created_at')[:10],
        'recent_jobs': JobOffer.objects.order_by('-created_at')[:5],
    }
    return render(request, 'telegram_agent/dashboard.html', context)


@login_required
def users_list(request):
    """Lista de usuarios de Telegram"""
    users = TelegramUser.objects.all().order_by('-created_at')
    
    # Búsqueda
    search = request.GET.get('search')
    if search:
        from django.db.models import Q
        users = users.filter(
            Q(username__icontains=search) | 
            Q(first_name__icontains=search) | 
            Q(email__icontains=search)
        )
    
    context = {
        'users': users,
        'search': search,
        'total': TelegramUser.objects.count(),
    }
    return render(request, 'telegram_agent/users_list.html', context)


@login_required
def user_detail(request, user_id):
    """Detalle de un usuario específico"""
    user = get_object_or_404(TelegramUser, telegram_id=user_id)
    messages = TelegramMessage.objects.filter(user=user).order_by('-created_at')
    ai_responses = AIResponse.objects.filter(message__user=user).order_by('-created_at')
    
    context = {
        'user': user,
        'messages': messages[:50],
        'ai_responses': ai_responses[:20],
        'message_count': TelegramMessage.objects.filter(user=user).count(),
        'response_count': AIResponse.objects.filter(message__user=user).count(),
    }
    return render(request, 'telegram_agent/user_detail.html', context)


@login_required
def conversations_list(request):
    """Lista de conversaciones"""
    messages = TelegramMessage.objects.select_related('user').order_by('-created_at')
    
    context = {
        'messages': messages[:100],
        'total': TelegramMessage.objects.count(),
    }
    return render(request, 'telegram_agent/conversations_list.html', context)


@login_required
def ai_feedback(request):
    """Gestionar feedback de respuestas de IA"""
    if request.method == 'POST':
        response_id = request.POST.get('response_id')
        feedback = request.POST.get('feedback')
        score = request.POST.get('score')
        
        ai_response = get_object_or_404(AIResponse, id=response_id)
        ai_response.feedback = feedback
        ai_response.feedback_score = int(score) if score else None
        ai_response.status = 'rated'
        ai_response.save()
        
        return redirect('telegram_agent:ai_feedback')
    
    responses = AIResponse.objects.select_related('message__user').order_by('-created_at')
    
    context = {
        'responses': responses[:50],
        'pending': AIResponse.objects.filter(status='pending').count(),
    }
    return render(request, 'telegram_agent/ai_feedback.html', context)


@login_required
def broadcasts_list(request):
    """Lista de broadcasts"""
    broadcasts = Broadcast.objects.order_by('-created_at')
    
    context = {
        'broadcasts': broadcasts,
    }
    return render(request, 'telegram_agent/broadcasts_list.html', context)


@login_required
def create_broadcast(request):
    """Crear nuevo broadcast"""
    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        scheduled_at = request.POST.get('scheduled_at')
        
        broadcast = Broadcast.objects.create(
            title=title,
            content=content,
            created_by=request.user,
            status='draft'
        )
        
        if scheduled_at:
            broadcast.scheduled_at = scheduled_at
            broadcast.status = 'scheduled'
            broadcast.save()
        
        return redirect('telegram_agent:broadcasts_list')
    
    return render(request, 'telegram_agent/create_broadcast.html')


# ============ VISTAS PARA ENCUESTAS ============

@login_required(login_url='/admin/login/')
def surveys_list(request):
    """Lista de encuestas con estadísticas"""
    surveys = Survey.objects.annotate(
        total_responses=Count('responses'),
        completed_responses=Count('responses', filter=Q(responses__is_completed=True))
    ).order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')
    
    if status_filter:
        surveys = surveys.filter(status=status_filter)
    if type_filter:
        surveys = surveys.filter(survey_type=type_filter)
    
    context = {
        'surveys': surveys,
        'status_choices': Survey.STATUS_CHOICES,
        'type_choices': Survey.SURVEY_TYPES,
        'current_status': status_filter,
        'current_type': type_filter,
    }
    return render(request, 'telegram_agent/surveys_list.html', context)


@login_required(login_url='/admin/login/')
def survey_detail(request, survey_id):
    """Detalle de encuesta con opción de responder (admin)"""
    survey = get_object_or_404(Survey, id=survey_id)
    questions = survey.questions.order_by('order')
    
    # No verificar respuesta anterior para admin (solo para usuarios Telegram)
    user_response = None
    
    context = {
        'survey': survey,
        'questions': questions,
        'user_response': user_response,
        'total_responses': survey.responses.count(),
        'completed_responses': survey.responses.filter(is_completed=True).count(),
    }
    return render(request, 'telegram_agent/survey_detail.html', context)


@login_required(login_url='/admin/login/')
def survey_results(request, survey_id):
    """Análisis detallado de respuestas de encuesta"""
    survey = get_object_or_404(Survey, id=survey_id)
    responses = SurveyResponse.objects.filter(survey=survey, is_completed=True)
    questions = survey.questions.order_by('order')
    
    # Estadísticas generales
    total_responses = survey.responses.count()
    completed_responses = responses.count()
    completion_rate = (completed_responses / total_responses * 100) if total_responses > 0 else 0
    
    # Análisis por pregunta
    question_stats = []
    for question in questions:
        stats = {
            'question': question,
            'question_type': question.question_type,
        }
        
        answers = SurveyAnswer.objects.filter(
            response__survey=survey,
            response__is_completed=True,
            question=question
        )
        
        if question.question_type == 'multiple':
            # Contar opciones seleccionadas
            options_count = {}
            for option in question.options.all():
                count = answers.filter(selected_option=option).count()
                options_count[option.option_text] = {
                    'count': count,
                    'percentage': (count / completed_responses * 100) if completed_responses > 0 else 0
                }
            stats['options'] = options_count
        
        elif question.question_type == 'rating':
            # Promedio de ratings
            avg_rating = answers.aggregate(Avg('rating'))['rating__avg'] or 0
            stats['average_rating'] = round(avg_rating, 2)
            stats['rating_distribution'] = {
                '5': answers.filter(rating=5).count(),
                '4': answers.filter(rating=4).count(),
                '3': answers.filter(rating=3).count(),
                '2': answers.filter(rating=2).count(),
                '1': answers.filter(rating=1).count(),
            }
        
        elif question.question_type == 'yes_no':
            # Contar sí/no
            yes_count = answers.filter(answer_text='yes').count()
            no_count = answers.filter(answer_text='no').count()
            stats['yes_count'] = yes_count
            stats['no_count'] = no_count
            stats['yes_percentage'] = (yes_count / completed_responses * 100) if completed_responses > 0 else 0
        
        elif question.question_type == 'text':
            # Listar respuestas texto
            text_answers = answers.values_list('answer_text', flat=True)
            stats['text_answers'] = text_answers
        
        stats['answer_count'] = answers.count()
        question_stats.append(stats)
    
    context = {
        'survey': survey,
        'question_stats': question_stats,
        'total_responses': total_responses,
        'completed_responses': completed_responses,
        'completion_rate': round(completion_rate, 2),
    }
    return render(request, 'telegram_agent/survey_results.html', context)


# ============ VISTAS PARA GENERACIÓN AUTOMÁTICA DE ENCUESTAS CON GEMINI ============

@login_required(login_url='/admin/login/')
def create_survey_with_ai(request):
    """Crear encuesta automáticamente con Gemini basado en prompt"""
    if request.method == 'POST':
        prompt = request.POST.get('prompt', '').strip()
        survey_title = request.POST.get('title', '').strip()
        survey_type = request.POST.get('survey_type', 'other')
        
        if not prompt or not survey_title:
            return render(request, 'telegram_agent/create_survey_ai.html', {
                'error': 'Por favor completa el título y el prompt'
            })
        
        try:
            # Generar estructura de encuesta con Gemini
            gemini = GeminiClient()
            
            generation_prompt = f"""
Genera una estructura JSON para una encuesta con las siguientes características:

TÍTULO: {survey_title}
TIPO: {survey_type}
DESCRIPCIÓN DEL USUARIO: {prompt}

El JSON debe tener esta estructura exacta:
{{
    "title": "Título de la encuesta",
    "description": "Descripción basada en el prompt",
    "questions": [
        {{
            "question_text": "Pregunta 1",
            "question_type": "multiple",
            "is_required": true,
            "order": 1,
            "options": [
                {{"option_text": "Opción 1", "order": 1}},
                {{"option_text": "Opción 2", "order": 2}},
                {{"option_text": "Opción 3", "order": 3}}
            ]
        }},
        {{
            "question_text": "Pregunta 2",
            "question_type": "rating",
            "is_required": true,
            "order": 2,
            "options": []
        }},
        {{
            "question_text": "Pregunta 3",
            "question_type": "yes_no",
            "is_required": true,
            "order": 3,
            "options": []
        }},
        {{
            "question_text": "Pregunta 4",
            "question_type": "text",
            "is_required": false,
            "order": 4,
            "options": []
        }}
    ]
}}

IMPORTANTE:
- Genera 3-5 preguntas bien estructuradas
- Usa tipos variados: multiple, rating, yes_no, text
- Las opciones múltiples deben tener 3-4 opciones
- Los tipos rating y yes_no NO tienen opciones
- El JSON debe ser válido y parseable
- Responde SOLO con el JSON, sin explicaciones adicionales
"""
            
            result = gemini.get_response(generation_prompt)
            response_text = result.get('response', '')
            
            # Parsear JSON
            import json
            try:
                # Limpiar la respuesta si tiene código markdown
                if '```json' in response_text:
                    response_text = response_text.split('```json')[1].split('```')[0]
                elif '```' in response_text:
                    response_text = response_text.split('```')[1].split('```')[0]
                
                survey_data = json.loads(response_text.strip())
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON: {str(e)}")
                return render(request, 'telegram_agent/create_survey_ai.html', {
                    'error': f'Error al procesar la respuesta de Gemini: {str(e)}'
                })
            
            # Crear encuesta
            survey = Survey.objects.create(
                title=survey_data.get('title', survey_title),
                description=survey_data.get('description', prompt),
                survey_type=survey_type,
                status='draft',
                created_by=request.user
            )
            
            # Crear preguntas y opciones
            for question_data in survey_data.get('questions', []):
                question = SurveyQuestion.objects.create(
                    survey=survey,
                    question_text=question_data.get('question_text'),
                    question_type=question_data.get('question_type'),
                    order=question_data.get('order', 1),
                    is_required=question_data.get('is_required', True)
                )
                
                # Crear opciones si es necesario
                for option_data in question_data.get('options', []):
                    SurveyOption.objects.create(
                        question=question,
                        option_text=option_data.get('option_text'),
                        order=option_data.get('order', 1)
                    )
            
            logger.info(f"Encuesta creada exitosamente: {survey.id}")
            
            return redirect('telegram_agent:survey_detail', survey_id=survey.id)
        
        except Exception as e:
            logger.error(f"Error creando encuesta con IA: {str(e)}", exc_info=True)
            return render(request, 'telegram_agent/create_survey_ai.html', {
                'error': f'Error al generar la encuesta: {str(e)}'
            })
    
    context = {
        'survey_types': Survey.SURVEY_TYPES,
    }
    return render(request, 'telegram_agent/create_survey_ai.html', context)
