import cv2
import tkinter as tk
from tkinter import Label, Button
from PIL import Image, ImageTk
import time
import socket
import threading
import numpy as np

# Initialiser les variables
is_video_on = False
is_paused = False
start_time = None
pause_start_time = None
total_paused_time = 0

# Paramètres du serveur
SERVER_IP = '127.0.0.1'  # Remplacez par l'IP du serveur
SERVER_PORT = 5000
BUFFER_SIZE = 4096

# Fonction pour capturer et afficher la vidéo
def show_frame():
    if is_video_on and not is_paused:
        ret, frame = cap.read()
        if ret:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5, minSize=(30, 30))
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            if start_time is not None:
                elapsed_time = int(time.time() - start_time - total_paused_time)
                minutes = elapsed_time // 60
                seconds = elapsed_time % 60
                time_string = f"Durée : {minutes:02d}:{seconds:02d}"
                cv2.putText(frame, time_string, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

            img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img)
            img_pil.thumbnail((label.winfo_width(), label.winfo_height()))
            imgtk = ImageTk.PhotoImage(image=img_pil)
            label.imgtk = imgtk
            label.configure(image=imgtk)

    root.after(10, show_frame)

def start_video():
    global is_video_on, start_time, total_paused_time
    is_video_on = True
    start_time = time.time()
    total_paused_time = 0
    video_button.config(state=tk.DISABLED)
    pause_button.config(state=tk.NORMAL)
    stop_button.config(state=tk.NORMAL)

    threading.Thread(target=send_video, daemon=True).start()
    threading.Thread(target=receive_video, daemon=True).start()

def pause_video():
    global is_paused, pause_start_time, total_paused_time
    if not is_paused:
        is_paused = True
        pause_start_time = time.time()
        pause_button.config(text="Reprendre")
    else:
        is_paused = False
        total_paused_time += time.time() - pause_start_time
        pause_button.config(text="Pause")

def stop_video():
    global is_video_on, is_paused, total_paused_time
    is_video_on = False
    is_paused = False
    total_paused_time = 0
    video_button.config(state=tk.NORMAL)
    pause_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.DISABLED)

def send_video():
    global cap
    while is_video_on:
        ret, frame = cap.read()
        if ret:
            frame_data = frame.tobytes()
            frame_size = len(frame_data)
            client_socket.send(frame_size.to_bytes(4, byteorder='big') + frame_data)

def receive_video():
    while is_video_on:
        try:
            frame_size_data = client_socket.recv(4)
            if not frame_size_data:
                break
            frame_size = int.from_bytes(frame_size_data, byteorder='big')
            frame_data = b""
            while len(frame_data) < frame_size:
                frame_data += client_socket.recv(BUFFER_SIZE)

            frame = np.frombuffer(frame_data, np.uint8).reshape((480, 640, 3))
            show_received_frame(frame)

        except Exception as e:
            print(f"Erreur lors de la réception de la vidéo : {e}")
            break

def show_received_frame(frame):
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img_pil = Image.fromarray(frame)
    img_pil.thumbnail((label.winfo_width(), label.winfo_height()))
    imgtk = ImageTk.PhotoImage(image=img_pil)
    label.imgtk = imgtk
    label.configure(image=imgtk)

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))

root = tk.Tk()
root.title("Visio-conférence")

face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
cap = cv2.VideoCapture(0)

image_frame = tk.Frame(root, bg="black", bd=5, relief=tk.RAISED)
image_frame.pack(padx=10, pady=10)

label = Label(image_frame, bg="black")
label.pack(fill=tk.BOTH, expand=True)

buttons_frame = tk.Frame(root)
buttons_frame.pack(pady=(5, 10))

video_button = Button(buttons_frame, text="Démarrer Vidéo", command=start_video)
video_button.pack(side=tk.LEFT, padx=5)

pause_button = Button(buttons_frame, text="Pause", command=pause_video, state=tk.DISABLED)
pause_button.pack(side=tk.LEFT, padx=5)

stop_button = Button(buttons_frame, text="Arrêter Vidéo", command=stop_video, state=tk.DISABLED)
stop_button.pack(side=tk.LEFT, padx=5)

show_frame()
root.mainloop()

cap.release()
client_socket.close()
