1. Prerequisites
Ensure you have Python installed, then install the required dependencies:

pip install opencv-python face-recognition pyttsx3 python-docx numpy



2- Registering Users
You have two ways to add people to the system:
- **Manual Registration:** Run `python register.py` to open the GUI. You can capture a photo via webcam or upload an existing image.
- **Bulk Registration:** Place images in a folder and use `bulk_register.py` to enroll many users at once.

3. Running the System
Start the main recognition engine:bash
python main.py

The webcam will open. When a face is recognized:
1. The system marks "Present" in the database.
2. A voice message welcomes the user.
3. On closing (press `q`), a daily CSV report is automatically generated and opened.

 4. Generating Reports
- **Daily CSV:** Automatically created by `main.py` or manually via `python export_attendance.py`.
- **Project Report:** Run `python generate_report.py` to generate a professional Word document summary of the project.
