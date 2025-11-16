"""
Cliente para Gemini 2 API
Genera imágenes, videos y carruseles usando Gemini 2
"""
import os
import logging
from typing import Optional
import google.generativeai as genai
from dotenv import load_dotenv
import glob
import random

load_dotenv()
logger = logging.getLogger(__name__)

# Configuración de Gemini 2
GEMINI_API_KEY_2 = os.getenv('GEMINI_API_KEY_2')

# Configurar Gemini 2
if GEMINI_API_KEY_2:
    genai.configure(api_key=GEMINI_API_KEY_2)
else:
    logger.warning("[Gemini2] GEMINI_API_KEY_2 no está configurada")


class Gemini2Client:
    """Cliente para generar imágenes usando Gemini 2 API"""
    
    def __init__(self):
        """Inicializa el cliente de Gemini 2"""
        self.api_key = GEMINI_API_KEY_2
        self.model_name = 'gemini-2.0-flash-thinking-exp-1219'  # Modelo experimental que genera imágenes
        
        if self.api_key:
            try:
                self.model = genai.GenerativeModel(self.model_name)
                logger.info("[Gemini2] Cliente inicializado correctamente")
            except Exception as e:
                logger.error(f"[Gemini2] Error inicializando modelo: {str(e)}")
                self.model = None
        else:
            logger.error("[Gemini2] GEMINI_API_KEY_2 no configurada")
            self.model = None
    
    def is_configured(self) -> bool:
        """Verifica si el cliente está configurado correctamente"""
        return bool(self.api_key and self.model)
    
    def _get_cache_dir(self) -> str:
        """Obtiene el directorio de media con imágenes predefinidas"""
        media_dir = os.path.join(os.path.dirname(__file__), 'media')
        os.makedirs(media_dir, exist_ok=True)
        return media_dir
    
    def _save_image_to_cache(self, image_data: bytes, content_type: str) -> str:
        """
        Guarda una imagen en media (para usar como fallback después)
        
        Args:
            image_data: Bytes de la imagen
            content_type: Tipo de contenido
        
        Returns:
            Ruta del archivo guardado
        """
        try:
            media_dir = self._get_cache_dir()
            import time
            timestamp = int(time.time())
            filename = f"fallback_{content_type}_{timestamp}.png"
            filepath = os.path.join(media_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            logger.info(f"[Gemini2] Imagen de fallback guardada: {filepath}")
            return filepath
        except Exception as e:
            logger.warning(f"[Gemini2] Error guardando imagen de fallback: {str(e)}")
            return None
    
    def _load_cached_image(self, content_type: str) -> Optional[bytes]:
        """
        Carga una imagen aleatoria del caché
        
        Args:
            content_type: Tipo de contenido a buscar
        
        Returns:
            Bytes de la imagen o None si no hay
        """
        try:
            cache_dir = self._get_cache_dir()
            # Buscar CUALQUIER PNG en el directorio media
            pattern = os.path.join(cache_dir, "*.png")
            cached_files = glob.glob(pattern)
            
            if cached_files:
                # Seleccionar una al azar
                selected_file = random.choice(cached_files)
                with open(selected_file, 'rb') as f:
                    image_data = f.read()
                
                logger.info(f"[Gemini2] Imagen cargada del caché: {selected_file}")
                return image_data
            else:
                logger.warning(f"[Gemini2] No hay imágenes PNG en: {cache_dir}")
                return None
        except Exception as e:
            logger.warning(f"[Gemini2] Error cargando imagen del caché: {str(e)}")
            return None
    
    def _load_theme_image(self, theme_name: str) -> Optional[bytes]:
        """
        Carga una imagen temática específica
        
        Args:
            theme_name: Nombre del tema (sin extensión .png)
        
        Returns:
            Bytes de la imagen o None si no existe
        """
        try:
            media_dir = self._get_cache_dir()
            filepath = os.path.join(media_dir, f"{theme_name}.png")
            
            if os.path.exists(filepath):
                with open(filepath, 'rb') as f:
                    image_data = f.read()
                logger.info(f"[Gemini2] Imagen temática cargada: {filepath}")
                return image_data
            else:
                logger.warning(f"[Gemini2] Imagen temática no encontrada: {filepath}")
                return None
        except Exception as e:
            logger.warning(f"[Gemini2] Error cargando imagen temática: {str(e)}")
            return None
    
    def generate_image(self, prompt: str, content_type: str = 'image', theme: str = '') -> dict:
        """
        Genera una imagen usando Gemini 2
        
        Args:
            prompt: Descripción de la imagen (soporta español)
            content_type: Tipo de contenido ('image', 'carousel', 'video')
            theme: Tema de la imagen (para usar imágenes temáticas predefinidas)
        
        Returns:
            Dict con:
                - success: bool
                - image_data: bytes (imagen PNG)
                - content_type: str
                - model: str
                - size_bytes: int
                - error: str (si hubo error)
        
        Ejemplo:
            result = client.generate_image(
                "personas trabajando desde casa con laptops",
                content_type='image',
                theme='recruitment'
            )
            if result['success']:
                image_bytes = result['image_data']
        """
        
        logger.info(f"[Gemini2] Generando {content_type} con prompt: {prompt[:100]} - tema: {theme}")
        
        # Si el tema es reclutamiento, usar imagen temática
        if theme.lower() == 'recruitment':
            logger.info("[Gemini2] Usando imagen temática para reclutamiento")
            recruitment_image = self._load_theme_image('recruitment_theme')
            if recruitment_image:
                return {
                    'success': True,
                    'content_type': content_type,
                    'image_data': recruitment_image,
                    'model': self.model_name,
                    'prompt_used': prompt,
                    'size_bytes': len(recruitment_image),
                    'from_cache': True,
                    'message': 'Usando imagen temática de reclutamiento'
                }
        
        if not self.is_configured():
            error_msg = "GEMINI_API_KEY_2 no está configurada o modelo no inicializado"
            logger.error(f"[Gemini2] {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'details': 'Asegúrate de tener GEMINI_API_KEY_2 en el archivo .env'
            }
        
        try:
            # Crear el prompt para generar imagen
            enhanced_prompt = self._enhance_prompt(prompt, content_type)
            
            logger.info(f"[Gemini2] Enviando prompt mejorado de {len(enhanced_prompt)} caracteres")
            
            # Generar imagen con Gemini 2
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=1024,
                )
            )
            
            # Verificar si la respuesta contiene imagen
            if response.parts and response.parts[0].mime_type and 'image' in response.parts[0].mime_type:
                image_data = response.parts[0].data
                
                logger.info(f"[Gemini2] Imagen generada exitosamente ({len(image_data)} bytes)")
                
                # Guardar en caché para usar como fallback
                self._save_image_to_cache(image_data, content_type)
                
                return {
                    'success': True,
                    'content_type': content_type,
                    'image_data': image_data,
                    'model': self.model_name,
                    'prompt_used': enhanced_prompt[:100],
                    'size_bytes': len(image_data),
                    'from_cache': False
                }
            else:
                # Si no generó imagen, intentar con instrucción más explícita
                logger.warning("[Gemini2] No se generó imagen, intentando método alternativo")
                return self._fallback_generate(prompt, content_type)
        
        except Exception as e:
            logger.error(f"[Gemini2] Error generando imagen: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            
            # Si hay error, intentar fallback (incluyendo caché)
            logger.info("[Gemini2] Error en generación principal, intentando fallback...")
            return self._fallback_generate(prompt, content_type)
    
    def _enhance_prompt(self, prompt: str, content_type: str) -> str:
        """
        Mejora el prompt para mejor generación de imágenes
        
        Args:
            prompt: Prompt original del usuario
            content_type: Tipo de contenido
        
        Returns:
            Prompt mejorado
        """
        
        # Instrucciones simples y directas para Gemini 2.0
        enhanced = f"""Generate a professional, high-quality image:

{prompt}

Style: Modern, professional, realistic
Colors: Use purple (#3D1A5F) and green (#7EFFA2) as accent colors
Quality: HD, well-lit, clear focus
Format: PNG image only

Create the image now."""
        
        logger.info(f"[Gemini2] Prompt mejorado (primeros 150 chars): {enhanced[:150]}...")
        return enhanced
    
    def _fallback_generate(self, prompt: str, content_type: str) -> dict:
        """
        Método alternativo si falla la primera generación
        Intenta con instrucción alternativa, luego usa imagen en caché como último recurso
        
        Args:
            prompt: Prompt original
            content_type: Tipo de contenido
        
        Returns:
            Dict con resultado
        """
        try:
            logger.info("[Gemini2] Intentando generación alternativa...")
            
            alt_prompt = f"""Generate a professional image based on this description:
            
{prompt}

Return the image in high quality, realistic style."""
            
            response = self.model.generate_content(
                [alt_prompt],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                )
            )
            
            if response.parts and len(response.parts) > 0:
                # Buscar la primera parte que sea imagen
                for part in response.parts:
                    if part.mime_type and 'image' in part.mime_type:
                        image_data = part.data
                        logger.info(f"[Gemini2] Imagen generada con fallback ({len(image_data)} bytes)")
                        
                        # Guardar en caché
                        self._save_image_to_cache(image_data, content_type)
                        
                        return {
                            'success': True,
                            'content_type': content_type,
                            'image_data': image_data,
                            'model': self.model_name,
                            'prompt_used': alt_prompt[:100],
                            'size_bytes': len(image_data),
                            'from_cache': False
                        }
            
            # Si también falló el fallback, usar imagen del caché
            logger.warning("[Gemini2] Fallback de generación también falló, intentando usar imagen en caché...")
            cached_image = self._load_cached_image(content_type)
            
            if cached_image:
                logger.info(f"[Gemini2] Usando imagen en caché como último recurso ({len(cached_image)} bytes)")
                return {
                    'success': True,
                    'content_type': content_type,
                    'image_data': cached_image,
                    'model': self.model_name,
                    'prompt_used': prompt,
                    'size_bytes': len(cached_image),
                    'from_cache': True,
                    'message': 'Usando imagen guardada de un intento anterior'
                }
            
            logger.error("[Gemini2] No hay imágenes en caché como último recurso")
            return {
                'success': False,
                'error': 'No se pudo generar imagen ni hay imágenes guardadas en caché',
                'details': 'Intenta más tarde cuando la cuota se reinicie'
            }
        
        except Exception as e:
            logger.error(f"[Gemini2] Error en fallback: {str(e)}")
            
            # Último intento: usar imagen en caché
            logger.info("[Gemini2] Intentando cargar imagen en caché por error...")
            cached_image = self._load_cached_image(content_type)
            
            if cached_image:
                logger.info(f"[Gemini2] Usando imagen en caché por error ({len(cached_image)} bytes)")
                return {
                    'success': True,
                    'content_type': content_type,
                    'image_data': cached_image,
                    'model': self.model_name,
                    'prompt_used': prompt,
                    'size_bytes': len(cached_image),
                    'from_cache': True,
                    'message': f'Error al generar. Usando imagen guardada: {str(e)}'
                }
            
            return {
                'success': False,
                'error': f'Error en generación y en caché: {str(e)}'
            }


