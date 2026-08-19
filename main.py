import collections
import os
import sys
import msvcrt
import time
import traceback

import numpy as np
import sounddevice as sd
import webrtcvad
from faster_whisper import WhisperModel

import auth
import database
import commands


def write_crash_log(context: str) -> None:
    log_dir = os.path.dirname(database.DB_PATH)
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, "error.log")
    with open(log_path, "a", encoding="utf-8") as log_file:
        log_file.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] {context}\n")
        traceback.print_exc(file=log_file)
    print(f"\n{context}. Details were written to: {log_path}")


def get_masked_password(prompt: str = "Password: "):
    print(prompt, end="", flush=True)
    password = ""
    while True:
        ch = msvcrt.getch()
        if ch in (b"\r", b"\n"):
            print("")
            break
        elif ch == b"\x08":
            if password:
                password = password[:-1]
                print("\b \b", end="", flush=True)
        elif ch == b"\x03":
            raise KeyboardInterrupt
        else:
            try:
                char = ch.decode("utf-8")
            except UnicodeDecodeError:
                continue
            password += char
            print("*", end="", flush=True)
    return password


def prompt_signup() -> str | None:
    print("\n--- Sign Up ---")

    while True:
        username = input("Choose a username: ").strip()

        if not auth._is_valid_username(username):
            print("Username must be 3 to 20 characters: letters, numbers, or underscores only.")
            continue

        if database.username_exists(username):
            print(f"The username {username} is already taken. Please choose another.")
            continue

        password = input("Choose a password (min 8 characters): ")

        if len(password) < 8:
            print("Password must be at least 8 characters. Please try again.")
            continue

        if not (any(c.isalpha() for c in password) and any(c.isdigit() for c in password)):
            print("Password must contain both letters and numbers. Please try again.")
            continue

        confirm = input("Confirm password: ")
        if password != confirm:
            print("Passwords do not match. Please try again.")
            continue

        break

    success, message = auth.signup(username, password)
    commands.speak(message)
    return username if success else None


def prompt_login() -> str | None:
    print("\n--- Log In ---")
    username = input("Username: ").strip()
    password = get_masked_password("Password: ")

    success, message = auth.login(username, password)
    commands.speak(message)
    return username if success else None


def transcribe(frames: list[np.ndarray]) -> str:
    audio_int16 = np.concatenate(frames).flatten()
    audio_float32 = audio_int16.astype(np.float32) / 32768.0

    peak = np.abs(audio_float32).max()
    if peak > 0:
        gain = min(0.9 / peak, 20.0)
        audio_float32 = audio_float32 * gain

    segments, _ = model.transcribe(
        audio_float32,
        language="en",
        beam_size=5,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    return " ".join(s.text.strip() for s in segments).strip()


database.init_db()
commands.speak("Welcome to your voice assistant.")

logged_in_user = None

while logged_in_user is None:
    print("\n1. Log In\n2. Sign Up\n3. Exit")
    try:
        choice = int(input("Choose an option: "))
    except ValueError:
        print("Please enter 1, 2, or 3.")
        continue

    match choice:
        case 1:
            logged_in_user = prompt_login()
        case 2:
            logged_in_user = prompt_signup()
        case 3:
            print("Goodbye.")
            sys.exit(0)
        case _:
            print("Please enter 1, 2, or 3.")

print(f"You are now logged in as {logged_in_user}.")

MODEL_SIZE = "small.en"
CPU_THREADS = 4
try:
    model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)
except Exception:
    write_crash_log("Could not load the speech-recognition model")
    input("Press Enter to close.")
    sys.exit(1)

vad = webrtcvad.Vad(2)

SAMPLE_RATE = 16000
FRAME_MS = 30                                   
BLOCK_SIZE = int(SAMPLE_RATE * FRAME_MS / 1000)       
PADDING_FRAMES = 10          
SILENCE_FRAMES_TO_STOP = 15  
MIN_SPEECH_FRAMES = 8
stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="int16",
    blocksize=BLOCK_SIZE,
)
stream.start()

print("Calibrating mic... stay quiet for a second.")
calibration_samples = []
for _ in range(30):
    data, overflowed = stream.read(BLOCK_SIZE)
    amplitude = np.abs(data).mean()
    calibration_samples.append(amplitude)

ambient_level = np.mean(calibration_samples)
SILENCE_THRESHOLD = max(ambient_level * 2, ambient_level + 40, 30)
print(f"Ambient level: {ambient_level:.0f} -> threshold set to {SILENCE_THRESHOLD:.0f}")

ring_buffer = collections.deque(maxlen=PADDING_FRAMES)
voiced_frames = []
speaking = False
silence_run = 0

WAKE_WORD = "hey siri"
AWAKE_TIMEOUT_SECONDS = 15
awake = False
last_active_time = 0.0

print(f"Ready! Say '{WAKE_WORD}' to activate. (press Ctrl+C to stop)")
try:
    running = True
    while running:
        if awake and not speaking and (time.time() - last_active_time) > AWAKE_TIMEOUT_SECONDS:
            awake = False
            commands.speak(f"\nNo command heard, going back to sleep. Say '{WAKE_WORD}' to wake me up.")

        data, overflowed = stream.read(BLOCK_SIZE)
        if overflowed:
            print("Warning: audio buffer overflowed, some audio may have been dropped.")

        is_speech = vad.is_speech(data.tobytes(), SAMPLE_RATE)

        if not speaking:
            ring_buffer.append((data.copy(), is_speech))
            num_voiced = sum(1 for _, s in ring_buffer if s)

            if ring_buffer.maxlen and num_voiced > 0.6 * ring_buffer.maxlen:
                speaking = True
                voiced_frames = [frame for frame, _ in ring_buffer]
                ring_buffer.clear()
        else:
            voiced_frames.append(data.copy())

            if is_speech:
                silence_run = 0
            else:
                silence_run += 1
                if silence_run >= SILENCE_FRAMES_TO_STOP:
                    if len(voiced_frames) - silence_run >= MIN_SPEECH_FRAMES:
                        try:
                            text = transcribe(voiced_frames)
                        except Exception:
                            write_crash_log("Speech recognition failed")
                            text = ""

                        if not awake:
                            if text and WAKE_WORD in text.lower():
                                print(f"\rYou said: {text}" + " " * 20)
                                commands.speak("How can i assist you?")
                                awake = True
                                last_active_time = time.time()
                        else:
                            if text:
                                print(f"\rYou said: {text}" + " " * 20)
                                running = commands.handle_command(text, logged_in_user)
                                last_active_time = time.time()

                    voiced_frames = []
                    speaking = False
                    silence_run = 0
                    ring_buffer.clear()

except KeyboardInterrupt:
    print("\nStopping... goodbye!")

finally:
    stream.stop()
    stream.close()