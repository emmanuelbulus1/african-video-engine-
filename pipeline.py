"""
pipeline.py — African Video Engine core pipeline
YouTube → AssemblyAI (transcription) → GPT-4o-mini (rewrite) → ElevenLabs (voice) → FFmpeg (merge)
"""

import os
import uuid
import asyncio
import requests
import assemblyai as aai
from openai import OpenAI
from elevenlabs import ElevenLabs
from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from config import (
    OPENAI_API_KEY,
    ELEVENLABS_API_KEY,
    ASSEMBLYAI_API_KEY,
    OPENAI_MODEL,
    ELEVENLABS_VOICE_ID,
    TEMP_DIR,
)

# ── Client initialisation ─────────────────────────────────
aai.settings.api_key = ASSEMBLYAI_API_KEY
openai_client        = OpenAI(api_key=OPENAI_API_KEY)
eleven_client        = ElevenLabs(api_key=ELEVENLABS_API_KEY)

os.makedirs(TEMP_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────
# 1.  Download YouTube video (audio-only via pytube)
# ─────────────────────────────────────────────────────────
async def download_youtube(url: str, progress_cb=None) -> dict:
    """Download YouTube video and return paths for video + audio."""
    from pytubefix import YouTube  # lightweight, no cookies needed

    if progress_cb:
        await progress_cb(5, "Fetching YouTube video…")

    job_id   = str(uuid.uuid4())[:8]
    out_dir  = os.path.join(TEMP_DIR, job_id)
    os.makedirs(out_dir, exist_ok=True)

    yt          = YouTube(url)
    video_path  = None
    audio_path  = None

    # Best progressive stream (video + audio together, fastest)
    stream = yt.streams.filter(progressive=True, file_extension="mp4") \
                        .order_by("resolution").last()
    if stream:
        video_path = stream.download(output_path=out_dir, filename="video.mp4")
        audio_path = video_path          # audio is embedded

    # Fallback: audio-only stream
    if not video_path:
        stream = yt.streams.filter(only_audio=True).first()
        audio_path = stream.download(output_path=out_dir, filename="audio.mp4")

    if progress_cb:
        await progress_cb(10, "Download complete")

    return {
        "job_id":     job_id,
        "out_dir":    out_dir,
        "video_path": video_path,
        "audio_path": audio_path,
        "title":      yt.title,
    }


# ─────────────────────────────────────────────────────────
# 2.  Transcribe with AssemblyAI
# ─────────────────────────────────────────────────────────
async def transcribe_audio(audio_path: str, progress_cb=None) -> str:
    """Upload audio to AssemblyAI and return transcript text."""
    if progress_cb:
        await progress_cb(15, "Sending to AssemblyAI…")

    # Run blocking SDK call in a thread so we don't block the event loop
    def _transcribe():
        transcriber = aai.Transcriber()
        transcript  = transcriber.transcribe(audio_path)
        if transcript.status == aai.TranscriptStatus.error:
            raise RuntimeError(f"AssemblyAI error: {transcript.error}")
        return transcript.text

    text = await asyncio.get_event_loop().run_in_executor(None, _transcribe)

    if progress_cb:
        await progress_cb(35, "Transcription complete ✅")

    return text


# ─────────────────────────────────────────────────────────
# 3.  Rewrite with GPT-4o-mini (African GURU style)
# ─────────────────────────────────────────────────────────
GURU_SYSTEM_PROMPT = """
You are GURU — Africa's most powerful storytelling AI.
Your job: take any script and rewrite it with African warmth, wisdom, and energy.

Rules:
- Keep the same core message and facts
- Add African proverbs, vivid imagery, and communal language
- Use "we", "our people", "the village knows"
- Keep sentences punchy and spoken-word friendly
- Target length: same as input (±10%)
- Output ONLY the rewritten script, nothing else
""".strip()

async def rewrite_script(transcript: str, mode: str = "guru", progress_cb=None) -> str:
    """Use GPT-4o-mini to rewrite transcript in African GURU style."""
    if progress_cb:
        await progress_cb(40, "GURU rewriting script…")

    mode_instructions = {
        "guru":        "Rewrite with African GURU wisdom, proverbs and energy.",
        "documentary": "Rewrite as an African documentary narration — powerful and factual.",
        "story":       "Rewrite as an African oral story — vivid, communal, gripping.",
        "news":        "Rewrite as African breaking news — urgent and authoritative.",
    }
    extra = mode_instructions.get(mode, mode_instructions["guru"])

    def _call_openai():
        response = openai_client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": GURU_SYSTEM_PROMPT},
                {"role": "user",   "content": f"{extra}\n\nOriginal:\n{transcript}"},
            ],
            temperature=0.8,
            max_tokens=2000,
        )
        return response.choices[0].message.content.strip()

    rewritten = await asyncio.get_event_loop().run_in_executor(None, _call_openai)

    if progress_cb:
        await progress_cb(55, "African script ready ✅")

    return rewritten