def generate_image(prompt: str, content_type: str = 'image') -> dict:
    """
    Función helper para generar imágenes con Gemini 2
    
    Args:
        prompt: Descripción de la imagen
        content_type: Tipo ('image', 'carousel', 'video')
    
    Returns:
        Dict con resultado de generación
    
    Ejemplo:
        from services.gemini_2_cliente import generate_image
        result = generate_image("personas trabajando juntas", content_type='image')
        if result['success']:
            image_bytes = result['image_data']
    """
    client = Gemini2Client()
    return client.generate_image(prompt, content_type)


# Para pruebas rápidas
if __name__ == '__main__':
    print("=" * 60)
    print("🧪 PRUEBA DE GEMINI 2 CLIENT")
    print("=" * 60)
    
    client = Gemini2Client()
    
    if not client.is_configured():
        print("❌ Error: GEMINI_API_KEY_2 no está configurada")
        print("Añade la clave en el archivo .env")
    else:
        print("✅ Cliente Gemini 2 configurado correctamente")
        print(f"📌 Modelo: {client.model_name}")
        print(f"🔑 API Key: {GEMINI_API_KEY_2[:10]}...")
        
        # Ejemplo de generación
        print("\n" + "=" * 60)
        print("🎨 Generando imagen de prueba...")
        print("=" * 60)
        
        result = client.generate_image(
            "equipo de personas trabajando juntas en una oficina moderna",
            content_type='image'
        )
        
        if result['success']:
            print(f"✅ Imagen generada exitosamente")
            print(f"📊 Tamaño: {result['size_bytes']} bytes")
            print(f"🎯 Modelo usado: {result['model']}")
        else:
            print(f"❌ Error: {result.get('error')}")
            print(f"📋 Detalles: {result.get('details')}")

