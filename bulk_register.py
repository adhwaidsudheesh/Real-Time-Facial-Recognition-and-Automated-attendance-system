import cv2
import face_recognition
import os
import pickle
import urllib.request
import numpy as np
import database
import ssl

ssl._create_default_https_context = ssl._create_unverified_context

famous_people = {
    "Elon Musk": "https://en.wikipedia.org/wiki/Special:FilePath/Elon_Musk_Royal_Society_(crop1).jpg",
    "Bill Gates": "https://en.wikipedia.org/wiki/Special:FilePath/Bill_Gates_2017_(cropped).jpg",
    "Steve Jobs": "https://en.wikipedia.org/wiki/Special:FilePath/Steve_Jobs_Headshot_2010-CROP_(cropped_2).jpg",
    "Mark Zuckerberg": "https://en.wikipedia.org/wiki/Special:FilePath/Mark_Zuckerberg_F8_2019_Keynote_(32830578717)_(cropped).jpg",
    "Jeff Bezos": "https://en.wikipedia.org/wiki/Special:FilePath/Jeff_Bezos_at_Amazon_Spheres_Grand_Opening_in_Seattle_-_2018_(39074799225)_(cropped).jpg",
    "Barack Obama": "https://en.wikipedia.org/wiki/Special:FilePath/President_Barack_Obama.jpg",
    "Donald Trump": "https://en.wikipedia.org/wiki/Special:FilePath/Donald_Trump_official_portrait.jpg",
    "Joe Biden": "https://en.wikipedia.org/wiki/Special:FilePath/Joe_Biden_presidential_portrait.jpg",
    "Albert Einstein": "https://en.wikipedia.org/wiki/Special:FilePath/Albert_Einstein_Head.jpg",
    "Marie Curie": "https://en.wikipedia.org/wiki/Special:FilePath/Marie_Curie_c._1920.jpg",
    "Taylor Swift": "https://en.wikipedia.org/wiki/Special:FilePath/Taylor_Swift_at_the_2023_MTV_Video_Music_Awards_4.png",
    "Selena Gomez": "https://en.wikipedia.org/wiki/Special:FilePath/Selena_Gomez_at_the_2019_American_Music_Awards.png",
    "Cristiano Ronaldo": "https://en.wikipedia.org/wiki/Special:FilePath/Cristiano_Ronaldo_2018.jpg",
    "Lionel Messi": "https://en.wikipedia.org/wiki/Special:FilePath/Lionel_Messi_20180626.jpg",
    "LeBron James": "https://en.wikipedia.org/wiki/Special:FilePath/LeBron_James_-_51959723161_(cropped).jpg",
    "Tom Cruise": "https://en.wikipedia.org/wiki/Special:FilePath/Tom_Cruise_by_Gage_Skidmore_2.jpg",
    "Brad Pitt": "https://en.wikipedia.org/wiki/Special:FilePath/Brad_Pitt_2019_by_Glenn_Francis.jpg",
    "Leonardo DiCaprio": "https://en.wikipedia.org/wiki/Special:FilePath/Leonardo_DiCaprio_visit_to_Goddard_Space_Flight_Center_in_2016_(26300181585).jpg",
    "Will Smith": "https://en.wikipedia.org/wiki/Special:FilePath/Will_Smith_by_Gage_Skidmore_2.jpg",
    "Scarlett Johansson": "https://en.wikipedia.org/wiki/Special:FilePath/Scarlett_Johansson_by_Gage_Skidmore_2_(cropped).jpg",
    "Robert Downey Jr": "https://en.wikipedia.org/wiki/Special:FilePath/Robert_Downey_Jr_2014_Comic_Con_(cropped).jpg",
    "Chris Evans": "https://en.wikipedia.org/wiki/Special:FilePath/Chris_Evans_-_Captain_America_2_press_conference_(cropped).jpg",
    "Chris Hemsworth": "https://en.wikipedia.org/wiki/Special:FilePath/Chris_Hemsworth_by_Gage_Skidmore_2_(cropped).jpg",
    "Marilyn Monroe": "https://en.wikipedia.org/wiki/Special:FilePath/Marilyn_Monroe_in_1952.jpg",
    "Emma Watson": "https://en.wikipedia.org/wiki/Special:FilePath/Emma_Watson_at_the_2014_Golden_Globes_(cropped).jpg",
    "Keanu Reeves": "https://en.wikipedia.org/wiki/Special:FilePath/Keanu_Reeves_(crop_and_levels)_(cropped).jpg",
    "Zendaya": "https://en.wikipedia.org/wiki/Special:FilePath/Zendaya_-_2019_by_Glenn_Francis.jpg",
    "Dwayne Johnson": "https://en.wikipedia.org/wiki/Special:FilePath/Dwayne_Johnson_2014_(cropped).jpg",
    "Morgan Freeman": "https://en.wikipedia.org/wiki/Special:FilePath/Morgan_Freeman_at_The_Pentagon_on_2_August_2023_-_230802-D-PM193-3363_(cropped).jpg",
    "Oprah Winfrey": "https://en.wikipedia.org/wiki/Special:FilePath/Oprah_in_2014.jpg"
}

ENCODINGS_FILE = "encodings.pickle"
headers = {'User-Agent': 'Mozilla/5.0 FaceRecogBulkDownloader'}

def run_bulk():
    os.makedirs("Dataset", exist_ok=True)
    
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            known_encodings = pickle.load(f)
    else:
        known_encodings = {}

    success_count = 0
    print(f"Starting bulk registration of {len(famous_people)} items...")
    
    for name, url in famous_people.items():
        print(f"Fetching {name}...")
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as response:
                image_bytes = np.asarray(bytearray(response.read()), dtype="uint8")
                img = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

            if img is None:
                print(f"  [X] Failed: Could not decode image for {name}.")
                continue
                
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            
            # Extract encoding (downscale if necessary)
            face_locations = face_recognition.face_locations(rgb_img)
            if not face_locations:
                img_small = cv2.resize(rgb_img, (0, 0), None, 0.25, 0.25)
                locs_S = face_recognition.face_locations(img_small)
                face_locations = [(t*4, r*4, b*4, l*4) for (t, r, b, l) in locs_S]
                
            if not face_locations:
                face_locations = face_recognition.face_locations(rgb_img, number_of_times_to_upsample=2)

            if not face_locations:
                print(f"  [X] Failed: No face detected in Wikipedia photo for {name}.")
                continue
                
            encodings = face_recognition.face_encodings(rgb_img, face_locations)
            if encodings:
                user_id = database.add_user(name)
                # save image
                cv2.imwrite(f"Dataset/{user_id}.jpg", img)
                known_encodings[user_id] = encodings[0]
                success_count += 1
                print(f"  [+] Success: {name} mapped to User ID {user_id}")
            else:
                print(f"  [X] Failed: Could not process face for {name}.")
                
        except Exception as e:
            print(f"  [X] Failed: Error fetching {name}: {e}")
            
    # Save back to pickle file
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(known_encodings, f)
        
    print(f"\nCompleted! {success_count} famous people successfully registered and added to database.")

if __name__ == "__main__":
    run_bulk()
