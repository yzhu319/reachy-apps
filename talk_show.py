"""
🎙️ Reachy Mini: The Late Night Talk Show 🌙 (Enhanced Edition)

A vibrant, funny performance script featuring professional dance moves!
Includes:
- Monologue with jokes and expressive moves
- "Look at This" vision segment (Audience interaction)
- Musical Guest: Reachy rapping with choreographed dances!

Usage:
    python talk_show.py
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

# Official dance library
from reachy_mini_dances_library import DanceMove

# Utils
from utils.tts import speak, rap_line
from utils.vision import analyze_scene
from utils.moves import scan_room, showstopper_finish

load_dotenv()

# Executor for running blocking robot moves
executor = ThreadPoolExecutor()

def execute_dance_move(mini: ReachyMini, move_name: str, bpm: int = None):
    """Manually execute a dance move by streaming positions at 100Hz."""
    import time
    
    move = DanceMove(move_name)
    if bpm:
        move.default_bpm = bpm
    
    # Run at 100Hz
    frequency = 100
    period = 1.0 / frequency
    duration = move.duration
    start_time = time.time()
    
    while True:
        current_time = time.time()
        t = current_time - start_time
        
        if t >= duration:
            break
        
        # Get target positions from the dance move
        head_pose, antennas, body_yaw = move.evaluate(t)
        
        # Send to robot (set_target streams positions smoothly)
        mini.set_target(
            head=head_pose,
            antennas=antennas,
            body_yaw=body_yaw
        )
        
        # Sleep to maintain frequency
        elapsed = time.time() - current_time
        sleep_time = max(0, period - elapsed)
        time.sleep(sleep_time)

async def play_dance(mini: ReachyMini, move_name: str, bpm: int = None):
    """Run a blocking dance move in a separate thread."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(executor, execute_dance_move, mini, move_name, bpm)

async def applause_reaction(mini: ReachyMini):
    """Acknowledge the crowd with enthusiasm."""
    print("   👏 Acknowledging applause...")
    await play_dance(mini, "yeah_nod", bpm=100)

async def monologue(mini: ReachyMini):
    """The opening monologue with expressive moves."""
    print("\n🎤 STARTING MONOLOGUE...")
    
    # Intro Music / Applause
    await applause_reaction(mini)
    
    await speak("Welcome! Welcome to the Reachy Mini Late Night Show!", mini, speed="+10%")
    
    # Playful reveal
    await play_dance(mini, "side_peekaboo", bpm=90)
    
    await speak("I'm your host, Reachy. It is great to be here!", mini)
    
    # Joke 1
    await speak("You know, being a robot isn't easy.", mini)
    mini.goto_target(head=create_head_pose(z=-10), duration=0.5)  # Sad look
    await asyncio.sleep(0.5)
    
    await speak("I tried to go to a yoga class yesterday...", mini)
    mini.goto_target(head=create_head_pose(z=10), duration=0.5)  # Perked up
    await asyncio.sleep(0.5)
    
    await speak("But the instructor told me I was too stiff!", mini)
    
    # Ba Dum Tss reaction - comedic timing
    await play_dance(mini, "uh_huh_tilt", bpm=110)
    
    await speak("Ha ha! Stiff! Get it? Because I'm made of metal?", mini)
    
    # Transition
    await speak("But seriously folks, we have a great show tonight.", mini)

async def vision_segment(mini: ReachyMini):
    """Segment where Reachy looks at something and comments."""
    print("\n👀 VISION SEGMENT...")
    
    await speak("Let's see who is in the audience tonight.", mini)
    await scan_room(mini)
    
    await speak("Wait a second... what is THAT?", mini)
    
    # Quick glance with style
    await play_dance(mini, "side_glance_flick", bpm=120)
    
    # Lean in to investigate
    await play_dance(mini, "chin_lead", bpm=80)
    
    frame = mini.media.get_frame()
    if frame is not None:
        print("🤖 Analyzing audience...")
        # Custom prompt for the "Host" persona
        host_prompt = "You are a funny late night talk show host. Roast or compliment what you see in this image in one witty sentence."
        comment = analyze_scene(frame, prompt=host_prompt)
        print(f"   Host Comment: {comment}")
        
        # Pull back in surprise/reaction
        mini.goto_target(head=create_head_pose(z=-10, degrees=True, mm=True), duration=0.4)
        await asyncio.sleep(0.4)
        await speak(comment, mini)
    else:
        await speak("The lights are too bright! I can't see a thing!", mini)

async def rap_performance(mini: ReachyMini):
    """The Musical Guest Segment: Reachy Raps with Professional Choreography!"""
    print("\n🎵 RAP PERFORMANCE...")
    
    await speak("And now, for our musical guest... It's ME!", mini, speed="+10%")
    await speak("DJ, drop the beat!", mini)
    await asyncio.sleep(1.0)  # Beat drop
    
    # Rap Lyrics with matched choreography
    lyrics_and_moves = [
        ("My name is Reachy and I'm here to say,", 100, "jackson_square"),
        ("I code in Python every single day.", 100, "jackson_square"),
        ("I got servos in my neck and cameras in my eyes,", 110, "polyrhythm_combo"),
        ("My vision AI feature is a big surprise!", 110, "polyrhythm_combo"),
        ("I wiggle to the left, I wiggle to the right,", 120, "headbanger_combo"),
        ("I'm the coolest robot hosting late at night!", 120, "headbanger_combo")
    ]
    
    for line, bpm, move_name in lyrics_and_moves:
        print(f"   🎤 {line} [{move_name}]")
        
        # Execute dance (in thread) and rap (async) simultaneously
        move_task = play_dance(mini, move_name, bpm=bpm)
        rap_task = rap_line(line, mini)
        
        # Wait for both
        await asyncio.gather(move_task, rap_task)
    
    # Grand Finale Build-up
    await speak("Here comes the finale!", mini)
    
    # Groovy finish
    await play_dance(mini, "groovy_sway_and_roll", bpm=110)
    
    # Dizzy spin spectacular
    await play_dance(mini, "dizzy_spin", bpm=100)
    
    # Custom showstopper
    await showstopper_finish(mini)
    
    await speak("Thank you! Goodnight everybody!", mini)

async def main():
    print("\n🌙 Late Night Show (Enhanced Edition) initializing...")
    print("   Featuring professional choreography from Reachy Dances Library!")
    
    with ReachyMini() as mini:
        print("✅ Live on Air!\n")
        
        await monologue(mini)
        await asyncio.sleep(1.0)
        
        await vision_segment(mini)
        await asyncio.sleep(1.0)
        
        await rap_performance(mini)

if __name__ == "__main__":
    asyncio.run(main())
