import asyncio
import numpy as np
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose

async def happy_wiggle(mini: ReachyMini, count: int = 3):
    """Wiggle antennas happily."""
    for _ in range(count):
        mini.goto_target(antennas=[0.6, -0.6], duration=0.15)
        await asyncio.sleep(0.15)
        mini.goto_target(antennas=[-0.6, 0.6], duration=0.15)
        await asyncio.sleep(0.15)
    mini.goto_target(antennas=[0, 0], duration=0.3)

async def nod(mini: ReachyMini):
    """Nod head yes."""
    for _ in range(2):
        mini.goto_target(head=create_head_pose(z=15, degrees=True, mm=True), duration=0.3)
        await asyncio.sleep(0.3)
        mini.goto_target(head=create_head_pose(z=-5, degrees=True, mm=True), duration=0.3)
        await asyncio.sleep(0.3)
    mini.goto_target(head=create_head_pose(z=0, degrees=True, mm=True), duration=0.3)

async def shake_head(mini: ReachyMini):
    """Shake head no."""
    for _ in range(2):
        mini.goto_target(head=create_head_pose(roll=20, degrees=True, mm=True), duration=0.3)
        await asyncio.sleep(0.3)
        mini.goto_target(head=create_head_pose(roll=-20, degrees=True, mm=True), duration=0.3)
        await asyncio.sleep(0.3)
    mini.goto_target(head=create_head_pose(roll=0, degrees=True, mm=True), duration=0.3)

async def scan_room(mini: ReachyMini):
    """Look around the room."""
    # Left
    mini.goto_target(
        head=create_head_pose(roll=20, degrees=True, mm=True),
        body_yaw=np.deg2rad(30),
        duration=1.0
    )
    await asyncio.sleep(1.0)
    # Right
    mini.goto_target(
        head=create_head_pose(roll=-20, degrees=True, mm=True),
        body_yaw=np.deg2rad(-30),
        duration=1.5
    )
    await asyncio.sleep(1.5)
    # Center
    mini.goto_target(
        head=create_head_pose(z=0, roll=0, degrees=True, mm=True),
        body_yaw=0,
        duration=1.0
    )

# --- Dance Moves ---

async def head_bob_rhythm(mini: ReachyMini, bpm: int = 100, duration_sec: float = 5.0):
    """Bob head to a beat."""
    beat_interval = 60.0 / bpm
    steps = int(duration_sec / beat_interval)
    
    for _ in range(steps):
        # Down on beat
        mini.goto_target(head=create_head_pose(z=-10, degrees=True, mm=True), duration=beat_interval * 0.4)
        await asyncio.sleep(beat_interval * 0.5)
        # Up off beat
        mini.goto_target(head=create_head_pose(z=5, degrees=True, mm=True), duration=beat_interval * 0.4)
        await asyncio.sleep(beat_interval * 0.5)

async def disco_spin(mini: ReachyMini):
    """Spin body while tilting head (disco style)."""
    # Spin Left + Head Right
    mini.goto_target(
        body_yaw=np.deg2rad(40),
        head=create_head_pose(roll=-30, z=10, degrees=True, mm=True),
        antennas=[0.5, 0.5],
        duration=0.6
    )
    await asyncio.sleep(0.6)
    
    # Spin Right + Head Left
    mini.goto_target(
        body_yaw=np.deg2rad(-40),
        head=create_head_pose(roll=30, z=10, degrees=True, mm=True),
        antennas=[-0.5, -0.5],
        duration=0.8
    )
    await asyncio.sleep(0.8)
    
    # Reset
    mini.goto_target(body_yaw=0, head=create_head_pose(z=0), antennas=[0,0], duration=0.4)

async def showstopper_finish(mini: ReachyMini):
    """Grand finale pose."""
    # Bow down
    mini.goto_target(head=create_head_pose(z=-20, degrees=True, mm=True), duration=0.5)
    await asyncio.sleep(0.5)
    # Big finish up
    mini.goto_target(
        head=create_head_pose(z=20, roll=0, degrees=True, mm=True),
        antennas=[0.8, -0.8],
        body_yaw=0,
        duration=0.3
    )
    await asyncio.sleep(1.0)
    # Neutral
    mini.goto_target(head=create_head_pose(z=0), antennas=[0,0], duration=0.5)

