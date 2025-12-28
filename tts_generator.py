#!/usr/bin/env python3
"""
TTS Generator - Convert long text to speech using multiple TTS engines.

Usage:
    python tts_generator.py "Your long text here"
    python tts_generator.py -f input.txt -o output.mp3
    python tts_generator.py "Text" --voice male --format mp3
    python tts_generator.py "Text" --voice sven --engine openaudio --lang de
    cat document.txt | python tts_generator.py -o speech.flac
    
Voices:
    female (default): af_heart (Kokoro)
    male: am_adam (Kokoro)
    sven: Cloned voice (openaudio, xtts, chatterbox)
    Or any specific voice ID
    
Engines:
    kokoro (default): Fastest, best quality preset voices
    openaudio: Best for voice cloning, supports "sven"
    xtts: Good multilingual, supports "sven"
    chatterbox: Expressive, supports "sven"

Languages:
    en (default), de, fr, es, it, pt, nl, pl, ru, zh, ja, ko, ar
"""

import argparse
import requests
import sys
import os
import tempfile
import subprocess
from pathlib import Path
import re
import time

# Server configuration
SERVERS = {
    "kokoro": "http://10.200.0.12:8769",
    "openaudio": "http://10.200.0.12:8770",
    "xtts": "http://10.200.0.12:8766",
    "chatterbox": "http://10.200.0.12:8767",
}

# Voice presets
VOICE_PRESETS = {
    "female": "af_heart",
    "male": "am_adam",
    "female_british": "bf_emma",
    "male_british": "bm_george",
}

# Kokoro voices (preset only, no cloning)
KOKORO_VOICES = [
    "af_heart", "af_nova", "af_bella", "af_sarah", "af_nicole",
    "bf_emma", "bf_isabella", "am_adam", "am_michael", "bm_george", "bm_lewis"
]

# Maximum characters per chunk
MAX_CHUNK_SIZE = 500


def split_text_into_chunks(text, max_size=MAX_CHUNK_SIZE):
    """Split text into chunks at sentence boundaries."""
    text = re.sub(r'\s+', ' ', text.strip())
    
    if len(text) <= max_size:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    sentences = re.split(r'(?<=[.!?])\s+', text)
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_size:
            current_chunk = (current_chunk + " " + sentence).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
            
            if len(sentence) > max_size:
                parts = re.split(r'(?<=[,;:])\s+', sentence)
                temp_chunk = ""
                for part in parts:
                    if len(temp_chunk) + len(part) + 1 <= max_size:
                        temp_chunk = (temp_chunk + " " + part).strip()
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        if len(part) > max_size:
                            words = part.split()
                            temp_chunk = ""
                            for word in words:
                                if len(temp_chunk) + len(word) + 1 <= max_size:
                                    temp_chunk = (temp_chunk + " " + word).strip()
                                else:
                                    if temp_chunk:
                                        chunks.append(temp_chunk)
                                    temp_chunk = word
                        else:
                            temp_chunk = part
                if temp_chunk:
                    current_chunk = temp_chunk
                else:
                    current_chunk = ""
            else:
                current_chunk = sentence
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def generate_tts_kokoro(text, voice="af_heart", speed=1.0):
    """Generate TTS using Kokoro engine."""
    url = f"{SERVERS['kokoro']}/tts"
    payload = {
        "text": text,
        "voice": voice,
        "speed": speed
    }
    
    response = requests.post(url, json=payload, timeout=60)
    if response.status_code == 200 and len(response.content) > 100:
        return response.content
    else:
        raise Exception(f"Kokoro TTS failed: {response.status_code} - {response.text[:200]}")


def generate_tts_openaudio(text, voice="sven", temperature=0.3, top_p=0.7):
    """Generate TTS using OpenAudio engine."""
    url = f"{SERVERS['openaudio']}/v1/tts"
    payload = {
        "text": text,
        "format": "wav",
        "temperature": temperature,
        "top_p": top_p,
        "reference_id": voice
    }
    
    response = requests.post(url, json=payload, timeout=180)
    if response.status_code == 200 and len(response.content) > 100:
        return response.content
    else:
        raise Exception(f"OpenAudio TTS failed: {response.status_code} - {response.text[:200]}")


def generate_tts_xtts(text, voice="sven", language="en"):
    """Generate TTS using XTTS engine."""
    url = f"{SERVERS['xtts']}/tts"
    payload = {
        "text": text,
        "voice": voice,
        "language": language
    }
    
    response = requests.post(url, json=payload, timeout=120)
    if response.status_code == 200 and len(response.content) > 100:
        return response.content
    else:
        raise Exception(f"XTTS TTS failed: {response.status_code} - {response.text[:200]}")


