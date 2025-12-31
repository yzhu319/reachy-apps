"""
Dance Party DJ - Reachy Mini dances to YouTube music!

Play music from YouTube and watch Reachy Mini dance to the beat.
The robot detects the tempo and selects appropriate dance moves.

Usage:
    python dance_party_dj.py "Uptown Funk"
    python dance_party_dj.py "Happy Pharrell Williams"
    python dance_party_dj.py --url "https://youtube.com/watch?v=..."
    python dance_party_dj.py --voice  # Voice-controlled mode!

Requirements:
    - ffmpeg must be installed (for audio conversion)
    - Internet connection (for YouTube downloads)
    - OPENAI_API_KEY env variable (for voice mode)
"""

# Fix SSL certificates on macOS (must be before other imports)
import os
try:
    import certifi
    os.environ['SSL_CERT_FILE'] = certifi.where()
    os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
except ImportError:
    pass

import asyncio
import argparse
import time
from dotenv import load_dotenv

from reachy_mini import ReachyMini

from utils.music import search_youtube, download_audio, play_audio_on_robot, get_audio_duration
from utils.beat_detection import analyze_beats, get_bpm_category
from utils.beat_sync_dancer import BeatSyncDancer
from utils.tts import speak

load_dotenv()


async def announce_song(mini: ReachyMini, title: str, bpm: float):
    """Announce the song and BPM before dancing."""
    category = get_bpm_category(bpm)

    if category == 'slow':
        mood = "smooth and groovy"
    elif category == 'medium':
        mood = "nice and funky"
    else:
        mood = "fast and energetic"

    announcement = f"Alright! This one's {mood} at {bpm:.0f} beats per minute. Let's dance!"
    print(f"   Announcing: {announcement}")
    await speak(announcement, mini)


async def play_song_with_dancing(
    mini: ReachyMini,
    song_query: str = None,
    song_url: str = None
):
    """
    Main dance party flow:
    1. Search/download song from YouTube
    2. Analyze beats with librosa
    3. Start music playback and dancing simultaneously
    """

    # Step 1: Get the song
    if song_url:
        url = song_url
        print(f"Using URL: {url}")
    else:
        print(f"Searching YouTube for: '{song_query}'")
        await speak(f"Let me find {song_query} for you!", mini)

        results = search_youtube(song_query, max_results=1)
        if not results:
            await speak("Sorry, I couldn't find that song. Try another one!", mini)
            return

        url = results[0]['url']
        title = results[0]['title']
        print(f"Found: {title}")

    # Step 2: Download audio
    print("Downloading audio...")
    try:
        wav_path, metadata = download_audio(url)
        title = metadata.get('title', 'Unknown Song')
        print(f"Downloaded: {title}")
    except Exception as e:
        print(f"Download failed: {e}")
        await speak("Oops! I had trouble downloading that song. Let's try another one!", mini)
        return

    # Step 3: Analyze beats
    print("Analyzing beats...")
    await speak("Analyzing the rhythm...", mini)

    try:
        beat_info = analyze_beats(wav_path)
        print(f"Detected tempo: {beat_info.bpm:.1f} BPM")
        print(f"Found {len(beat_info.beat_times)} beats")
    except Exception as e:
        print(f"Beat analysis failed: {e}")
        # Use default BPM as fallback
        from utils.beat_detection import BeatInfo
        import numpy as np
        beat_info = BeatInfo(
            bpm=120.0,
            beat_times=np.array([]),
            downbeat_times=np.array([]),
            onset_envelope=np.array([]),
            onset_times=np.array([]),
        )
        print("Using default 120 BPM")

    # Step 4: Announce and prepare
    await announce_song(mini, title, beat_info.bpm)

    # Short pause before starting
    await asyncio.sleep(0.5)

    # Step 5: Start dancing and playing simultaneously
    print("\nStarting dance party!")
    print(f"   Song: {title}")
    print(f"   BPM: {beat_info.bpm:.0f}")
    print("   Press Ctrl+C to stop\n")

    # Get song duration first
    song_duration = get_audio_duration(wav_path)

    # Initialize dancer with actual song duration
    dancer = BeatSyncDancer(mini)
    playback_start = time.monotonic()

    # Start dancer (schedules all moves for full song)
    dancer.start(beat_info, playback_start, song_duration=song_duration)

    # Start audio playback
    mini.media.play_sound(str(wav_path))

    # Wait for song to finish
    try:
        await asyncio.sleep(song_duration)
    except asyncio.CancelledError:
        print("\nStopping early...")

    # Stop dancer
    dancer.stop()

    # Finale
    print("\nSong finished!")
    await speak("Wooo! That was fun! Want to dance to another song?", mini)


async def interactive_mode(mini: ReachyMini):
    """Interactive mode - keep asking for songs."""
    await speak("Welcome to Dance Party DJ! What would you like to dance to?", mini)

    while True:
        print("\n" + "=" * 50)
        query = input("Enter song name (or 'quit' to exit): ").strip()

        if query.lower() in ['quit', 'exit', 'q']:
            await speak("Thanks for dancing with me! See you next time!", mini)
            break

        if not query:
            continue

        await play_song_with_dancing(mini, song_query=query)


async def voice_mode(mini: ReachyMini):
    """Voice-controlled DJ mode using OpenAI Realtime API."""
    from utils.voice_dj import run_voice_dj

    print("\n" + "=" * 50)
    print("VOICE MODE - DJ Reachy is listening!")
    print("=" * 50)
    print("\nTry saying:")
    print("  - 'Play Uptown Funk'")
    print("  - 'Play some disco music'")
    print("  - 'Stop the music'")
    print("  - 'Play something from the 80s'")
    print("\nPress Ctrl+C to exit\n")

    await run_voice_dj(mini)


async def main(
    song_query: str = None,
    song_url: str = None,
    interactive: bool = False,
    voice: bool = False
):
    """Main entry point."""
    print("Dance Party DJ initializing...")
    print("=" * 50)

    with ReachyMini() as mini:
        print("Reachy Mini connected!")

        if voice:
            await voice_mode(mini)
        elif interactive:
            await interactive_mode(mini)
        elif song_query or song_url:
            await play_song_with_dancing(mini, song_query, song_url)
        else:
            # Default demo song
            print("No song specified, playing demo...")
            await play_song_with_dancing(mini, song_query="Happy Pharrell Williams")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Dance Party DJ - Reachy Mini dances to YouTube music!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python dance_party_dj.py "Uptown Funk"
    python dance_party_dj.py "Taylor Swift Shake It Off"
    python dance_party_dj.py --url "https://youtube.com/watch?v=..."
    python dance_party_dj.py --interactive
    python dance_party_dj.py --voice   # Voice-controlled DJ mode!
        """
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Song search query (artist, song name, etc.)"
    )
    parser.add_argument(
        "--url",
        help="Direct YouTube URL"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode - keep asking for songs"
    )
    parser.add_argument(
        "--voice", "-v",
        action="store_true",
        help="Voice-controlled mode using OpenAI Realtime API (requires OPENAI_API_KEY)"
    )

    args = parser.parse_args()

    try:
        asyncio.run(main(
            song_query=args.query,
            song_url=args.url,
            interactive=args.interactive,
            voice=args.voice
        ))
    except KeyboardInterrupt:
        print("\n\nDance party ended!")
