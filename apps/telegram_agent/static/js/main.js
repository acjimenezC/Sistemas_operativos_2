// ============================================
// UTILS
// ============================================

// Obtener CSRF token desde las cookies
function getCsrfToken() {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, 'csrftoken'.length + 1) === ('csrftoken' + '=')) {
                cookieValue = decodeURIComponent(cookie.substring('csrftoken'.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Debounce para eventos
function debounce(func, delay) {
    let timeoutId;
    return function (...args) {
        clearTimeout(timeoutId);
        timeoutId = setTimeout(() => func.apply(this, args), delay);
    };
}

// Throttle para eventos
function throttle(func, limit) {
    let lastFunc;
    let lastRan;
    return function (...args) {
        if (!lastRan) {
            func.apply(this, args);
            lastRan = Date.now();
        } else {
            clearTimeout(lastFunc);
            lastFunc = setTimeout(() => {
                if ((Date.now() - lastRan) >= limit) {
                    func.apply(this, args);
                    lastRan = Date.now();
                }
            }, limit - (Date.now() - lastRan));
        }
    };
}

// Mostrar notificación
function showNotification(message, type = 'success') {
    const notification = document.createElement('div');
    notification.className = `${type} show`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 9999;
        animation: slideInRight 0.4s ease;
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        notification.style.animation = 'fadeOut 0.3s ease';
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// ============================================
// FEEDBACK FORM
// ============================================

function toggleFeedback(messageId) {
    const form = document.getElementById(`feedback-${messageId}`);
    if (form) {
        form.classList.toggle('show');
    }
}

function submitFeedback(messageId) {
    const textarea = document.getElementById(`feedback-text-${messageId}`);
    const rating = document.getElementById(`feedback-rating-${messageId}`);
    
    if (!textarea || !rating) {
        console.error('Feedback form elements not found');
        return;
    }

    const csrfToken = getCsrfToken();
    
    fetch(`/telegram/api/feedback/${messageId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            feedback: textarea.value,
            rating: parseInt(rating.value)
        })
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('Feedback enviado correctamente', 'success');
            toggleFeedback(messageId);
            // Limpiar formulario
            textarea.value = '';
            rating.value = '3';
        } else {
            showNotification('Error al enviar feedback: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al enviar feedback', 'error');
    });
}

// ============================================
// SEARCH FUNCTIONALITY
// ============================================

function initializeSearch(searchInputId, itemSelector) {
    const searchInput = document.getElementById(searchInputId);
    if (!searchInput) return;

    searchInput.addEventListener('keyup', debounce(function(e) {
        const searchTerm = e.target.value.toLowerCase();
        const items = document.querySelectorAll(itemSelector);
        
        items.forEach(item => {
            const content = item.textContent.toLowerCase();
            item.style.display = content.includes(searchTerm) ? 'block' : 'none';
            if (content.includes(searchTerm)) {
                item.style.animation = 'slideInRight 0.3s ease';
            }
        });
    }, 300));
}

// ============================================
// IMAGE GENERATOR
// ============================================

let currentImageData = null;

function initializeImageGenerator() {
    const imageForm = document.getElementById('imageForm');
    if (!imageForm) return;

    imageForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const prompt = document.getElementById('prompt')?.value;
        const title = document.getElementById('title')?.value;
        const description = document.getElementById('description')?.value;
        
        if (!prompt || !title || !description) {
            showNotification('Por favor completa todos los campos', 'error');
            return;
        }
        
        const loadingEl = document.getElementById('loading');
        if (loadingEl) loadingEl.classList.add('show');
        
        try {
            const response = await fetch('/telegram/api/generate-image/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken()
                },
                body: JSON.stringify({
                    prompt: prompt,
                    title: title,
                    description: description
                })
            });
            
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            
            if (data.success) {
                currentImageData = data;
                const previewImage = document.getElementById('previewImage');
                const previewTitle = document.getElementById('previewTitle');
                const previewDesc = document.getElementById('previewDesc');
                const preview = document.getElementById('preview');
                
                if (previewImage) previewImage.src = data.image_url;
                if (previewTitle) previewTitle.textContent = title;
                if (previewDesc) previewDesc.textContent = description;
                if (preview) preview.classList.add('show');
                if (imageForm) imageForm.style.display = 'none';
                
                showNotification('¡Imagen generada exitosamente!', 'success');
            } else {
                showNotification('Error: ' + (data.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            showNotification('Error al generar imagen', 'error');
        } finally {
            if (loadingEl) loadingEl.classList.remove('show');
        }
    });
}

function cancelPreview() {
    const preview = document.getElementById('preview');
    const imageForm = document.getElementById('imageForm');
    
    if (preview) preview.classList.remove('show');
    if (imageForm) {
        imageForm.style.display = 'block';
        imageForm.reset();
    }
    currentImageData = null;
}

function generateNewImage() {
    cancelPreview();
    const prompt = document.getElementById('prompt');
    if (prompt) prompt.focus();
}

function publishImage() {
    if (!currentImageData) {
        showNotification('No hay imagen para publicar', 'error');
        return;
    }
    
    const publishLoading = document.getElementById('publishLoading');
    if (publishLoading) publishLoading.classList.add('show');
    
    fetch('/telegram/api/publish-image/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCsrfToken()
        },
        body: JSON.stringify(currentImageData)
    })
    .then(response => {
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('¡Imagen publicada correctamente!', 'success');
            setTimeout(() => location.reload(), 1000);
        } else {
            showNotification('Error: ' + (data.error || 'Unknown error'), 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error al publicar imagen', 'error');
    })
    .finally(() => {
        if (publishLoading) publishLoading.classList.remove('show');
    });
}

// ============================================
// CHARTS
// ============================================

function createChart(canvasId, type, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    const defaultOptions = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: {
                labels: {
                    color: '#3D1A5F',
                    font: { size: 13, weight: '600' }
                }
            }
        },
        scales: {
            y: {
                ticks: { color: '#666' },
                grid: { color: 'rgba(0, 0, 0, 0.05)' }
            },
            x: {
                ticks: { color: '#666' },
                grid: { color: 'rgba(0, 0, 0, 0.05)' }
            }
        }
    };

    const finalOptions = { ...defaultOptions, ...options };

    if (typeof Chart !== 'undefined') {
        return new Chart(canvas, {
            type: type,
            data: data,
            options: finalOptions
        });
    }
    
    console.warn('Chart.js not loaded');
    return null;
}

// ============================================
// SMOOTH SCROLL
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll para links internos
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Active nav link
    const currentUrl = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentUrl) {
            link.classList.add('active');
        }
    });

    // Inicializar búsqueda si existe
    if (document.getElementById('searchInput')) {
        initializeSearch('searchInput', '.message-item');
    }

    // Inicializar generador de imágenes si existe
    if (document.getElementById('imageForm')) {
        initializeImageGenerator();
    }
});

// Exportar funciones globales
window.toggleFeedback = toggleFeedback;
window.submitFeedback = submitFeedback;
window.cancelPreview = cancelPreview;
window.generateNewImage = generateNewImage;
window.publishImage = publishImage;
window.createChart = createChart;

