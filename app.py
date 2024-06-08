import cv2
import pyttsx3
import mediapipe as mp
import numpy as np
import pytesseract
from PIL import Image

# Inicializar el detector de manos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Inicializar la captura de video
cap = cv2.VideoCapture(1)

# Variables para almacenar la posición anterior del dedo índice
prev_x, prev_y = None, None

# Crear una imagen en blanco para dibujar
canvas = np.zeros((480, 640, 3), dtype=np.uint8) + 255  # Blanco
canvas_color = (0, 0, 0)  # Negro
camera_paint_color = (0, 255, 255)  # Rojo
camera_paint = np.zeros((480, 640, 3), dtype=np.uint8)



# Definir el tamaño de la ventana para el filtro de media móvil
window_size = 5
x_history, y_history = [], []





# Definir una variable para controlar el estado de dibujo
is_drawing = True

# Definir una variable para almacenar el texto del lienzo

def leer_y_pronunciar(ruta_archivo_txt, idioma):
    """
    Lee un archivo txt y lo pronuncia usando texto a voz.

    Args:
        ruta_archivo_txt (str): Ruta del archivo txt a leer.
        idioma (str): Idioma de la voz (por ejemplo, 'es' para español, 'en' para inglés).
    """

    # Abrir el archivo txt en modo lectura
    with open(ruta_archivo_txt, 'r') as archivo:
        # Leer el contenido del archivo
        contenido = archivo.read()

    # Inicializar el motor de texto a voz
    motor = pyttsx3.init()

    # Cambiar el idioma de la voz
    voces = motor.getProperty('voices')
    for voz in voces:
        if 'Sabina' in voz.name:
            motor.setProperty('voice', voz.id)
            break

    # Pronunciar el contenido del archivo
    motor.say(contenido)

    # Esperar a que termine de pronunciar
    motor.runAndWait()



def leer_imagen_y_guardar_texto(ruta_imagen, ruta_archivo_txt):
    """
    Lee una imagen, la procesa con OCR y guarda el texto reconocido en un archivo txt.

    Args:
        ruta_imagen (str): Ruta de la imagen a leer.
        ruta_archivo_txt (str): Ruta del archivo txt donde se guardará el texto.
    """

    # Leer la imagen PNG
    image = cv2.imread(ruta_imagen)

    # Convertir la imagen a escala de grises
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Aplicar umbral adaptativo para mejorar la calidad de la imagen
    thresh_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

    # Extraer el texto usando Tesseract
    texto = pytesseract.image_to_string(thresh_image, lang='spa')

    # Guardar el texto en un archivo txt
    with open(ruta_archivo_txt, 'w') as archivo:
        archivo.write(texto)



idioma = 'spanish mexico'
leer_y_pronunciar('lienzo.txt', idioma)

color_circle = (0, 255, 0)


canvas_text = ''

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        continue



    # Convertir la imagen a color
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Procesar la imagen con el detector de manos
    results = hands.process(rgb_frame)

    # Si se detecta al menos una mano
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Obtener la posición de la punta del dedo índice (ID 8)
            index_tip = hand_landmarks.landmark[8]
            x = int(index_tip.x * frame.shape[1])
            y = int(index_tip.y * frame.shape[0])

            # Aplicar filtro de media móvil a las coordenadas del dedo índice
            x_history.append(x)
            y_history.append(y)
            if len(x_history) > window_size:
                x_filtered = int(np.mean(x_history[-window_size:]))
                y_filtered = int(np.mean(y_history[-window_size:]))
            else:
                x_filtered, y_filtered = x, y

            # Dibujar un círculo en la punta del dedo índice
            cv2.circle(frame, (x_filtered, y_filtered), 5, color_circle, -1)
            


            if is_drawing:

                # Si hay una posición anterior, dibujar una línea desde la posición anterior hasta la actual en el lienzo
                if prev_x is not None and prev_y is not None:
                    cv2.line(canvas, (prev_x, prev_y), (x_filtered, y_filtered), canvas_color, 5)
                    cv2.line(camera_paint, (prev_x, prev_y), (x_filtered, y_filtered), camera_paint_color, 5)

                # Actualizar la posición anterior
                prev_x, prev_y = x_filtered, y_filtered
            else:
                # Reiniciar la posición anterior si no está en modo de dibujo
                prev_x, prev_y = None, None

            
    # Superponer la pintura de la cámara en la imagen de la cámara
    frame = cv2.add(frame, camera_paint)
    # Mostrar la imagen y el lienzo
    cv2.imshow('Drawing App', frame)
    cv2.imshow('Canvas', canvas)

    # Verificar si se presiona la tecla 'n' para limpiar el lienzo
    key = cv2.waitKey(1)
    if key & 0xFF == ord('q'):
        break
    elif key & 0xFF == ord('n'):
        # Limpiar el lienzo y restablecer el historial de coordenadas si se presiona la tecla 'n'
        canvas = np.zeros((480, 640, 3), dtype=np.uint8) + 255  # Blanco
        x_history, y_history = [], []
        camera_paint = np.zeros((480, 640, 3), dtype=np.uint8)
    elif key & 0xFF == ord('b'):
        # Cambiar el estado de dibujo si se presiona la tecla 'b'
        is_drawing = not is_drawing
    elif key & 0xFF == ord('s'):
        # Guardar el contenido del lienzo como una imagen PNG si se presiona la tecla 's'
        cv2.imwrite('lienzo.png', canvas)
        # Ejemplo de uso
        ruta_imagen = 'lienzo.png'  # Reemplaza con la ruta de tu imagen
        ruta_archivo_txt = 'lienzo.txt'  # Reemplaza con la ruta deseada para el archivo txt
        leer_imagen_y_guardar_texto(ruta_imagen, ruta_archivo_txt)
        idioma = 'spanish mexico'
        leer_y_pronunciar(ruta_archivo_txt, idioma)
    elif key & 0xFF == ord('m'):
    # Cambiar el color del trazo a blanco si actualmente es negro, y viceversa, si se presiona la tecla 'm'
        canvas_color = (255, 255, 255) if canvas_color == (0, 0, 0) else (0, 0, 0)
        camera_paint_color = (0, 0, 0) if camera_paint_color == (0, 255, 255) else (0, 255, 255)
        color_circle = ((255, 0, 0) if color_circle == (0, 255, 0) else (0, 255, 0))


# Liberar la captura y cerrar las ventanas
cap.release()
cv2.destroyAllWindows()
