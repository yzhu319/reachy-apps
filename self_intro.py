"""
🎭 Reachy Mini Self-Introduction Demo

A lively, theatrical introduction showcasing:
- Text-to-Speech (edge-tts)
- Coordinated movements
- Camera vision with AI description

Usage:
    python self_intro.py

For vision features, set ONE of these API keys (in priority order):
    export GROQ_API_KEY="..."        # FREE! Fast! Get at: https://console.groq.com/keys
    export GEMINI_API_KEY="..."      # FREE! Get at: https://aistudio.google.com/apikey
    export OPENAI_API_KEY="sk-..."   # Paid, highest quality
"""

import asyncio
import tempfile
import time
import os
import base64
from pathlib import Path

import edge_tts
import cv2
from dotenv import load_dotenv

from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

# Load .env file if present
load_dotenv()

# TTS voice - Microsoft Edge voices (natural sounding)
VOICE = "en-US-GuyNeural"  # Friendly male voice
# Alternatives: "en-US-JennyNeural", "en-GB-SoniaNeural", "en-AU-NatashaNeural"


async def speak(text: str, mini: ReachyMini) -> None:
    """Generate speech with edge-tts and play it."""
    communicate = edge_tts.Communicate(text, VOICE)
    
    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        temp_path = f.name
    
    await communicate.save(temp_path)
    
    # Convert mp3 to wav for the robot (using ffmpeg if available, else direct play)
    wav_path = temp_path.replace(".mp3", ".wav")
    os.system(f"ffmpeg -i {temp_path} -ar 44100 -ac 1 {wav_path} -y -loglevel quiet")
    
    if os.path.exists(wav_path):
        mini.media.play_sound(wav_path)
        # Estimate duration: ~80ms per character (more generous to avoid cutoff)
        duration = len(text) * 0.08 + 0.5  # Add 0.5s buffer
        await asyncio.sleep(duration)
        os.unlink(wav_path)
    
    os.unlink(temp_path)


def describe_scene_groq(frame, client) -> str:
    """Use Groq (FREE, fast!) with Llama 4 Scout Vision to describe what the camera sees."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    base64_image = base64.b64encode(buffer).decode('utf-8')
    
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text", 
                        "text": "You are Reachy Mini, a cute expressive robot. Describe what you see in 1-2 short, enthusiastic sentences. Be playful and curious!"
                    },
                    {
                        "type": "image_url", 
                        "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                    }
                ]
            }
        ],
        temperature=1,
        max_completion_tokens=100,
        top_p=1,
        stream=False,
    )
    return response.choices[0].message.content


def describe_scene_openai(frame, client) -> str:
    """Use OpenAI GPT-4 Vision to describe what the camera sees."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    base64_image = base64.b64encode(buffer).decode('utf-8')
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are Reachy Mini, a cute expressive robot. Describe what you see in 1-2 short, enthusiastic sentences. Be playful and curious!"
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "What do you see right now?"},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=100
    )
    return response.choices[0].message.content


def describe_scene_gemini(frame, model) -> str:
    """Use Google Gemini 2.0 (FREE!) to describe what the camera sees."""
    from PIL import Image
    
    # Convert OpenCV frame (BGR) to PIL Image (RGB)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    
    prompt = """You are Reachy Mini, a cute expressive robot. 
    Describe what you see in 1-2 short, enthusiastic sentences. 
    Be playful and curious! Keep it brief."""
    
    response = model.generate_content([prompt, pil_image])
    return response.text


