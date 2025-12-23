"""
Hardware Test Script for Reachy Mini
Full demo with speech, movements, and sound.
"""

import asyncio
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np
import time
from dotenv import load_dotenv

# Load .env file for API keys
load_dotenv()

# Import utils
from utils.tts import speak

async def run_tests(mini: ReachyMini):
    """Run all hardware tests with narration."""
    print("🤖 Connected to Reachy Mini!")
    await asyncio.sleep(0.5)

    # --- Test 1: Antennas ---
    print("\n🐜 Test 1: Wiggling antennas...")
    mini.goto_target(antennas=[0.5, -0.5], duration=0.4)
    await asyncio.sleep(0.4)
    mini.goto_target(antennas=[-0.5, 0.5], duration=0.4)
    await asyncio.sleep(0.4)
    mini.goto_target(antennas=[0, 0], duration=0.4)
    await asyncio.sleep(0.4)

    # --- Test 2: Head movement ---
    print("🗣️ Test 2: Moving head (look up, down, tilt)...")
    await speak("Watch this! I can move my head in all directions.", mini)
    
    # Look up
    mini.goto_target(head=create_head_pose(z=15, degrees=True, mm=True), duration=0.6)
    await asyncio.sleep(0.6)
    # Look down
    mini.goto_target(head=create_head_pose(z=-15, degrees=True, mm=True), duration=0.6)
    await asyncio.sleep(0.6)
    # Tilt right
    mini.goto_target(head=create_head_pose(roll=20, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.5)
    # Tilt left
    mini.goto_target(head=create_head_pose(roll=-20, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.5)
    # Back to center
    mini.goto_target(head=create_head_pose(z=0, roll=0, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.5)
    
    await speak("Pretty cool, right?", mini)
    mini.goto_target(antennas=[0.4, -0.4], duration=0.3)
    await asyncio.sleep(0.3)

    # --- Test 3: Antennas with narration ---
    print("🐜 Test 3: Demonstrating antennas...")
    await speak("And check out my antennas! They show how I'm feeling.", mini)
    
    # Happy wiggle
    for _ in range(3):
        mini.goto_target(antennas=[0.6, -0.6], duration=0.15)
        await asyncio.sleep(0.15)
        mini.goto_target(antennas=[-0.6, 0.6], duration=0.15)
        await asyncio.sleep(0.15)
    mini.goto_target(antennas=[0, 0], duration=0.3)
    await asyncio.sleep(0.3)
    
    await speak("When I'm excited, they wiggle like crazy!", mini)

    # --- Test 4: Body/Torso rotation ---
    print("💃 Test 4: Rotating torso...")
    await speak("I can also spin my whole body around.", mini)
    
    mini.goto_target(body_yaw=np.deg2rad(25), duration=0.6)   # Turn right
    await asyncio.sleep(0.6)
    mini.goto_target(body_yaw=np.deg2rad(-25), duration=0.6)  # Turn left
    await asyncio.sleep(0.6)
    mini.goto_target(body_yaw=0, duration=0.5)                # Back to center
    await asyncio.sleep(0.5)
    
    await speak("It helps me look around and find interesting things!", mini)

    # --- Test 5: Vision ---
    print("📷 Test 5: Using vision...")
    await speak("Speaking of looking around... let me see what's in front of me.", mini)
    
    # Look forward attentively
    mini.goto_target(
        head=create_head_pose(z=5, degrees=True, mm=True),
        antennas=[0.2, 0.2],
        duration=0.5
    )
    await asyncio.sleep(0.5)
    
    # Capture and describe
    frame = mini.media.get_frame()
    if frame is not None:
        print("🤖 Analyzing scene...")
        try:
            from utils.vision import analyze_scene
            description = analyze_scene(frame, prompt="You are Reachy Mini, a cute expressive robot. Describe what you see in 1-2 short, enthusiastic sentences. Be playful and curious!")
            print(f"   Vision: {description}")
            
            # React while describing
            mini.goto_target(
                head=create_head_pose(roll=8, degrees=True, mm=True),
                antennas=[0.3, -0.1],
                duration=0.4
            )
            await asyncio.sleep(0.4)
            await speak(description, mini)
            
        except Exception as e:
            print(f"   ⚠️ Vision error: {e}")
            await speak("Hmm, I'm having trouble seeing clearly right now.", mini)
    else:
        await speak("Oops! My camera seems to be taking a nap.", mini)

    # --- Test 6: Sound ---
    print("🔊 Test 6: Playing sound...")
    try:
        mini.media.play_sound("wake_up.wav")
        await asyncio.sleep(1)  # Wait for sound to finish
    except Exception as e:
        print(f"   ⚠️  Sound test skipped: {e}")

    # --- Finale: Professional Dance Showcase! ---
    print("🎉 Finale: Professional dance showcase!")
    await speak("And now, for my signature move!", mini)
    await asyncio.sleep(0.3)
    
    # Use professional dance from the library
    try:
        from reachy_mini_dances_library import DanceMove
        
        def execute_dance(name, bpm):
            """Execute a dance move by streaming positions at 100Hz."""
            move = DanceMove(name)
            move.default_bpm = bpm
            
            frequency = 100
            period = 1.0 / frequency
            duration = move.duration
            start_time = time.time()
            
            while True:
                current_time = time.time()
                t = current_time - start_time
                
                if t >= duration:
                    break
                
                head_pose, antennas, body_yaw = move.evaluate(t)
                mini.set_target(head=head_pose, antennas=antennas, body_yaw=body_yaw)
                
                elapsed = time.time() - current_time
                sleep_time = max(0, period - elapsed)
                time.sleep(sleep_time)
        
        await speak("Watch this dizzy spin!", mini)
        await asyncio.to_thread(execute_dance, "dizzy_spin", 100)
        
        await speak("And a groovy sway to finish!", mini)
        await asyncio.to_thread(execute_dance, "groovy_sway_and_roll", 90)
        
    except Exception as e:
        print(f"   ⚠️ Dance library not available, using simple moves: {e}")
        # Fallback to simple moves
        mini.goto_target(
            head=create_head_pose(z=10, roll=15, degrees=True, mm=True),
            antennas=[0.3, -0.3],
            body_yaw=np.deg2rad(15),
            duration=0.5
        )
        await asyncio.sleep(0.5)
        mini.goto_target(
            head=create_head_pose(z=10, roll=-15, degrees=True, mm=True),
            antennas=[-0.3, 0.3],
            body_yaw=np.deg2rad(-15),
            duration=0.5
        )
        await asyncio.sleep(0.5)
    
    # Reset to neutral
    mini.goto_target(
        head=create_head_pose(z=0, roll=0, degrees=True, mm=True),
        antennas=[0, 0],
        body_yaw=0,
        duration=0.5
    )
    await asyncio.sleep(0.5)
    
    await speak("Ta-da! Thanks for watching. I can't wait to hang out with you!", mini)
    await asyncio.sleep(1.0)

    print("\n✅ All tests complete!")

async def main():
    with ReachyMini() as mini:
        await run_tests(mini)

if __name__ == "__main__":
    asyncio.run(main())