def generate_tts_chatterbox(text, voice="sven", exaggeration=0.15, cfg_weight=0.9, temperature=0.3):
    """Generate TTS using Chatterbox engine."""
    url = f"{SERVERS['chatterbox']}/tts"
    payload = {
        "text": text,
        "voice": voice,
        "exaggeration": exaggeration,
        "cfg_weight": cfg_weight,
        "temperature": temperature
    }
    
    response = requests.post(url, json=payload, timeout=180)
    if response.status_code == 200 and len(response.content) > 100:
        return response.content
    else:
        raise Exception(f"Chatterbox TTS failed: {response.status_code} - {response.text[:200]}")


def generate_tts(text, engine, voice, language="en", **kwargs):
    """Generate TTS using specified engine."""
    resolved_voice = VOICE_PRESETS.get(voice, voice)
    
    if engine == "kokoro":
        if resolved_voice not in KOKORO_VOICES:
            resolved_voice = VOICE_PRESETS.get(voice, "af_heart")
        return generate_tts_kokoro(text, voice=resolved_voice, speed=kwargs.get("speed", 1.0))
    
    elif engine == "openaudio":
        return generate_tts_openaudio(
            text, 
            voice=resolved_voice,
            temperature=kwargs.get("temperature", 0.3),
            top_p=kwargs.get("top_p", 0.7)
        )
    
    elif engine == "xtts":
        return generate_tts_xtts(text, voice=resolved_voice, language=language)
    
    elif engine == "chatterbox":
        return generate_tts_chatterbox(
            text,
            voice=resolved_voice,
            exaggeration=kwargs.get("exaggeration", 0.15),
            cfg_weight=kwargs.get("cfg_weight", 0.9),
            temperature=kwargs.get("temperature", 0.3)
        )
    
    else:
        raise ValueError(f"Unknown engine: {engine}")


def merge_wav_files(wav_files, output_path):
    """Merge multiple WAV files using ffmpeg."""
    if len(wav_files) == 1:
        with open(wav_files[0], 'rb') as f:
            data = f.read()
        with open(output_path, 'wb') as f:
            f.write(data)
        return
    
    list_file = tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False)
    for wav_file in wav_files:
        list_file.write(f"file '{wav_file}'\n")
    list_file.close()
    
    try:
        subprocess.run([
            'ffmpeg', '-y', '-f', 'concat', '-safe', '0',
            '-i', list_file.name,
            '-c', 'copy', output_path
        ], check=True, capture_output=True)
    finally:
        os.unlink(list_file.name)


def convert_audio(input_path, output_path, output_format):
    """Convert audio to specified format using ffmpeg."""
    format_options = {
        'wav': ['-c:a', 'pcm_s16le'],
        'flac': ['-c:a', 'flac', '-compression_level', '8'],
        'mp3': ['-c:a', 'libmp3lame', '-b:a', '192k'],
        'ogg': ['-c:a', 'libvorbis', '-q:a', '6'],
        'aac': ['-c:a', 'aac', '-b:a', '192k'],
        'm4a': ['-c:a', 'aac', '-b:a', '192k'],
    }
    
    options = format_options.get(output_format, format_options['mp3'])
    
    subprocess.run([
        'ffmpeg', '-y', '-i', input_path,
        *options, output_path
    ], check=True, capture_output=True)


def check_server(engine):
    """Check if TTS server is available."""
    url = SERVERS.get(engine)
    if not url:
        return False
    
    try:
        if engine == "openaudio":
            r = requests.get(f"{url}/v1/health", timeout=3)
        elif engine == "kokoro":
            r = requests.get(f"{url}/", timeout=3)
        else:
            r = requests.get(f"{url}/health", timeout=3)
        return r.status_code == 200
    except:
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Convert text to speech using various TTS engines.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Hello world"
  %(prog)s -f input.txt -o output.mp3
  %(prog)s "Guten Tag" --voice sven --engine xtts --lang de
  %(prog)s "Long text..." --voice male --format flac
  cat document.txt | %(prog)s -o speech.mp3
  
Voices:
  female      - af_heart (Kokoro preset)
  male        - am_adam (Kokoro preset)
  sven        - Cloned voice (openaudio, xtts, chatterbox)
  af_*, am_*  - Kokoro preset voices
  
