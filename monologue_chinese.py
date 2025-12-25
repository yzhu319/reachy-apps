"""
🛒 Reachy Mini: 网络直播间带货 (Online Sales Livestream)

A Chinese monologue performance featuring an energetic online salesperson:
- 网络主播 (Online Salesperson): Mimicking TV shopping host style with fast-paced, 
  passionate, and exaggerated tone to create urgency and buying frenzy.

Usage:
    python monologue_chinese.py
"""

import asyncio
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

# Official dance library
from reachy_mini_dances_library import DanceMove

# Utils
from utils.tts import speak, init_salesman_voice

load_dotenv()

# Initialize custom Qwen Chinese voice (required for this script)
_salesman_voice = init_salesman_voice()
USE_QWEN = _salesman_voice is not None

if not USE_QWEN:
    print("❌ Error: QWEN_API_KEY required for Chinese monologue!")
    print("   Please set QWEN_API_KEY in your .env file")
    exit(1)

print("   ✅ Chinese voice loaded:")
print(f"      - 网络主播: {_salesman_voice}")

# Helper function for salesperson speech
async def salesman_speak(text: str, mini: ReachyMini):
    """Speak as 网络主播 (Online Salesperson)."""
    await speak(text, mini, use_qwen=True, qwen_voice_name=_salesman_voice)

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

def estimate_speech_duration(text: str) -> float:
    """Estimate speech duration for Chinese text (~0.10s per character)."""
    return len(text) * 0.04 

async def sales_monologue(mini: ReachyMini):
    """网络直播间带货：激情销售"""
    print("\n🛒 开始直播带货...")
    
    # 开场 - 激情开场，简单活泼动作
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("家人们！不要九百九十八，也不要八百八十八，今天在我直播间，直接给你们砍到地板价 —— 只要九十八！", mini),
        play_dance(mini, "side_peekaboo", bpm=110)  # 简单活泼动作，营造激情开场
    )
    await asyncio.sleep(estimate_speech_duration("家人们！不要九百九十八，也不要八百八十八，今天在我直播间，直接给你们砍到地板价 —— 只要九十八！"))
    
    # 对比强调 - 身体左右摇摆，强调价格优势
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("九十八块钱，你去菜市场买斤好点的排骨都不够，今天在我这就能把宝贝带回家！", mini),
        play_dance(mini, "side_to_side_sway", bpm=105)  # 简单左右摇摆，强调对比
    )
    await asyncio.sleep(estimate_speech_duration("九十八块钱，你去菜市场买斤好点的排骨都不够，今天在我这就能把宝贝带回家！"))
    
    # 重复强调价格 - 简单点头
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("对，你没有听错，就是九十八！", mini),
        play_dance(mini, "yeah_nod", bpm=110)  # 简单点头，强调"没听错"
    )
    await asyncio.sleep(estimate_speech_duration("对，你没有听错，就是九十八！"))
    
    # 营造紧迫感 - 快速旋转，体现"抢购"
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("库存就剩最后这几百单了，手快有手慢无，错过今天，再等一年！", mini),
        play_dance(mini, "pendulum_swing", bpm=110)  # 身体摆动，营造紧迫感
    )
    await asyncio.sleep(estimate_speech_duration("库存就剩最后这几百单了，手快有手慢无，错过今天，再等一年！"))
    
    # 身体旋转动作 - 强调紧迫感
    mini.goto_target(body_yaw=np.deg2rad(25), duration=0.5)   # Turn right
    await asyncio.sleep(0.5)
    mini.goto_target(body_yaw=np.deg2rad(-25), duration=0.5)  # Turn left
    await asyncio.sleep(0.5)
    mini.goto_target(body_yaw=0, duration=0.4)                # Back to center
    await asyncio.sleep(0.4)
    
    # 行动号召 - 向前探身，指向"小黄车"
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("想要的家人们，直接点下方小黄车一号链接，赶紧拍！赶紧抢！", mini),
        play_dance(mini, "chin_lead", bpm=100)  # 向前探身，指向下方动作
    )
    await asyncio.sleep(estimate_speech_duration("想要的家人们，直接点下方小黄车一号链接，赶紧拍！赶紧抢！"))
    
    # 额外强调 - 复杂动作组合
    print("\n🎤 网络主播:")
    await asyncio.gather(
        salesman_speak("赶紧拍！赶紧抢！", mini),
        play_dance(mini, "polyrhythm_combo", bpm=120)  # 复杂动作组合，强调行动
    )
    await asyncio.sleep(estimate_speech_duration("赶紧拍！赶紧抢！") + 0.3)
    
    # 结束 - 简单点头致谢
    print("\n🛒 直播结束！")
    await play_dance(mini, "simple_nod", bpm=100)  # 简单点头致谢
    await asyncio.sleep(0.5)

async def main():
    print("\n🛒 Reachy Mini: 网络直播间带货")
    print("   使用Qwen TTS中文语音合成")
    
    with ReachyMini() as mini:
        print("✅ 准备就绪！\n")
        
        await sales_monologue(mini)

if __name__ == "__main__":
    asyncio.run(main())

