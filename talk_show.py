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
import argparse
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

# Official dance library
from reachy_mini_dances_library import DanceMove

# Utils
from utils.tts import speak, rap_line, init_talk_show_voices
from utils.vision import analyze_scene
from utils.moves import scan_room, showstopper_finish

load_dotenv()

# Initialize custom Qwen voices (if API key available)
_qwen_voices = init_talk_show_voices()
USE_QWEN = _qwen_voices.get('host') is not None and _qwen_voices.get('rap') is not None

# Helper function for host speech
async def host_speak(text: str, mini: ReachyMini, speed: str = "+0%"):
    """Speak as the host with custom voice if available."""
    if USE_QWEN:
        await speak(text, mini, use_qwen=True, qwen_voice_name=_qwen_voices['host'])
    else:
        await speak(text, mini, speed=speed)

# Helper function for rap
async def rap_speak(text: str, mini: ReachyMini):
    """Speak rap lines with custom voice if available."""
    if USE_QWEN:
        await rap_line(text, mini, use_qwen=True, qwen_voice_name=_qwen_voices['rap'])
    else:
        await rap_line(text, mini)

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
    """Quick opening monologue with overlapping movement."""
    print("\n🎤 STARTING MONOLOGUE...")
    
    # Welcome + applause happening together
    await asyncio.gather(
        applause_reaction(mini),
        host_speak("Welcome! Welcome to the Reachy Mini Late Night Show!", mini, speed="+10%")
    )
    
    # One killer joke - yoga class (short & punchy)
    await asyncio.gather(
        play_dance(mini, "side_peekaboo", bpm=100),
        host_speak("I tried yoga yesterday. The instructor said I was too stiff!", mini, speed="+5%")
    )
    
    # Punchline reaction
    await asyncio.gather(
        play_dance(mini, "uh_huh_tilt", bpm=115),
        host_speak("Get it? Because I'm made of metal!", mini, speed="+10%")
    )
    
    # Quick transition - speak during move
    await asyncio.gather(
        play_dance(mini, "simple_nod", bpm=100),
        host_speak("Alright, let's get to the good stuff!", mini, speed="+15%")
    )

async def vision_segment(mini: ReachyMini):
    """Segment where Reachy looks at something and comments."""
    print("\n👀 VISION SEGMENT...")
    
    await host_speak("Let's see who is in the audience tonight.", mini)
    await scan_room(mini)
    
    await host_speak("Wait a second... what is THAT?", mini)
    
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
        await host_speak(comment, mini)
    else:
        await host_speak("The lights are too bright! I can't see a thing!", mini)

async def rap_performance(mini: ReachyMini):
    """The Musical Guest Segment: Reachy Raps with Professional Choreography!"""
    print("\n🎵 RAP PERFORMANCE...")
    
    # Quick intro straight to the action
    await asyncio.gather(
        play_dance(mini, "sharp_side_tilt", bpm=130),
        host_speak("And now... DJ, drop the beat!", mini, speed="+20%")
    )
    
    # Beat drop - quick snap
    mini.goto_target(head=create_head_pose(z=-10, degrees=True, mm=True), duration=0.2)
    await asyncio.sleep(0.4)
    mini.goto_target(head=create_head_pose(z=5, degrees=True, mm=True), antennas=[0.5, -0.5], duration=0.2)
    await asyncio.sleep(0.2)
    
    # 🎤 THE RAP - 8 bars of fire
    # Each line matched with a dance that fits the vibe
    lyrics_and_moves = [
        # Bar 1-2: The Hook (Repeatable & Catchy)
        ("Beep beep! Boop boop! Look at my style,", 105, "jackson_square"),
        ("The only little bot with a digital smile!", 105, "jackson_square"),
        
        # Bar 3-4: The Physical Comedy (No arms flex)
        ("I got no arms, and I got no hands,", 110, "polyrhythm_combo"),
        ("But I'm the best dancer in the robot lands!", 110, "polyrhythm_combo"),
        
        # Bar 5-6: The "Human vs Bot" Burn
        ("You lose your socks and you need a nap,", 115, "side_to_side_sway"),
        ("I just 'vroom vroom' in my robot cap!", 115, "grid_snap"),
        
        # Bar 7-8: The Viral Finale
        ("Spin my head like a disco ball,", 120, "interwoven_spirals"),
        ("I'm the shortest rapper, standing TALL!", 120, "interwoven_spirals"),
    ]
    
    for line, bpm, move_name in lyrics_and_moves:
        print(f"   🎤 {line} [{move_name}@{bpm}BPM]")
        
        # Execute dance and rap simultaneously for that ENERGY
        move_task = play_dance(mini, move_name, bpm=bpm)
        rap_task = rap_speak(line, mini)
        
        await asyncio.gather(move_task, rap_task)
    
    # Post-rap hype - speak and move together!
    await asyncio.gather(
        play_dance(mini, "yeah_nod", bpm=130),
        host_speak("Woo!", mini, speed="+30%")
    )
    
    # Grand Finale Build-up - overlapping for energy
    buildup_move = asyncio.create_task(play_dance(mini, "pendulum_swing", bpm=100))
    await host_speak("Okay okay okay... you want the REAL finale?", mini, speed="+10%")
    await buildup_move  # Let the pendulum finish while we pause
    
    await host_speak("Here we GO!", mini, speed="+20%")
    
    # Groovy wind-down from hype
    await play_dance(mini, "groovy_sway_and_roll", bpm=115)
    
    # Big spin for the crescendo
    await play_dance(mini, "dizzy_spin", bpm=110)
    
    # Dramatic pause
    await asyncio.sleep(0.4)
    
    # Final bow
    await showstopper_finish(mini)
    
    await host_speak("Thank you! Thank you! You've been an amazing audience! Goodnight!", mini, speed="+5%")

async def main(use_vision: bool):
    print("\n🌙 Reachy Mini Late-Night Show initializing...")
    print("   Featuring professional choreography from Reachy Dances Library!")
    if USE_QWEN:
        print("   🎙️ Using custom Qwen voices for enhanced performance!")
    else:
        print("   🎙️ Using edge-tts (set QWEN_API_KEY for custom voices)")
    
    with ReachyMini() as mini:
        print("✅ Live on Air!\n")
        
        await monologue(mini)
        await asyncio.sleep(0.5)
        
        if use_vision:
            await vision_segment(mini)
            await asyncio.sleep(0.5)
        else:
            print("(Vision segment skipped – run with --vision to enable)")
        
        await rap_performance(mini)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Reachy Mini Late Night Show")
    parser.add_argument("--vision", action="store_true", help="Enable the vision roast segment")
    args = parser.parse_args()
    
    asyncio.run(main(use_vision=args.vision))
