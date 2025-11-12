# How to Install ffmpeg on macOS

## Option 1: Install Homebrew (Recommended - Most Reliable)

Homebrew is the most popular package manager for macOS and makes installing tools like ffmpeg very easy.

### Step 1: Install Homebrew
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Follow the on-screen instructions. At the end, it may tell you to run some commands to add Homebrew to your PATH. Make sure to run those commands!

### Step 2: Install ffmpeg
```bash
brew install ffmpeg
```

### Step 3: Verify Installation
```bash
ffmpeg -version
ffprobe -version
```

---

## Option 2: Download Pre-built Binaries (No Homebrew)

If you don't want to install Homebrew, you can download pre-built ffmpeg binaries.

### Step 1: Download ffmpeg
1. Go to: https://evermeet.cx/ffmpeg/
2. Download these two files:
   - **ffmpeg** (click "Download" button)
   - **ffprobe** (scroll down, click "Download" button for ffprobe)

### Step 2: Extract and Install
```bash
# Create a local bin directory if it doesn't exist
mkdir -p ~/bin

# Move to your Downloads folder
cd ~/Downloads

# Extract the zip files (if they're zipped)
# The files should be executables

# Move them to your local bin
mv ffmpeg ~/bin/
mv ffprobe ~/bin/

# Make them executable
chmod +x ~/bin/ffmpeg
chmod +x ~/bin/ffprobe
```

### Step 3: Add to PATH
Edit your shell configuration file:
```bash
# For zsh (default on newer macOS)
nano ~/.zshrc
```

Add this line at the end:
```bash
export PATH="$HOME/bin:$PATH"
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 4: Reload your shell
```bash
source ~/.zshrc
```

### Step 5: Verify Installation
```bash
ffmpeg -version
ffprobe -version
```

---

## Option 3: Using MacPorts

If you have MacPorts installed:
```bash
sudo port install ffmpeg
```

---

## Troubleshooting

### "command not found" after installation

If you still get "command not found" after installing:

1. **Find where ffmpeg was installed:**
```bash
which ffmpeg
# or
find /usr/local -name ffmpeg 2>/dev/null
find /opt -name ffmpeg 2>/dev/null
```

2. **Check your PATH:**
```bash
echo $PATH
```

3. **If using Homebrew and it's not in PATH:**
```bash
# For M1/M2 Macs (Apple Silicon)
echo 'export PATH="/opt/homebrew/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# For Intel Macs
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

4. **Restart your terminal completely** (close and reopen)

---

## Quick Test

Once installed, test that everything works:

```bash
# Check versions
ffmpeg -version
ffprobe -version

# Test on a video file (if you have one)
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /path/to/video.mp4
```

---

## Still Having Issues?

If you're still getting errors:

1. **Check if you're on Apple Silicon (M1/M2/M3) or Intel:**
```bash
uname -m
# arm64 = Apple Silicon
# x86_64 = Intel
```

2. **Try installing Homebrew** - It's really the easiest way and handles architecture differences automatically.

3. **Close and reopen your terminal** - Sometimes PATH changes don't take effect until you restart the terminal.

4. **Check for typos** - Make sure you're typing `ffmpeg` not `ffmepg` or similar.

---

## Recommendation

**I strongly recommend Option 1 (Installing Homebrew)** because:
- It's the standard way to install developer tools on macOS
- It handles dependencies automatically
- It's easy to update: `brew upgrade ffmpeg`
- You'll need it for other development tools anyway
- It works seamlessly with both Intel and Apple Silicon Macs

Just run:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

Then:
```bash
brew install ffmpeg
```

And you're done!

