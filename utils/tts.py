import asyncio
import tempfile
import os
import base64
import struct
import ssl
import edge_tts
import requests
import threading
import time
from reachy_mini import ReachyMini
try:
    import certifi
    import dashscope
    from dashscope.audio.qwen_tts_realtime import QwenTtsRealtime, QwenTtsRealtimeCallback, AudioFormat
    DASHSCOPE_AVAILABLE = True
    # Configure SSL certificates
    try:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
    except:
        # Fallback: create context without certifi if not available
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
except ImportError:
    DASHSCOPE_AVAILABLE = False
    ssl_context = None

# Microsoft Edge voices (fallback)
VOICE = "en-US-GuyNeural"  # Friendly male
RAP_VOICE = "en-US-SteffanNeural"  # More energetic

# Qwen TTS Voice Profiles (created on first use, cached)
_qwen_voices_cache = {}

def create_qwen_voice(voice_prompt: str, preferred_name: str, language: str = "en", preview_text: str = None) -> str:
    """
    Create a custom Qwen voice from a natural language description.
    
    Args:
        voice_prompt: Description of the voice (e.g., "A witty late-night talk show host with 
                     a smooth, energetic voice, perfect for comedy and audience engagement.")
        preferred_name: Name for the voice (e.g., "host_voice")
        language: Language code (default: "en")
        preview_text: Optional preview text to test the voice
        
    Returns:
        Voice name/ID that can be used for synthesis, or None if creation failed
    """
    api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return None
    
    # Check cache first
    cache_key = f"{preferred_name}_{language}"
    if cache_key in _qwen_voices_cache:
        return _qwen_voices_cache[cache_key]
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen-voice-design",
        "input": {
            "action": "create",
            "target_model": "qwen3-tts-vd-realtime-2025-12-16",
            "voice_prompt": voice_prompt,
            "preview_text": preview_text or "Hello, this is a test of the custom voice.",
            "preferred_name": preferred_name,
            "language": language
        },
        "parameters": {
            "sample_rate": 24000,
            "response_format": "wav"
        }
    }
    
    url = "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/tts/customization"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)
        if response.status_code == 200:
            result = response.json()
            voice_name = result["output"]["voice"]
            _qwen_voices_cache[cache_key] = voice_name
            print(f"   ✅ Created Qwen voice '{preferred_name}': {voice_name}")
            return voice_name
        else:
            print(f"   ⚠️ Qwen voice creation failed: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"   ⚠️ Qwen voice creation error: {e}")
        return None

if DASHSCOPE_AVAILABLE:
    class QwenAudioCallback(QwenTtsRealtimeCallback):
        """Callback to collect audio chunks from Qwen TTS WebSocket."""
        def __init__(self, mini: ReachyMini):
            super().__init__()
            self.mini = mini
            self.audio_chunks = []
            self.complete_event = threading.Event()
            self.error_occurred = False
            
        def on_open(self) -> None:
            pass
            
        def on_close(self, close_status_code, close_msg) -> None:
            self.complete_event.set()
            
        def on_event(self, response: dict) -> None:
            try:
                event_type = response.get('type', '')
                if event_type == 'response.audio.delta':
                    # Collect audio chunks
                    audio_data = base64.b64decode(response['delta'])
                    self.audio_chunks.append(audio_data)
                elif event_type == 'response.done':
                    pass
                elif event_type == 'session.finished':
                    self.complete_event.set()
                elif event_type == 'error':
                    print(f"   ⚠️ Qwen WebSocket error: {response.get('message', 'Unknown error')}")
                    self.error_occurred = True
                    self.complete_event.set()
            except Exception as e:
                print(f"   ⚠️ Qwen callback error: {e}")
                self.error_occurred = True
                self.complete_event.set()
        
        def wait_for_finished(self, timeout=30):
            return self.complete_event.wait(timeout)
        
        def get_audio_bytes(self):
            return b''.join(self.audio_chunks)

async def speak_qwen(text: str, mini: ReachyMini, voice_name: str, max_retries: int = 2) -> bool:
    """
    Synthesize speech using Qwen TTS with a custom voice via WebSocket realtime API.
    
    Args:
        text: Text to speak
        mini: ReachyMini instance
        voice_name: Voice name from create_qwen_voice() or use built-in voices
        max_retries: Maximum retry attempts
        
    Returns:
        True if successful, False otherwise (caller should fall back to edge-tts)
    """
    if not DASHSCOPE_AVAILABLE:
        print("   ⚠️ DashScope SDK not installed. Install with: uv add dashscope")
        return False
        
    api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return False
    
    # Configure SSL certificates for WebSocket connection
    # On macOS, Python sometimes can't find certificates. Try certifi first.
    try:
        import certifi
        cert_path = certifi.where()
        # Set environment variables that Python's SSL will use
        os.environ['SSL_CERT_FILE'] = cert_path
        os.environ['REQUESTS_CA_BUNDLE'] = cert_path
    except ImportError:
        # If certifi not available, check if we should disable SSL verification
        # (Only for development - set QWEN_DISABLE_SSL_VERIFY=1 if needed)
        if os.getenv("QWEN_DISABLE_SSL_VERIFY") == "1":
            # This is a workaround for SSL issues - not recommended for production
            import ssl
            ssl._create_default_https_context = ssl._create_unverified_context
    
    dashscope.api_key = api_key
    
    for attempt in range(max_retries):
        try:
            # Create callback to collect audio
            callback = QwenAudioCallback(mini)
            
            # Create realtime TTS client
            qwen_tts = QwenTtsRealtime(
                model="qwen3-tts-vd-realtime-2025-12-16",
                callback=callback,
                url='wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime'
            )
            
            # Connect
            qwen_tts.connect()
            
            # Update session with voice
            qwen_tts.update_session(
                voice=voice_name,
                pitch_rate=1.5,
                volume=100,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode='server_commit'
            )
            
            # Send text
            qwen_tts.append_text(text)
            qwen_tts.finish()
            
            # Wait for completion (with timeout)
            if callback.wait_for_finished(timeout=30):
                if callback.error_occurred:
                    if attempt == max_retries - 1:
                        return False
                    await asyncio.sleep(0.5)
                    continue
                
                # Get collected audio
                audio_bytes = callback.get_audio_bytes()
                if not audio_bytes:
                    if attempt == max_retries - 1:
                        print("   ⚠️ Qwen: No audio received")
                        return False
                    await asyncio.sleep(0.5)
                    continue
                
                # Save to temp file
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    # Convert PCM to WAV format
                    # PCM 24kHz mono 16-bit
                    sample_rate = 24000
                    num_channels = 1
                    bits_per_sample = 16
                    
                    # WAV header
                    wav_header = struct.pack('<4sI4s4sIHHIIHH4sI',
                        b'RIFF',
                        36 + len(audio_bytes),
                        b'WAVE',
                        b'fmt ',
                        16,  # fmt chunk size
                        1,   # audio format (PCM)
                        num_channels,
                        sample_rate,
                        sample_rate * num_channels * (bits_per_sample // 8),
                        num_channels * (bits_per_sample // 8),
                        bits_per_sample,
                        b'data',
                        len(audio_bytes)
                    )
                    f.write(wav_header)
                    f.write(audio_bytes)
                    wav_path = f.name
                
                # Play audio
                mini.media.play_sound(wav_path)
                
                # Estimate duration
                duration = len(text) * 0.08 + 0.5
                await asyncio.sleep(duration)
                
                # Cleanup
                os.unlink(wav_path)
                return True
            else:
                print("   ⚠️ Qwen: Timeout waiting for audio")
                if attempt == max_retries - 1:
                    return False
                await asyncio.sleep(0.5)
                
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"   ⚠️ Qwen TTS error: {e}")
                return False
            await asyncio.sleep(0.5)
    
    return False

async def speak(text: str, mini: ReachyMini, voice: str = VOICE, speed: str = "+0%", max_retries: int = 3, use_qwen: bool = False, qwen_voice_name: str = None) -> None:
    """
    Generate speech with edge-tts (default) or Qwen TTS (if use_qwen=True).
    
    Args:
        text: The text to speak
        mini: ReachyMini instance
        voice: Voice ID to use (for edge-tts)
        speed: Speed adjustment (e.g. "+0%", "+20%") - only for edge-tts
        max_retries: Maximum retry attempts on network failure
        use_qwen: If True, use Qwen TTS instead of edge-tts
        qwen_voice_name: Qwen voice name (required if use_qwen=True)
    """
    # Use Qwen TTS if requested - fall back to edge-tts on failure
    if use_qwen and qwen_voice_name:
        success = await speak_qwen(text, mini, qwen_voice_name, max_retries=2)
        if success:
            return
        # Fall through to edge-tts on failure
        print("   🔄 Falling back to edge-tts...")
    
    # Default: edge-tts
    communicate = edge_tts.Communicate(text, voice, rate=speed)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = f.name
    
    # Retry logic for network timeouts
    for attempt in range(max_retries):
        try:
            await communicate.save(temp_path)
            break  # Success!
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed - print error and continue without speech
                print(f"   ⚠️ TTS failed after {max_retries} attempts: {e}")
                print(f"   Continuing without speech for: '{text[:50]}...'")
                os.unlink(temp_path)
                # Estimate duration and wait anyway so timing stays consistent
                duration = len(text) * 0.08 + 0.5
                await asyncio.sleep(duration)
                return
            else:
                # Wait before retry (exponential backoff)
                wait_time = 2 ** attempt
                print(f"   ⚠️ TTS attempt {attempt + 1} failed, retrying in {wait_time}s...")
                await asyncio.sleep(wait_time)
    
    # Check if file was created successfully
    if not os.path.exists(temp_path):
        return  # Already handled in retry logic above
    
    # Convert mp3 to wav
    wav_path = temp_path.replace(".mp3", ".wav")
    os.system(f"ffmpeg -i {temp_path} -ar 44100 -ac 1 {wav_path} -y -loglevel quiet")
    
    if os.path.exists(wav_path):
        try:
            mini.media.play_sound(wav_path)
            # Estimate duration: ~80ms per character normally
            # Adjust based on speed roughly
            base_char_time = 0.08
            if "+" in speed:
                try:
                    pct = int(speed.replace("+", "").replace("%", ""))
                    base_char_time *= (100 / (100 + pct))
                except:
                    pass
                    
            duration = len(text) * base_char_time + 0.5
            await asyncio.sleep(duration)
        except Exception as e:
            print(f"   ⚠️ Error playing sound: {e}")
        finally:
            # Clean up files
            if os.path.exists(wav_path):
                os.unlink(wav_path)
    
    if os.path.exists(temp_path):
        os.unlink(temp_path)

async def rap_line(text: str, mini: ReachyMini, use_qwen: bool = False, qwen_voice_name: str = None) -> None:
    """Speak a line with faster rhythm for rapping."""
    if use_qwen and qwen_voice_name:
        await speak(text, mini, use_qwen=True, qwen_voice_name=qwen_voice_name)
    else:
        await speak(text, mini, voice=RAP_VOICE, speed="+20%")

def init_talk_show_voices() -> dict:
    """
    Initialize custom Qwen voices for the talk show.
    Returns dict with voice names: {'host': voice_name, 'rap': voice_name}
    Falls back to None if Qwen API not available.
    """
    voices = {}
    
    # Host voice: Witty late-night show host
    host_voice = create_qwen_voice(
        voice_prompt="A witty, energetic late-night talk show host with a smooth, charismatic voice. "
                     "Perfect for comedy, audience engagement, and delivering punchlines with perfect timing. "
                     "Warm but sharp, like Jimmy Kimmel or Seth Meyers.",
        preferred_name="late_night_host",
        language="en",
        preview_text="Welcome to the show! Let's have some fun tonight!"
    )
    voices['host'] = host_voice
    
    # Rap voice: High-energy, rhythmic rapper
    rap_voice = create_qwen_voice(
        voice_prompt="A high-energy, rhythmic rapper with a bold, confident voice. "
                     "Perfect for fast-paced rap verses, hype tracks, and dropping beats. "
                     "Energetic, punchy, and full of swagger.",
        preferred_name="rap_artist",
        language="en",
        preview_text="Beep beep! Boop boop! Look at my style!"
    )
    voices['rap'] = rap_voice
    
    return voices

