# Bot de Reclutamiento - Telegram + Django + Gemini AI

Bot inteligente para gestionar ofertas de trabajo, generar encuestas automáticas y responder preguntas sobre empleos usando IA.

## 🚀 Características Principales

- ✅ **Bot de Telegram** - Interacción con usuarios en tiempo real
- ✅ **Respuestas con IA (Gemini)** - Generación automática de respuestas inteligentes
- ✅ **Generación de Imágenes** - Creación de imágenes con Gemini 2.0 Flash
- ✅ **Sistema de Encuestas** - Crear encuestas automáticamente con IA
- ✅ **Dashboard Web** - Panel de administración completo
- ✅ **Análisis de Datos** - Estadísticas y visualizaciones
- ✅ **Gestión de Ofertas** - CRUD completo de ofertas de trabajo
- ✅ **Publicación de Imágenes** - Envío automático a usuarios

## 📋 Inicio Rápido

### 1. Configurar Variables de Entorno

Crea archivo `.env` en la raíz del proyecto:

```env
# Telegram
TELEGRAM_TOKEN=tu_token_aqui
TELEGRAM_CHANNEL_ID=tu_channel_id

# Gemini AI
GEMINI_API_KEY=tu_api_key_gemini
GEMINI_API_KEY_2=tu_api_key_gemini_2  # Para imagen generation

# Django
DJANGO_SECRET_KEY=tu_clave_secreta_muy_segura
DEBUG=1
```

### 2. Preparar Base de Datos

```bash
python manage.py migrate
python manage.py createsuperuser
```

### 3. Ejecutar en Dos Terminales

**Terminal 1 - Django Server:**
```bash
python manage.py runserver
# O en producción:
python manage.py runserver 0.0.0.0:8000
```

**Terminal 2 - Bot de Telegram:**
```bash
python manage.py runbot
```

## 🎮 Comandos del Bot

| Comando | Descripción |
|---------|------------|
| `/start` | Mensaje de bienvenida |
| `/ofertas` | Ver últimas 5 ofertas |
| `/perfil` | Ver tu perfil y estadísticas |
| `/ayuda` | Mostrar ayuda |
| `/encuesta` | Responder encuestas disponibles |
| Mensaje cualquiera | Gemini responde automáticamente |

## 🌐 Acceso al Panel Admin

**URL:** http://localhost:8000/admin

**Usuario:** El que creaste con `createsuperuser`

### Secciones del Admin

- **Dashboard** - Estadísticas generales `/telegram/dashboard/`
- **Mensajes** - Historial de conversaciones `/telegram/conversations/`
- **Análisis** - Gráficos y estadísticas `/telegram/analytics/`
- **Imágenes** - Generador de imágenes `/telegram/image-generator/`
- **Encuestas** - Sistema de sondeos `/telegram/surveys/`

## 📊 Sistema de Encuestas (HU11)

### Crear Encuesta Automáticamente

1. Ve a `/telegram/surveys/`
2. Haz clic en **"✨ Crear con Gemini"**
3. Describe qué quieres preguntar
4. **Gemini genera automáticamente** la estructura completa

### Tipos de Preguntas Soportadas

- ✅ Opción múltiple
- ✅ Sí/No
- ✅ Calificación (1-5 estrellas)
- ✅ Texto libre

### Ver Resultados

- **Lista:** `/telegram/surveys/`
- **Detalle:** `/telegram/surveys/{id}/`
- **Resultados:** `/telegram/surveys/{id}/results/`

### En el Bot de Telegram

```
Usuario: /encuesta
Bot: "Selecciona una encuesta: 1. Satisfacción  2. Bienestar"
Usuario: 1
Bot: "Pregunta 1/5: ¿Qué tal tu experiencia?"
... (continúa automáticamente)
Bot: "¡Gracias por responder!"
```

## 🖼️ Generación de Imágenes

### Acceso

