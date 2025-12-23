# Reachy Apps 🤖

My custom apps for Reachy Mini / Reachy Mini Lite.

This repo is set up alongside the official [reachy_mini SDK](https://github.com/pollen-robotics/reachy_mini) for reference, but all development happens here.

---

## 🏗️ Project Structure

```
~/
├── reachy_mini/        # Official SDK (read-only, for docs & examples)
└── reachy-apps/        # YOUR apps (this repo)
    ├── .venv/          # Python virtual environment
    ├── hello.py        # Hardware test script
    ├── hello_vision.py # Camera test script
    ├── self_intro.py   # 🎭 Theatrical self-introduction demo
    ├── pyproject.toml  # Project dependencies
    └── README.md       # This file
```

---

## 🚀 Setup from Scratch

Follow these steps if you're starting fresh on a new machine.

### Prerequisites

- **Python 3.10–3.12**
- **Git + Git LFS**
- **uv** (fast Python package manager)

Install uv if you haven't:

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Step 1: Clone the Official SDK (for reference)

```bash
cd ~
git clone https://github.com/pollen-robotics/reachy_mini.git
```

This gives you access to documentation and examples. You won't modify this repo.

### Step 2: Create Your App Directory

```bash
mkdir ~/reachy-apps
cd ~/reachy-apps
```

### Step 3: Initialize the Project with uv

```bash
uv init --name reachy_apps
```

This creates a `pyproject.toml` and `.venv/` virtual environment.

### Step 4: Install Reachy Mini SDK

```bash
uv add reachy-mini --extra mujoco
```

- `reachy-mini` → Core SDK for controlling the robot
- `--extra mujoco` → Adds simulation support (optional but recommended)

### Step 5: Verify Installation

```bash
source .venv/bin/activate
python -c "from reachy_mini import ReachyMini; print('✅ SDK installed!')"
```

---

## 🎮 Running Your Robot

You need **two terminals**: one for the daemon, one for your scripts.

### Terminal 1: Start the Daemon

```bash
cd ~/reachy-apps
source .venv/bin/activate

# For Reachy Mini Lite (USB connection)
uv run reachy-mini-daemon

# For simulation (no robot needed)
uv run reachy-mini-daemon --sim --headless
```

Keep this terminal running! The daemon is the bridge between your code and the robot.

**Verify:** Open http://localhost:8000 — you should see the Reachy Dashboard.

### Terminal 2: Run Your Script

```bash
cd ~/reachy-apps
source .venv/bin/activate
python hello.py
```

---

## 🎭 Professional Dance Integration

This project integrates the [Reachy Mini Dances Library](https://github.com/pollen-robotics/reachy_mini_dances_library) — 20 pre-built professional dance moves including:

| Category | Moves |
|----------|-------|
| **High Energy** | `jackson_square`, `headbanger_combo`, `polyrhythm_combo` |
| **Smooth & Groovy** | `groovy_sway_and_roll`, `dizzy_spin`, `pendulum_swing` |
| **Expressive** | `yeah_nod`, `uh_huh_tilt`, `side_peekaboo` |
| **Quick & Sharp** | `side_glance_flick`, `grid_snap`, `sharp_side_tilt` |

All moves are BPM-adjustable and perfectly choreographed for dramatic performances!

---

## 🧪 Test Scripts

### `hello.py` — Full Hardware Test

Tests antennas, head movement, torso rotation, vision, sound, and features a **professional dance finale**!

```bash
python hello.py
```

**New**: Finale now includes `dizzy_spin` and `groovy_sway_and_roll` from the official dance library!

### `hello_vision.py` — Camera Test

Opens a live camera feed. Press `q` to quit, `s` to save a snapshot.

```bash
python hello_vision.py
```

### `self_intro.py` — 🎭 Theatrical Self-Introduction

A lively demo where Reachy Mini introduces itself with speech and coordinated movements!

### `talk_show.py` — 🎙️ The Late Night Show (Enhanced Edition)

**"The Show That Never Sleeps (Because It's A Robot)"**

A full 2-minute late-night performance featuring **professional choreography** and comedy writing!

**🎭 Show Structure:**
- **Cold Open**: Sharp one-liner with physical comedy (`sharp_side_tilt`)
- **Monologue**: 3 rapid-fire jokes with perfect dance timing
  - Tech humor: "Roomba with anxiety"
  - Python/JavaScript async joke → `grid_snap` + `neck_recoil`
  - Dating app roast → `stumble_and_recover`
- **Commercial Break**: 2-second techno bumper (`headbanger_combo` @ 140 BPM)
- **Vision Roast** *(optional)*: Ronny Chieng-style audience roast
- **Musical Guest (Reachy)**: 8-bar rap with choreographed moves
  - Confident intro → `jackson_square`
  - Tech flex → `polyrhythm_combo`
  - Playful diss → `side_to_side_sway` + `grid_snap`
  - Hype finale → `interwoven_spirals`
- **Grand Finale**: `groovy_sway_and_roll` + `dizzy_spin` + bow

**NEW**: Speech and movement now **overlap naturally** (just like human hosts!) for maximum energy and natural flow.

```bash
# Default (no vision, faster show)
python talk_show.py

# With vision roast segment
python talk_show.py --vision
```

**Style inspired by**: Ronny Chieng, Jimmy Kimmel, John Oliver  
**Powered by**: [Reachy Mini Dances Library](https://github.com/pollen-robotics/reachy_mini_dances_library) (20 professional moves)

**Features:**
- Text-to-Speech using Microsoft Edge voices (edge-tts)
- Coordinated movements synced with speech
- Optional: AI vision that describes what the robot sees

**Prerequisites:**
- Install ffmpeg for audio conversion: `brew install ffmpeg` (macOS)

```bash
# Basic run (speech + movement only)
python self_intro.py

# 🏆 RECOMMENDED: Groq (FREE, fast, generous limits!)
# Get your free key at: https://console.groq.com/keys
export GROQ_API_KEY="your-key-here"
python self_intro.py

# Alternative: Google Gemini (free but rate-limited)
export GEMINI_API_KEY="your-key-here"
python self_intro.py

# Or with OpenAI vision (paid, highest quality)
export OPENAI_API_KEY="sk-your-key-here"
python self_intro.py
```

---

## 📚 Quick Reference

### Daemon Commands

| Command | Use Case |
|---------|----------|
| `uv run reachy-mini-daemon` | Real robot (Mini Lite via USB) |
| `uv run reachy-mini-daemon --sim` | Simulation with visual window |
| `uv run reachy-mini-daemon --sim --headless` | Simulation without window |

### SDK Basics

```python
from reachy_mini import ReachyMini
from reachy_mini.utils import create_head_pose
import numpy as np

with ReachyMini() as mini:
    # Move head
    mini.goto_target(
        head=create_head_pose(z=10, roll=15, degrees=True, mm=True),
        duration=1.0
    )
    
    # Move antennas
    mini.goto_target(antennas=[0.5, -0.5], duration=0.5)
    
    # Rotate body
    mini.goto_target(body_yaw=np.deg2rad(30), duration=0.5)
    
    # Play sound
    mini.media.play_sound("wake_up.wav")
    
    # Get camera frame
    frame = mini.media.get_frame()
```

---

## 🔗 Resources

- [Official SDK Docs](https://github.com/pollen-robotics/reachy_mini/tree/main/docs/SDK)
- [Python SDK Reference](https://github.com/pollen-robotics/reachy_mini/blob/main/docs/SDK/python-sdk.md)
- [Example Scripts](https://github.com/pollen-robotics/reachy_mini/tree/main/examples)
- [Discord Community](https://discord.gg/2bAhWfXme9)

---

## 🚢 Publishing to Hugging Face

When you're ready to share your app:

1. Push this repo to GitHub
2. Create a [Hugging Face Space](https://huggingface.co/spaces)
3. Link your GitHub repo or use the HF web editor
4. Add `reachy-mini` to your `requirements.txt`

Your app will then be installable from the Reachy Mini dashboard!

---

## 📝 License

MIT — do whatever you want with this code.

