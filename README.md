## Mental Health Companion Chatbot

This project is a simple mental‑health companion web app. It:

- **Analyzes text** messages for sentiment and mood and responds like a supportive therapist.
- **Analyzes voice** recordings for rough energy/tempo to guess mood and respond supportively.

> **Important:** This app is for learning and support only. It is **not** a replacement for professional care or emergency services.

### Project structure

- `backend/`
  - `main.py` – FastAPI server with:
    - `POST /api/chat` – text mood + reply
    - `POST /api/analyze_voice` – voice mood + reply
- `frontend/`
  - `index.html`, `styles.css`, `script.js` – single‑page UI with chat and voice mood checker
- `requirements.txt` – Python dependencies

### How to run (Windows)

1. **Create and activate a virtual environment (recommended)**

```powershell
cd C:\Users\kamalan\Documents\Pavithra\MentalHealthCompanion
python -m venv .venv
.venv\Scripts\activate
```

2. **Install dependencies**

```powershell
pip install -r requirements.txt
```

3. **Start the backend API**

```powershell
cd backend
uvicorn main:app --reload --port 8000
```

The API will be at `http://localhost:8000`.

4. **Open the frontend**

Simply open `frontend/index.html` in your browser (right‑click → Open With → your browser).  
For best results, you can also serve it with a simple static server (optional).

5. **Use the chatbot**

- Type a message in the text box and press **Send**.
- Use **Start Recording / Stop Recording** in the Voice Mood Check section and allow microphone access in your browser.

### Safety note

If you or someone you know is in immediate danger or considering self‑harm, please contact your local emergency number or a crisis hotline right away. This chatbot cannot respond to emergencies.