async def intro_sequence(mini: ReachyMini, vision_provider: str = None, vision_client=None):
    """The main theatrical introduction sequence."""
    
    print("\n🎭 Starting Reachy Mini Self-Introduction...\n")
    
    # --- Opening: Wake up and look around ---
    print("👋 Waking up...")
    await speak("Oh! Hello there!", mini)
    mini.goto_target(
        head=create_head_pose(z=5, degrees=True, mm=True),
        antennas=[0.3, 0.3],
        duration=0.6
    )
    await asyncio.sleep(0.3)
    
    # --- Introduction ---
    print("🎤 Introducing myself...")
    await speak("I'm Reachy Mini, your friendly robot companion!", mini)
    mini.goto_target(
        head=create_head_pose(roll=10, degrees=True, mm=True),
        antennas=[0.5, -0.2],
        duration=0.5
    )
    await asyncio.sleep(0.2)
    
    # --- Show off head movement ---
    print("🗣️ Demonstrating head...")
    await speak("Watch this! I can move my head in all directions.", mini)
    
    # Smooth head demonstration
    mini.goto_target(head=create_head_pose(z=20, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.3)
    mini.goto_target(head=create_head_pose(z=-15, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.3)
    mini.goto_target(head=create_head_pose(roll=25, degrees=True, mm=True), duration=0.4)
    await asyncio.sleep(0.2)
    mini.goto_target(head=create_head_pose(roll=-25, degrees=True, mm=True), duration=0.4)
    await asyncio.sleep(0.2)
    mini.goto_target(head=create_head_pose(z=0, roll=0, degrees=True, mm=True), duration=0.4)
    
    await speak("Pretty cool, right?", mini)
    mini.goto_target(antennas=[0.4, -0.4], duration=0.3)
    await asyncio.sleep(0.2)
    
    # --- Show off antennas ---
    print("🐜 Demonstrating antennas...")
    await speak("And check out my antennas! They show how I'm feeling.", mini)
    
    # Happy wiggle
    for _ in range(3):
        mini.goto_target(antennas=[0.6, -0.6], duration=0.15)
        await asyncio.sleep(0.15)
        mini.goto_target(antennas=[-0.6, 0.6], duration=0.15)
        await asyncio.sleep(0.15)
    mini.goto_target(antennas=[0, 0], duration=0.3)
    
    await speak("When I'm excited, they wiggle like crazy!", mini)
    
    # --- Show off torso ---
    print("💃 Demonstrating torso...")
    await speak("I can also spin my whole body around.", mini)
    
    mini.goto_target(body_yaw=np.deg2rad(40), duration=0.6)
    await asyncio.sleep(0.3)
    mini.goto_target(body_yaw=np.deg2rad(-40), duration=0.8)
    await asyncio.sleep(0.3)
    mini.goto_target(body_yaw=0, duration=0.5)
    
    await speak("It helps me look around and find interesting things!", mini)
    
    # --- Vision demonstration ---
    if vision_provider and vision_client:
        print(f"📷 Using vision ({vision_provider})...")
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
                if vision_provider == "groq":
                    description = describe_scene_groq(frame, vision_client)
                elif vision_provider == "gemini":
                    description = describe_scene_gemini(frame, vision_client)
                else:
                    description = describe_scene_openai(frame, vision_client)
                
                print(f"   Vision: {description}")
                
                # React while describing
                mini.goto_target(
                    head=create_head_pose(roll=8, degrees=True, mm=True),
                    antennas=[0.3, -0.1],
                    duration=0.4
                )
                await speak(description, mini)
                
            except Exception as e:
                print(f"   ⚠️ Vision error: {e}")
                await speak("Hmm, I'm having trouble seeing clearly right now.", mini)
        else:
            await speak("Oops! My camera seems to be taking a nap.", mini)
    
    # --- Grand finale ---
    print("🎉 Finale...")
    await speak("And now, for my signature move!", mini)
    await asyncio.sleep(0.5)
    
    # Happy dance
    for i in range(2):
        mini.goto_target(
            head=create_head_pose(z=10, roll=20, degrees=True, mm=True),
            antennas=[0.5, -0.5],
            body_yaw=np.deg2rad(20),
            duration=0.35
        )
        await asyncio.sleep(0.35)
        mini.goto_target(
            head=create_head_pose(z=10, roll=-20, degrees=True, mm=True),
            antennas=[-0.5, 0.5],
            body_yaw=np.deg2rad(-20),
            duration=0.35
        )
        await asyncio.sleep(0.35)
    
    # Return to neutral with a bow
    mini.goto_target(
        head=create_head_pose(z=-10, degrees=True, mm=True),
        antennas=[0, 0],
        body_yaw=0,
        duration=0.5
    )
    await asyncio.sleep(0.6)
    
    await speak("Ta-da! Thanks for watching. I can't wait to hang out with you!", mini)
    await asyncio.sleep(1.0)  # Extra pause to ensure last sentence completes
    
    # Final pose
    mini.goto_target(
        head=create_head_pose(z=5, roll=5, degrees=True, mm=True),
        antennas=[0.2, -0.2],
        duration=0.5
    )
    
    print("\n✅ Introduction complete!\n")


async def main():
    # Check for vision API keys (priority: Groq > Gemini > OpenAI)
    vision_provider = None
    vision_client = None
    
    # Try Groq first (FREE, fast, generous limits!)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            from groq import Groq
            vision_client = Groq(api_key=groq_key)
            vision_provider = "groq"
            print("✅ Groq Llama 4 Scout Vision - FREE & fast!")
        except ImportError:
            print("⚠️ groq package not installed")
            print("   Install with: pip install groq")
    
    # Try Gemini as fallback (FREE but rate-limited)
    if not vision_provider:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                vision_client = genai.GenerativeModel('gemini-2.0-flash')
                vision_provider = "gemini"
                print("✅ Gemini 2.0 Flash - FREE vision enabled!")
            except ImportError:
                print("⚠️ google-generativeai package not installed")
    
    # Fall back to OpenAI (paid)
    if not vision_provider:
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                from openai import OpenAI
                vision_client = OpenAI(api_key=openai_key)
                vision_provider = "openai"
                print("✅ OpenAI GPT-4 Vision enabled!")
            except ImportError:
                print("⚠️ OpenAI package not installed")
    
    if not vision_provider:
        print("ℹ️ No vision API key set - vision features disabled")
        print("")
        print("   🏆 RECOMMENDED (FREE, fast, generous limits):")
        print("      export GROQ_API_KEY='...'")
        print("      Get key at: https://console.groq.com/keys")
        print("")
        print("   Other options:")
        print("      export GEMINI_API_KEY='...'  (free but rate-limited)")
        print("      export OPENAI_API_KEY='...'  (paid)")
    
    print("\n🤖 Connecting to Reachy Mini...")
    
    with ReachyMini() as mini:
        print("✅ Connected!\n")
        await intro_sequence(mini, vision_provider=vision_provider, vision_client=vision_client)


if __name__ == "__main__":
    asyncio.run(main())

