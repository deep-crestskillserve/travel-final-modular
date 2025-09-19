import pyaudio
import websocket
import json
import threading
import time
import wave
from urllib.parse import urlencode
from datetime import datetime
from dotenv import load_dotenv
import os
from queue import Queue

load_dotenv()
YOUR_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")

CONNECTION_PARAMS = {
    "sample_rate": 16000,
    "format_turns": True,
}
API_ENDPOINT_BASE_URL = "wss://streaming.assemblyai.com/v3/ws"
API_ENDPOINT = f"{API_ENDPOINT_BASE_URL}?{urlencode(CONNECTION_PARAMS)}"

# Audio Configuration
FRAMES_PER_BUFFER = 800
SAMPLE_RATE = CONNECTION_PARAMS["sample_rate"]
CHANNELS = 1
FORMAT = pyaudio.paInt16

class AssemblyAITranscriber:
    def __init__(self):
        self.ws_app = None
        self.audio = None
        self.stream = None
        self.audio_thread = None
        self.ws_thread = None
        self.stop_event = threading.Event()
        self.transcript_queue = Queue()
        self.current_transcript = ""
        self.recorded_frames = []
        self.recording_lock = threading.Lock()

    def start(self):
        self.current_transcript = ""
        self.recorded_frames = []
        self.stop_event.clear()
        self.audio = pyaudio.PyAudio()
        try:
            self.stream = self.audio.open(
                format=FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=FRAMES_PER_BUFFER
            )
        except Exception as e:
            print(f"Error opening microphone stream: {e}")
            if self.audio:
                self.audio.terminate()
                self.audio = None
            return

        def stream_audio():
            while not self.stop_event.is_set():
                try:
                    data = self.stream.read(FRAMES_PER_BUFFER, exception_on_overflow=False)
                    with self.recording_lock:
                        self.recorded_frames.append(data)
                    self.ws_app.send(data, websocket.ABNF.OPCODE_BINARY)
                except:
                    break

        def on_open(ws):
            print("WebSocket connection opened.")
            self.audio_thread = threading.Thread(target=stream_audio)
            self.audio_thread.daemon = True
            self.audio_thread.start()

        def on_message(ws, message):
            try:
                data = json.loads(message)
                msg_type = data.get('type')
                if msg_type == 'Turn':
                    transcript = data.get('transcript', '')
                    formatted = data.get('turn_is_formatted', False)
                    print(f"\r{transcript}" if not formatted else transcript)
                    self.transcript_queue.put((transcript, formatted))
                elif msg_type == "Begin":
                    session_id = data.get('id')
                    expires_at = data.get('expires_at')
                    print(f"Session began: ID={session_id}, ExpiresAt={datetime.fromtimestamp(expires_at)}")
                elif msg_type == "Termination":
                    audio_duration = data.get('audio_duration_seconds', 0)
                    session_duration = data.get('session_duration_seconds', 0)
                    print(f"Session Terminated: Audio Duration={audio_duration}s, Session Duration={session_duration}s")
            except json.JSONDecodeError as e:
                print(f"Error decoding message: {e}")

        def on_error(ws, error):
            print(f"WebSocket Error: {error}")
            self.stop_event.set()

        def on_close(ws, close_status_code, close_msg):
            print(f"WebSocket Disconnected: Status={close_status_code}, Msg={close_msg}")
            # self.save_wav_file()
            if self.stream:
                if self.stream.is_active():
                    self.stream.stop_stream()
                self.stream.close()
                self.stream = None
            if self.audio:
                self.audio.terminate()
                self.audio = None

        self.ws_app = websocket.WebSocketApp(
            API_ENDPOINT,
            header={"Authorization": YOUR_API_KEY},
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
        )
        self.ws_thread = threading.Thread(target=self.ws_app.run_forever)
        self.ws_thread.daemon = True
        self.ws_thread.start()

    def stop(self):
        self.stop_event.set()
        if self.ws_app and self.ws_app.sock and self.ws_app.sock.connected:
            try:
                self.ws_app.send(json.dumps({"type": "Terminate"}))
                time.sleep(2)  # Wait for final messages
            except Exception as e:
                print(f"Error sending termination message: {e}")
        while not self.transcript_queue.empty():
            trans, formatted = self.transcript_queue.get()
            if formatted:
                self.current_transcript += trans + " "
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=2)
        if self.ws_app:
            self.ws_app.close()
        if self.ws_thread and self.ws_thread.is_alive():
            self.ws_thread.join(timeout=2)

    def get_transcript(self):
        return self.current_transcript.strip()

    def save_wav_file(self):
        if not self.recorded_frames:
            print("No audio data recorded.")
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recorded_audio_{timestamp}.wav"
        try:
            with wave.open(filename, 'wb') as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)  # 16-bit
                wf.setframerate(SAMPLE_RATE)
                with self.recording_lock:
                    wf.writeframes(b''.join(self.recorded_frames))
            print(f"Audio saved to: {filename}")
        except Exception as e:
            print(f"Error saving WAV file: {e}")