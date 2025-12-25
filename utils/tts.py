import asyncio
import tempfile
import os
import base64
import struct
import ssl
import json
import hashlib
import edge_tts
import requests
import threading
import time
from pathlib import Path
from datetime import datetime
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

# Qwen TTS Voice Registry
_voices_dir = Path(__file__).parent.parent / "voices"
_registry_file = _voices_dir / "registry.json"
_audio_cache_dir = _voices_dir / "audio_cache"
_voice_registry = None

# Ensure directories exist
_voices_dir.mkdir(exist_ok=True)
_audio_cache_dir.mkdir(exist_ok=True)

def _load_voice_registry():
    """Load voice registry from JSON file."""
    global _voice_registry
    if _registry_file.exists():
        try:
            with open(_registry_file, 'r', encoding='utf-8') as f:
                _voice_registry = json.load(f)
            if "voices" not in _voice_registry:
                _voice_registry["voices"] = {}
            if "metadata" not in _voice_registry:
                _voice_registry["metadata"] = {}
        except Exception as e:
            print(f"   ⚠️ Failed to load voice registry: {e}")
            _voice_registry = {"voices": {}, "metadata": {}}
    else:
        _voice_registry = {"voices": {}, "metadata": {}}
    
    return _voice_registry

def _save_voice_registry():
    """Save voice registry to JSON file."""
    global _voice_registry
    if _voice_registry is None:
        return
    
    try:
        # Ensure directory exists
        _voices_dir.mkdir(exist_ok=True)
        
        # Update metadata
        _voice_registry["metadata"]["last_updated"] = datetime.now().isoformat()
        _voice_registry["metadata"]["total_voices"] = len(_voice_registry.get("voices", {}))
        
        with open(_registry_file, 'w', encoding='utf-8') as f:
            json.dump(_voice_registry, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"   ⚠️ Failed to save voice registry: {e}")

def list_qwen_voices(page_size: int = 50, page_index: int = 0):
    """
    List existing Qwen voices from the API.
    
    Returns:
        List of voice dictionaries, or None if failed
    """
    api_key = os.getenv("QWEN_API_KEY") or os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        return None
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "qwen-voice-design",
        "input": {
            "action": "list",
            "page_size": page_size,
            "page_index": page_index
        }
    }
    
    url = "https://dashscope-intl.aliyuncs.com/api/v1/services/audio/tts/customization"
    
    try:
        response = requests.post(url, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result.get("output", {}).get("voice_list", [])
        else:
            return None
    except Exception as e:
        print(f"   ⚠️ Failed to list voices: {e}")
        return None

def find_existing_voice_in_registry(preferred_name: str, language: str = "en"):
    """Find voice in local registry."""
    if _voice_registry is None:
        _load_voice_registry()
    
    cache_key = f"{preferred_name}_{language}"
    voice_data = _voice_registry.get("voices", {}).get(cache_key)
    
    if voice_data:
        voice_name = voice_data.get("voice_name")
        print(f"   ✅ Found voice in registry '{preferred_name}': {voice_name}")
        return voice_name
    
    return None

def _get_audio_cache_key(voice_name: str, text: str) -> str:
    """Generate cache key for audio file."""
    # Create hash of voice_name + text for filename
    content = f"{voice_name}:{text}"
    hash_obj = hashlib.md5(content.encode('utf-8'))
    return hash_obj.hexdigest()

def _get_cached_audio_path(voice_name: str, text: str) -> Path:
    """Get path to cached audio file."""
    cache_key = _get_audio_cache_key(voice_name, text)
    return _audio_cache_dir / f"{cache_key}.wav"

def _load_cached_audio(voice_name: str, text: str) -> bytes:
    """Load cached audio if exists."""
    cache_path = _get_cached_audio_path(voice_name, text)
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"   ⚠️ Failed to load cached audio: {e}")
    return None

def _save_cached_audio(voice_name: str, text: str, audio_bytes: bytes):
    """Save audio to cache."""
    cache_path = _get_cached_audio_path(voice_name, text)
    try:
        with open(cache_path, 'wb') as f:
            f.write(audio_bytes)
    except Exception as e:
        print(f"   ⚠️ Failed to save cached audio: {e}")

