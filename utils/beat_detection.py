"""
Beat detection and tempo analysis for Dance Party DJ.

Uses librosa for robust beat tracking and BPM estimation.
"""

import random
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import numpy as np
import librosa


@dataclass
class BeatInfo:
    """Beat analysis results."""
    bpm: float                      # Tempo in beats per minute
    beat_times: np.ndarray          # Array of beat timestamps (seconds)
    downbeat_times: np.ndarray      # Stronger beats (measure starts, every 4th)
    onset_envelope: np.ndarray      # Onset strength over time
    onset_times: np.ndarray         # Time values for onset_envelope


def analyze_beats(
    wav_path: Path,
    start_sec: float = 0,
    duration_sec: Optional[float] = None
) -> BeatInfo:
    """
    Analyze audio file for beats and tempo.

    Uses librosa for robust beat tracking:
    - Computes onset strength envelope
    - Estimates tempo via autocorrelation
    - Tracks beat positions

    Args:
        wav_path: Path to WAV file
        start_sec: Start position for analysis
        duration_sec: Duration to analyze (None = entire file)

    Returns:
        BeatInfo with tempo and beat positions
    """
    # Load audio (librosa handles resampling to 22050Hz)
    y, sr = librosa.load(
        wav_path,
        sr=22050,
        offset=start_sec,
        duration=duration_sec
    )

    # Get onset envelope (~43Hz resolution)
    hop_length = 512  # ~23ms at 22050Hz
    onset_env = librosa.onset.onset_strength(
        y=y,
        sr=sr,
        hop_length=hop_length
    )
    onset_times = librosa.times_like(onset_env, sr=sr, hop_length=hop_length)

    # Estimate tempo and beat positions
    tempo, beat_frames = librosa.beat.beat_track(
        y=y,
        sr=sr,
        hop_length=hop_length,
        onset_envelope=onset_env
    )

    # Handle tempo being an array (newer librosa versions)
    if isinstance(tempo, np.ndarray):
        tempo = float(tempo[0]) if len(tempo) > 0 else 120.0

    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop_length)

    # Estimate downbeats (every 4th beat for 4/4 time)
    if len(beat_frames) >= 4:
        downbeat_frames = beat_frames[::4]
    else:
        downbeat_frames = beat_frames
    downbeat_times = librosa.frames_to_time(downbeat_frames, sr=sr, hop_length=hop_length)

    # Adjust times for start offset
    beat_times = beat_times + start_sec
    downbeat_times = downbeat_times + start_sec
    onset_times = onset_times + start_sec

    return BeatInfo(
        bpm=float(tempo),
        beat_times=beat_times,
        downbeat_times=downbeat_times,
        onset_envelope=onset_env,
        onset_times=onset_times,
    )


def get_bpm_category(bpm: float) -> str:
    """
    Categorize BPM for dance move selection.

    Args:
        bpm: Beats per minute

    Returns:
        'slow' (<90), 'medium' (90-120), 'fast' (>120)
    """
    if bpm < 90:
        return 'slow'
    elif bpm <= 120:
        return 'medium'
    else:
        return 'fast'


# Dance moves mapped to BPM categories
# These are from reachy_mini_dances_library
DANCE_BPM_MAP = {
    'slow': [
        'groovy_sway_and_roll',
        'pendulum_swing',
        'side_to_side_sway',
        'chin_lead',
    ],
    'medium': [
        'jackson_square',
        'polyrhythm_combo',
        'yeah_nod',
        'uh_huh_tilt',
        'simple_nod',
        'head_tilt_roll',
    ],
    'fast': [
        'grid_snap',
        'dizzy_spin',
        'sharp_side_tilt',
        'interwoven_spirals',
        'chicken_peck',
        'side_glance_flick',
    ],
}

# All available moves (flat list)
ALL_DANCE_MOVES = [move for moves in DANCE_BPM_MAP.values() for move in moves]


def select_dance_for_bpm(bpm: float, exclude: Optional[List[str]] = None) -> str:
    """
    Select an appropriate dance move for the given BPM.

    Args:
        bpm: Beats per minute
        exclude: List of move names to exclude (for variety)

    Returns:
        Name of a dance move suitable for the tempo
    """
    category = get_bpm_category(bpm)
    available = DANCE_BPM_MAP[category].copy()

    # Remove excluded moves
    if exclude:
        available = [m for m in available if m not in exclude]

    # Fallback if all filtered out
    if not available:
        available = DANCE_BPM_MAP[category].copy()

    return random.choice(available)


def get_beat_at_time(beat_info: BeatInfo, time_sec: float) -> Optional[int]:
    """
    Get the beat index at a given time.

    Args:
        beat_info: BeatInfo from analyze_beats()
        time_sec: Time in seconds

    Returns:
        Beat index (0-based), or None if before first beat
    """
    if len(beat_info.beat_times) == 0:
        return None

    # Find the beat at or before this time
    idx = np.searchsorted(beat_info.beat_times, time_sec, side='right') - 1
    if idx < 0:
        return None
    return int(idx)


def is_downbeat(beat_info: BeatInfo, beat_index: int) -> bool:
    """
    Check if a beat index is a downbeat (start of measure).

    Args:
        beat_info: BeatInfo from analyze_beats()
        beat_index: Beat index (0-based)

    Returns:
        True if this is a downbeat (every 4th beat)
    """
    return beat_index % 4 == 0


def estimate_energy_level(onset_envelope: np.ndarray, onset_times: np.ndarray,
                          time_sec: float, window_sec: float = 1.0) -> float:
    """
    Estimate the energy level at a given time.

    Useful for adjusting dance intensity.

    Args:
        onset_envelope: Onset strength array
        onset_times: Time values for onset_envelope
        time_sec: Time to estimate energy at
        window_sec: Window size for averaging

    Returns:
        Energy level (0.0 to 1.0)
    """
    # Find indices within window
    mask = (onset_times >= time_sec - window_sec / 2) & \
           (onset_times <= time_sec + window_sec / 2)

    if not np.any(mask):
        return 0.5  # Default mid-level

    # Average onset strength in window
    energy = np.mean(onset_envelope[mask])

    # Normalize to 0-1 (rough normalization)
    max_energy = np.percentile(onset_envelope, 95)
    if max_energy > 0:
        energy = min(1.0, energy / max_energy)

    return float(energy)
