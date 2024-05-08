from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, unquote
from pathlib import Path
import face_recognition
import numpy as np
import base64
import pickle
import json
import cv2
import os

def create_person_folder(person_id):
    path = os.path.join('data', person_id)
    os.makedirs(path, exist_ok=True)
    return path

def filter_image(path, img, count):
    filename = f'face_{count}.png'
    face_locations = face_recognition.face_locations(img)
    
    for (top, right, bottom, left) in face_locations:
        face_img = img[top:bottom, left:right]
        try:
            path_photo = os.path.join(path, filename)
            face_img = cv2.resize(face_img, (345, 345), interpolation=cv2.INTER_CUBIC)
            cv2.imwrite(path_photo, face_img)
            print(f"filter_image: ##### SE GUARDA REGISTRO EN DISCO: {path_photo} ########")
        except Exception as e:
            print("filter_image: ##### NO SE PUDO REDIMENSIONAR Y GUARDAR ########", e)

def add_person_to_pkl(person_id, path_person_to_add, database_file):
    person_images = list(Path(path_person_to_add).glob('*.png'))
    known_encodings = []
    for image_path in person_images:
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        for encoding in face_encodings:
            known_encodings.append((person_id, encoding))

    if len(known_encodings) == 0:
        print("No se encontraron codificaciones faciales válidas para agregar.")
        return

    # Cargar la lista actual de representaciones faciales del archivo .pkl si existe
    if os.path.exists(database_file):
        with open(database_file, 'rb') as f:
            database_list = pickle.load(f)
    else:
        database_list = []

    # Agregar las nuevas representaciones faciales a la lista principal
    database_list.extend(known_encodings)

    # Guardar la lista actualizada de representaciones faciales en el archivo .pkl
    with open(database_file, 'wb') as output:
        pickle.dump(database_list, output, protocol=pickle.HIGHEST_PROTOCOL)
        
def generate_and_save_representation(person_id):
    person_folder = Path('data', str(person_id))
    database_file = Path(person_folder.parent, 'representations_vgg_face.pkl')

    if person_folder.exists():
        add_person_to_pkl(person_id, str(person_folder), str(database_file))
    else:
        print(f"La carpeta '{person_id}' no existe. No se generará el archivo .pkl.")

base_dir = os.path.abspath(os.path.dirname(__file__))
photo_dir = os.path.join(base_dir, 'photo')
html_file = os.path.join(base_dir, 'template', 'saveFace.html')
html_file2 = os.path.join(base_dir, 'template', 'verifyFace.html')
static_dir = os.path.join(base_dir, 'template', 'static')
database_file = os.path.join(base_dir, 'representations_vgg_face.pkl')

class PhotoHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        file_path = unquote(parsed_path.path.lstrip('/'))

        if file_path == '':
            self.serve_file(html_file, 'text/html')
        elif file_path.startswith('static/'):
            static_file_path = os.path.join(static_dir, file_path.split('/', 1)[1])
            self.serve_static_file(static_file_path)
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found\n')
        

    def serve_file(self, file_path, content_type):
        try:
            with open(file_path, 'rb') as f:
                self.send_response(200)
                self.send_header('Content-type', content_type)
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal Server Error\n')

    def serve_static_file(self, file_path):
        try:
            if os.path.isfile(file_path):
                ext = os.path.splitext(file_path)[1]
                mime_type = {
                    '.html': 'text/html',
                    '.css': 'text/css',
                    '.js': 'application/javascript',
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg'
                }.get(ext, 'application/octet-stream')

                self.serve_file(file_path, mime_type)
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'File Not Found\n')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Internal Server Error\n')

    def do_POST(self):
        if self.path == '/save-photo':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)

            try:
                data = json.loads(post_data.decode('utf-8'))
                imageData = data['imageData']
                personId = data['photoName']

                person_folder = create_person_folder(personId)

                img_bytes = base64.b64decode(imageData.split(',')[1])
                img_np = np.frombuffer(img_bytes, dtype=np.uint8)
                img = cv2.imdecode(img_np, cv2.IMREAD_COLOR)

                count = len(os.listdir(person_folder)) + 1
                if count <= 6:
                    filter_image(person_folder, img, count)

                    if count == 5:
                        # Generar y guardar las representaciones faciales después de recibir 5 fotos
                        generate_and_save_representation(personId)      

                    self.send_response(200)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Foto guardada exitosamente.\n')
                else:
                    self.send_response(400)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'Ya se han guardado 5 fotos.\n')

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Error al guardar la foto.\n')
                print('Error al guardar la foto:', e)

        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not Found\n')

def run(server_class=HTTPServer, handler_class=PhotoHandler, port=8000):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Servidor iniciado en http://localhost:{port}')
    httpd.serve_forever()

if __name__ == '__main__':
    run()