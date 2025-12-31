"""
Beat-synchronized dancing for Dance Party DJ.

Provides a 100Hz control loop that executes dance moves synchronized to music beats.
"""

import time
import asyncio
import threading
import random
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Optional, List, Callable

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
from reachy_mini_dances_library import DanceMove

from .beat_detection import BeatInfo, select_dance_for_bpm, get_bpm_category


@dataclass
class ScheduledDance:
    """A dance scheduled to start at a specific time."""
    start_time: float       # Monotonic time to start
    move_name: str          # Name of the dance move
    bpm: float              # BPM to execute at
    duration: float         # Duration in seconds


class BeatSyncDancer:
    """
    Coordinates robot dancing synchronized to music beats.

    Architecture:
    - Main thread schedules dances based on beat analysis
    - Worker thread runs 100Hz control loop executing moves

    Usage:
        dancer = BeatSyncDancer(mini)
        dancer.start(beat_info, playback_start_time)
        # ... wait for song to finish ...
        dancer.stop()
    """

    CONTROL_HZ = 100

    def __init__(self, mini: ReachyMini):
        self.mini = mini
        self._stop_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

        # Dance scheduling
        self._dance_queue: Queue[ScheduledDance] = Queue()
        self._current_dance: Optional[DanceMove] = None
        self._dance_start_time: float = 0
        self._last_move_name: Optional[str] = None

        # Timing
        self._playback_start: float = 0
        self._beat_info: Optional[BeatInfo] = None

        # Energy/style modifiers
        self._energy_multiplier: float = 1.0

    def start(self, beat_info: BeatInfo, playback_start: float):
        """
        Start the dancer synchronized to music.

        Args:
            beat_info: BeatInfo from analyze_beats()
            playback_start: Monotonic time when music playback started
        """
        self._beat_info = beat_info
        self._playback_start = playback_start
        self._stop_event.clear()

        # Schedule dances for the entire song
        self._schedule_dances()

        # Start control loop
        self._worker_thread = threading.Thread(
            target=self._control_loop,
            daemon=True,
            name="BeatSyncDancer"
        )
        self._worker_thread.start()

    def stop(self):
        """Stop dancing and return to neutral position."""
        self._stop_event.set()
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        self._return_to_neutral()

    def set_energy(self, multiplier: float):
        """
        Adjust dance energy level.

        Args:
            multiplier: 1.0 = normal, >1.0 = more energetic, <1.0 = calmer
        """
        self._energy_multiplier = max(0.5, min(2.0, multiplier))

    def _schedule_dances(self):
        """Schedule dance moves throughout the song."""
        if self._beat_info is None:
            return

        bpm = self._beat_info.bpm
        beat_interval = 60.0 / bpm
        song_duration = float(self._beat_info.beat_times[-1]) if len(self._beat_info.beat_times) > 0 else 60.0

        current_time = 0.0
        recent_moves: List[str] = []

        while current_time < song_duration:
            # Select a dance move (avoid repeating recent ones)
            move_name = select_dance_for_bpm(bpm, exclude=recent_moves[-3:] if len(recent_moves) >= 3 else None)

            # Get move duration
            try:
                temp_move = DanceMove(move_name)
                temp_move.default_bpm = bpm
                move_duration = temp_move.duration
            except Exception:
                move_duration = 2.0  # Fallback duration

            # Schedule it
            scheduled = ScheduledDance(
                start_time=self._playback_start + current_time,
                move_name=move_name,
                bpm=bpm,
                duration=move_duration,
            )
            self._dance_queue.put(scheduled)

            # Track recent moves for variety
            recent_moves.append(move_name)
            if len(recent_moves) > 5:
                recent_moves.pop(0)

            # Advance time - add small gap between moves
            gap = random.uniform(0.3, 1.0)
            current_time += move_duration + gap

    def _control_loop(self):
        """100Hz control loop - runs in worker thread."""
        period = 1.0 / self.CONTROL_HZ

        while not self._stop_event.is_set():
            loop_start = time.monotonic()

            # Check for new dance events
            if self._current_dance is None:
                self._try_start_next_dance(loop_start)

            # Evaluate current dance
            if self._current_dance is not None:
                elapsed = loop_start - self._dance_start_time

                if elapsed >= self._current_dance.duration:
                    # Dance finished
                    self._current_dance = None
                else:
                    # Apply dance pose
                    self._apply_dance_pose(elapsed)

            # Maintain loop frequency
            elapsed = time.monotonic() - loop_start
            sleep_time = max(0, period - elapsed)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _try_start_next_dance(self, current_time: float):
        """Try to start the next scheduled dance."""
        try:
            scheduled = self._dance_queue.get_nowait()

            # Check if it's time to start
            if current_time >= scheduled.start_time:
                self._start_dance(scheduled)
            else:
                # Not time yet, put it back
                # (In practice, with good scheduling this rarely happens)
                self._dance_queue.put(scheduled)
        except Empty:
            pass

    def _start_dance(self, scheduled: ScheduledDance):
        """Initialize a new dance move."""
        try:
            self._current_dance = DanceMove(scheduled.move_name)
            self._current_dance.default_bpm = scheduled.bpm
            self._dance_start_time = time.monotonic()
            self._last_move_name = scheduled.move_name
        except Exception as e:
            print(f"Failed to start dance {scheduled.move_name}: {e}")
            self._current_dance = None

    def _apply_dance_pose(self, t: float):
        """Apply current dance pose to robot."""
        if self._current_dance is None:
            return

        try:
            head_pose, antennas, body_yaw = self._current_dance.evaluate(t)

            # Apply energy modifier (scale movements)
            if self._energy_multiplier != 1.0:
                # Scale translation components of head pose
                head_pose[0:3, 3] *= self._energy_multiplier
                # Scale antenna movements
                antennas = (
                    antennas[0] * self._energy_multiplier,
                    antennas[1] * self._energy_multiplier
                )
                # Scale body yaw
                body_yaw *= self._energy_multiplier

            self.mini.set_target(
                head=head_pose,
                antennas=antennas,
                body_yaw=body_yaw
            )
        except Exception as e:
            # Don't crash the control loop on errors
            pass

    def _return_to_neutral(self):
        """Return robot to neutral position."""
        try:
            neutral = create_head_pose(0, 0, 0, 0, 0, 0, degrees=True)
            self.mini.goto_target(
                head=neutral,
                antennas=[0, 0],
                body_yaw=0,
                duration=1.0
            )
        except Exception as e:
            print(f"Failed to return to neutral: {e}")