Formats:
  wav   - Uncompressed (largest, lossless)
  flac  - Compressed lossless (recommended)
  mp3   - Compressed lossy (smallest)
  ogg   - Compressed lossy (open format)
        """
    )
    
    parser.add_argument('text', nargs='?', help='Text to convert to speech')
    parser.add_argument('-f', '--file', help='Input text file')
    parser.add_argument('-o', '--output', default='output.wav', help='Output file (default: output.wav)')
    parser.add_argument('--format', choices=['wav', 'flac', 'mp3', 'ogg', 'aac', 'm4a'], 
                        help='Output format (auto-detected from extension)')
    parser.add_argument('--voice', default='female', help='Voice: female, male, sven, or voice ID')
    parser.add_argument('--engine', default='kokoro', choices=['kokoro', 'openaudio', 'xtts', 'chatterbox'],
                        help='TTS engine (default: kokoro)')
    parser.add_argument('--lang', default='en', help='Language code (default: en)')
    parser.add_argument('--speed', type=float, default=1.0, help='Speech speed for Kokoro (default: 1.0)')
    parser.add_argument('--chunk-size', type=int, default=MAX_CHUNK_SIZE, 
                        help=f'Max characters per chunk (default: {MAX_CHUNK_SIZE})')
    parser.add_argument('--quiet', '-q', action='store_true', help='Suppress progress output')
    parser.add_argument('--list-voices', action='store_true', help='List available voices')
    parser.add_argument('--check', action='store_true', help='Check server availability')
    
    args = parser.parse_args()
    
    # List voices
    if args.list_voices:
        print("Voice Presets:")
        for name, voice_id in VOICE_PRESETS.items():
            print(f"  {name}: {voice_id}")
        print("\nKokoro Voices (preset only):")
        for v in KOKORO_VOICES:
            print(f"  {v}")
        print("\nCloned Voices (openaudio, xtts, chatterbox):")
        print("  sven")
        return
    
    # Check servers
    if args.check:
        print("Server Status:")
        for engine in SERVERS:
            status = "OK" if check_server(engine) else "OFFLINE"
            print(f"  {engine}: {status}")
        return
    
    # Get input text
    if args.text:
        text = args.text
    elif args.file:
        with open(args.file, 'r', encoding='utf-8') as f:
            text = f.read()
    elif not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        parser.error("No input text provided. Use positional argument, -f FILE, or pipe text.")
    
    if not text.strip():
        parser.error("Input text is empty.")
    
    # Check server
    if not check_server(args.engine):
        print(f"Error: {args.engine} server is not available at {SERVERS[args.engine]}", file=sys.stderr)
        sys.exit(1)
    
    # Determine output format
    output_path = Path(args.output)
    if args.format:
        output_format = args.format
    else:
        output_format = output_path.suffix.lstrip('.').lower()
        if output_format not in ['wav', 'flac', 'mp3', 'ogg', 'aac', 'm4a']:
            output_format = 'wav'
    
    # Adjust voice for engine
    voice = args.voice
    if args.engine == "kokoro" and voice == "sven":
        print("Warning: Kokoro doesn't support cloned voices. Using 'male' instead.", file=sys.stderr)
        voice = "male"
    
    # Split text into chunks
    chunks = split_text_into_chunks(text, args.chunk_size)
    
    if not args.quiet:
        print(f"Engine: {args.engine}")
        print(f"Voice: {voice} -> {VOICE_PRESETS.get(voice, voice)}")
        print(f"Language: {args.lang}")
        print(f"Chunks: {len(chunks)}")
        print(f"Output: {output_path} ({output_format})")
        print()
    
    # Generate audio for each chunk
    temp_dir = tempfile.mkdtemp()
    wav_files = []
    
    try:
        for i, chunk in enumerate(chunks):
            if not args.quiet:
                print(f"Processing chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...", end=' ', flush=True)
            
            start_time = time.time()
            
            audio_data = generate_tts(
                chunk, 
                engine=args.engine, 
                voice=voice,
                language=args.lang,
                speed=args.speed
            )
            
            wav_path = os.path.join(temp_dir, f"chunk_{i:04d}.wav")
            with open(wav_path, 'wb') as f:
                f.write(audio_data)
            wav_files.append(wav_path)
            
            elapsed = time.time() - start_time
            if not args.quiet:
                print(f"done ({elapsed:.1f}s)")
        
        # Merge WAV files
        if not args.quiet:
            print(f"\nMerging {len(wav_files)} audio files...")
        
        merged_wav = os.path.join(temp_dir, "merged.wav")
        merge_wav_files(wav_files, merged_wav)
        
        # Convert to output format
        if output_format == 'wav':
            # Just copy the merged WAV
            with open(merged_wav, 'rb') as f:
                data = f.read()
            with open(output_path, 'wb') as f:
                f.write(data)
        else:
            if not args.quiet:
                print(f"Converting to {output_format}...")
            convert_audio(merged_wav, str(output_path), output_format)
        
        # Get file size
        file_size = output_path.stat().st_size
        if file_size > 1024 * 1024:
            size_str = f"{file_size / (1024*1024):.1f} MB"
        else:
            size_str = f"{file_size / 1024:.1f} KB"
        
        if not args.quiet:
            print(f"\nDone! Output: {output_path} ({size_str})")
    
    finally:
        # Cleanup temp files
        for f in wav_files:
            try:
                os.unlink(f)
            except:
                pass
        try:
            if os.path.exists(merged_wav):
                os.unlink(merged_wav)
            os.rmdir(temp_dir)
        except:
            pass


if __name__ == "__main__":
    main()