1. Dashboard → **Imágenes** (o `/telegram/image-generator/`)
2. Ingresa un prompt en español
3. Selecciona el tema (recruitment, eventos, etc.)
4. Genera y publica a todos los usuarios

### Características

- ✅ Gemini 2.0 Flash Thinking Exp
- ✅ Traducción automática ES → EN
- ✅ Sistema de 3 niveles de fallback
- ✅ Caché automático de imágenes
- ✅ Publicación directa a usuarios

## 📁 Estructura del Código

```
apps/
├── jobs/
│   ├── models.py           # JobOffer
│   ├── views.py
│   ├── urls.py
│   └── admin.py
│
└── telegram_agent/
    ├── models.py           # Survey, SurveyQuestion, etc.
    ├── views.py            # Vistas del dashboard
    ├── urls.py
    ├── bot.py              # Lógica del bot Telegram
    ├── admin.py            # Admin panel
    ├── templatetags/
    │   └── math_filters.py # Filtros personalizados
    ├── templates/
    │   └── telegram_agent/
    │       ├── dashboard.html
    │       ├── conversations.html
    │       ├── analytics.html
    │       ├── image_generator.html
    │       ├── surveys_list.html
    │       ├── survey_detail.html
    │       ├── survey_results.html
    │       ├── create_survey_ai.html
    │       └── base.html
    └── migrations/

services/
├── gemini_client.py        # IA para respuestas
├── gemini_2_cliente.py     # IA para imágenes
├── telegram_api.py         # API REST Telegram
├── scheduler.py            # Tareas programadas
└── media/                  # Imágenes fallback

static/
└── css/
    ├── base.css
    ├── navbar.css
    ├── dashboard.css
    ├── conversations.css
    ├── analytics.css
    └── image_generator.css

templates/
└── admin/                  # Templates admin personalizados

recruitment_bot/           # Configuración Django
├── settings.py
├── urls.py
├── asgi.py
└── wsgi.py
```

## 🗄️ Modelos de Base de Datos

### Telegram
- **TelegramUser** - Usuarios del bot
- **TelegramMessage** - Historial de mensajes
- **AIResponse** - Respuestas de Gemini
- **TelegramConfig** - Configuración

### Encuestas
- **Survey** - Encuestas
- **SurveyQuestion** - Preguntas
- **SurveyOption** - Opciones múltiples
- **SurveyResponse** - Respuestas de usuarios
- **SurveyAnswer** - Respuestas individuales

### Jobs
- **JobOffer** - Ofertas de trabajo

### Broadcasting
- **Broadcast** - Mensajes masivos

## 📦 Requisitos

```
Python 3.10+
Django 5.2+
python-telegram-bot 21.0+
google-generativeai 0.3+
Pillow 10.0+
requests 2.31+
```

## 🔧 Configuración Adicional

### Aumentar Límite de Memoria para Imágenes

En `settings.py`:
```python
DATA_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024  # 100MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 100 * 1024 * 1024
```

### Logging

Los logs se guardan en:
- `logs/bot.log`
- `logs/recruitment_bot.log`

## 🐛 Troubleshooting

### "El token de Telegram no es válido"
- Verifica que `TELEGRAM_TOKEN` está correcto en `.env`
- Reinicia el bot: `python manage.py runbot`

### "Error al generar imagen"
- Verifica que `GEMINI_API_KEY_2` está configurado
- Revisa los logs en `logs/bot.log`
- El sistema caerá a imágenes almacenadas en caché

### "Encuesta no aparece en Telegram"
- Verifica que el estado sea "active"
- La encuesta debe tener al menos 1 pregunta
- Revisa que el usuario es un TelegramUser registrado

## 🚀 Desplegar a Producción

```bash
# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Compilar mensajes
python manage.py compilemessages

# Ejecutar con Gunicorn
gunicorn recruitment_bot.wsgi:application --bind 0.0.0.0:8000

# Bot en background
nohup python manage.py runbot > logs/bot.log 2>&1 &
```

## 📝 Licencia

MIT License - Magneto Empleos 2025