# ─────────────────────────────────────────────────────────
# 4.  Generate voice with ElevenLabs
# ─────────────────────────────────────────────────────────
async def generate_voice(script: str, out_dir: str, progress_cb=None) -> str:
    """Convert script to speech using ElevenLabs. Returns path to audio file."""
    if progress_cb:
        await progress_cb(60, "Generating African voice…")

    audio_path = os.path.join(out_dir, "voiceover.mp3")

    def _generate():
        audio_bytes = eleven_client.generate(
            text=script,
            voice=ELEVENLABS_VOICE_ID,
            model="eleven_multilingual_v2",
        )
        with open(audio_path, "wb") as f:
            for chunk in audio_bytes:
                f.write(chunk)

    await asyncio.get_event_loop().run_in_executor(None, _generate)

    if progress_cb:
        await progress_cb(75, "Voice complete ✅")

    return audio_path


# ─────────────────────────────────────────────────────────
# 5.  Merge video + new voiceover with MoviePy
# ─────────────────────────────────────────────────────────
async def merge_video(video_path: str, voice_path: str, out_dir: str, progress_cb=None) -> str:
    """Replace original audio with GURU voiceover. Returns output video path."""
    if progress_cb:
        await progress_cb(80, "Merging video…")

    output_path = os.path.join(out_dir, "output_african.mp4")

    def _merge():
        video = VideoFileClip(video_path)
        voice = AudioFileClip(voice_path)

        # Trim voice if longer than video, loop video if voice is longer
        if voice.duration > video.duration:
            video = video.loop(duration=voice.duration)
        else:
            voice = voice.subclip(0, video.duration)

        final = video.set_audio(voice)
        final.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            temp_audiofile=os.path.join(out_dir, "temp_audio.m4a"),
            remove_temp=True,
            verbose=False,
            logger=None,
        )
        video.close()
        voice.close()
        final.close()

    await asyncio.get_event_loop().run_in_executor(None, _merge)

    if progress_cb:
        await progress_cb(95, "Merge complete ✅")

    return output_path


# ─────────────────────────────────────────────────────────
# MASTER PIPELINE — orchestrates all 5 steps
# ─────────────────────────────────────────────────────────
async def run_pipeline(youtube_url: str, mode: str = "guru", progress_cb=None) -> dict:
    """
    Full pipeline: YouTube → AssemblyAI → GPT-4o-mini → ElevenLabs → FFmpeg

    Args:
        youtube_url: Any valid YouTube URL
        mode:        guru | documentary | story | news
        progress_cb: async callable(percent: int, message: str)

    Returns:
        dict with keys: output_path, transcript, rewritten_script, title
    """

    # Step 1 — Download
    dl = await download_youtube(youtube_url, progress_cb)

    # Step 2 — Transcribe
    transcript = await transcribe_audio(dl["audio_path"], progress_cb)

    # Step 3 — Rewrite
    rewritten = await rewrite_script(transcript, mode, progress_cb)

    # Step 4 — Voice
    voice_path = await generate_voice(rewritten, dl["out_dir"], progress_cb)

    # Step 5 — Merge (only if we have a video file)
    output_path = None
    if dl["video_path"]:
        output_path = await merge_video(dl["video_path"], voice_path, dl["out_dir"], progress_cb)
    else:
        output_path = voice_path   # audio-only fallback

    if progress_cb:
        await progress_cb(100, "🎉 Video ready!")

    return {
        "output_path":      output_path,
        "transcript":       transcript,
        "rewritten_script": rewritten,
        "title":            dl["title"],
        "job_id":           dl["job_id"],
    }
