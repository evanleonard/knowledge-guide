#!/usr/bin/env python3
"""
generate_podcast_audio.py - Multi-Backend Audio & Interactive Web Player Synthesizer for OKF Episodes.

Supported Voice Backends:
1. Google Cloud / Gemini Neural TTS (Studio & Journey voices via REST API, requires GOOGLE_API_KEY)
2. Microsoft Edge Neural TTS (Free, high-fidelity neural voices, no API key needed)
3. ElevenLabs Studio Voices (Ultra-realistic, requires ELEVENLABS_API_KEY)
4. macOS Native Speech (Offline, built-in to macOS using Samantha & Daniel via say + afconvert)
5. Interactive Web Player Only (Browser Web Speech API, zero installation)
"""

import os
import sys
import re
import json
import base64
import argparse
import subprocess
import shutil
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

# Add root scripts to path if available
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2] if len(SCRIPT_DIR.parents) >= 3 else SCRIPT_DIR.parent
if (REPO_ROOT / "scripts").exists():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    from validate import parse_yaml_frontmatter
except ImportError:
    def parse_yaml_frontmatter(text):
        if not text.startswith("---"):
            return None, text
        parts = text.split("---", 2)
        if len(parts) < 3:
            return None, text
        raw = parts[1]
        body = parts[2]
        meta = {}
        for line in raw.splitlines():
            if ":" in line and not line.strip().startswith("#"):
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip().strip("\"'")
        return meta, body


def load_env_file(root_dir: Path):
    """Loads environment variables from .env file in repository root if present."""
    env_file = root_dir / ".env"
    if env_file.exists():
        try:
            for line in env_file.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("\"'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        except Exception:
            pass


def get_google_api_key(cli_key: str = None) -> str:
    """Retrieves Google API key from CLI argument, environment, or .env."""
    load_env_file(REPO_ROOT)
    return cli_key or os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""


def get_elevenlabs_api_key(cli_key: str = None) -> str:
    """Retrieves ElevenLabs API key from CLI argument, environment, or .env."""
    load_env_file(REPO_ROOT)
    return cli_key or os.environ.get("ELEVENLABS_API_KEY") or ""


def clean_spoken_text(text: str) -> str:
    """Removes markdown links, formatting, and vocal stage directions for natural speech."""
    # Strip vocal cues like [laughs], [chuckles], [curious], [leaning in]
    cleaned = re.sub(r"\[[a-zA-Z0-9_\s\-\,\.\'\!]+\]", "", text)
    # Convert markdown links [text](url) to just text
    cleaned = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cleaned)
    # Strip backticks, asterisks, formatting
    cleaned = cleaned.replace("`", "").replace("*", "").replace("#", "")
    # Clean file extensions in text e.g. "core-architecture.md" -> "core architecture"
    cleaned = re.sub(r"([a-zA-Z0-9_\-]+)\.(?:md|json|ts|py|yaml)", r"\1", cleaned)
    # Normalize hyphens in stems
    cleaned = cleaned.replace("-", " ")
    # Normalize whitespace
    return re.sub(r"\s+", " ", cleaned).strip()


def parse_timestamp_seconds(ts: str) -> int:
    """Converts MM:SS or HH:MM:SS to integer seconds."""
    if not ts:
        return 0
    parts = ts.split(":")
    if len(parts) == 2:
        return int(parts[0]) * 60 + int(parts[1])
    elif len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    return 0


def parse_dialogue_turns(content: str) -> tuple[dict, list[dict]]:
    """Extracts frontmatter and structured dialog turns from episode markdown."""
    meta, body = parse_yaml_frontmatter(content)
    if not meta:
        meta = {}

    turns = []
    lines = body.splitlines()
    
    current_time = "00:00"
    
    for line in lines:
        line_str = line.strip()
        if not line_str:
            continue
            
        m = re.match(r"^\*{0,2}\[?(\d{2}:\d{2})?\]?\s*([A-Za-z0-9_\s]+?):\*{0,2}\s*(.+)$", line_str)
        if m:
            t_stamp, speaker, text = m.groups()
            if t_stamp:
                current_time = t_stamp
                
            speaker = speaker.strip().strip("*").strip()
            tone_match = re.match(r"^\[([a-zA-Z0-9_\s\-\,\.\'\!]+)\]\s*(.*)$", text.strip())
            tone = tone_match.group(1).strip() if tone_match else None
            spoken_text = tone_match.group(2).strip() if tone_match else text.strip()
            
            clean_speech = clean_spoken_text(spoken_text)
            if clean_speech:
                turns.append({
                    "timestamp": current_time,
                    "seconds": parse_timestamp_seconds(current_time),
                    "speaker": speaker,
                    "tone": tone,
                    "raw_text": spoken_text,
                    "clean_speech": clean_speech
                })

    return meta, turns


# ==============================================================================
# Voice Synthesis Backend 1: Google Cloud / Gemini Neural TTS
# ==============================================================================

import time

