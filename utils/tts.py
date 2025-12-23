import asyncio
import tempfile
import os
import edge_tts
from reachy_mini import ReachyMini

# Microsoft Edge voices
VOICE = "en-US-GuyNeural"  # Friendly male
RAP_VOICE = "en-US-SteffanNeural"  # More energetic

async def speak(text: str, mini: ReachyMini, voice: str = VOICE, speed: str = "+0%") -> None:
    """
    Generate speech with edge-tts and play it.
    
    Args:
        text: The text to speak
        mini: ReachyMini instance
        voice: Voice ID to use
        speed: Speed adjustment (e.g. "+0%", "+20%")
    """
    communicate = edge_tts.Communicate(text, voice, rate=speed)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = f.name
    
    await communicate.save(temp_path)
    
    # Convert mp3 to wav
    wav_path = temp_path.replace(".mp3", ".wav")
    os.system(f"ffmpeg -i {temp_path} -ar 44100 -ac 1 {wav_path} -y -loglevel quiet")
    
    if os.path.exists(wav_path):
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
        os.unlink(wav_path)
    
    os.unlink(temp_path)

async def rap_line(text: str, mini: ReachyMini) -> None:
    """Speak a line with faster rhythm for rapping."""
    await speak(text, mini, voice=RAP_VOICE, speed="+20%")

