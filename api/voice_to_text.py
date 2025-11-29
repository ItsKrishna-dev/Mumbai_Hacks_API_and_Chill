# api/voice_to_text.py
import os
import tempfile
import uuid
from pathlib import Path
from utils import log
from config import settings

# ✅ Configure ffmpeg and ffprobe paths
TOOLS_DIR = Path(__file__).parent.parent / "tools"
FFMPEG_PATH = TOOLS_DIR / "ffmpeg.exe"
FFPROBE_PATH = TOOLS_DIR / "ffprobe.exe"

# Check if both files exist
ffmpeg_exists = FFMPEG_PATH.exists()
ffprobe_exists = FFPROBE_PATH.exists()

if ffmpeg_exists and ffprobe_exists:
    # Configure pydub to use bundled binaries
    from pydub import AudioSegment
    AudioSegment.converter = str(FFMPEG_PATH)
    AudioSegment.ffmpeg = str(FFMPEG_PATH)
    AudioSegment.ffprobe = str(FFPROBE_PATH)
    
    log.info(f"✅ Using bundled ffmpeg: {FFMPEG_PATH}")
    log.info(f"✅ Using bundled ffprobe: {FFPROBE_PATH}")
    
    # Verify file sizes (should be ~120-130 MB each)
    ffmpeg_size = FFMPEG_PATH.stat().st_size / (1024 * 1024)
    ffprobe_size = FFPROBE_PATH.stat().st_size / (1024 * 1024)
    log.info(f"📊 ffmpeg.exe: {ffmpeg_size:.1f} MB")
    log.info(f"📊 ffprobe.exe: {ffprobe_size:.1f} MB")
    
else:
    # Log what's missing
    if not ffmpeg_exists:
        log.error(f"❌ ffmpeg.exe NOT FOUND at: {FFMPEG_PATH}")
    if not ffprobe_exists:
        log.error(f"❌ ffprobe.exe NOT FOUND at: {FFPROBE_PATH}")
    
    log.error("⚠️ Download both files from: https://www.gyan.dev/ffmpeg/builds/")
    log.error("   Required: ffmpeg-release-essentials.zip (101 MB)")
    log.error("   Extract bin/ffmpeg.exe and bin/ffprobe.exe to tools/ folder")


async def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using Google Speech Recognition
    
    Args:
        audio_path: Path to audio file (.ogg or .wav)
    
    Returns:
        Transcribed text or error message
    """
    wav_path = None
    
    try:
        log.info(f"🎤 Starting transcription for: {audio_path}")
        
        # Verify ffmpeg/ffprobe are available
        if not (ffmpeg_exists and ffprobe_exists):
            log.error("❌ FFmpeg not properly configured")
            return "Voice transcription unavailable. Please configure FFmpeg."
        
        # Convert OGG to WAV
        wav_path = convert_ogg_to_wav(audio_path)
        
        if not wav_path or not os.path.exists(wav_path):
            log.error("❌ Audio conversion failed")
            return "Failed to process audio file"
        
        log.info(f"✅ Converted to WAV: {wav_path}")
        
        # Transcribe using speech recognition
        import speech_recognition as sr
        
        recognizer = sr.Recognizer()
        
        with sr.AudioFile(wav_path) as source:
            log.info("🎧 Reading audio data...")
            # Adjust for ambient noise
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            
            log.info("🔄 Transcribing with Google Speech Recognition...")
            
            # Try Hindi first
            try:
                text = recognizer.recognize_google(audio_data, language="hi-IN")
                log.info(f"✅ Transcription (Hindi) successful: '{text}'")
                return text
                
            except sr.UnknownValueError:
                log.warning("⚠️ Could not understand in Hindi, trying English...")
                
                # Fallback to English
                try:
                    text = recognizer.recognize_google(audio_data, language="en-US")
                    log.info(f"✅ Transcription (English) successful: '{text}'")
                    return text
                    
                except sr.UnknownValueError:
                    log.error("❌ Could not understand audio in any language")
                    return "Sorry, I couldn't understand the audio. Please speak clearly or type your message."
                    
            except sr.RequestError as e:
                log.error(f"❌ Speech recognition service error: {e}")
                return "Speech recognition service unavailable. Please type your message."
                
    except Exception as e:
        log.error(f"❌ Transcription error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return "Error processing voice message. Please try again or type your message."
        
    finally:
        # Cleanup WAV file
        if wav_path and os.path.exists(wav_path):
            try:
                os.remove(wav_path)
                log.debug(f"🗑️ Cleaned up WAV file: {wav_path}")
            except Exception as cleanup_error:
                log.warning(f"Could not delete WAV file: {cleanup_error}")


def convert_ogg_to_wav(ogg_path: str) -> str:
    """
    Convert OGG audio to WAV format using bundled ffmpeg
    
    Args:
        ogg_path: Path to OGG file
    
    Returns:
        Path to converted WAV file
    """
    try:
        log.info(f"🔄 Converting OGG to WAV: {ogg_path}")
        
        # Create unique WAV filename
        unique_id = str(uuid.uuid4())[:8]
        temp_dir = tempfile.gettempdir()
        wav_path = os.path.join(temp_dir, f"audio_{unique_id}.wav")
        
        # Verify ffmpeg is available
        if not (ffmpeg_exists and ffprobe_exists):
            raise FileNotFoundError(
                f"FFmpeg or FFprobe not found. "
                f"ffmpeg: {ffmpeg_exists}, ffprobe: {ffprobe_exists}"
            )
        
        # Use pydub with bundled ffmpeg
        from pydub import AudioSegment
        
        log.info("🔧 Using bundled ffmpeg for conversion...")
        
        # Load OGG file
        audio = AudioSegment.from_ogg(ogg_path)
        
        # Convert to mono 16kHz (optimal for speech recognition)
        audio = audio.set_channels(1)
        audio = audio.set_frame_rate(16000)
        
        # Export as WAV
        audio.export(wav_path, format="wav")
        
        log.info(f"✅ Conversion successful: {wav_path}")
        return wav_path
            
    except Exception as e:
        log.error(f"❌ Error converting audio: {type(e).__name__}: {str(e)}")
        raise
