"""
🎭 Reachy Mini Self-Introduction Demo (Refactored)

Uses the shared `utils` package for TTS, Vision, and Moves.
"""

import asyncio
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

# Import from our new utils package
from utils.tts import speak
from utils.vision import analyze_scene
from utils.moves import happy_wiggle, nod, scan_room, showstopper_finish

# Load .env file
load_dotenv()

async def intro_sequence(mini: ReachyMini):
    """The main introduction sequence using refactored utils."""
    
    print("\n🎭 Starting Reachy Mini Self-Introduction (Refactored)...\n")
    
    # --- Opening ---
    print("👋 Waking up...")
    await speak("Oh! Hello there!", mini)
    mini.goto_target(head=create_head_pose(z=5, degrees=True, mm=True), duration=0.6)
    await asyncio.sleep(0.3)
    
    # --- Intro ---
    print("🎤 Introducing myself...")
    await speak("I'm Reachy Mini, running on the new shared utilities library!", mini)
    await happy_wiggle(mini)
    
    # --- Vision ---
    print("📷 Using vision utility...")
    await speak("Let me take a quick look around.", mini)
    await scan_room(mini)
    
    frame = mini.media.get_frame()
    if frame is not None:
        print("🤖 Analyzing scene...")
        description = analyze_scene(frame)
        print(f"   Vision: {description}")
        await speak(description, mini)
    else:
        await speak("My camera is shy today.", mini)

    # --- Finale ---
    print("🎉 Finale...")
    await speak("And now, the grand finale!", mini)
    await showstopper_finish(mini)
    
    await speak("Thanks for watching! Now check out the talk show script.", mini)
    print("\n✅ Introduction complete!\n")


async def main():
    print("\n🤖 Connecting to Reachy Mini...")
    with ReachyMini() as mini:
        print("✅ Connected!\n")
        await intro_sequence(mini)

if __name__ == "__main__":
    asyncio.run(main())