def synthesize_gemini_turn(text: str, voice_name: str, api_key: str, max_retries: int = 5) -> bytes:
    """Calls Gemini Speech Synthesis API (gemini-2.5-flash-preview-tts) with exponential backoff on 429."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": text}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {
                        "voiceName": voice_name
                    }
                }
            }
        }
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                cand = res_data["candidates"][0]["content"]["parts"][0]
                return base64.b64decode(cand["inlineData"]["data"])
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait_time = 15 + (attempt * 10)  # 15s, 25s, 35s, 45s
                print(f"\n⏳ Google rate limit (429) hit. Waiting {wait_time}s for quota window to reset...", flush=True)
                time.sleep(wait_time)
                continue
            raise e


def synthesize_google_tts(turns: list[dict], output_audio: Path, api_key: str) -> bool:
    """
    Synthesizes dialogue turns using Google Gemini TTS API (Aoede & Charon voices)
    with automatic fallback to Google Cloud Text-to-Speech REST API (Journey/Neural2 voices).
    Zero third-party pip dependencies required; uses Python standard library urllib.
    """
    if not api_key:
        print("Error: Google API Key is required for Google Neural TTS.")
        return False

    speakers = sorted(list({t["speaker"] for t in turns}))
    host1 = speakers[0] if len(speakers) > 0 else "Alex"

    # Strategy 1: Test Gemini Native TTS API (supported on Google AI Studio keys)
    print(f"\n🎙️ Synthesizing {len(turns)} turns with Google Neural TTS...")
    
    use_gemini = False
    alex_gemini_voice = "Aoede"   # Lively, articulate female voice
    jordan_gemini_voice = "Charon" # Deep, analytical, grounded male voice

    try:
        # Quick ping test on turn 0
        test_pcm = synthesize_gemini_turn("Testing connection.", alex_gemini_voice, api_key)
        if test_pcm:
            use_gemini = True
            print("✨ Connected to Google Gemini Neural TTS engine (voices: 'Aoede' & 'Charon').")
    except Exception as gemini_err:
        pass

    if use_gemini:
        pcm_chunks = []
        import wave
        import hashlib
        pause_bytes = b"\x00" * int(24000 * 0.35 * 2) # 350ms silence at 24kHz

        # Persistent disk cache directory for turns
        cache_id = hashlib.md5(str(output_audio).encode("utf-8")).hexdigest()[:10]
        cache_dir = Path(tempfile.gettempdir()) / f"gemini_podcast_{cache_id}"
        cache_dir.mkdir(parents=True, exist_ok=True)

        for idx, turn in enumerate(turns):
            is_host1 = turn["speaker"].lower().startswith(host1.lower()[:3])
            v_name = alex_gemini_voice if is_host1 else jordan_gemini_voice
            cached_turn_path = cache_dir / f"turn_{idx:03d}_{v_name}.raw"

            if cached_turn_path.exists():
                chunk = cached_turn_path.read_bytes()
                print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']} ({v_name}) [cached]", flush=True)
            else:
                print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']} ({v_name}): \"{turn['clean_speech'][:40]}...\"", flush=True)
                chunk = synthesize_gemini_turn(turn["clean_speech"], v_name, api_key)
                cached_turn_path.write_bytes(chunk)
                # Pacing between turns to stay comfortably within rate limits
                time.sleep(5.0)

            pcm_chunks.append(chunk)

        print(f"\n✅ All {len(turns)} turns synthesized via Google Gemini Neural TTS.")
        
        temp_wav = output_audio.with_suffix(".wav")
        with wave.open(str(temp_wav), "wb") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(24000)
            for idx, chunk in enumerate(pcm_chunks):
                f.writeframes(chunk)
                if idx < len(pcm_chunks) - 1:
                    f.writeframes(pause_bytes)

        # Convert to M4A/AAC on macOS or keep target
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        if output_audio.suffix.lower() == ".m4a" or sys.platform == "darwin":
            target_m4a = output_audio.with_suffix(".m4a")
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", str(temp_wav), str(target_m4a)], check=False)
            if target_m4a.exists():
                temp_wav.unlink(missing_ok=True)
                print(f"🎉 Saved complete Google Gemini podcast audio: {target_m4a}")
                return True

        print(f"🎉 Saved complete Google Gemini podcast audio: {temp_wav}")
        return True

    # Strategy 2: Google Cloud Text-to-Speech API (Journey -> Neural2)
    print("✨ Using Google Cloud Text-to-Speech API...")
    host1_voices = ["en-US-Journey-F", "en-US-Neural2-F", "en-US-Studio-O", "en-US-Standard-C"]
    host2_voices = ["en-US-Journey-D", "en-US-Neural2-D", "en-US-Studio-Q", "en-US-Standard-B"]

    mp3_chunks = []
    active_v1 = None
    active_v2 = None
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"

    def call_cloud_tts_api(text: str, voice_candidates: list[str]) -> tuple[bytes, str]:
        for voice_name in voice_candidates:
            payload = {
                "input": {"text": text},
                "voice": {"languageCode": "en-US", "name": voice_name},
                "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0, "pitch": 0.0}
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    audio_b64 = resp_data.get("audioContent", "")
                    if audio_b64:
                        return base64.b64decode(audio_b64), voice_name
            except urllib.error.HTTPError as e:
                if e.code == 400:
                    continue
                raise e
        raise RuntimeError("Failed to synthesize with any of the requested Google Cloud voices.")

    try:
        for idx, turn in enumerate(turns):
            is_host1 = turn["speaker"].lower().startswith(host1.lower()[:3])
            candidates = [active_v1] if (is_host1 and active_v1) else ([active_v2] if (not is_host1 and active_v2) else (host1_voices if is_host1 else host2_voices))
            
            print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']}: \"{turn['clean_speech'][:45]}...\"", end="\r", flush=True)
            chunk, used_voice = call_cloud_tts_api(turn["clean_speech"], candidates)
            if is_host1 and not active_v1:
                active_v1 = used_voice
            elif not is_host1 and not active_v2:
                active_v2 = used_voice
            mp3_chunks.append(chunk)

        print(f"\n✅ All {len(turns)} turns synthesized using Google Cloud voices '{active_v1}' & '{active_v2}'.")
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        with open(output_audio, "wb") as f:
            for chunk in mp3_chunks:
                f.write(chunk)

        print(f"🎉 Saved complete Google Cloud podcast audio: {output_audio}")
        return True
    except Exception as ex:
        print(f"\n❌ Google TTS synthesis error: {ex}")
        return False


# ==============================================================================
# Voice Synthesis Backend 2: Microsoft Edge Neural TTS
# ==============================================================================

def synthesize_edge_tts(turns: list[dict], output_audio: Path) -> bool:
    """
    Synthesizes dialogue turns using Microsoft Edge free neural voices (en-US-AvaNeural / en-US-AndrewNeural).
    """
    speakers = sorted(list({t["speaker"] for t in turns}))
    host1 = speakers[0] if len(speakers) > 0 else "Alex"

    voice1 = "en-US-AvaNeural"
    voice2 = "en-US-AndrewNeural"

    # Check if edge-tts CLI or module exists
    has_cli = bool(shutil.which("edge-tts"))
    has_module = False
    if not has_cli:
        try:
            import edge_tts
            has_module = True
        except ImportError:
            pass

    if not has_cli and not has_module:
        print("📦 Microsoft Edge TTS requires the 'edge-tts' package.")
        print("Install via: pip install edge-tts")
        return False

    temp_dir = Path(tempfile.mkdtemp(prefix="podcast_edge_"))
    mp3_files = []

    print(f"\n🎙️ Synthesizing {len(turns)} turns with Microsoft Edge Neural TTS ('{voice1}' & '{voice2}')...")

    try:
        for idx, turn in enumerate(turns):
            is_host1 = turn["speaker"].lower().startswith(host1.lower()[:3])
            voice = voice1 if is_host1 else voice2
            clip_path = temp_dir / f"clip_{idx:04d}.mp3"

            text = turn["clean_speech"]
            print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']}: \"{text[:45]}...\"", end="\r", flush=True)

            if has_cli:
                subprocess.run(["edge-tts", "--voice", voice, "--text", text, "--write-media", str(clip_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run([sys.executable, "-m", "edge_tts", "--voice", voice, "--text", text, "--write-media", str(clip_path)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
            mp3_files.append(clip_path)

        print(f"\n✅ All {len(turns)} turns synthesized.")
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        with open(output_audio, "wb") as outfile:
            for clip in mp3_files:
                with open(clip, "rb") as infile:
                    outfile.write(infile.read())

        print(f"🎉 Saved complete Edge Neural podcast: {output_audio}")
        return True
    except Exception as ex:
        print(f"\n❌ Edge TTS synthesis error: {ex}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# Voice Synthesis Backend 3: ElevenLabs Studio TTS
# ==============================================================================

def synthesize_elevenlabs_tts(turns: list[dict], output_audio: Path, api_key: str) -> bool:
    """
    Synthesizes dialogue turns using ElevenLabs API (Rachel & Adam voices).
    """
    if not api_key:
        print("Error: ELEVENLABS_API_KEY is required for ElevenLabs synthesis.")
        return False

    speakers = sorted(list({t["speaker"] for t in turns}))
    host1 = speakers[0] if len(speakers) > 0 else "Alex"

    # Default voice IDs: Rachel (Female) & Adam (Male)
    voice_rachel = "21m00Tcm4TlvDq8ikWAM"
    voice_adam = "pNInz6obpgDQGcFmaJgB"

    print(f"\n🎙️ Synthesizing {len(turns)} turns with ElevenLabs Studio Voices...")

    mp3_chunks = []
    try:
        for idx, turn in enumerate(turns):
            is_host1 = turn["speaker"].lower().startswith(host1.lower()[:3])
            voice_id = voice_rachel if is_host1 else voice_adam
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

            payload = {
                "text": turn["clean_speech"],
                "model_id": "eleven_monolingual_v1",
                "voice_settings": {
                    "stability": 0.5,
                    "similarity_boost": 0.75
                }
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "xi-api-key": api_key
                }
            )
            print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']}: \"{turn['clean_speech'][:45]}...\"", end="\r", flush=True)
            with urllib.request.urlopen(req, timeout=30) as resp:
                mp3_chunks.append(resp.read())

        print(f"\n✅ All {len(turns)} turns synthesized.")
        output_audio.parent.mkdir(parents=True, exist_ok=True)
        with open(output_audio, "wb") as f:
            for chunk in mp3_chunks:
                f.write(chunk)

        print(f"🎉 Saved complete ElevenLabs podcast: {output_audio}")
        return True
    except Exception as ex:
        print(f"\n❌ ElevenLabs synthesis error: {ex}")
        return False


# ==============================================================================
# Voice Synthesis Backend 4: macOS Native Speech (say + afconvert)
# ==============================================================================

def synthesize_macos_say(turns: list[dict], output_audio: Path) -> bool:
    """Synthesizes physical audio using macOS native `say` and `afconvert` with natural pauses."""
    if sys.platform != "darwin":
        print("macOS native speech is only available on Apple macOS.")
        return False
    if not shutil.which("say") or not shutil.which("afconvert"):
        print("macOS say/afconvert tools not found.")
        return False

    speakers = sorted(list({t["speaker"] for t in turns}))
    host1 = speakers[0] if len(speakers) > 0 else "Alex"
    
    res = subprocess.run(["say", "-v", "?"], stdout=subprocess.PIPE, text=True)
    available_voices = res.stdout.lower()

    voice1 = "Samantha" if "samantha" in available_voices else "Victoria"
    voice2 = "Daniel" if "daniel" in available_voices else ("Alex" if "alex" in available_voices else "Fred")

    temp_dir = Path(tempfile.mkdtemp(prefix="podcast_macos_"))
    print(f"\n🎙️ Synthesizing {len(turns)} turns on macOS using voices '{voice1}' & '{voice2}'...")

    try:
        import wave
        clip_wavs = []
        for idx, turn in enumerate(turns):
            is_host1 = turn["speaker"].lower().startswith(host1.lower()[:3])
            voice = voice1 if is_host1 else voice2
            clip_path = temp_dir / f"clip_{idx:04d}.wav"

            text = turn["clean_speech"]
            print(f"  [{idx + 1}/{len(turns)}] {turn['speaker']}: \"{text[:45]}...\"", end="\r", flush=True)
            subprocess.run(["say", "-v", voice, "-o", str(clip_path), "--data-format=LEI16@22050", text], check=True)
            clip_wavs.append(clip_path)

        combined_wav = temp_dir / "combined.wav"
        pause_bytes = b"\x00" * int(22050 * 0.35 * 2)

        with wave.open(str(combined_wav), "wb") as outfile:
            for idx, clip in enumerate(clip_wavs):
                with wave.open(str(clip), "rb") as infile:
                    if idx == 0:
                        outfile.setparams(infile.getparams())
                    outfile.writeframes(infile.readframes(infile.getnframes()))
                    if idx < len(clip_wavs) - 1:
                        outfile.writeframes(pause_bytes)

        output_audio.parent.mkdir(parents=True, exist_ok=True)
        target_ext = output_audio.suffix.lower()
        if target_ext == ".m4a":
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", str(combined_wav), str(output_audio)], check=True)
        elif target_ext == ".wav":
            shutil.copyfile(combined_wav, output_audio)
        else:
            subprocess.run(["afconvert", "-f", "m4af", "-d", "aac", str(combined_wav), str(output_audio.with_suffix(".m4a"))], check=True)

        print(f"\n🎉 Saved complete macOS podcast audio: {output_audio}")
        return True
    except Exception as ex:
        print(f"\n❌ macOS synthesis error: {ex}")
        return False
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


# ==============================================================================
# Interactive HTML5 Web Player Generator
# ==============================================================================

def generate_interactive_html(meta: dict, turns: list[dict], output_html: Path, audio_filename: str = None) -> str:
    """Creates a standalone interactive HTML5 audio/speech player matching NotebookLM aesthetic."""
    title = meta.get("title", output_html.stem.replace("-", " ").title())
    desc = meta.get("description", "A two-host conversational deep dive audio overview.")
    
    speakers = sorted(list({t["speaker"] for t in turns}))
    host1 = speakers[0] if len(speakers) > 0 else "Alex"
    host2 = speakers[1] if len(speakers) > 1 else "Jordan"

    turns_json = json.dumps(turns, indent=2)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title} - NotebookLM Audio Overview</title>
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #38bdf8;
      --accent-glow: rgba(56, 189, 248, 0.25);
      --host1-color: #38bdf8;
      --host2-color: #4ade80;
      --highlight: #2dd4bf;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.6;
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }}
    header {{
      background: rgba(30, 41, 59, 0.85);
      backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      z-index: 10;
    }}
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      background: rgba(56, 189, 248, 0.15);
      color: var(--accent);
      padding: 4px 10px;
      border-radius: 9999px;
      font-size: 0.75rem;
      font-weight: 600;
      letter-spacing: 0.05em;
      text-transform: uppercase;
    }}
    .header-info h1 {{
      font-size: 1.25rem;
      font-weight: 700;
      margin-top: 4px;
    }}
    .header-info p {{
      font-size: 0.85rem;
      color: var(--text-muted);
      max-width: 650px;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }}
    .hosts-container {{
      display: flex;
      gap: 12px;
    }}
    .host-pill {{
      display: flex;
      align-items: center;
      gap: 8px;
      background: var(--card-bg);
      padding: 6px 14px;
      border-radius: 20px;
      border: 1px solid var(--border);
      font-size: 0.85rem;
      transition: all 0.3s ease;
    }}
    .host-pill.active {{
      border-color: var(--accent);
      box-shadow: 0 0 12px var(--accent-glow);
    }}
    .avatar {{
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 0.75rem;
      font-weight: bold;
    }}
    .avatar.host1 {{ background: var(--host1-color); color: #0f172a; }}
    .avatar.host2 {{ background: var(--host2-color); color: #0f172a; }}

    main {{
      flex: 1;
      overflow-y: auto;
      padding: 32px 24px 140px;
      scroll-behavior: smooth;
    }}
    .transcript {{
      max-width: 820px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }}
    .turn {{
      display: flex;
      gap: 16px;
      padding: 16px;
      border-radius: 12px;
      background: rgba(30, 41, 59, 0.4);
      border: 1px solid transparent;
      transition: all 0.25s ease;
      cursor: pointer;
    }}
    .turn:hover {{
      background: rgba(30, 41, 59, 0.8);
      border-color: rgba(56, 189, 248, 0.3);
    }}
    .turn.active {{
      background: rgba(30, 41, 59, 0.95);
      border-color: var(--accent);
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
      transform: scale(1.01);
    }}
    .turn-time {{
      font-size: 0.75rem;
      font-family: monospace;
      color: var(--text-muted);
      min-width: 45px;
      padding-top: 4px;
    }}
    .turn-body {{
      flex: 1;
    }}
    .turn-speaker {{
      font-weight: 700;
      font-size: 0.95rem;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 8px;
    }}
    .turn-speaker.host1 {{ color: var(--host1-color); }}
    .turn-speaker.host2 {{ color: var(--host2-color); }}
    .turn-tone {{
      font-size: 0.75rem;
      font-style: italic;
      color: var(--text-muted);
      font-weight: normal;
    }}
    .turn-text {{
      font-size: 1rem;
      color: #cbd5e1;
    }}
    .turn.active .turn-text {{
      color: #ffffff;
      font-weight: 500;
    }}

    footer.player-bar {{
      position: fixed;
      bottom: 0;
      left: 0;
      right: 0;
      background: rgba(15, 23, 42, 0.95);
      backdrop-filter: blur(16px);
      border-top: 1px solid var(--border);
      padding: 16px 24px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      z-index: 100;
    }}
    .scrub-container {{
      display: flex;
      align-items: center;
      gap: 12px;
      max-width: 900px;
      width: 100%;
      margin: 0 auto;
    }}
    .scrub-bar {{
      flex: 1;
      height: 6px;
      background: var(--border);
      border-radius: 3px;
      position: relative;
      cursor: pointer;
    }}
    .scrub-progress {{
      height: 100%;
      background: linear-gradient(90deg, var(--host1-color), var(--host2-color));
      border-radius: 3px;
      width: 0%;
      transition: width 0.1s linear;
    }}
    .controls {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      max-width: 900px;
      width: 100%;
      margin: 0 auto;
    }}
    .btn-circle {{
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background: var(--accent);
      color: #0f172a;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
      font-weight: bold;
      font-size: 1.2rem;
      box-shadow: 0 0 16px var(--accent-glow);
      transition: transform 0.2s ease;
    }}
    .btn-circle:hover {{
      transform: scale(1.08);
    }}
    .btn-secondary {{
      background: transparent;
      border: 1px solid var(--border);
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 8px;
      font-size: 0.85rem;
      cursor: pointer;
      transition: all 0.2s ease;
    }}
    .btn-secondary:hover {{
      color: var(--text);
      border-color: var(--text);
    }}
    .waveform {{
      display: flex;
      align-items: center;
      gap: 3px;
      height: 24px;
    }}
    .waveform-bar {{
      width: 3px;
      height: 8px;
      background: var(--accent);
      border-radius: 2px;
      transition: height 0.15s ease;
    }}
    .playing .waveform-bar {{
      animation: wave 1s ease-in-out infinite alternate;
    }}
    .playing .waveform-bar:nth-child(2) {{ animation-delay: 0.15s; }}
    .playing .waveform-bar:nth-child(3) {{ animation-delay: 0.3s; }}
    .playing .waveform-bar:nth-child(4) {{ animation-delay: 0.45s; }}
    .playing .waveform-bar:nth-child(5) {{ animation-delay: 0.6s; }}
    @keyframes wave {{
      0% {{ height: 6px; }}
      100% {{ height: 22px; }}
    }}
  </style>
</head>
<body>

  <header>
    <div class="header-info">
      <div class="badge">🎙️ NotebookLM Deep Dive Overview</div>
      <h1>{title}</h1>
      <p>{desc}</p>
    </div>
    <div class="hosts-container">
      <div class="host-pill" id="pill-{host1}">
        <div class="avatar host1">{host1[0]}</div>
        <span>{host1}</span>
      </div>
      <div class="host-pill" id="pill-{host2}">
        <div class="avatar host2">{host2[0]}</div>
        <span>{host2}</span>
      </div>
    </div>
  </header>

  <main>
    <div class="transcript" id="transcript"></div>
  </main>

  <footer class="player-bar">
    <div class="scrub-container">
      <span id="time-current" style="font-size: 0.75rem; font-family: monospace; color: var(--text-muted);">00:00</span>
      <div class="scrub-bar" id="scrub-bar">
        <div class="scrub-progress" id="scrub-progress"></div>
      </div>
      <span id="time-total" style="font-size: 0.75rem; font-family: monospace; color: var(--text-muted);">--:--</span>
    </div>

    <div class="controls">
      <div class="waveform" id="waveform">
        <div class="waveform-bar"></div>
        <div class="waveform-bar"></div>
        <div class="waveform-bar"></div>
        <div class="waveform-bar"></div>
        <div class="waveform-bar"></div>
      </div>

      <div style="display: flex; align-items: center; gap: 16px;">
        <button class="btn-secondary" id="btn-prev">⏮️</button>
        <button class="btn-circle" id="btn-play">▶</button>
        <button class="btn-secondary" id="btn-next">⏭️</button>
      </div>

      <div style="display: flex; align-items: center; gap: 8px;">
        <button class="btn-secondary" id="btn-speed">1.0x</button>
        <button class="btn-secondary" id="btn-restart">↺ Restart</button>
      </div>
    </div>
  </footer>

  <script>
    const TURNS = {turns_json};
    const HOST1 = "{host1}";
    const HOST2 = "{host2}";
    const AUDIO_FILE = "{audio_filename or ''}";

    let currentTurnIndex = 0;
    let isPlaying = false;
    let playbackRate = 1.0;
    const speeds = [0.8, 1.0, 1.25, 1.5, 2.0];
    
    // Audio engine: Real audio track or browser Web Speech API
    let audioElem = AUDIO_FILE ? new Audio(AUDIO_FILE) : null;
    let synth = window.speechSynthesis;
    let currentUtterance = null;

    const transcriptEl = document.getElementById("transcript");
    TURNS.forEach((turn, idx) => {{
      const div = document.createElement("div");
      div.className = "turn";
      div.id = `turn-${{idx}}`;
      div.onclick = () => jumpToTurn(idx);

      const isHost1 = turn.speaker.toLowerCase().includes(HOST1.toLowerCase());
      const speakerClass = isHost1 ? "host1" : "host2";

      div.innerHTML = `
        <div class="turn-time">${{turn.timestamp || "00:00"}}</div>
        <div class="turn-body">
          <div class="turn-speaker ${{speakerClass}}">
            ${{turn.speaker}}
            ${{turn.tone ? `<span class="turn-tone">[${{turn.tone}}]</span>` : ""}}
          </div>
          <div class="turn-text">${{turn.raw_text}}</div>
        </div>
      `;
      transcriptEl.appendChild(div);
    }});

    function formatTime(secs) {{
      const m = Math.floor(secs / 60);
      const s = Math.floor(secs % 60);
      return `${{m.toString().padStart(2, '0')}}:${{s.toString().padStart(2, '0')}}`;
    }}

    function updateActiveUI(idx) {{
      document.querySelectorAll(".turn").forEach((el, i) => {{
        el.classList.toggle("active", i === idx);
      }});
      
      const activeEl = document.getElementById(`turn-${{idx}}`);
      if (activeEl) {{
        activeEl.scrollIntoView({{ behavior: "smooth", block: "center" }});
      }}

      const turn = TURNS[idx];
      if (turn) {{
        const isHost1 = turn.speaker.toLowerCase().includes(HOST1.toLowerCase());
        document.getElementById(`pill-${{HOST1}}`).classList.toggle("active", isHost1);
        document.getElementById(`pill-${{HOST2}}`).classList.toggle("active", !isHost1);
      }}
    }}

    // Real Audio Track Handling
    if (audioElem) {{
      audioElem.onloadedmetadata = () => {{
        document.getElementById("time-total").innerText = formatTime(audioElem.duration);
      }};

      audioElem.ontimeupdate = () => {{
        const curr = audioElem.currentTime;
        document.getElementById("time-current").innerText = formatTime(curr);
        const dur = audioElem.duration || 1;
        document.getElementById("scrub-progress").style.width = `${{(curr / dur) * 100}}%`;

        // Sync turn with timestamps
        for (let i = TURNS.length - 1; i >= 0; i--) {{
          if (curr >= (TURNS[i].seconds || 0)) {{
            if (currentTurnIndex !== i) {{
              currentTurnIndex = i;
              updateActiveUI(i);
            }}
            break;
          }}
        }}
      }};

      audioElem.onended = () => {{
        stopPlayback();
      }};
    }}

    // Browser Speech Synthesis Fallback Setup
    let voices = [];
    function loadVoices() {{
      if (synth) voices = synth.getVoices();
    }}
    if (synth) {{
      loadVoices();
      if (speechSynthesis.onvoiceschanged !== undefined) {{
        speechSynthesis.onvoiceschanged = loadVoices;
      }}
    }}

    function getVoiceForSpeaker(speaker) {{
      if (!voices.length) return null;
      const isHost1 = speaker.toLowerCase().includes(HOST1.toLowerCase());
      const englishVoices = voices.filter(v => v.lang.startsWith("en"));
      if (!englishVoices.length) return voices[0];
      if (isHost1) {{
        return englishVoices.find(v => v.name.toLowerCase().includes("samantha") || v.name.toLowerCase().includes("female") || v.name.toLowerCase().includes("zira")) || englishVoices[0];
      }} else {{
        return englishVoices.find(v => v.name.toLowerCase().includes("daniel") || v.name.toLowerCase().includes("david") || v.name.toLowerCase().includes("alex") || v.name.toLowerCase().includes("male")) || englishVoices[1] || englishVoices[0];
      }}
    }}

    function playTurnSpeech(idx) {{
      if (idx >= TURNS.length) {{
        stopPlayback();
        return;
      }}
      currentTurnIndex = idx;
      updateActiveUI(idx);
      document.getElementById("time-current").innerText = TURNS[idx].timestamp || "00:00";
      document.getElementById("scrub-progress").style.width = `${{((idx + 1) / TURNS.length) * 100}}%`;

      synth.cancel();
      const turn = TURNS[idx];
      currentUtterance = new SpeechSynthesisUtterance(turn.clean_speech);
      const voice = getVoiceForSpeaker(turn.speaker);
      if (voice) currentUtterance.voice = voice;
      currentUtterance.rate = playbackRate;
      currentUtterance.pitch = turn.speaker.toLowerCase().includes(HOST1.toLowerCase()) ? 1.05 : 0.95;

      currentUtterance.onend = () => {{
        if (isPlaying) {{
          setTimeout(() => playTurnSpeech(currentTurnIndex + 1), 350 / playbackRate);
        }}
      }};
      currentUtterance.onerror = () => {{
        if (isPlaying) playTurnSpeech(currentTurnIndex + 1);
      }};
      synth.speak(currentUtterance);
    }}

    function startPlayback() {{
      isPlaying = true;
      document.getElementById("btn-play").innerText = "⏸";
      document.getElementById("waveform").classList.add("playing");

      if (audioElem) {{
        audioElem.playbackRate = playbackRate;
        audioElem.play();
      }} else {{
        playTurnSpeech(currentTurnIndex);
      }}
    }}

    function stopPlayback() {{
      isPlaying = false;
      document.getElementById("btn-play").innerText = "▶";
      document.getElementById("waveform").classList.remove("playing");
      if (audioElem) {{
        audioElem.pause();
      }} else if (synth) {{
        synth.cancel();
      }}
    }}

    function jumpToTurn(idx) {{
      currentTurnIndex = idx;
      updateActiveUI(idx);
      if (audioElem) {{
        const targetSecs = TURNS[idx].seconds || 0;
        audioElem.currentTime = targetSecs;
        if (!isPlaying) startPlayback();
      }} else {{
        if (isPlaying) playTurnSpeech(idx);
      }}
    }}

    document.getElementById("btn-play").onclick = () => {{
      if (isPlaying) stopPlayback();
      else startPlayback();
    }};

    document.getElementById("btn-prev").onclick = () => {{
      jumpToTurn(Math.max(0, currentTurnIndex - 1));
    }};

    document.getElementById("btn-next").onclick = () => {{
      jumpToTurn(Math.min(TURNS.length - 1, currentTurnIndex + 1));
    }};

    document.getElementById("btn-restart").onclick = () => {{
      if (audioElem) audioElem.currentTime = 0;
      jumpToTurn(0);
      if (!isPlaying) startPlayback();
    }};

    document.getElementById("btn-speed").onclick = (e) => {{
      const currIdx = speeds.indexOf(playbackRate);
      playbackRate = speeds[(currIdx + 1) % speeds.length];
      e.target.innerText = `${{playbackRate}}x`;
      if (audioElem) audioElem.playbackRate = playbackRate;
      else if (isPlaying) playTurnSpeech(currentTurnIndex);
    }};

    document.getElementById("scrub-bar").onclick = (e) => {{
      const rect = e.target.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      if (audioElem && audioElem.duration) {{
        audioElem.currentTime = pct * audioElem.duration;
      }} else {{
        const targetIdx = Math.floor(pct * TURNS.length);
        jumpToTurn(Math.max(0, Math.min(TURNS.length - 1, targetIdx)));
      }}
    }};

    window.addEventListener("keydown", (e) => {{
      if (e.code === "Space") {{
        e.preventDefault();
        if (isPlaying) stopPlayback();
        else startPlayback();
      }} else if (e.code === "ArrowRight") {{
        jumpToTurn(Math.min(TURNS.length - 1, currentTurnIndex + 1));
      }} else if (e.code === "ArrowLeft") {{
        jumpToTurn(Math.max(0, currentTurnIndex - 1));
      }}
    }});
  </script>
</body>
</html>
"""
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(html, encoding="utf-8")
    return str(output_html)


