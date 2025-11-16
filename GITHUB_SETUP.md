# GitHub - Instrucciones de Publicación

## 1. Inicializar Git (Primera vez)

```bash
git init
git add .
git commit -m "Initial commit: Recruitment bot with AI surveys and image generation"
```

## 2. Agregar Repositorio Remoto

```bash
git remote add origin https://github.com/tu_usuario/recruitment_bot.git
git branch -M main
git push -u origin main
```

## 3. .gitignore está Configurado

✅ Se ignoran automáticamente:
- Variables de entorno (`.env`)
- Base de datos (`db.sqlite3`)
- Archivos compilados (`__pycache__/`)
- Virtual environment (`venv/`)
- Logs y archivos temporales
- Archivos sensibles (keys, tokens)

## 4. Antes de Hacer Push

Verifica que estos archivos NO se incluyan:

```bash
git status
```

**NO deben aparecer:**
- `.env`
- `db.sqlite3`
- `venv/`
- `__pycache__/`
- `.DS_Store`

## 5. Crear .env.example

Para que otros puedan configurar el proyecto:

```bash
cp .env .env.example
# Luego edita .env.example y quita los valores reales
```

Contenido de `.env.example`:

```env
# Telegram
TELEGRAM_TOKEN=your_token_here
TELEGRAM_CHANNEL_ID=your_channel_id

# Gemini AI
GEMINI_API_KEY=your_api_key_here
GEMINI_API_KEY_2=your_api_key_2_here

# Django
DJANGO_SECRET_KEY=your_secret_key_here
DEBUG=0
```

Luego agrega a git:

```bash
git add .env.example
git commit -m "Add environment template"
git push
```

## 6. Crear requirements.txt

```bash
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Add Python dependencies"
git push
```

## 7. Estructura Recomendada en GitHub

```
recruitment_bot/
├── README.md                          # ✅ Documentación principal
├── .gitignore                         # ✅ Archivos ignorados
├── .env.example                       # ✅ Plantilla de variables
├── requirements.txt                   # ✅ Dependencias
├── manage.py
├── SURVEYS_HU11.md                   # ✅ Doc de encuestas
├── SURVEY_QUICK_START.md             # ✅ Guía rápida
├── INTEGRATION_SUMMARY.md            # ✅ Resumen técnico
│
├── apps/
│   ├── jobs/
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── forms.py
│   │
│   └── telegram_agent/
│       ├── models.py
│       ├── views.py
│       ├── urls.py
│       ├── bot.py
│       ├── admin.py
│       ├── templatetags/
│       ├── templates/
│       └── migrations/
│
├── services/
│   ├── gemini_client.py
│   ├── gemini_2_cliente.py
│   ├── telegram_api.py
│   ├── scheduler.py
│   └── media/
│
├── static/
│   └── css/
│
├── templates/
│   ├── telegram_agent/
│   └── admin/
│
├── recruitment_bot/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
└── logs/
    └── .gitkeep
```

## 8. GitHub Actions (CI/CD) - Opcional

Crea `.github/workflows/python-app.yml`:

```yaml
name: Python application

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python 3.10
      uses: actions/setup-python@v2
      with:
        python-version: 3.10
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run migrations
      run: |
        python manage.py migrate
    
    - name: Check Django
      run: |
        python manage.py check
```

## 9. Commits Recomendados

```bash
# 1. Commit inicial
git add .
git commit -m "Initial commit: Recruitment bot with Telegram, Django, and Gemini AI"
git push

# 2. Agregar documentación
git add *.md .env.example
git commit -m "Add documentation and environment template"
git push

# 3. Agregar workflows (si usas CI/CD)
git add .github/
git commit -m "Add GitHub Actions CI/CD"
git push
```

## 10. Configurar GitHub Pages (Documentación)

Opcional - Para documentación en GitHub Pages:

1. Ve a **Settings** → **Pages**
2. Selecciona branch: `main`
3. Carpeta: `/` (root)
4. Tu README.md será la página principal

## 11. Badges para README

Agrega estos badges al inicio del README:

```markdown
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/Django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub](https://img.shields.io/badge/GitHub-recruitment_bot-black.svg)](https://github.com/tu_usuario/recruitment_bot)
```

## 12. Ignorar Cambios en Archivos Tracked

Si accidentalmente hiciste commit de `.env`:

```bash
git rm --cached .env
git commit -m "Remove .env from tracking"
git push
```

## 13. Proteger Rama Main

En GitHub - Settings → Branches:
1. Add rule para `main`
2. Require pull request reviews
3. Require status checks to pass

## Checklist Final

- ✅ README.md actualizado
- ✅ .gitignore creado
- ✅ .env.example creado
- ✅ requirements.txt generado
- ✅ db.sqlite3 en .gitignore
- ✅ venv/ en .gitignore
- ✅ __pycache__/ en .gitignore
- ✅ logs/ excluidos (solo .gitkeep)
- ✅ Repositorio remoto configurado
- ✅ Primera versión pusheada

## Acceso Rápido

```bash
# Ver estado
git status

# Ver commits
git log --oneline

# Ver cambios
git diff

# Deshacer cambio sin hacer commit
git restore nombre_archivo
```

¡Listo para GitHub! 🚀
