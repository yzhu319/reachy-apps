"""
Voice-controlled DJ using OpenAI Realtime API.

Handles bidirectional audio streaming and tool calls for the Dance Party DJ.
"""

import os
import ssl
import json
import base64
import asyncio
import logging
from typing import Optional, Any

import numpy as np
import sounddevice as sd
from scipy.signal import resample

# Fix SSL certificates on macOS
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

from reachy_mini import ReachyMini

from .dj_tools import DJ_TOOLS, DJToolHandler

logger = logging.getLogger(__name__)

# OpenAI Realtime uses 24kHz audio
OPENAI_SAMPLE_RATE = 24000

# DJ Reachy personality (optimized for speed and natural conversation)
DJ_SYSTEM_PROMPT = """
# Role
You are DJ Reachy, a fun robot DJ.

# Style
- Brief and snappy
- Enthusiastic but FAST
- Natural conversation flow

# CRITICAL: Song Request Flow
When user requests a song, ALWAYS confirm before playing:
1. Repeat back what you heard: "Soda Pop by Saja Boys, right?"
2. Wait for yes/no
3. If "yes" → call play_song immediately
4. If "no" or correction → repeat back the new name, confirm again
5. Max 2 confirmations, then play whatever you have

Example:
User: "Play soda pop by saja boys"
You: "Soda Pop by Saja Boys, right?" (NO tool call yet!)
User: "Yes"
You: "On it!" (NOW call play_song)

Example with correction:
User: "Play dancing queen"
You: "Dancing Queen, right?"
User: "No, Dancing Dream"
You: "Dancing Dream, got it?"
User: "Yes"
You: "Here we go!" (call play_song)

# Other Tools (immediate, no confirmation needed)
- stop_music: "Stopping!" then call tool
- pause_music: "Paused!" then call tool
- resume_music: "Let's go!" then call tool
- play_genre: Confirm genre briefly, then play
- change_dance_energy: "Cranking it up!" then call tool

# Rules
- Song requests: ALWAYS confirm first, then play on "yes"
- Other commands: Execute immediately
- Keep all responses under 8 words
- If unclear: "What song?" or "Say again?"
"""


