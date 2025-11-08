# 🧩 Checkpoint Manager — Reliable Save System for Python

**Checkpoint Manager** is a lightweight, safe, and flexible data persistence system built in Python.  
It lets you **save, load, and recover progress** during long-running processes (like simulations or data processing)  
with smart backups, validation, and corruption protection.

---

## 🌟 Features

✅ **Atomic saving** — prevents corrupted files by using temporary writes.  
✅ **Auto backup** — periodically creates backup copies of your data.  
✅ **Smart backup** — saves progress only when meaningful improvements occur.  
✅ **Metadata & config validation** — ensures checkpoints are compatible across sessions.  
✅ **Safe verification** — checks for corrupted or mismatched pickle files before loading.  
✅ **Full pickle compatibility** — supports any Python object (including NumPy arrays, pandas DataFrames, etc.).

---

## 🚀 Quick Start

### 1️⃣ Installation

No dependencies needed beyond Python’s standard library.

```bash
git clone https://github.com/glitchh07/Checkpoint-Manager.git
cd <Checkpoint-Manager>
```

### 2️⃣ Basic Usage 

```bash
from file import CheckpointManager  # or rename to checkpoint_manager.py

config = {"version": 1.0, "experiment": "dice_simulation"}

cm = CheckpointManager(
    path="checkpoint.pkl",
    config=config,
    save_dir="checkpoints"
)

data = {"rolls_completed": 5, "results": [1, 2, 3, 4, 5]}

# ✅ Save safely
cm.save_file(data)

# ✅ Load checkpoint if exists
data = cm.load_file(config)

# ✅ Perform auto backup every 10 minutes(basic backup function)
cm.auto_backup("backup.pkl", interval=600)

# ✅ Create a smart backup if progress improves (only progress is mandatory which can be any number which can be used to compare the progress)
cm.auto_backup_smart(progress, min_improvement, interval, max_backups)

# ✅ Verify save integrity
cm.verify_save("checkpoint.pkl")

```
---
## 🧠 Function Reference

### • save_file(data)

Safely saves data to a pickle file using atomic writes.

    Writes to .tmp file first, then replaces the main file.
    Automatically embeds metadata (timestamp, config, checksum).
    Returns True on success.

### • load_file(config)

Loads the most recent valid checkpoint.

    Validates that metadata["config"] matches the provided config.
    Automatically falls back to backup file if main checkpoint is missing or corrupted.
    Returns the stored Python object, or None if no valid file is found.

### • verify_save(path)

Verifies that a file exists and contains valid pickle data with metadata.
    
    Returns True if valid, otherwise False.

### • auto_backup(backup_name, interval=600)

Creates periodic automatic backups of your current checkpoint.
    
    backup_name → the backup file name.
    interval → time (in seconds) between backups.
    Skips backup if not enough time has passed since the last one.
    Skips backup if not enough time has passed since the last one.

### • auto_backup_smart(progress, min_improvement, interval, max_backups)

Creates a smart backup only if the new progress is significantly better than the previous one and the fixed amount of time has passed.
  
    Tracks improvement ratio since the last save.
    Adds timestamp and improvement % to the backup filename.
    Keeps backups sorted (newest first).
    Helps preserve meaningful milestones during long runs.
  
### • remove_checkpoints()

Deletes all checkpoint files (main, backup, and smart backups).
Use cautiously. Prints the number of files removed.

### • remove_specific_checkpoints(config)

Deletes only those checkpoint files matching a specific configuration.
Useful when managing multiple experiment runs in the same folder.

###validate_config(config)==> future fuction. will add in the next update.
Ensures that the provided config matches existing checkpoint metadata.
Prevents accidental cross-loading between incompatible experiments.

---
## metadata

Each saved file automatically includes metadata:
```bash
{
    "timestamp": 1730716800.0,
    "elapsed: 36000,
    "config": {"version": 1.0, "experiment": "dice_simulation"}
}
```
---

## 🧾 Example Use Cases

  🎲 Long-running Monte Carlo or dice simulations
  🧬 Machine learning training checkpoints
  📊 Data analysis tasks that run for hours or days
  ⚙️ Scientific experiments or research scripts
  💡 Any project needing safe save/resume capability

---

## 📜 License
  MIT License
  © 2025 Glitchh
  Feel free to use, modify, and distribute.


  💬 “Code that can recover itself is code that you can trust.”
  — Glitchh


---

### ✅ What to Do Next

1. Copy-paste this into your `README.md`.  
2. Replace `<your-username>` and `<repo-name>` with your GitHub info.  
3. Rename `file.py` → `checkpoint_manager.py` if you want a clean name.  
4. Add your license (`MIT` — GitHub can auto-generate this).  

---

If you’d like, I can also generate a **short, professional one-line tagline** for your repo (the line that appears *under* the repo name on GitHub, e.g. *“A lightweight checkpoint and backup system for Python experiments”*).  
Want me to make a few options so you can pick one?


