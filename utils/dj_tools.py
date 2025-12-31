"""
DJ Tool definitions for OpenAI Realtime API.

These tools allow the voice-controlled DJ to play songs, stop music,
change dance styles, and handle genre requests.
"""

from typing import Any, Dict, List

# Tool schemas for OpenAI Realtime API
DJ_TOOLS: List[Dict[str, Any]] = [
    {
        "type": "function",
        "name": "play_song",
        "description": "Search for and play a song from YouTube. The robot will dance to the beat.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Song name, artist, or search query (e.g., 'Uptown Funk', 'Taylor Swift Shake It Off', 'happy music')"
                }
            },
            "required": ["query"]
        }
    },
    {
        "type": "function",
        "name": "stop_music",
        "description": "Stop the currently playing music and dancing.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "type": "function",
        "name": "change_dance_energy",
        "description": "Change the robot's dance energy level.",
        "parameters": {
            "type": "object",
            "properties": {
                "energy": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "crazy"],
                    "description": "The energy level for dancing"
                }
            },
            "required": ["energy"]
        }
    },
    {
        "type": "function",
        "name": "play_genre",
        "description": "Play a popular song from a specific music genre.",
        "parameters": {
            "type": "object",
            "properties": {
                "genre": {
                    "type": "string",
                    "enum": ["pop", "rock", "hip-hop", "edm", "jazz", "disco", "80s", "90s", "kids", "latin"],
                    "description": "The music genre to play"
                }
            },
            "required": ["genre"]
        }
    },
    {
        "type": "function",
        "name": "get_current_song",
        "description": "Get information about the currently playing song.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "type": "function",
        "name": "pause_music",
        "description": "Pause the current music and dancing. Music can be resumed later.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "type": "function",
        "name": "resume_music",
        "description": "Resume playing the paused music and dancing.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
]

# Genre to search query mapping for variety
GENRE_QUERIES: Dict[str, List[str]] = {
    "pop": [
        "top pop hits 2024",
        "best pop dance songs",
        "upbeat pop music",
    ],
    "rock": [
        "classic rock greatest hits",
        "rock anthems",
        "upbeat rock songs",
    ],
    "hip-hop": [
        "hip hop dance hits",
        "best rap songs to dance to",
        "hip hop party music",
    ],
    "edm": [
        "edm dance music",
        "electronic dance hits",
        "best EDM drops",
    ],
    "jazz": [
        "upbeat jazz music",
        "jazz dance songs",
        "swing jazz classics",
    ],
    "disco": [
        "disco dance classics",
        "70s disco hits",
        "best disco songs",
    ],
    "80s": [
        "80s dance hits",
        "best 80s pop songs",
        "80s party music",
    ],
    "90s": [
        "90s dance party",
        "best 90s hits",
        "90s pop classics",
    ],
    "kids": [
        "kids dance songs",
        "children party music",
        "fun songs for kids",
    ],
    "latin": [
        "latin dance music",
        "reggaeton hits",
        "salsa dance songs",
    ],
}

# Energy level multipliers
ENERGY_LEVELS: Dict[str, float] = {
    "low": 0.6,
    "medium": 1.0,
    "high": 1.4,
    "crazy": 1.8,
}