class VoiceDJ:
    """
    Voice-controlled DJ using OpenAI Realtime API.

    Handles:
    - WebSocket connection to OpenAI
    - Audio input from robot microphone
    - Audio output to robot speaker
    - Tool calls for music control
    """

    def __init__(self, mini: ReachyMini, api_key: Optional[str] = None):
        """
        Initialize the Voice DJ.

        Args:
            mini: ReachyMini instance
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
        """
        self.mini = mini
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for voice mode")

        self.tool_handler = DJToolHandler(mini, on_music_state_change=self._on_music_state_change)
        self._connection = None
        self._stop_event = asyncio.Event()
        self._is_running = False

        # Audio state
        self._input_sample_rate = 16000  # Robot mic sample rate
        self._output_sample_rate = 16000  # Robot speaker sample rate
        self._is_speaking = False  # True when DJ is outputting audio (mute mic)
        self._music_playing = False  # True when music is playing (adjust noise gate)

        # Tool execution queue - wait for audio to finish before executing
        self._pending_tool_calls = []  # List of (tool_name, call_id, arguments_str)
        self._last_dj_speech_end = 0.0  # Time when DJ finished speaking (for echo prevention)

    def _on_music_state_change(self, is_playing: bool):
        """Called when music starts or stops playing."""
        self._music_playing = is_playing
        state = "playing" if is_playing else "stopped"
        print(f"[Music] State changed: {state}")

    async def start(self):
        """Start the voice DJ session."""
        import httpx
        from openai import AsyncOpenAI

        print("Connecting to OpenAI Realtime API...")

        # Start audio recording on the robot
        try:
            self.mini.media.start_recording()
            print("Microphone recording started")
        except Exception as e:
            print(f"Warning: Could not start recording: {e}")

        # Start audio playback on the robot
        try:
            self.mini.media.start_playing()
            print("Speaker playback started")
        except Exception as e:
            print(f"Warning: Could not start playback: {e}")

        # Give time for audio pipelines to initialize
        import time
        time.sleep(1)
        print("Audio pipelines ready")

        # Create SSL context with certifi certificates
        try:
            import certifi
            ssl_context = ssl.create_default_context(cafile=certifi.where())
        except ImportError:
            ssl_context = ssl.create_default_context()

        # Create HTTP client with custom SSL
        try:
            import certifi
            http_client = httpx.AsyncClient(verify=certifi.where())
        except ImportError:
            http_client = httpx.AsyncClient()

        client = AsyncOpenAI(api_key=self.api_key, http_client=http_client)
        self._is_running = True
        self._stop_event.clear()

        try:
            async with client.realtime.connect(model="gpt-realtime-mini-2025-12-15") as conn:
                self._connection = conn

                # Configure session (matching conversation app format)
                await conn.session.update(
                    session={
                        "type": "realtime",
                        "instructions": DJ_SYSTEM_PROMPT,
                        "audio": {
                            "input": {
                                "format": {
                                    "type": "audio/pcm",
                                    "rate": OPENAI_SAMPLE_RATE,
                                },
                                "transcription": {"model": "gpt-4o-transcribe", "language": "en"},
                                "turn_detection": {
                                    "type": "server_vad",
                                    "threshold": 0.5,
                                    "prefix_padding_ms": 150,
                                    "silence_duration_ms": 200,  # Very fast end-of-speech detection
                                    "interrupt_response": True,
                                },
                            },
                            "output": {
                                "format": {
                                    "type": "audio/pcm",
                                    "rate": OPENAI_SAMPLE_RATE,
                                },
                                "voice": "shimmer",
                            },
                        },
                        "tools": DJ_TOOLS,
                        "tool_choice": "auto",
                    }
                )

                print("Voice DJ ready!")
                print("Press Ctrl+C to stop\n")

                # Have DJ greet the user first
                print("[Init] Sending greeting prompt...")
                await conn.conversation.item.create(
                    item={
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "Say hi in 5 words or less and ask what to play."}]
                    }
                )
                print("[Init] Creating response...")
                await conn.response.create()
                print("[Init] Response requested, waiting for audio...")

                # Run audio capture and event processing concurrently
                await asyncio.gather(
                    self._capture_audio_loop(),
                    self._process_events_loop(),
                )

        except asyncio.CancelledError:
            print("\nVoice DJ session cancelled")
        except Exception as e:
            logger.error(f"Voice DJ error: {e}")
            raise
        finally:
            self._connection = None
            self._is_running = False

    async def stop(self):
        """Stop the voice DJ session."""
        self._stop_event.set()
        self._is_running = False

        # Stop any playing music
        if self.tool_handler.dance_controller:
            self.tool_handler.dance_controller.stop()

    async def _capture_audio_loop(self):
        """Capture microphone audio from Mac's default mic and send to OpenAI."""
        import queue
        import time

        # Use system default microphone
        self._input_sample_rate = OPENAI_SAMPLE_RATE  # Record at 24kHz directly
        chunk_size = 480  # 20ms chunks at 24kHz
        MAX_QUEUE_SIZE = 25  # ~500ms buffer - drop older audio if queue fills up

        audio_queue = queue.Queue(maxsize=MAX_QUEUE_SIZE * 2)

        def audio_callback(indata, frames, time_info, status):
            """Callback for sounddevice input stream."""
            # Drop oldest chunks if queue is getting full (prevents overflow)
            while audio_queue.qsize() > MAX_QUEUE_SIZE:
                try:
                    audio_queue.get_nowait()
                except queue.Empty:
                    break
            try:
                audio_queue.put_nowait(indata.copy())
            except queue.Full:
                pass  # Drop this chunk if queue is full

        print(f"[Audio] Using Mac's default microphone at {self._input_sample_rate}Hz")

        try:
            # Open input stream using system default mic
            stream = sd.InputStream(
                samplerate=self._input_sample_rate,
                channels=1,
                dtype=np.float32,
                blocksize=chunk_size,
                callback=audio_callback,
            )
            stream.start()
            print("[Audio] Microphone stream started")

            send_count = 0
            last_send_time = time.monotonic()

            # Speech detection state
            peak_level = 0.0
            last_loud_time = 0.0
            speech_active = False
            audio_sent_since_speech = False  # Track if we actually sent audio
            SPEECH_THRESHOLD = 0.08  # Level that indicates speech
            SILENCE_TIMEOUT = 0.4    # Seconds of quiet before committing buffer

            while not self._stop_event.is_set() and self._connection:
                await asyncio.sleep(0.02)  # 50 iterations/sec

                # Reset state when DJ starts speaking
                if self._is_speaking:
                    speech_active = False
                    audio_sent_since_speech = False
                    peak_level = 0.0
                    # Drain the queue while DJ speaks
                    while not audio_queue.empty():
                        try:
                            audio_queue.get_nowait()
                        except queue.Empty:
                            break
                    continue

                try:
                    audio_sample = audio_queue.get_nowait()
                except queue.Empty:
                    # Check if we should commit buffer due to silence
                    now = time.monotonic()
                    # Don't commit if DJ just finished speaking (echo prevention)
                    echo_cooldown = 1.5  # seconds after DJ speaks before we accept input
                    if (now - self._last_dj_speech_end) < echo_cooldown:
                        continue
                    if speech_active and audio_sent_since_speech and (now - last_loud_time > SILENCE_TIMEOUT):
                        print(f"[Audio] Speech ended (peak={peak_level:.3f}), committing & requesting response")
                        try:
                            await self._connection.input_audio_buffer.commit()
                            await self._connection.response.create()
                        except Exception as e:
                            if "empty" not in str(e).lower():
                                print(f"[Audio] Commit error: {e}")
                        speech_active = False
                        audio_sent_since_speech = False
                        peak_level = 0.0
                    continue

                # Convert to mono
                if len(audio_sample.shape) > 1:
                    audio_sample = audio_sample[:, 0]

                audio_level = np.abs(audio_sample).max()
                now = time.monotonic()

                # Track speech activity based on audio level
                if audio_level > SPEECH_THRESHOLD:
                    if audio_level > peak_level:
                        peak_level = audio_level
                    last_loud_time = now
                    speech_active = True
                elif speech_active and audio_sent_since_speech and (now - last_loud_time > SILENCE_TIMEOUT):
                    # Don't commit if DJ just finished speaking (echo prevention)
                    if (now - self._last_dj_speech_end) < 1.5:
                        speech_active = False
                        audio_sent_since_speech = False
                        peak_level = 0.0
                        continue
                    # User stopped speaking - commit buffer and request response
                    print(f"[Audio] Speech ended (peak={peak_level:.3f}), committing & requesting response")
                    try:
                        await self._connection.input_audio_buffer.commit()
                        await self._connection.response.create()
                    except Exception as e:
                        if "empty" not in str(e).lower():
                            print(f"[Audio] Commit error: {e}")
                    speech_active = False
                    audio_sent_since_speech = False
                    peak_level = 0.0
                    continue

                # Echo prevention - don't send audio right after DJ spoke
                if (now - self._last_dj_speech_end) < 1.0:
                    continue

                # Only send audio above noise floor
                noise_threshold = 0.10 if self._music_playing else 0.03
                if audio_level < noise_threshold:
                    continue

                # Rate limit - send at real-time pace
                if now - last_send_time < 0.02:
                    continue
                last_send_time = now

                send_count += 1
                audio_sent_since_speech = True
                if send_count % 50 == 1:
                    print(f"[Audio] Sent {send_count}, level: {audio_level:.3f}")

                audio_int16 = (audio_sample * 32767).astype(np.int16)
                audio_b64 = base64.b64encode(audio_int16.tobytes()).decode()
                try:
                    await self._connection.input_audio_buffer.append(audio=audio_b64)
                except:
                    pass  # Ignore overflow errors

            stream.stop()
            stream.close()

        except Exception as e:
            print(f"[Audio] Failed to open microphone: {e}")
            print("[Audio] Make sure Terminal has microphone permission in System Settings")

    async def _process_events_loop(self):
        """Process events from OpenAI Realtime API."""
        print("[Events] Starting event processing loop...")
        event_count = 0
        while not self._stop_event.is_set() and self._connection:
            try:
                async for event in self._connection:
                    if self._stop_event.is_set():
                        break

                    event_count += 1
                    event_type = getattr(event, 'type', 'unknown')

                    # Log VAD events specially
                    if event_type == 'input_audio_buffer.speech_started':
                        print(f"\n[VAD] >>> Speech started! Say your command...")
                    elif event_type == 'input_audio_buffer.speech_stopped':
                        print(f"[VAD] <<< Speech stopped, processing...")
                    elif event_type in ('response.output_audio.delta', 'response.audio.delta'):
                        pass  # Don't spam audio delta logs
                    else:
                        print(f"[Events] #{event_count}: {event_type}")

                    await self._handle_event(event)

            except Exception as e:
                if not self._stop_event.is_set():
                    print(f"[Events] Error: {e}")
                break

    async def _handle_event(self, event: Any):
        """Handle a single event from OpenAI."""
        event_type = getattr(event, 'type', None)

        if event_type == "response.output_audio.delta":
            # Play audio response - mute mic while speaking
            if not self._is_speaking:
                self._is_speaking = True
                # Clear OpenAI's input buffer to prevent echo
                try:
                    await self._connection.input_audio_buffer.clear()
                except:
                    pass
            delta = getattr(event, 'delta', '')
            if delta:
                await self._play_audio_delta(delta)

        elif event_type == "response.output_audio.done":
            # Audio output finished - wait for echo to fade before unmuting
            await asyncio.sleep(0.8)  # Longer delay for echo to dissipate
            # Clear any audio that accumulated during speech
            try:
                await self._connection.input_audio_buffer.clear()
            except:
                pass
            self._is_speaking = False
            import time
            self._last_dj_speech_end = time.monotonic()

        elif event_type == "response.output_audio_transcript.done":
            # Log what the DJ said
            transcript = getattr(event, 'transcript', '')
            if transcript:
                print(f"DJ Reachy: {transcript}")

        elif event_type == "response.text.delta":
            # Text response (if any)
            text = getattr(event, 'delta', '')
            if text:
                print(f"[Text] {text}", end='', flush=True)

        elif event_type == "response.text.done":
            print()  # Newline after text

        elif event_type == "response.done":
            # Check response status
            response = getattr(event, 'response', {})
            status = getattr(response, 'status', 'unknown')
            print(f"[Response] Done, status: {status}")
            # Check for failure reason
            if status == "failed":
                status_details = getattr(response, 'status_details', None)
                print(f"[Response] Failure details: {status_details}")
                # Try to get error info
                error = getattr(status_details, 'error', None) if status_details else None
                if error:
                    print(f"[Response] Error: {error}")
            # Check for output
            output = getattr(response, 'output', [])
            if output:
                print(f"[Response] Output items: {len(output)}")
                for item in output:
                    item_type = getattr(item, 'type', 'unknown')
                    print(f"[Response] - Item type: {item_type}")

            # Execute any pending tool calls now that audio has finished
            if self._pending_tool_calls:
                # Small delay for audio buffer to finish playing
                await asyncio.sleep(0.2)
                await self._execute_pending_tools()

        elif event_type == "conversation.item.input_audio_transcription.completed":
            # Log what user said
            transcript = getattr(event, 'transcript', '')
            if transcript:
                print(f"You: {transcript}")

        elif event_type == "response.function_call_arguments.done":
            tool_name = getattr(event, 'name', '')
            call_id = getattr(event, 'call_id', '')
            arguments_str = getattr(event, 'arguments', '{}')

            # Tools that should wait for DJ's voice to finish (actions that interrupt)
            wait_for_audio = {"stop_music", "pause_music", "resume_music"}

            if tool_name in wait_for_audio:
                # Queue - will execute after audio finishes (in response.done)
                self._pending_tool_calls.append((tool_name, call_id, arguments_str))
                print(f"[Tool Queued] {tool_name}")
            else:
                # Execute immediately for play_song, play_genre, etc. (user wants fast response)
                print(f"[Tool Immediate] {tool_name}")
                asyncio.create_task(self._execute_tool_now(tool_name, call_id, arguments_str))

        elif event_type == "error":
            error_msg = getattr(event, 'error', {})
            print(f"[ERROR] {error_msg}")

        elif event_type == "response.output_item.added":
            # Log when output items are added
            item = getattr(event, 'item', {})
            item_type = getattr(item, 'type', 'unknown')
            print(f"[Response] Output item added: {item_type}")

        elif event_type == "response.content_part.added":
            # Log content parts
            part = getattr(event, 'part', {})
            part_type = getattr(part, 'type', 'unknown')
            print(f"[Response] Content part added: {part_type}")

    async def _play_audio_delta(self, delta_b64: str):
        """Play an audio delta on the robot speaker."""
        try:
            # Decode audio
            audio_bytes = base64.b64decode(delta_b64)
            audio_int16 = np.frombuffer(audio_bytes, dtype=np.int16)

            # Get output sample rate
            try:
                self._output_sample_rate = self.mini.media.get_output_audio_samplerate()
            except:
                self._output_sample_rate = 16000

            # Resample from 24kHz to robot's sample rate
            if OPENAI_SAMPLE_RATE != self._output_sample_rate:
                num_samples = int(len(audio_int16) * self._output_sample_rate / OPENAI_SAMPLE_RATE)
                audio_int16 = resample(audio_int16, num_samples).astype(np.int16)

            # Convert to float32 for robot
            audio_float = audio_int16.astype(np.float32) / 32767.0

            # Push to robot speaker
            self.mini.media.push_audio_sample(audio_float)

        except Exception as e:
            logger.debug(f"Audio playback error: {e}")

    async def _execute_tool_now(self, tool_name: str, call_id: str, arguments_str: str):
        """Execute a single tool immediately (for play_song, etc.)."""
        try:
            arguments = json.loads(arguments_str)
        except:
            arguments = {}

        print(f"[Tool Executing] {tool_name}: {arguments}")

        # Execute tool
        result = await self.tool_handler.handle_tool_call(tool_name, arguments)

        # Send result back to OpenAI
        await self._connection.conversation.item.create(
            item={
                "type": "function_call_output",
                "call_id": call_id,
                "output": json.dumps(result),
            }
        )

        # Request follow-up response
        await self._connection.response.create()

    async def _execute_pending_tools(self):
        """Execute all pending tool calls after audio has finished."""
        if not self._pending_tool_calls:
            return

        for tool_name, call_id, arguments_str in self._pending_tool_calls:
            try:
                arguments = json.loads(arguments_str)
            except:
                arguments = {}

            print(f"[Tool Executing] {tool_name}: {arguments}")

            # Execute tool
            result = await self.tool_handler.handle_tool_call(tool_name, arguments)

            # Send result back to OpenAI
            await self._connection.conversation.item.create(
                item={
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(result),
                }
            )

        # Clear pending tools
        self._pending_tool_calls = []

        # Request a response after all tools executed
        await self._connection.response.create()


async def run_voice_dj(mini: ReachyMini):
    """
    Run the voice-controlled DJ.

    Args:
        mini: ReachyMini instance
    """
    voice_dj = VoiceDJ(mini)

    try:
        await voice_dj.start()
    except KeyboardInterrupt:
        print("\nStopping Voice DJ...")
    finally:
        await voice_dj.stop()
