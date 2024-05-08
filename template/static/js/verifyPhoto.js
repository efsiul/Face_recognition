const videoElement = document.getElementById('video');
const captureButton = document.getElementById('capture-btn');
const photoNameInput = document.getElementById('photo-name');
const gallery = document.getElementById('gallery');

// Inicializar variables para almacenar la información de verificación
let isVerified = false;
let bestMatchId = '';
let probability = 0;

// Función para capturar la foto
async function capturePhoto() {
    const canvas = document.createElement('canvas');
    const context = canvas.getContext('2d');

    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    context.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL('image/png');
    const photoName = photoNameInput.value.trim();

    // Envía la foto al backend para la verificación
    try {
        const response = await fetch('/verify-face', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ imageData: imageData, photoName: photoName })
        });
        const data = await response.json();

        // Actualiza las variables de verificación
        isVerified = data.is_verified;
        bestMatchId = data.best_match_id;
        probability = data.probability;

        // Muestra el resultado en la página
        if (isVerified) {
            alert(`Verificado: ${photoName} con probabilidad ${probability}`);
        } else {
            alert(`No se reconoce: ${photoName}`);
        }
    } catch (error) {
        console.error('Error al verificar la foto:', error);
        alert('Error al verificar la foto.');
    }
}

// Asigna la función de captura al botón
captureButton.addEventListener('click', capturePhoto);
