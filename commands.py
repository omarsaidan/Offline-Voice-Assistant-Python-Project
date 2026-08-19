import subprocess
import webbrowser
import pyttsx3
import os
import re
from PIL import Image
import time
import pyperclip
import pyautogui

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
ASSETS_FOLDER = os.path.join(PROJECT_ROOT, "assets")
SCREENSHOT_FOLDER = os.path.join(PROJECT_ROOT, "screenshots")

def speak(text: str) -> None:
    print(f"Assistant: {text}")
    engine = pyttsx3.init()
    engine.setProperty("rate", 175)
    engine.setProperty("volume", 1.0)
    voices = engine.getProperty("voices")
    engine.setProperty("voice", voices[1].id)
    engine.say(text)
    engine.runAndWait()
    engine.stop()


def open_notepad() -> None:
    subprocess.Popen(["notepad.exe"])
    speak("Opening Notepad.")


def open_calculator() -> None:
    subprocess.Popen(["calc.exe"])
    speak("Opening Calculator.")


def open_browser() -> None:
    webbrowser.open("https://www.google.com")
    speak("Opening your web browser.")


def greet(username: str = "") -> None:
    speak(f"Hello {username}! How can I help you today?")


def exit_assistant(username: str = "") -> None:
    speak(f"Goodbye {username}!")

def show_image() -> None:
    image_path1: str = os.path.join(ASSETS_FOLDER, "Voice-Assistance Project_page-0003.jpg")
    image_path2: str = os.path.join(ASSETS_FOLDER, "Voice-Assistance Project_page-0004.jpg")

    if not os.path.isfile(image_path1) and not os.path.isfile(image_path2):
        speak("I couldn't find these image!")
        return

    speak("Opening voice commands image.")
    image1 = Image.open(image_path1)
    image2 = Image.open(image_path2)
    image1.show()
    image2.show()    
 
 
def paste_clipboard() -> None:
    time.sleep(3)  
    pyautogui.hotkey("ctrl", "v")
    speak("Clipboard pasted.")
    
def minimize_all_windows() -> None:
    pyautogui.hotkey("win", "d")
    speak("Minimized all windows.")
    
 
def take_screenshot() -> None:
    os.makedirs(SCREENSHOT_FOLDER, exist_ok=True)

    filename = f"screenshot_{time.strftime('%Y-%m-%d_%H-%M-%S')}.png"
    filepath = os.path.join(SCREENSHOT_FOLDER, filename)

    screenshot = pyautogui.screenshot()
    screenshot.save(filepath)
    
    speak(f"Screenshot saved.")
    image = Image.open(filepath)
    image.show()

waiting_to_close_window = False
def close_active_window() -> None:
    global waiting_to_close_window
    waiting_to_close_window = True
    speak("Do you want to close the current active window?")
    
def maximize_window() -> None:
    pyautogui.hotkey("win", "up")
    speak("Window maximized.")
    
def switch_window() -> None:
    pyautogui.hotkey("alt", "tab")
    speak("Switching window.")
    
search_query = ""
SEARCH_TRIGGERS = ["search about", "search for", "search"]
def search_web() -> None:
    query = ""
    for trigger in SEARCH_TRIGGERS:
        if search_query.startswith(trigger):
            query = search_query[len(trigger):].strip()
            break

    if not query:
        speak("I didn't catch what you wanted me to search for.")
        return

    url = "https://www.google.com/search?q=" + query.replace(" ", "+")
    webbrowser.open(url)
    speak(f"Searching for {query}.")
    
    
COPY_TRIGGERS = ["copy this text", "copy text", "copy this"]
def copy_text() -> None:
    text_to_copy = ""
    for trigger in COPY_TRIGGERS:
        if search_query.startswith(trigger):
            text_to_copy = search_query[len(trigger):].strip()
            break

    if not text_to_copy:
        speak("I didn't catch what you wanted me to copy.")
        return

    pyperclip.copy(text_to_copy)
    speak(f"Copied '{text_to_copy}' to clipboard.")
    
def read_clipboard() -> None:
    clipboard_text = pyperclip.paste()
    if clipboard_text:
        speak(f"Your clipboard contains: {clipboard_text}")
    else:
        speak("Your clipboard is empty.")
            
TYPE_TRIGGERS = ["type"]
def type_text() -> None:
    text_to_type = ""
    for trigger in TYPE_TRIGGERS:
        if search_query.startswith(trigger):
            text_to_type = search_query[len(trigger):].strip()
            break

    if not text_to_type:
        speak("I didn't catch what you wanted me to type.")
        return

    time.sleep(0.3)
    pyautogui.typewrite(text_to_type, interval=0.03)
    speak("Done typing.")


ARG_COMMANDS = [
    ("copy this text", copy_text),
    ("copy text", copy_text),
    ("copy this", copy_text),
    ("search about", search_web),
    ("search for", search_web),
    ("search", search_web),
    ("type", type_text),
]

NO_ARG_COMMANDS = {
    "open notepad": open_notepad,
    "open calculator": open_calculator,
    "open web browser": open_browser,
    "show images": show_image,
    "display images": show_image,
    "minimize all windows": minimize_all_windows,
    "take screenshot": take_screenshot,
    "close window": close_active_window,
    "maximize window": maximize_window,
    "switch window": switch_window,
    "paste text": paste_clipboard,
    "read clipboard": read_clipboard,
}

USER_AWARE_COMMANDS = {
    "hi": greet,
    "hello": greet,
    "exit": exit_assistant,
    "quit": exit_assistant,
}


def handle_command(text: str, username: str = "") -> bool:
    
    global search_query, waiting_to_close_window
    text = text.strip().lower()
    
    if waiting_to_close_window:
        waiting_to_close_window = False

        answer = re.sub(r"[^a-z\s]", "", text.lower()).strip()

        if re.search(r"\b(yes|yeah|yep|confirm)\b", answer):
            time.sleep(0.3)
            pyautogui.hotkey("alt", "f4")
            speak("Closed the active window.")

        elif re.search(r"\b(no|nope|cancel)\b", answer):
            speak("Okay, I will not close the window.")

        else:
            print(f"Assistant: Confirmation heard as: {text!r}")
            speak("I did not understand your answer. The window was not closed.")

        return True

    search_query = text

    try:
        for keyword, action in ARG_COMMANDS:
            if text == keyword or text.startswith(keyword + " "):
                action()
                return True

        for keyword, action in NO_ARG_COMMANDS.items():
            if keyword in text:
                action()
                return True

        for keyword, action in USER_AWARE_COMMANDS.items():
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                action(username)
                if action is exit_assistant:
                    return False
                return True

        speak("Sorry, I didn't understand that command.")
        return True

    except Exception as error:
        print(f"Assistant: Something went wrong running that command ({error}).")
        speak("Sorry, something went wrong with that command.")
        return True