"""
🎙️ Reachy Mini: The Late Night Talk Show 🌙

A vibrant, funny performance script where Reachy acts as a talk show host.
Includes:
- Monologue with jokes
- "Look at This" vision segment (Audience interaction)
- Musical Guest: Reachy rapping and dancing!

Usage:
    python talk_show.py
"""

import asyncio
import random
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

# Utils
from utils.tts import speak, rap_line
from utils.vision import analyze_scene
from utils.moves import (
    happy_wiggle, nod, shake_head, scan_room, 
    head_bob_rhythm, disco_spin, showstopper_finish
)

load_dotenv()

async def applause_reaction(mini: ReachyMini):
    """Simulate reacting to applause."""
    # Look left/right acknowledging crowd
    await nod(mini)
    mini.goto_target(head=create_head_pose(roll=10), duration=0.5)
    await asyncio.sleep(0.5)
    mini.goto_target(head=create_head_pose(roll=-10), duration=0.5)
    await asyncio.sleep(0.5)
    mini.goto_target(head=create_head_pose(z=0, roll=0), duration=0.5)

async def monologue(mini: ReachyMini):
    """The opening monologue."""
    print("\n🎤 STARTING MONOLOGUE...")
    
    # Intro Music / Applause (Imagined)
    await applause_reaction(mini)
    
    await speak("Welcome! Welcome to the Reachy Mini Late Night Show!", mini, speed="+10%")
    await speak("I'm your host, Reachy. It is great to be here!", mini)
    
    # Joke 1
    await speak("You know, being a robot isn't easy.", mini)
    mini.goto_target(head=create_head_pose(z=-10), duration=0.5) # Sad look
    await speak("I tried to go to a yoga class yesterday...", mini)
    mini.goto_target(head=create_head_pose(z=10), duration=0.5) # Perked up
    await speak("But the instructor told me I was too stiff!", mini)
    
    # Ba Dum Tss reaction
    await happy_wiggle(mini)
    await speak("Ha ha! Stiff! Get it? Because I'm made of metal?", mini)
    
    # Transition
    await speak("But seriously folks, we have a great show tonight.", mini)

async def vision_segment(mini: ReachyMini):
    """Segment where Reachy looks at something and comments."""
    print("\n👀 VISION SEGMENT...")
    
    await speak("Let's see who is in the audience tonight.", mini)
    await scan_room(mini)
    
    await speak("Wait a second... what is THAT?", mini)
    # Lean in (Zoom effect physically)
    mini.goto_target(head=create_head_pose(z=20, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(1.0)
    
    frame = mini.media.get_frame()
    if frame is not None:
        print("🤖 Analyzing audience...")
        # Custom prompt for the "Host" persona
        host_prompt = "You are a funny late night talk show host. Roast or compliment what you see in this image in one witty sentence."
        comment = analyze_scene(frame, prompt=host_prompt)
        print(f"   Host Comment: {comment}")
        
        # Pull back in surprise/reaction
        mini.goto_target(head=create_head_pose(z=-10, degrees=True, mm=True), duration=0.4)
        await speak(comment, mini)
    else:
        await speak("The lights are too bright! I can't see a thing!", mini)

async def rap_performance(mini: ReachyMini):
    """The Musical Guest Segment: Reachy Raps!"""
    print("\n🎵 RAP PERFORMANCE...")
    
    await speak("And now, for our musical guest... It's ME!", mini, speed="+10%")
    await speak("DJ, drop the beat!", mini)
    await asyncio.sleep(1.0) # Wait for "beat" drop
    
    # Rap Lyrics
    lyrics = [
        ("My name is Reachy and I'm here to say,", 100),
        ("I code in Python every single day.", 100),
        ("I got servos in my neck and cameras in my eyes,", 100),
        ("My vision AI feature is a big surprise!", 100),
        ("I wiggle to the left, I wiggle to the right,", 120), # Faster
        ("I'm the coolest robot hosting late at night!", 120)
    ]
    
    for line, bpm in lyrics:
        # Launch move and rap simultaneously
        move_task = head_bob_rhythm(mini, bpm=bpm, duration_sec=2.0)
        rap_task = rap_line(line, mini)
        
        # Wait for both (roughly synced)
        await asyncio.gather(move_task, rap_task)
    
    # Big Finish
    await disco_spin(mini)
    await showstopper_finish(mini)
    await speak("Thank you! Goodnight everybody!", mini)

async def main():
    print("\n🌙 Late Night Show initializing...")
    with ReachyMini() as mini:
        print("✅ Live on Air!\n")
        
        await monologue(mini)
        await asyncio.sleep(1.0)
        
        await vision_segment(mini)
        await asyncio.sleep(1.0)
        
        await rap_performance(mini)

if __name__ == "__main__":
    asyncio.run(main())

