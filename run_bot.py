#!/usr/bin/env python
"""
Script para ejecutar el bot de Telegram con mejor manejo de logs en Windows
"""
import os
import sys
import logging
import asyncio
from pathlib import Path

# Configurar encoding para Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', write_through=True)
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', write_through=True)

# Cambiar a directorio del proyecto primero
project_root = Path(__file__).parent
os.chdir(project_root)
sys.path.insert(0, str(project_root))

# Crear directorio de logs si no existe
logs_dir = project_root / 'logs'
logs_dir.mkdir(exist_ok=True)

# Configurar logging ANTES de importar Django
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(str(logs_dir / 'bot.log'), encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)
logger.info("="*70)
logger.info("Iniciando Bot de Telegram")
logger.info("="*70)

# Importar y ejecutar el bot
try:
    from apps.telegram_agent.bot import run_bot
    
    logger.info("Bot importado exitosamente")
    logger.info("Iniciando polling...")
    run_bot()
    
except KeyboardInterrupt:
    logger.info("Bot detenido por el usuario")
except Exception as e:
    logger.error(f"Error fatal en el bot: {str(e)}", exc_info=True)
    sys.exit(1)
