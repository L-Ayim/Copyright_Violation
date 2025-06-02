# Copyright Violation

This script downloads YouTube audio as MP3 and optionally splits it into stems via Demucs. Supports 4- or 6-stem layouts, resume-safe folder sweeping, and automatic GPU detection.

---

## Prerequisites

1. **Python 3.8+** (with `pip`)

2. **ffmpeg** (CLI)  
   - **Chocolatey**  
     ```powershell
     choco install ffmpeg
     ```
   - **Manual download**  
     1. Go to https://ffmpeg.org/download.html  
     2. Download the Windows build.  
     3. Extract and add `ffmpeg\bin` to your `PATH`.

3. **Demucs** (CLI)  
   ```powershell
   pip install demucs
   ```

4. **PyTorch**  
   - **CPU-only** (default):  
     ```powershell
     pip install torch torchvision torchaudio
     ```
   - **GPU-enabled** (CUDA 11.8 example):  
     ```powershell
     pip uninstall torch torchvision torchaudio
     pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
     ```

---

## Installation

```powershell
# 1. Clone the repo
git clone https://github.com/L-Ayim/Copyright_Violation.git
cd Copyright_Violation

# 2. Create & activate a venv
python -m venv venv
venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Usage

Run the script from PowerShell or CMD in the project root:

```powershell
# Download only (no splitting)
python Copyright_Violation.py https://youtu.be/VIDEO_ID1 https://youtu.be/VIDEO_ID2

# Download & split (auto GPU detection, default 6 stems)
python Copyright_Violation.py https://youtu.be/VIDEO_ID --split

# Download & split into 4 stems
python Copyright_Violation.py https://youtu.be/VIDEO_ID --split --stems 4

# Sweep already-downloaded folders for missing stems
python Copyright_Violation.py --sweep

# Force CPU mode (even if a GPU/CUDA is detected)
python Copyright_Violation.py https://youtu.be/VIDEO_ID --split --cpu
```

- You may pass **multiple URLs** separated by spaces.
- All output (downloads & stems) go into `.\downloads\`.

---

## Command-Line Flags

| Flag           | Description                                                                                 |
|---------------|---------------------------------------------------------------------------------------------|
| `--split`     | After downloading, run Demucs to split newly downloaded MP3s into stems.                    |
| `--sweep`     | Scan each subfolder under `.\downloads\` for MP3s missing stems and split them.             |
| `--cpu`       | Force Demucs to run on CPU (even if a CUDA-capable GPU is available).                       |
| `--stems 4|6` | Choose 4-stem (`vocals`, `drums`, `bass`, `other`) or 6-stem (`vocals`, `drums`, `bass`, `guitar`, `piano`, `other`) layout. Default is `6`. |

---

## Folder Layout

```
.
├── downloads\               ← All MP3s & stem-folders appear here
│   ├── My Video Title.mp3
│   └── htdemucs_6s\         ← or htdemucs\ (for 4 stems)
│       └── My Video Title\
│           ├── vocals.mp3
│           ├── drums.mp3
│           └── …other stems…
├── requirements.txt
└── Copyright_Violation.py  ← Main script
```

---

## License

MIT © 2025 Lawrence Ayim (L-Ayim)
