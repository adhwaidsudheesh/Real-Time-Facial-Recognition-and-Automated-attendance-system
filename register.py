import cv2
import face_recognition
import os
import pickle
import tkinter as tk
from tkinter import messagebox, filedialog
import database

# Ensure Dataset folder exists
os.makedirs("Dataset", exist_ok=True)
ENCODINGS_FILE = "encodings.pickle"

def save_encoding(user_id, img):
    rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    # Try detecting face on normal scale
    face_locations = face_recognition.face_locations(rgb_img)
    
    # If failed, try downscaling (helps if face is too close/large)
    if not face_locations:
        img_small = cv2.resize(rgb_img, (0, 0), None, 0.25, 0.25)
        small_locations = face_recognition.face_locations(img_small)
        # scale back up
        face_locations = [(t*4, r*4, b*4, l*4) for (t, r, b, l) in small_locations]
        
    # If still failed, try upsampling (helps if face is small)
    if not face_locations:
        face_locations = face_recognition.face_locations(rgb_img, number_of_times_to_upsample=2)

    if not face_locations:
        return False, "No face detected. Try moving the camera back, ensuring good lighting, and looking straight."
    if len(face_locations) > 1:
        return False, "Multiple faces detected. Please use a photo with exactly one face."
    
    encodings = face_recognition.face_encodings(rgb_img, face_locations)
    if not len(encodings):
        return False, "Could not extract face encoding."
    
    # Save the encoding inside a dictionary mapping User ID -> Encoding
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            known_encodings = pickle.load(f)
    else:
        known_encodings = {}
        
    known_encodings[user_id] = encodings[0]
    
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(known_encodings, f)
        
    return True, "Registration successful!"

def register_via_webcam(name_entry):
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name first.")
        return
        
    cap = cv2.VideoCapture(0)
    messagebox.showinfo("Instructions", "Press SPACE to take a photo, or ESC to cancel.")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        # Draw some instructions on screen
        display_frame = frame.copy()
        cv2.putText(display_frame, "Press SPACE to snap photo", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv2.imshow("Webcam Registration", display_frame)
        
        key = cv2.waitKey(1)
        if key == 32: # SPACE key
            # Process frame
            user_id = database.add_user(name)
            img_path = f"Dataset/{user_id}.jpg"
            cv2.imwrite(img_path, frame)
            
            success, msg = save_encoding(user_id, frame)
            if success:
                messagebox.showinfo("Success", f"{name} registered successfully!")
            else:
                # Cleanup database entry if face extraction failed
                os.remove(img_path)
                messagebox.showerror("Error", msg)
            break
        elif key == 27: # ESC key
            break
            
    cap.release()
    cv2.destroyAllWindows()

def register_via_upload(name_entry):
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name first.")
        return

    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
    if not file_path:
        return
        
    img = cv2.imread(file_path)
    if img is None:
        messagebox.showerror("Error", "Could not read the uploaded image.")
        return
        
    user_id = database.add_user(name)
    img_path = f"Dataset/{user_id}.jpg"
    cv2.imwrite(img_path, img)
    
    success, msg = save_encoding(user_id, img)
    if success:
        messagebox.showinfo("Success", f"{name} registered successfully from file!")
    else:
        os.remove(img_path)
        messagebox.showerror("Error", msg)

def create_ui():
    root = tk.Tk()
    root.title("Face Registration System")
    root.geometry("400x250")
    root.configure(padx=20, pady=20)
    
    title_label = tk.Label(root, text="Register New User", font=("Helvetica", 16, "bold"))
    title_label.pack(pady=10)
    
    name_frame = tk.Frame(root)
    name_frame.pack(pady=10)
    
    name_label = tk.Label(name_frame, text="Full Name:")
    name_label.pack(side=tk.LEFT, padx=5)
    
    name_entry = tk.Entry(name_frame, width=30)
    name_entry.pack(side=tk.LEFT)
    
    btn_frame = tk.Frame(root)
    btn_frame.pack(pady=20)
    
    upload_btn = tk.Button(btn_frame, text="Upload Photo", width=15, command=lambda: register_via_upload(name_entry))
    upload_btn.pack(side=tk.LEFT, padx=10)
    
    webcam_btn = tk.Button(btn_frame, text="Use Webcam", width=15, command=lambda: register_via_webcam(name_entry))
    webcam_btn.pack(side=tk.LEFT, padx=10)
    
    root.mainloop()

if __name__ == "__main__":
    create_ui()
