import cv2
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import face_recognition
import os
import pickle
import smtplib
import socket
import struct
import time
import traceback


known_face_encodings = []
known_face_names = []

images_path = r'./images'

for filename in os.listdir(images_path):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        image_path = os.path.join(images_path, filename)
        image = face_recognition.load_image_file(image_path)
        face_encodings = face_recognition.face_encodings(image)
        if face_encodings:
            known_face_encodings.append(face_encodings[0])
            known_face_names.append(os.path.splitext(filename)[0])

print(f"Loaded {len(known_face_encodings)} face(s) from the images directory.")


SERVER_IP = socket.gethostbyname(socket.gethostname())
SERVER_PORT = 9999

print(SERVER_IP)

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((SERVER_IP, SERVER_PORT))
server_socket.listen()
print(f"Listening for connections on {SERVER_IP}:{SERVER_PORT}...")


client_socket, addr = server_socket.accept()
print(f"Connection from {addr} has been established.")

data = b""


def notify_user(frame, name):
    
    my_email = "pi.ring.server@gmail.com"
    my_passkey = "txkb dcyv dxex yoal"
    user_email = "eshaan.vimal@somaiya.edu"
    
    _, buffer = cv2.imencode('.jpg', frame)
    image_data = buffer.tobytes()

    msg = MIMEMultipart()
    msg['From'] = my_email
    msg['To'] = user_email
    msg['Subject'] = "Alert: Someone is at the door"
    
    body = f"{name} is at the door."
    msg.attach(MIMEText(body, 'plain'))
    
    img = MIMEImage(image_data, name="door_image.jpg")
    msg.attach(img)

    try:
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=my_email, password=my_passkey)
            connection.sendmail(from_addr=my_email, to_addrs=user_email, msg=msg.as_string())
        print("Notification email sent successfully!")

    except Exception as e:
        print(f"Error sending email: {e}")


last_seen = {}

try:
    while True:

        while len(data) < struct.calcsize("Q"):
            packet = client_socket.recv(4 * 1024)
            if not packet:
                break
            data += packet
        if not data:
            break

        packed_msg_size = data[:struct.calcsize("Q")]
        data = data[struct.calcsize("Q"):]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(data) < msg_size:
            data += client_socket.recv(4 * 1024)

        frame_data = data[:msg_size]
        data = data[msg_size:]

        frame = pickle.loads(frame_data)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        small_frame = cv2.resize(rgb_frame, (0, 0), fx=0.25, fy=0.25)

        face_locations = face_recognition.face_locations(small_frame, model="hog")
        face_encodings = face_recognition.face_encodings(small_frame, face_locations)

        name = "Stranger"
        notify_flag = True;

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):

            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = face_distances.argmin() if len(face_distances) > 0 else None

            if best_match_index is not None and matches[best_match_index]:

                name = known_face_names[best_match_index]

                current_time = time.time()
                last_seen_time = last_seen.get(name, 0)

                if current_time - last_seen_time < 90:
                    notify_flag = False
                    break

                last_seen[name] = current_time
                notify_flag = True

            top *= 4
            right *= 4
            bottom *= 4
            left *= 4

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_DUPLEX, 0.75, (255, 255, 255), 1)

        if notify_flag:

            name_data = name.encode('utf-8')
            name_length = struct.pack("Q", len(name_data))
            client_socket.sendall(name_length + name_data)

            cv2.imshow("Face Recognition", frame)
            cv2.waitKey(0)

            notify_user(frame, name)

        else:

            name_data = ''.encode('utf-8')
            name_length = struct.pack("Q", len(name_data))
            client_socket.send(name_length)
            client_socket.send(name_data)


except socket.error as e:
    print(f"Socket error: {e}")

except cv2.error as e:
    print(f"OpenCV error: {e}")

except Exception as e:
    print(traceback.format_exc())
    print(f"An unexpected error occurred: {e}")

finally:
    client_socket.close()
    server_socket.close()
    cv2.destroyAllWindows()
