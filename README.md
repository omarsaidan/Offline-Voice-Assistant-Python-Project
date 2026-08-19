# Voice Assistant

A Windows desktop voice assistant built in Python. It listens for a wake word, transcribes speech locally using [faster-whisper](https://github.com/SYSTRAN/faster-whisper), and executes system commands — opening apps, taking screenshots, searching the web, typing dictated text, and more. User accounts are protected with salted, hashed passwords stored in a local SQLite database.

## Features

- **Wake-word activation** — stays idle until it hears "Hey Siri," then listens for a command for a configurable timeout window.
- **Local speech recognition** — uses `faster-whisper` (small.en, int8) for fast, offline transcription with no cloud API calls.
- **Voice activity detection** — `webrtcvad` filters silence so the assistant only transcribes actual speech, with an auto-calibrated ambient-noise threshold.
- **User accounts** — sign up / log in with PBKDF2-HMAC-SHA256 password hashing (200,000 iterations) and per-user salts. No plaintext passwords are ever stored.
- **System commands**, including:
  - Open Notepad, Calculator, or the default web browser
  - Take and open a screenshot
  - Minimize all windows / maximize / switch / close the active window
  - Search Google by voice
  - Copy, paste, and read the clipboard aloud
  - Type dictated text into the active window
- **Text-to-speech feedback** — every action is confirmed out loud via `pyttsx3`.
- **Packaged as a standalone `.exe`** — includes a pre-configured PyInstaller spec file with all the hidden imports and bundled data `faster-whisper`, `pyttsx3`, and `sounddevice` need to run outside a Python environment.

## Tech Stack

| Purpose | Library |
|---|---|
| Speech-to-text | `faster-whisper` |
| Voice activity detection | `webrtcvad` |
| Audio capture | `sounddevice`, `numpy` |
| Text-to-speech | `pyttsx3` |
| System automation | `pyautogui`, `pyperclip`, `Pillow` |
| Persistence | `sqlite3` (standard library) |
| Packaging | `PyInstaller` |

## Requirements

- **Windows only** — password entry uses `msvcrt`, and TTS uses the SAPI5 driver via `pyttsx3`.
- Python 3.10+
- A working microphone

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/<your-username>/<your-repo>.git
   cd <your-repo>
   ```
2. (Recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the assistant:
```bash
python main.py
```

On first run you'll be prompted to **sign up** or **log in**. Once authenticated, the assistant calibrates to your microphone's ambient noise level, then waits for the wake word.

**Example flow:**
1. Say **"Hey Siri"** → the assistant responds and starts listening for a command.
2. Say a command, e.g. **"open notepad"**, **"take screenshot"**, or **"search for python tutorials"**.
3. If no command is heard within 15 seconds, it automatically goes back to sleep.

### Available voice commands

| Say | Action |
|---|---|
| "open notepad" | Opens Notepad |
| "open calculator" | Opens Calculator |
| "open web browser" | Opens your default browser to Google |
| "show images" | Opens the project's reference images (voice-command diagrams) |
| "take screenshot" | Captures and opens a screenshot |
| "minimize all windows" | Minimizes all open windows |
| "maximize window" | Maximizes the active window |
| "switch window" | Alt-tabs to the next window |
| "close window" | Closes the active window (Alt+F4) |
| "search for \<query\>" / "search about \<query\>" | Searches Google |
| "copy this text \<text\>" / "copy text \<text\>" / "copy this \<text\>" | Copies the dictated text to the clipboard |
| "paste text" | Pastes clipboard contents |
| "read clipboard" | Reads clipboard contents aloud |
| "type \<text\>" | Types the dictated text into the active window |
| "hi" / "hello" | Greets you |
| "exit" / "quit" | Ends the session |

## Building a standalone executable

The repository includes a pre-configured `main.spec` file with all the hidden imports and bundled data that `faster-whisper`, `pyttsx3`, and `sounddevice` need — building without it typically fails with missing-module errors.

1. Install the extra build dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```
2. Build using the existing spec file:
   ```bash
   pyinstaller main.spec
   ```
3. The compiled app will be in `dist/main/`.

> **Note:** the spec file expects an `assets/` folder, a `whisper_model/` folder, and a `voice-assistant.ico` icon to be present in the project root at build time.

## Project Structure

```
.
├── main.py             # Entry point: audio pipeline, wake-word loop, login flow
├── commands.py         # Voice command implementations and dispatch table
├── auth.py             # Signup/login logic, password hashing and validation
├── database.py         # SQLite schema and user account persistence
├── main.spec           # PyInstaller build configuration
├── requirements.txt    # Runtime dependencies
├── requirements-dev.txt# Build-only dependencies (PyInstaller, comtypes)
└── assets/             # Reference images shown by "show images"
```

## Data & Privacy

- User accounts are stored locally in `%LOCALAPPDATA%\VoiceAssistant\users.db` — never inside the project folder, and never committed to version control.
- Passwords are hashed with PBKDF2-HMAC-SHA256 (200,000 iterations) and a unique random salt per user; plaintext passwords are never stored or logged.
- All speech recognition runs locally — no audio is sent to any external service.

## License

MIT License
