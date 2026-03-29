import cv2
import numpy as np
import face_recognition
import os
import pickle
import database
import export_attendance
import threading
import pyttsx3

ENCODINGS_FILE = "encodings.pickle"

def speak(text):
    def run_speech():
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    threading.Thread(target=run_speech, daemon=True).start()

def load_encodings():
    if not os.path.exists(ENCODINGS_FILE):
        return [], []
    with open(ENCODINGS_FILE, "rb") as f:
        known_encodings_dict = pickle.load(f)
    user_ids = list(known_encodings_dict.keys())
    encodings = list(known_encodings_dict.values())
    return user_ids, encodings

def start_recognition():
    user_ids, encodeListKnown = load_encodings()
    if not encodeListKnown:
        print("No registered users found. Please run register.py to add users first.")
        return

    print(f"Loaded {len(encodeListKnown)} known faces. Starting webcam...")
    
    # Load user dictionary for quick name lookups
    user_name_cache = database.get_all_users()
    
    cap = cv2.VideoCapture(0)
    
    process_this_frame = True

    while True:
        success, img = cap.read()
        if not success:
            break
            
        # Resize frame of video to 1/2 size for slightly faster processing without losing small faces
        imgS = cv2.resize(img, (0, 0), None, 0.5, 0.5)
        imgS = cv2.cvtColor(imgS, cv2.COLOR_BGR2RGB)
        
        # Only process every other frame to save time
        if process_this_frame:
            facesCurFrame = face_recognition.face_locations(imgS)
            encodesCurFrame = face_recognition.face_encodings(imgS, facesCurFrame)
            
            face_names = []
            for encodeFace in encodesCurFrame:
                # See if the face is a match for the known face(s)
                matches = face_recognition.compare_faces(encodeListKnown, encodeFace, tolerance=0.5)
                faceDis = face_recognition.face_distance(encodeListKnown, encodeFace)
                name = "Unknown"
                
                if len(faceDis) > 0:
                    matchIndex = np.argmin(faceDis)
                    if matches[matchIndex]:
                        user_id = user_ids[matchIndex]
                        name = user_name_cache.get(user_id, "Unknown")
                        # Log attendance directly
                        is_new_log = database.log_attendance(user_id)
                        if is_new_log and name != "Unknown":
                            speak(f"Welcome {name}, your attendance is marked.")
                        
                face_names.append(name)
                
        process_this_frame = not process_this_frame
        
        # Display the results
        for (y1, x2, y2, x1), name in zip(facesCurFrame, face_names):
            # Scale back up face locations since the frame we detected in was scaled to 1/2 size
            y1, x2, y2, x1 = y1 * 2, x2 * 2, y2 * 2, x1 * 2
            
            color = (0, 255, 0) if name != "Unknown" else (0, 0, 255)
            
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            cv2.rectangle(img, (x1, y2 - 35), (x2, y2), color, cv2.FILLED)
            cv2.putText(img, name, (x1 + 6, y2 - 6), cv2.FONT_HERSHEY_COMPLEX, 1, (255, 255, 255), 2)
            
        cv2.imshow('Face Recognition & Attendance', img)
        
        # Hit 'q' or ESC on the keyboard to quit!
        key = cv2.waitKey(1)
        if key & 0xFF == ord('q') or key == 27:
            break
            
    cap.release()
    cv2.destroyAllWindows()
    
    print("Generating Daily Excel Report...")
    export_attendance.generate_csv_report()

if __name__ == "__main__":
    start_recognition()
