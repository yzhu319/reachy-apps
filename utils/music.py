"""
YouTube music download and playback utilities for Dance Party DJ.

Uses yt-dlp for downloading audio from YouTube and converts to WAV for robot playback.
"""

import subprocess
import os
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import yt_dlp

# Cache directory for downloaded audio
_cache_dir = Path(__file__).parent.parent / "audio_cache"
_cache_dir.mkdir(exist_ok=True)


def search_youtube(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search YouTube for videos matching query.

    Args:
        query: Search query (song name, artist, etc.)
        max_results: Maximum number of results to return

    Returns:
        List of dicts with keys: title, url, duration, video_id
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': 'in_playlist',
        'skip_download': True,
    }

    # Use explicit ytsearch format
    search_query = f'ytsearch{max_results}:{query}'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            results = ydl.extract_info(search_query, download=False)
            entries = results.get('entries', []) if results else []

            return [
                {
                    'title': e.get('title', 'Unknown'),
                    'url': f"https://youtube.com/watch?v={e.get('id')}",
                    'duration': e.get('duration'),
                    'video_id': e.get('id'),
                }
                for e in entries if e and e.get('id')
            ]
    except Exception as e:
        print(f"YouTube search error: {e}")
        return []


def get_cached_audio(video_id: str) -> Optional[Path]:
    """
    Check if audio is already cached.

    Args:
        video_id: YouTube video ID

    Returns:
        Path to cached WAV file, or None if not cached
    """
    mono_path = _cache_dir / f"{video_id}_mono.wav"
    if mono_path.exists():
        return mono_path
    return None


def download_audio(url: str, output_dir: Optional[Path] = None) -> Tuple[Path, Dict]:
    """
    Download audio from YouTube URL.

    Uses yt-dlp to download best audio, then converts to mono WAV at 44100Hz
    for robot speaker playback.

    Args:
        url: YouTube URL or video ID
        output_dir: Where to save files (default: audio_cache/)

    Returns:
        Tuple of (wav_path, metadata_dict)
        metadata_dict has keys: title, duration, video_id
    """
    if output_dir is None:
        output_dir = _cache_dir
    output_dir.mkdir(exist_ok=True)

    # Extract video ID from URL
    video_id = None
    if 'watch?v=' in url:
        video_id = url.split('watch?v=')[1].split('&')[0]
    elif 'youtu.be/' in url:
        video_id = url.split('youtu.be/')[1].split('?')[0]

    # Check cache first
    if video_id:
        cached = get_cached_audio(video_id)
        if cached:
            print(f"Using cached audio: {cached.name}")
            # Get duration from cached file
            import soundfile as sf
            data, sr = sf.read(cached)
            duration = len(data) / sr
            return cached, {
                'title': 'Cached',
                'duration': duration,
                'video_id': video_id,
            }

    # Download options
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': str(output_dir / '%(id)s.%(ext)s'),
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            print("Downloading audio...")
            info = ydl.extract_info(url, download=True)
            video_id = info.get('id')
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)

            # Find the downloaded WAV file
            wav_path = output_dir / f"{video_id}.wav"

            if not wav_path.exists():
                # yt-dlp might have used a different extension, search for it
                for ext in ['.wav', '.webm', '.m4a', '.mp3']:
                    potential_path = output_dir / f"{video_id}{ext}"
                    if potential_path.exists():
                        wav_path = potential_path
                        break

            # Convert to mono 44100Hz WAV for robot playback
            mono_path = output_dir / f"{video_id}_mono.wav"
            if not mono_path.exists():
                print("Converting to mono 44100Hz WAV...")
                result = subprocess.run([
                    'ffmpeg', '-i', str(wav_path),
                    '-ar', '44100',  # Sample rate
                    '-ac', '1',       # Mono
                    '-y',             # Overwrite
                    '-loglevel', 'quiet',
                    str(mono_path)
                ], capture_output=True)

                if result.returncode != 0:
                    # Fallback: use original file
                    print(f"FFmpeg conversion warning, using original file")
                    mono_path = wav_path

            # Clean up original if we have mono version
            if mono_path != wav_path and mono_path.exists() and wav_path.exists():
                try:
                    wav_path.unlink()
                except:
                    pass

            return mono_path, {
                'title': title,
                'duration': duration,
                'video_id': video_id,
            }

    except Exception as e:
        raise RuntimeError(f"Failed to download audio: {e}")


def get_audio_duration(wav_path: Path) -> float:
    """
    Get duration of a WAV file in seconds.

    Args:
        wav_path: Path to WAV file

    Returns:
        Duration in seconds
    """
    import soundfile as sf
    data, sr = sf.read(wav_path)
    return len(data) / sr


async def play_audio_on_robot(mini, wav_path: Path) -> float:
    """
    Play WAV file on robot speaker.

    Args:
        mini: ReachyMini instance
        wav_path: Path to WAV file

    Returns:
        Duration in seconds
    """
    duration = get_audio_duration(wav_path)
    mini.media.play_sound(str(wav_path))
    return duration


def clear_cache():
    """Remove all cached audio files."""
    for file in _cache_dir.glob("*.wav"):
        try:
            file.unlink()
            print(f"Removed: {file.name}")
        except Exception as e:
            print(f"Failed to remove {file.name}: {e}")


def list_cached_songs() -> List[Dict]:
    """
    List all cached songs.

    Returns:
        List of dicts with video_id and path
    """
    songs = []
    for file in _cache_dir.glob("*_mono.wav"):
        video_id = file.stem.replace("_mono", "")
        songs.append({
            'video_id': video_id,
            'path': file,
            'size_mb': file.stat().st_size / (1024 * 1024),
        })
    return songs