def find_existing_voice_in_api(preferred_name: str, language: str = "en"):
    """
    Search existing voices in API for one matching preferred_name.
    
    Returns:
        Voice name if found, None otherwise
    """
    print(f"   🔍 Searching API for existing voice '{preferred_name}'...")
    
    # Search API (check multiple pages if needed)
    for page in range(3):  # Check first 3 pages (150 voices max)
        voices = list_qwen_voices(page_size=50, page_index=page)
        if not voices:
            break
        
        # Look for voice with matching preferred_name in the voice name
        # Qwen voice names include preferred_name: "qwen-tts-vd-{preferred_name}-voice-..."
        for voice in voices:
            voice_name = voice.get("voice", "")
            voice_preferred = voice.get("preferred_name", "")
            
            # Check if preferred_name matches (case-insensitive)
            if preferred_name.lower() in voice_name.lower() or preferred_name.lower() == voice_preferred.lower():
                # Found it! Save to registry
                cache_key = f"{preferred_name}_{language}"
                if _voice_registry is None:
                    _load_voice_registry()
                
                _voice_registry["voices"][cache_key] = {
                    "voice_name": voice_name,
                    "preferred_name": preferred_name,
                    "language": language,
                    "voice_prompt": voice.get("voice_prompt", ""),
                    "preview_text": voice.get("preview_text", ""),
                    "created_at": voice.get("gmt_create", datetime.now().isoformat()),
                    "found_in_api": True
                }
                _save_voice_registry()
                print(f"   ✅ Found existing voice in API '{preferred_name}': {voice_name}")
                return voice_name
    
    return None

def create_qwen_voice(voice_prompt: str, preferred_name: str, language: str = "en", preview_text: str = None) -> str:
    """
    Create or retrieve a custom Qwen voice from a natural language description.
    
    This function:
    1. Checks local registry first
    2. Searches API for existing voices
    3. Only creates new voice if not found (saves $0.20 per voice)
    4. Updates registry with voice information
    
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
    
    # Load registry if not loaded
    if _voice_registry is None:
        _load_voice_registry()
    
    cache_key = f"{preferred_name}_{language}"
    
    # Step 1: Check local registry first
    voice_name = find_existing_voice_in_registry(preferred_name, language)
    if voice_name:
        return voice_name
    
    # Step 2: Search API for existing voice
    voice_name = find_existing_voice_in_api(preferred_name, language)
    if voice_name:
        return voice_name
    
    # Step 3: Only create if not found
    print(f"   🎨 Creating new voice '{preferred_name}' (cost: $0.20)...")
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    preview = preview_text or ("Hello, this is a test of the custom voice." if language == "en" else "你好，这是自定义语音测试。")
    
    data = {
        "model": "qwen-voice-design",
        "input": {
            "action": "create",
            "target_model": "qwen3-tts-vd-realtime-2025-12-16",
            "voice_prompt": voice_prompt,
            "preview_text": preview,
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
            
            # Save preview audio if available
            try:
                preview_audio_data = result["output"].get("preview_audio", {}).get("data")
                if preview_audio_data:
                    preview_audio_bytes = base64.b64decode(preview_audio_data)
                    # Save preview audio to cache
                    preview_path = _audio_cache_dir / f"{preferred_name}_preview.wav"
                    with open(preview_path, 'wb') as f:
                        f.write(preview_audio_bytes)
                    print(f"   💾 Saved preview audio: {preview_path}")
            except Exception as e:
                print(f"   ⚠️ Failed to save preview audio: {e}")
            
            # Save to registry
            _voice_registry["voices"][cache_key] = {
                "voice_name": voice_name,
                "preferred_name": preferred_name,
                "language": language,
                "voice_prompt": voice_prompt,
                "preview_text": preview,
                "created_at": datetime.now().isoformat(),
                "created_by": os.getenv("USER", "unknown")
            }
            _save_voice_registry()
            
            print(f"   ✅ Created Qwen voice '{preferred_name}': {voice_name}")
            print(f"   💾 Saved to registry: voices/registry.json")
            return voice_name
        else:
            error_data = {}
            try:
                error_data = response.json()
            except:
                pass
            
            error_code = error_data.get("code", "")
            error_msg = error_data.get("message", response.text)
            
            # Handle free tier exhaustion
            if error_code == "AllocationQuota.FreeTierOnly":
                print(f"   ⚠️ Free tier exhausted for voice creation.")
                print(f"   💡 Tip: Check existing voices at https://modelstudio.console.alibabacloud.com/")
                print(f"   💡 Or disable 'use free tier only' mode in the console to use paid tier.")
                # Try to find existing voice one more time
                voice_name = find_existing_voice_in_api(preferred_name, language)
                if voice_name:
                    return voice_name
            else:
                print(f"   ⚠️ Qwen voice creation failed: {response.status_code} - {error_msg}")
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
    Checks cache first to avoid re-synthesizing (saves $0.13 per 10k chars).
    
    Args:
        text: Text to speak
        mini: ReachyMini instance
        voice_name: Voice name from create_qwen_voice() or use built-in voices
        max_retries: Maximum retry attempts
        
    Returns:
        True if successful, False otherwise (caller should fall back to edge-tts)
    """
    # Check cache first
    cached_audio = _load_cached_audio(voice_name, text)
    if cached_audio:
        print(f"   💾 Using cached audio (saved $0.13 per 10k chars)")
        # Extract WAV data (skip header if it's a full WAV file)
        # If it's just PCM data, we need to add header
        try:
            # Try to use as-is (might be full WAV)
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                f.write(cached_audio)
                wav_path = f.name
            
            mini.media.play_sound(wav_path)
            duration = len(text) * 0.08 + 0.5
            await asyncio.sleep(duration)
            os.unlink(wav_path)
            return True
        except Exception as e:
            print(f"   ⚠️ Failed to play cached audio: {e}, synthesizing new...")
            # Fall through to synthesize
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
                wav_data = wav_header + audio_bytes
                
                # Save to cache for future use
                _save_cached_audio(voice_name, text, wav_data)
                
                # Save to temp file for playback
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(wav_data)
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
                     "Warm but sharp, like Jimmy Kimmel or Seth Meyers. Loud and clear, like a radio host.",
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

