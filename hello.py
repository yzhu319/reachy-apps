from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np
import time

with ReachyMini() as mini:
    print("🤖 Connected to Reachy Mini!")
    time.sleep(0.5)

    # --- Test 1: Antennas ---
    print("\n🐜 Test 1: Wiggling antennas...")
    mini.goto_target(antennas=[0.5, -0.5], duration=0.4)
    mini.goto_target(antennas=[-0.5, 0.5], duration=0.4)
    mini.goto_target(antennas=[0, 0], duration=0.4)

    # --- Test 2: Head movement ---
    print("🗣️ Test 2: Moving head (look up, down, tilt)...")
    # Look up
    mini.goto_target(head=create_head_pose(z=15, degrees=True, mm=True), duration=0.6)
    # Look down
    mini.goto_target(head=create_head_pose(z=-15, degrees=True, mm=True), duration=0.6)
    # Tilt right
    mini.goto_target(head=create_head_pose(roll=20, degrees=True, mm=True), duration=0.5)
    # Tilt left
    mini.goto_target(head=create_head_pose(roll=-20, degrees=True, mm=True), duration=0.5)
    # Back to center
    mini.goto_target(head=create_head_pose(z=0, roll=0, degrees=True, mm=True), duration=0.5)

    # --- Test 3: Body/Torso rotation ---
    print("💃 Test 3: Rotating torso...")
    mini.goto_target(body_yaw=np.deg2rad(25), duration=0.6)   # Turn right
    mini.goto_target(body_yaw=np.deg2rad(-25), duration=0.6)  # Turn left
    mini.goto_target(body_yaw=0, duration=0.5)                # Back to center

    # --- Test 4: Sound ---
    print("🔊 Test 4: Playing sound...")
    try:
        mini.media.play_sound("wake_up.wav")
        time.sleep(1)  # Wait for sound to finish
    except Exception as e:
        print(f"   ⚠️  Sound test skipped: {e}")

    # --- Finale: Combined movement ---
    print("🎉 Finale: Happy dance!")
    mini.goto_target(
        head=create_head_pose(z=10, roll=15, degrees=True, mm=True),
        antennas=[0.3, -0.3],
        body_yaw=np.deg2rad(15),
        duration=0.5
    )
    mini.goto_target(
        head=create_head_pose(z=10, roll=-15, degrees=True, mm=True),
        antennas=[-0.3, 0.3],
        body_yaw=np.deg2rad(-15),
        duration=0.5
    )
    # Reset to neutral
    mini.goto_target(
        head=create_head_pose(z=0, roll=0, degrees=True, mm=True),
        antennas=[0, 0],
        body_yaw=0,
        duration=0.5
    )

    print("\n✅ All tests complete!")