async def run_dance_party(
    mini: ReachyMini,
    beat_info: BeatInfo,
    song_duration: float,
    on_beat_callback: Optional[Callable[[int], None]] = None
) -> BeatSyncDancer:
    """
    Start a dance party that runs for the duration of a song.

    Args:
        mini: ReachyMini instance
        beat_info: BeatInfo from analyze_beats()
        song_duration: Duration of the song in seconds
        on_beat_callback: Optional callback called on each beat with beat index

    Returns:
        BeatSyncDancer instance (call .stop() when song ends)
    """
    dancer = BeatSyncDancer(mini)
    playback_start = time.monotonic()
    dancer.start(beat_info, playback_start)

    return dancer


def get_dance_for_mood(mood: str, bpm: float) -> str:
    """
    Select a dance based on mood and tempo.

    Args:
        mood: 'happy', 'chill', 'energetic', 'silly'
        bpm: Beats per minute

    Returns:
        Name of an appropriate dance move
    """
    mood_preferences = {
        'happy': ['yeah_nod', 'uh_huh_tilt', 'jackson_square', 'groovy_sway_and_roll'],
        'chill': ['pendulum_swing', 'side_to_side_sway', 'chin_lead', 'simple_nod'],
        'energetic': ['dizzy_spin', 'grid_snap', 'sharp_side_tilt', 'interwoven_spirals'],
        'silly': ['chicken_peck', 'side_peekaboo', 'dizzy_spin', 'stumble_and_recover'],
    }

    # Get mood-appropriate dances
    preferred = mood_preferences.get(mood, mood_preferences['happy'])

    # Filter by BPM category
    category = get_bpm_category(bpm)
    from .beat_detection import DANCE_BPM_MAP
    bpm_appropriate = DANCE_BPM_MAP[category]

    # Find intersection
    available = [d for d in preferred if d in bpm_appropriate]

    if available:
        return random.choice(available)
    else:
        # Fallback to any BPM-appropriate dance
        return select_dance_for_bpm(bpm)
