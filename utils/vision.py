import os
import cv2
import base64
import numpy as np

def encode_frame(frame):
    """Convert OpenCV frame to base64 string."""
    _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    return base64.b64encode(buffer).decode('utf-8')

def analyze_scene(frame, prompt: str = "Describe what you see briefly and enthusiastically.") -> str:
    """
    Analyze the scene using available vision providers.
    Priority: Groq > Gemini > OpenAI
    """
    # 1. Try Groq (Free & Fast)
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        print("   Trying Groq vision...")
        try:
            from groq import Groq
            client = Groq(api_key=groq_key)
            return _analyze_groq(frame, client, prompt)
        except Exception as e:
            print(f"   ⚠️ Groq failed: {e}")
    else:
        print("   No GROQ_API_KEY found")

    # 2. Try Gemini (Free)
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        print("   Trying Gemini vision...")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            # Try 2.0 then 1.5
            try:
                model = genai.GenerativeModel('gemini-2.0-flash')
                return _analyze_gemini(frame, model, prompt)
            except:
                model = genai.GenerativeModel('gemini-1.5-flash')
                return _analyze_gemini(frame, model, prompt)
        except Exception as e:
            print(f"   ⚠️ Gemini failed: {e}")
    else:
        print("   No GEMINI_API_KEY found")

    # 3. Try OpenAI (Paid)
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        print("   Trying OpenAI vision...")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            return _analyze_openai(frame, client, prompt)
        except Exception as e:
            print(f"   ⚠️ OpenAI failed: {e}")
    else:
        print("   No OPENAI_API_KEY found")
            
    print("   No vision providers available or all failed!")
    return "I'm having trouble seeing right now, but I bet it looks great!"

def _analyze_groq(frame, client, prompt):
    base64_image = encode_frame(frame)
    response = client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        temperature=1,
        max_completion_tokens=100,
        top_p=1,
        stream=False,
    )
    return response.choices[0].message.content

def _analyze_gemini(frame, model, prompt):
    from PIL import Image
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    response = model.generate_content([prompt, pil_image])
    return response.text

def _analyze_openai(frame, client, prompt):
    base64_image = encode_frame(frame)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                ]
            }
        ],
        max_tokens=100
    )
    return response.choices[0].message.content

