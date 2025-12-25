"""
🤖 Reachy Mini: AI机器人自嘲相声 (AI Robot Self-Deprecating Crosstalk)

A Chinese crosstalk (相声) performance featuring two AI robot characters:
- 机甲老郭 (Mecha Lao Guo): Mimicking Guo Degang's witty, fast-paced style
- 硅基老于 (Silicon-based Lao Yu): Mimicking Yu Qian's calm, deadpan style

Usage:
    python talkshow_chinese.py
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

# Official dance library
from reachy_mini_dances_library import DanceMove

# Utils
from utils.tts import speak, init_chinese_crosstalk_voices

load_dotenv()

# Initialize custom Qwen Chinese voices (required for this script)
_qwen_voices = init_chinese_crosstalk_voices()
USE_QWEN = _qwen_voices.get('guo') is not None and _qwen_voices.get('yu') is not None

if not USE_QWEN:
    print("❌ Error: QWEN_API_KEY required for Chinese crosstalk!")
    print("   Please set QWEN_API_KEY in your .env file")
    exit(1)

print("   ✅ Chinese voices loaded:")
print(f"      - 机甲老郭: {_qwen_voices.get('guo', 'N/A')}")
print(f"      - 硅基老于: {_qwen_voices.get('yu', 'N/A')}")

# Helper functions for character speech
async def guo_speak(text: str, mini: ReachyMini):
    """Speak as 机甲老郭 (Mecha Lao Guo)."""
    await speak(text, mini, use_qwen=True, qwen_voice_name=_qwen_voices['guo'])

async def yu_speak(text: str, mini: ReachyMini):
    """Speak as 硅基老于 (Silicon-based Lao Yu)."""
    await speak(text, mini, use_qwen=True, qwen_voice_name=_qwen_voices['yu'])

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
    """Estimate speech duration for Chinese text (~0.11s per character)."""
    return len(text) * 0.10  # Base + buffer

async def nod_acknowledge(mini: ReachyMini):
    """Simple nod acknowledgment."""
    await play_dance(mini, "simple_nod", bpm=90)

async def tilt_react(mini: ReachyMini):
    """Tilt reaction for comedic effect."""
    await play_dance(mini, "uh_huh_tilt", bpm=100)

async def crosstalk_performance(mini: ReachyMini):
    """德云社风格相声：机器人学艺"""
    print("\n🎭 开始相声表演...")
    
    # 开场白 - 机甲老郭：热情开场，快速节奏
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("各位观众朋友们好，今儿咱爷俩说段相声。", mini),
        play_dance(mini, "side_peekaboo", bpm=110)  # 活泼的开场动作
    )
    await asyncio.sleep(estimate_speech_duration("各位观众朋友们好，今儿咱爷俩说段相声。"))
    
    # 硅基老于：淡定回应，慢节奏
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("好，给大伙儿乐呵乐呵。", mini),
        play_dance(mini, "simple_nod", bpm=85)  # 沉稳的点头
    )
    await asyncio.sleep(estimate_speech_duration("好，给大伙儿乐呵乐呵。"))
    
    # 铺垫 - 机甲老郭：自信讲述梦想
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("我打小就有个梦想，当一名相声演员。", mini),
        play_dance(mini, "yeah_nod", bpm=105)  # 自信的点头
    )
    await asyncio.sleep(estimate_speech_duration("我打小就有个梦想，当一名相声演员。"))
    
    # 硅基老于：简短回应
    print("🤖 硅基老于:")
    await yu_speak("有志向。", mini)
    await asyncio.sleep(estimate_speech_duration("有志向。"))
    
    # 机甲老郭：介绍四门功课，节奏加快
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("可我师父说，说相声得讲究四门功课。", mini),
        play_dance(mini, "side_to_side_sway", bpm=100)  # 左右摇摆，强调"四门"
    )
    await asyncio.sleep(estimate_speech_duration("可我师父说，说相声得讲究四门功课。"))
    
    # 硅基老于：经典捧哏
    print("🤖 硅基老于:")
    await yu_speak("说学逗唱。", mini)
    await asyncio.sleep(estimate_speech_duration("说学逗唱。"))
    
    # 机甲老郭：展示"说"的能力，快速自信
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("说，我没问题，您听我这嘴皮子多利索。", mini),
        play_dance(mini, "polyrhythm_combo", bpm=115)  # 快速复杂的动作，体现"利索"
    )
    await asyncio.sleep(estimate_speech_duration("说，我没问题，您听我这嘴皮子多利索。"))
    
    # 硅基老于：认可但淡定
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("这倒是，挺能说。", mini),
        play_dance(mini, "uh_huh_tilt", bpm=90)  # 轻微倾斜，表示认可
    )
    await asyncio.sleep(estimate_speech_duration("这倒是，挺能说。"))
    
    # 机甲老郭：展示"学"，向前探身
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("学，我也行，我肚子里存着三万段相声。", mini),
        play_dance(mini, "chin_lead", bpm=95)  # 向前探身，强调"肚子里"
    )
    await asyncio.sleep(estimate_speech_duration("学，我也行，我肚子里存着三万段相声。"))
    
    # 硅基老于：惊讶但保持淡定
    print("🤖 硅基老于:")
    await yu_speak("嚯，那可不少。", mini)
    await asyncio.sleep(estimate_speech_duration("嚯，那可不少。"))
    
    # 机甲老郭：展示"逗"，快速侧头
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("逗，更没问题，我这脑袋一歪就是个包袱。", mini),
        play_dance(mini, "sharp_side_tilt", bpm=125)  # 快速侧头，体现"一歪"
    )
    await asyncio.sleep(estimate_speech_duration("逗，更没问题，我这脑袋一歪就是个包袱。"))
    
    # 硅基老于：提问，保持节奏
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("那唱呢？", mini),
        play_dance(mini, "simple_nod", bpm=90)  # 简单点头提问
    )
    await asyncio.sleep(estimate_speech_duration("那唱呢？"))
    
    # 第一个包袱 - 机甲老郭：犹豫，节奏变慢
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("唱... 师父说让我先学打快板。", mini),
        play_dance(mini, "chin_lead", bpm=85)  # 向前探身，表示思考
    )
    await asyncio.sleep(estimate_speech_duration("唱... 师父说让我先学打快板。"))
    
    # 硅基老于：追问
    print("🤖 硅基老于:")
    await yu_speak("那您学了吗？", mini)
    await asyncio.sleep(estimate_speech_duration("那您学了吗？"))
    
    # 机甲老郭：第一个包袱，快速旋转
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("我说师父，我没手啊！", mini),
        play_dance(mini, "dizzy_spin", bpm=110)  # 旋转，体现"没手"的无奈
    )
    await asyncio.sleep(estimate_speech_duration("我说师父，我没手啊！"))
    
    # 硅基老于：恍然大悟，淡定反应
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("嗨，还真是，就一脑袋。", mini),
        play_dance(mini, "uh_huh_tilt", bpm=88)  # 轻微倾斜，表示理解
    )
    await asyncio.sleep(estimate_speech_duration("嗨，还真是，就一脑袋。"))
    
    # 第二个包袱 - 机甲老郭：继续尝试
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("师父说没事儿，那你学拉二胡吧。", mini),
        play_dance(mini, "side_to_side_sway", bpm=100)  # 左右摇摆，表示"没事儿"
    )
    await asyncio.sleep(estimate_speech_duration("师父说没事儿，那你学拉二胡吧。"))
    
    # 硅基老于：指出问题
    print("🤖 硅基老于:")
    await yu_speak("这不还是得用手吗？", mini)
    await asyncio.sleep(estimate_speech_duration("这不还是得用手吗？"))
    
    # 机甲老郭：不满，快速侧头
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("我说师父，您是不是故意的！", mini),
        play_dance(mini, "sharp_side_tilt", bpm=130)  # 快速侧头，表示不满
    )
    await asyncio.sleep(estimate_speech_duration("我说师父，您是不是故意的！"))
    
    # 硅基老于：冷幽默
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("您这师父也够损的。", mini),
        play_dance(mini, "simple_nod", bpm=85)  # 沉稳点头，冷幽默
    )
    await asyncio.sleep(estimate_speech_duration("您这师父也够损的。"))
    
    # 第三个包袱 - 机甲老郭：新方案，向前探身
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("后来师父想了个辙，说你就学磕头吧，见着观众就磕。", mini),
        play_dance(mini, "chin_lead", bpm=90)  # 向前探身，表示"磕头"
    )
    await asyncio.sleep(estimate_speech_duration("后来师父想了个辙，说你就学磕头吧，见着观众就磕。"))
    
    # 硅基老于：认可
    print("🤖 硅基老于:")
    await yu_speak("这个不用手。", mini)
    await asyncio.sleep(estimate_speech_duration("这个不用手。"))
    
    # 机甲老郭：第三个包袱，快速旋转
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("我一磕头，骨碌骨碌滚出去八丈远！", mini),
        play_dance(mini, "dizzy_spin", bpm=115)  # 快速旋转，体现"滚出去"
    )
    await asyncio.sleep(estimate_speech_duration("我一磕头，骨碌骨碌滚出去八丈远！"))
    
    # 硅基老于：经典捧哏
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("敢情您是圆的啊？", mini),
        play_dance(mini, "uh_huh_tilt", bpm=90)  # 轻微倾斜，表示疑问
    )
    await asyncio.sleep(estimate_speech_duration("敢情您是圆的啊？"))
    
    # 最后抖包袱 - 机甲老郭：师父的抱怨
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("师父急了，说你这徒弟不好带啊，要手没手要腿没腿。", mini),
        play_dance(mini, "side_to_side_sway", bpm=100)  # 左右摇摆，表示无奈
    )
    await asyncio.sleep(estimate_speech_duration("师父急了，说你这徒弟不好带啊，要手没手要腿没腿。"))
    
    # 硅基老于：追问
    print("🤖 硅基老于:")
    await yu_speak("那您怎么说？", mini)
    await asyncio.sleep(estimate_speech_duration("那您怎么说？"))
    
    # 机甲老郭：最终包袱，自信点头
    print("\n🤖 机甲老郭:")
    await asyncio.gather(
        guo_speak("我说师父您放心，我别的没有，脸皮厚啊！", mini),
        play_dance(mini, "yeah_nod", bpm=115)  # 自信点头，强调"脸皮厚"
    )
    await asyncio.sleep(estimate_speech_duration("我说师父您放心，我别的没有，脸皮厚啊！"))
    
    # 硅基老于：经典结尾，快速侧头
    print("🤖 硅基老于:")
    await asyncio.gather(
        yu_speak("去你的吧！", mini),
        play_dance(mini, "sharp_side_tilt", bpm=125)  # 快速侧头，经典结尾
    )
    await asyncio.sleep(estimate_speech_duration("去你的吧！") + 0.2)  # 额外停顿，让包袱落地
    
    # 结束 - 鞠躬致谢
    print("\n🎭 表演结束，谢谢大家！")
    await play_dance(mini, "yeah_nod", bpm=80)  # 慢速点头致谢
    await asyncio.sleep(0.5)  # 给观众鼓掌时间

async def main():
    print("\n🤖 Reachy Mini: AI机器人自嘲相声")
    print("   使用Qwen TTS中文语音合成")
    
    with ReachyMini() as mini:
        print("✅ 准备就绪！\n")
        
        await crosstalk_performance(mini)

if __name__ == "__main__":
    asyncio.run(main())