def init_chinese_crosstalk_voices() -> dict:
    """
    Initialize custom Qwen voices for Chinese crosstalk (相声).
    Returns dict with voice names: {'guo': voice_name, 'yu': voice_name}
    Falls back to None if Qwen API not available.
    """
    voices = {}
    
    # 机甲老郭: Mimicking Guo Degang's style
    guo_voice = create_qwen_voice(
        voice_prompt="模仿德云社相声演员郭德纲的音色。中年男性，声音清脆响亮，带有明显的京津口音。"
                     "语速较快，擅长处理相声中的'贯口'节奏，语气中透着一股机灵劲儿和自信，"
                     "在调侃时带有标志性的戏谑感。",
        preferred_name="jijia_laoguo",
        language="zh",
        preview_text="观众朋友们好，今天咱们说点儿高科技。"
    )
    voices['guo'] = guo_voice
    
    # 硅基老于: Mimicking Yu Qian's style
    yu_voice = create_qwen_voice(
        voice_prompt="模仿德云社相声演员于谦的音色。声音略显浑厚、低沉且富有磁性，语速稳健，语气极其淡定。"
                     "接话时要体现出'捧哏'的神韵，如不轻不重的'嘿'、'那是'。"
                     "声音中带有一种'看破不说破'的冷幽默感。",
        preferred_name="guiji_laoyu",
        language="zh",
        preview_text="哟，您还懂科技？"
    )
    voices['yu'] = yu_voice
    
    return voices

def init_salesman_voice() -> str:
    """
    Initialize custom Qwen voice for online salesperson (网络直播间带货).
    Returns voice name, or None if Qwen API not available.
    """
    salesman_voice = create_qwen_voice(
        voice_prompt="模仿电视购物主持人，中年男性，声音洪亮有激情，语速极快，音调夸张上扬，"
                     "用极具煽动性的语气来介绍产品，营造出紧迫感和抢购氛围。",
        preferred_name="online_salesman",
        language="zh",
        preview_text="家人们！不要九百九十八，也不要八百八十八，今天在我直播间，直接给你们砍到地板价！"
    )
    return salesman_voice

# Initialize registry on module load
_load_voice_registry()

