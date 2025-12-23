import asyncio
import tempfile
import os
import edge_tts
from reachy_mini import ReachyMini

# Microsoft Edge voices
VOICE = "en-US-GuyNeural"  # Friendly male
RAP_VOICE = "en-US-SteffanNeural"  # More energetic

async def speak(text: str, mini: ReachyMini, voice: str = VOICE, speed: str = "+0%", max_retries: int = 3) -> None:
    """
    Generate speech with edge-tts and play it.
    
    Args:
        text: The text to speak
        mini: ReachyMini instance
        voice: Voice ID to use
        speed: Speed adjustment (e.g. "+0%", "+20%")
        max_retries: Maximum retry attempts on network failure
    """
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

async def rap_line(text: str, mini: ReachyMini) -> None:
    """Speak a line with faster rhythm for rapping."""
    await speak(text, mini, voice=RAP_VOICE, speed="+20%")

