"""
Script para obtener el ID del canal/grupo de Telegram
Nota: Debes agregar el bot como administrador primero
"""
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_TOKEN')

print("=" * 60)
print("📱 OBTENER ID DEL CANAL/GRUPO DE TELEGRAM")
print("=" * 60)
print("\n⚠️  PASOS PARA OBTENER EL ID:")
print("\n1. Abre tu navegador y ve a:")
print(f"   https://api.telegram.org/bot{TOKEN}/getUpdates")
print("\n2. Agrega tu bot al canal/grupo como administrador")
print("\n3. Envía un mensaje en el canal/grupo")
print("\n4. Vuelve a ejecutar el comando anterior (actualiza la página)")
print("\n5. Busca 'chat_id' en el JSON")
print("   - Será un número negativo para grupos/canales")
print("   - Ejemplo: -1001234567890")
print("\n6. Copia ese número y reemplaza TELEGRAM_CHANNEL_ID en .env")
print("\n" + "=" * 60)
print("\nAlternativa rápida:")
print("1. Envía /start al bot en privado")
print("2. Tu ID aparecerá en los logs o en el navegador")
print("3. Para canal usa: -100{CHANNEL_ID}")
print("=" * 60)