# ==============================================================================
# Interactive Voice Backend Selector CLI
# ==============================================================================

def prompt_user_for_backend(repo_root: Path) -> tuple[str, dict]:
    """Prompts the user interactively to choose a voice engine."""
    load_env_file(repo_root)
    has_google = bool(os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY"))
    has_eleven = bool(os.environ.get("ELEVENLABS_API_KEY"))

    print("\n" + "=" * 62)
    print("🎙️  NOTEBOOKLM AUDIO OVERVIEW: SELECT VOICE SYNTHESIS ENGINE")
    print("=" * 62)
    g_tag = " [API Key Detected]" if has_google else " [Requires GOOGLE_API_KEY]"
    e_tag = " [API Key Detected]" if has_eleven else " [Requires ELEVENLABS_API_KEY]"
    
    print(f"  1) Google Cloud / Gemini Neural TTS{g_tag}")
    print("  2) Microsoft Edge Neural TTS (Free, high-fidelity neural, no key needed)")
    print(f"  3) ElevenLabs Studio Voices{e_tag}")
    if sys.platform == "darwin":
        print("  4) macOS Native System Voices (Samantha & Daniel, offline, zero setup)")
        print("  5) Interactive Web Player Only (Browser Web Speech API, zero install)")
    else:
        print("  4) Interactive Web Player Only (Browser Web Speech API, zero install)")
    print("-" * 62)

    default_choice = "1" if has_google else "2"
    choice = input(f"Select engine [1-5] (default: {default_choice}): ").strip() or default_choice

    config = {}
    if choice == "1":
        engine = "google"
        key = get_google_api_key()
        if not key:
            key = input("Enter your Google API Key: ").strip()
            if key:
                save_prompt = input("Save to .env for future episodes? [Y/n]: ").strip().lower()
                if save_prompt != "n":
                    env_path = repo_root / ".env"
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\nGOOGLE_API_KEY={key}\n")
                    print(f"💾 Saved key to {env_path} (git-ignored).")
        config["api_key"] = key
    elif choice == "2":
        engine = "edge"
    elif choice == "3":
        engine = "elevenlabs"
        key = get_elevenlabs_api_key()
        if not key:
            key = input("Enter your ElevenLabs API Key: ").strip()
            if key:
                save_prompt = input("Save to .env for future episodes? [Y/n]: ").strip().lower()
                if save_prompt != "n":
                    env_path = repo_root / ".env"
                    with open(env_path, "a", encoding="utf-8") as f:
                        f.write(f"\nELEVENLABS_API_KEY={key}\n")
        config["api_key"] = key
    elif choice == "4":
        engine = "macos" if sys.platform == "darwin" else "web"
    else:
        engine = "web"

    return engine, config


def main():
    parser = argparse.ArgumentParser(description="Synthesize podcast audio and interactive web players for OKF episodes.")
    parser.add_argument("episode", help="Path to markdown podcast episode file")
    parser.add_argument("--backend", choices=["google", "edge", "elevenlabs", "macos", "web", "auto"],
                        help="Voice synthesis engine to use (default: interactive prompt)")
    parser.add_argument("--api-key", help="API key for Google Cloud TTS or ElevenLabs")
    parser.add_argument("--html", action="store_true", help="Generate standalone interactive HTML player only")
    parser.add_argument("--open", action="store_true", help="Open generated HTML player in default browser")
    parser.add_argument("--output", help="Custom output path for generated HTML or audio")
    
    args = parser.parse_args()

    episode_path = Path(args.episode).resolve()
    if not episode_path.exists():
        print(f"Error: Episode file not found at {episode_path}")
        sys.exit(1)

    content = episode_path.read_text(encoding="utf-8")
    meta, turns = parse_dialogue_turns(content)

    if not turns:
        print(f"Error: No conversational dialogue turns found in {episode_path}.")
        print("Ensure lines follow the format: **[00:00] Alex:** [tone] Dialogue text...")
        sys.exit(1)

    print(f"📋 Parsed episode '{meta.get('title', episode_path.stem)}' ({len(turns)} turns).")

    backend = args.backend
    config = {"api_key": args.api_key}

    # If backend not explicitly provided and running in interactive terminal
    if not backend:
        if args.html:
            backend = "web"
        elif sys.stdin.isatty():
            backend, config = prompt_user_for_backend(REPO_ROOT)
        else:
            # Non-interactive default: Google if key present, else Edge, else macOS
            if get_google_api_key(args.api_key):
                backend = "google"
                config["api_key"] = get_google_api_key(args.api_key)
            elif sys.platform == "darwin":
                backend = "macos"
            else:
                backend = "edge"

    audio_file_generated = None
    
    if backend == "google":
        key = config.get("api_key") or get_google_api_key(args.api_key)
        audio_target = Path(args.output) if args.output else episode_path.with_suffix(".mp3")
        success = synthesize_google_tts(turns, audio_target, key)
        if success:
            audio_file_generated = audio_target
        else:
            print("\n⚠️ Google Neural TTS quota was exceeded or unavailable.")
            if not episode_path.with_suffix(".mp3").exists():
                print("🔄 Gracefully falling back to Microsoft Edge Neural TTS...")
                success_edge = synthesize_edge_tts(turns, audio_target)
                if success_edge:
                    audio_file_generated = audio_target
    elif backend == "edge":
        audio_target = Path(args.output) if args.output else episode_path.with_suffix(".mp3")
        success = synthesize_edge_tts(turns, audio_target)
        if success:
            audio_file_generated = audio_target
    elif backend == "elevenlabs":
        key = config.get("api_key") or get_elevenlabs_api_key(args.api_key)
        audio_target = Path(args.output) if args.output else episode_path.with_suffix(".mp3")
        success = synthesize_elevenlabs_tts(turns, audio_target, key)
        if success:
            audio_file_generated = audio_target
    elif backend == "macos":
        audio_target = Path(args.output) if args.output else episode_path.with_suffix(".m4a")
        success = synthesize_macos_say(turns, audio_target)
        if success:
            audio_file_generated = audio_target
    elif backend == "web":
        print("🌐 Selected Web Player Only (Browser Web Speech API).")

    # Generate interactive HTML player linked to the generated audio track (or Web Speech)
    html_target = episode_path.with_suffix(".html")
    audio_rel = audio_file_generated.name if audio_file_generated else (episode_path.with_suffix(".mp3").name if episode_path.with_suffix(".mp3").exists() else (episode_path.with_suffix(".m4a").name if episode_path.with_suffix(".m4a").exists() else None))
    generate_interactive_html(meta, turns, html_target, audio_filename=audio_rel)
    print(f"🎧 Interactive NotebookLM player ready: file://{html_target.resolve()}")

    if args.open:
        subprocess.run(["open", str(html_target)])


if __name__ == "__main__":
    main()
