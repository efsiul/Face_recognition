const photoFrame = document.querySelector('.photo-frame');
const enableFrameBtn = document.getElementById('enableFrame');
const cameraView = document.getElementById('video');
const photoNameLabel = document.querySelector('label[for="photo-name"]');
const photoNameInput = document.getElementById('photo-name');
const gallery = document.getElementById('gallery');
const clearGalleryBtn = document.getElementById('clearGallery');
let stream = null;
let photoCount = 0;
let captureBtn = null; // Declarado fuera de la función para tener acceso global

enableFrameBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        cameraView.srcObject = stream;
        cameraView.play();
        photoFrame.style.display = 'flex';
        photoNameInput.value = ''; // Limpiar el input al habilitar el marco
        photoNameLabel.style.display = 'inline';
        photoNameInput.style.display = 'inline';
        enableFrameBtn.style.display = 'none';
        clearGalleryBtn.style.display = 'none'; // Ocultar el botón de borrar al inicio
        createTakePhotoButton(); // Llamar a la función para crear el botón "Tomar 5 Fotos"
    } catch (err) {
        console.error('Error al acceder a la cámara:', err);
    }
});

function createTakePhotoButton() {
    if (captureBtn) {
        captureBtn.remove(); // Eliminar el botón existente si hay uno
    }

    captureBtn = document.createElement('button');
    captureBtn.id = 'capture-btn';
    captureBtn.textContent = 'Tomar 5 Fotos';
    document.body.appendChild(captureBtn);

    captureBtn.addEventListener('click', function() {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        const photoName = photoNameInput.value.trim();

        if (photoName === '') {
            alert('Por favor, ingrese un número de documento.');
            return;
        }

        captureBtn.disabled = true; // Deshabilitar el botón mientras se toman las fotos

        for (let i = 0; i < 5; i++) {
            setTimeout(() => {
                canvas.width = cameraView.videoWidth;
                canvas.height = cameraView.videoHeight;
                context.drawImage(cameraView, 0, 0, canvas.width, canvas.height);

                const imageData = canvas.toDataURL('image/png');
                const img = new Image();
                img.src = imageData;
                img.style.width = '100px';
                gallery.appendChild(img);

                photoCount++;

                if (photoCount === 5) {
                    cameraView.pause();
                    cameraView.srcObject.getTracks().forEach(track => track.stop()); // Detener la transmisión de video
                    photoFrame.style.display = 'none';
                    photoNameLabel.style.display = 'none';
                    photoNameInput.style.display = 'none';
                    clearGalleryBtn.style.display = 'inline'; // Mostrar el botón de borrar al tomar las 5 fotos
                    enableFrameBtn.style.display = 'none'; // Ocultar el botón de habilitar marco al tomar las 5 fotos
                    captureBtn.style.display = 'none'; // Ocultar el botón "Tomar 5 Fotos"
                }

                fetch('/save-photo', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ imageData: imageData, photoName: photoName })
                })
                .then(function(response) {
                    console.log('Response:', response);
                    if (response.ok) {
                        console.log('Foto guardada exitosamente.');
                    } else {
                        throw new Error('Error al guardar la foto.');
                    }
                })
                .catch(function(error) {
                    console.error('Error:', error);
                    alert('Error al guardar la foto.');
                });

            }, i * 1000); // Captura cada foto con un intervalo de 1 segundo
        }
    });
}

clearGalleryBtn.addEventListener('click', function() {
    gallery.innerHTML = '';
    photoCount = 0;
    cameraView.srcObject = null; // Detener la transmisión de video al borrar las fotos
    photoFrame.style.display = 'none';
    photoNameLabel.style.display = 'none';
    photoNameInput.style.display = 'none';
    clearGalleryBtn.style.display = 'none';
    enableFrameBtn.style.display = 'inline'; // Mostrar el botón de habilitar marco al borrar las fotos

    if (captureBtn) {
        captureBtn.remove(); // Eliminar el botón "Tomar 5 Fotos" al borrar las fotos
        captureBtn = null; // Reiniciar la variable del botón
    }
});
