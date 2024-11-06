import cv2
from gtts import gTTS
import os
import pickle
from playsound import playsound
# import RPi.GPIO as io
import socket
import struct
import threading
import time


SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 9999

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, SERVER_PORT))
print("Connected to server")

# PIR_PIN = 11
# BUTTON_PIN = 17
# BUZZER_PIN = 18

# io.setmode(io.BOARD) 
# io.setup(PIR_PIN, io.IN) 
# io.setup(BUTTON_PIN, io.IN, pull_up_down=io.PUD_UP)
# io.setup(BUZZER_PIN, io.OUT)

# time.sleep(1.5)


def activateCamera():

    camera = cv2.VideoCapture(0)

    try:
        for _ in range(5):
            ret, frame = camera.read()
            if not ret:
                print("Failed to grab frame")
                break

            data = pickle.dumps(frame)
            message_size = struct.pack("Q", len(data))
            client_socket.sendall(message_size + data)

            time.sleep(0.4)

    except socket.error as e:
        print(f"Socket error: {e}")

    except cv2.error as e:
        print(f"OpenCV error: {e}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

    finally:
        camera.release()


def get_name():

    try:
        packed_name_length = client_socket.recv(struct.calcsize("Q"))

        if not packed_name_length:
            return None
        
        name_length = struct.unpack("Q", packed_name_length)[0]
        name_data = b""

        while len(name_data) < name_length:
            packet = client_socket.recv(name_length - len(name_data))

            if not packet:
                break

            name_data += packet

        name = name_data.decode('utf-8')
        return name
    
    except socket.error as e:

        print(f"Socket error while receiving name: {e}")
        return None


def play_greeting(name):

    tts = gTTS(text=f"Welcome {name}. Nice to see you again.", lang='en')
    tts.save("greeting.mp3")
    playsound("greeting.mp3")
    os.remove("greeting.mp3")


# def button_buzzer_thread():

#     while True:
#         button_state = io.input(BUTTON_PIN)
        
#         if button_state == io.LOW:
#             io.output(BUZZER_PIN, io.HIGH)
#             time.sleep(0.1)
#             io.output(BUZZER_PIN, io.LOW)

#         time.sleep(0.1)


try:

    # buzzer_thread = threading.Thread(target=button_buzzer_thread)
    # buzzer_thread.daemon = True
    # buzzer_thread.start()

    while True:

        if input('Enter:  ') == 'x':
            activateCamera()
            
            name = get_name()
            if name and name != 'Stranger':
        
                print(f"Recognized person: {name}")
                play_greeting(name)

        # if io.input(PIR_PIN):

        #     print("Motion Detected!")
        #     activateCamera()
        
        #     name = get_name()
        #     if name:
        #         print(f"Recognized person: {name}")
        #         play_greeting(name)
            

        else:
            print("No Motion")

        time.sleep(0.5)  

except KeyboardInterrupt:
    print("Program exited by user")

finally:
    client_socket.close()
    # io.cleanup()