class DJToolHandler:
    """
    Handles tool calls from OpenAI Realtime API.

    Manages the dance controller and music playback state.
    """

    def __init__(self, mini, dance_controller=None, on_music_state_change=None):
        """
        Initialize the tool handler.

        Args:
            mini: ReachyMini instance
            dance_controller: Optional BeatSyncDancer instance
            on_music_state_change: Callback(is_playing: bool) when music starts/stops
        """
        self.mini = mini
        self.dance_controller = dance_controller
        self._current_song: Dict[str, Any] = {}
        self._is_playing: bool = False
        self._is_paused: bool = False
        self._on_music_state_change = on_music_state_change

    def _notify_music_state(self, is_playing: bool):
        """Notify listener about music state change."""
        if self._on_music_state_change:
            self._on_music_state_change(is_playing)

    def set_dance_controller(self, controller):
        """Set the dance controller (can be updated after init)."""
        self.dance_controller = controller

    async def handle_tool_call(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Dispatch tool call to appropriate handler.

        Args:
            tool_name: Name of the tool to call
            args: Arguments for the tool

        Returns:
            Result dictionary
        """
        handlers = {
            "play_song": self._play_song,
            "stop_music": self._stop_music,
            "pause_music": self._pause_music,
            "resume_music": self._resume_music,
            "change_dance_energy": self._change_energy,
            "play_genre": self._play_genre,
            "get_current_song": self._get_current_song,
        }

        handler = handlers.get(tool_name)
        if handler is None:
            return {"error": f"Unknown tool: {tool_name}"}

        try:
            return await handler(args)
        except Exception as e:
            return {"error": str(e)}

    async def _play_song(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Play a song matching the query."""
        import asyncio
        from utils.music import search_youtube, download_audio, get_audio_duration
        from utils.beat_detection import analyze_beats
        from utils.beat_sync_dancer import BeatSyncDancer
        import time

        query = args.get("query", "")
        if not query:
            return {"error": "No song query provided"}

        # Stop current playback if any
        if self._is_playing:
            await self._stop_music({})

        # Search YouTube
        results = search_youtube(query, max_results=1)
        if not results:
            return {"error": "No songs found", "query": query}

        song = results[0]

        # Download audio
        try:
            wav_path, metadata = download_audio(song['url'])
        except Exception as e:
            return {"error": f"Download failed: {e}"}

        # Analyze beats
        try:
            beat_info = analyze_beats(wav_path)
        except Exception as e:
            # Use default BPM
            from utils.beat_detection import BeatInfo
            import numpy as np
            beat_info = BeatInfo(
                bpm=120.0,
                beat_times=np.array([]),
                downbeat_times=np.array([]),
                onset_envelope=np.array([]),
                onset_times=np.array([]),
            )

        # Update current song info
        self._current_song = {
            "title": song['title'],
            "bpm": beat_info.bpm,
            "duration": metadata.get('duration', 0),
            "video_id": song.get('video_id'),
        }

        # Get audio duration first
        duration = get_audio_duration(wav_path)

        # Create and start dancer with actual song duration
        dancer = BeatSyncDancer(self.mini)
        self.dance_controller = dancer

        playback_start = time.monotonic()
        dancer.start(beat_info, playback_start, song_duration=duration)
        self.mini.media.play_sound(str(wav_path))
        self._is_playing = True
        self._notify_music_state(True)

        # Schedule stop after song ends
        async def auto_stop():
            await asyncio.sleep(duration)
            if self._is_playing:
                dancer.stop()
                self._is_playing = False
                self._notify_music_state(False)

        asyncio.create_task(auto_stop())

        return {
            "status": "playing",
            "title": song['title'],
            "bpm": round(beat_info.bpm),
            "duration": round(duration),
        }

    async def _stop_music(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Stop current playback completely."""
        if self.dance_controller:
            self.dance_controller.stop()
            self.dance_controller = None

        # Clear audio buffer to stop music immediately
        try:
            self.mini.media.audio.clear_output_buffer()
        except:
            pass

        self._is_playing = False
        self._is_paused = False
        self._current_song = {}
        self._notify_music_state(False)

        return {"status": "stopped", "message": "Music and dancing stopped"}

    async def _change_energy(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Change dance energy level."""
        energy = args.get("energy", "medium")
        multiplier = ENERGY_LEVELS.get(energy, 1.0)

        if self.dance_controller:
            self.dance_controller.set_energy(multiplier)

        return {"status": "energy_changed", "energy": energy, "multiplier": multiplier}

    async def _play_genre(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Play a song from a specific genre."""
        import random

        genre = args.get("genre", "pop")
        queries = GENRE_QUERIES.get(genre, GENRE_QUERIES["pop"])
        query = random.choice(queries)

        return await self._play_song({"query": query})

    async def _pause_music(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Pause current playback - both dancing and music."""
        if self.dance_controller and self._is_playing:
            # Pause dancing
            self.dance_controller.pause()
            # Stop music by clearing the audio buffer
            try:
                self.mini.media.audio.clear_output_buffer()
            except:
                pass
            self._is_paused = True
            self._notify_music_state(False)  # Music paused
            return {"status": "paused", "message": "Dancing and music paused"}
        return {"status": "nothing_to_pause"}

    async def _resume_music(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Resume paused playback - both dancing and music."""
        if self.dance_controller and self._is_playing and getattr(self, '_is_paused', False):
            # Resume dancing
            self.dance_controller.resume()
            # Note: Can't resume music from where it was - would need to restart song
            self._is_paused = False
            self._notify_music_state(True)  # Music resumed
            return {"status": "resumed", "message": "Dancing resumed (music continues from buffer if any remains)"}
        return {"status": "nothing_to_resume"}

    async def _get_current_song(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Get info about current song."""
        if not self._is_playing or not self._current_song:
            return {"status": "not_playing"}

        return {
            "status": "playing",
            **self._current_song
        }
