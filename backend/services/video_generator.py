"""Video generation pipeline: LLM script -> Pillow slides -> OpenAI TTS -> MoviePy assembly."""

from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from langchain_core.messages import HumanMessage, SystemMessage

from .llm_config import get_llm

GENERATED_VIDEOS_DIR = Path(tempfile.gettempdir()) / "teaching_assistant_videos"
GENERATED_VIDEOS_DIR.mkdir(exist_ok=True)

SLIDE_WIDTH = 1280
SLIDE_HEIGHT = 720


@dataclass
class Slide:
    title: str
    bullets: list[str]
    narration: str


@dataclass
class VideoJob:
    job_id: str
    session_id: str
    topic_index: int
    status: str = "pending"  # pending | processing | completed | failed
    video_path: str | None = None
    error: str | None = None


video_jobs: dict[str, VideoJob] = {}


def generate_script(topic_title: str, topic_content: str) -> list[Slide]:
    """Use LLM to generate a structured slide script from topic content."""
    system_prompt = (
        "You are creating a short educational video script. Break the content into 4-8 slides.\n"
        "Each slide must have:\n"
        '- "title": short slide heading\n'
        '- "bullets": 2-4 concise bullet points\n'
        '- "narration": a 40-70 word paragraph the narrator reads aloud for this slide\n\n'
        "Return valid JSON only. Format:\n"
        '[{"title": "...", "bullets": ["...", "..."], "narration": "..."}, ...]'
    )
    user_prompt = (
        f"Topic: {topic_title}\n\nContent:\n\n{topic_content[:20000]}\n\n"
        "Create the slide script as JSON."
    )

    llm = get_llm()
    messages = [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    response = llm.invoke(messages)
    content = response.content if hasattr(response, "content") else str(response)
    return _parse_script(content)


def _parse_script(content: str) -> list[Slide]:
    content = content.strip()
    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?\s*", "", content)
        content = re.sub(r"\s*```$", "", content)
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        return [Slide(title="Overview", bullets=["Content overview"], narration=content[:200])]

    if not isinstance(data, list):
        return [Slide(title="Overview", bullets=["Content overview"], narration=str(data)[:200])]

    slides: list[Slide] = []
    for item in data:
        if isinstance(item, dict):
            title = str(item.get("title", "Slide"))
            bullets = item.get("bullets", [])
            if not isinstance(bullets, list):
                bullets = [str(bullets)]
            bullets = [str(b) for b in bullets]
            narration = str(item.get("narration", ""))
            slides.append(Slide(title=title, bullets=bullets, narration=narration))
    return slides or [Slide(title="Overview", bullets=["Content overview"], narration="Overview of the topic.")]


def _get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try to load a system font, falling back to default."""
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
    ]
    for fp in font_paths:
        if Path(fp).exists():
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def render_slide(slide: Slide, slide_num: int, total_slides: int, topic_title: str) -> Image.Image:
    """Render a single slide as a 1280x720 PIL image."""
    img = Image.new("RGB", (SLIDE_WIDTH, SLIDE_HEIGHT))
    draw = ImageDraw.Draw(img)

    # Dark gradient background
    for y in range(SLIDE_HEIGHT):
        ratio = y / SLIDE_HEIGHT
        r = int(15 + ratio * 10)
        g = int(23 + ratio * 12)
        b = int(42 + ratio * 20)
        draw.line([(0, y), (SLIDE_WIDTH, y)], fill=(r, g, b))

    # Accent bar at top
    draw.rectangle([(0, 0), (SLIDE_WIDTH, 4)], fill=(59, 130, 246))

    title_font = _get_font(36)
    body_font = _get_font(24)
    small_font = _get_font(16)

    # Topic title (small, top-left)
    draw.text((40, 20), topic_title, fill=(148, 163, 184), font=small_font)

    # Slide title
    draw.text((40, 70), slide.title, fill=(255, 255, 255), font=title_font)

    # Separator line
    draw.line([(40, 120), (SLIDE_WIDTH - 40, 120)], fill=(59, 130, 246), width=2)

    # Bullet points
    y_pos = 150
    for bullet in slide.bullets:
        wrapped = _wrap_text(f"  •  {bullet}", body_font, SLIDE_WIDTH - 120)
        for line in wrapped:
            draw.text((60, y_pos), line, fill=(226, 232, 240), font=body_font)
            y_pos += 36
        y_pos += 12

    # Slide number
    slide_indicator = f"{slide_num} / {total_slides}"
    draw.text((SLIDE_WIDTH - 100, SLIDE_HEIGHT - 40), slide_indicator, fill=(100, 116, 139), font=small_font)

    return img


def _wrap_text(text: str, font, max_width: int) -> list[str]:
    """Simple word-wrap for Pillow text rendering."""
    words = text.split()
    lines: list[str] = []
    current_line = ""
    for word in words:
        test = f"{current_line} {word}".strip()
        try:
            bbox = font.getbbox(test)
            w = bbox[2] - bbox[0]
        except AttributeError:
            w = len(test) * 10
        if w <= max_width:
            current_line = test
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines or [text]


def generate_tts_audio(text: str, output_path: str) -> str:
    """Generate TTS audio using OpenAI API. Returns path to the audio file."""
    import openai

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY required for TTS")

    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text,
    )
    response.stream_to_file(output_path)
    return output_path


def assemble_video(slides: list[Slide], slide_images: list[str], audio_files: list[str], output_path: str) -> str:
    """Combine slide images and audio into an MP4 video using MoviePy."""
    from moviepy.editor import AudioFileClip, ImageClip, concatenate_videoclips

    clips = []
    for img_path, audio_path in zip(slide_images, audio_files):
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration

        image_clip = (
            ImageClip(img_path)
            .set_duration(duration)
            .set_audio(audio_clip)
        )
        clips.append(image_clip)

    final = concatenate_videoclips(clips, method="compose")
    final.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None,
    )

    for clip in clips:
        clip.close()
    final.close()

    return output_path


def generate_video_for_topic(job: VideoJob, topic_title: str, topic_content: str) -> None:
    """Full pipeline: script -> slides -> TTS -> video. Updates job in-place."""
    job.status = "processing"
    tmp_dir = None
    try:
        tmp_dir = tempfile.mkdtemp(prefix="ta_video_")
        slides = generate_script(topic_title, topic_content)

        slide_image_paths: list[str] = []
        audio_paths: list[str] = []

        for i, slide in enumerate(slides):
            img = render_slide(slide, i + 1, len(slides), topic_title)
            img_path = os.path.join(tmp_dir, f"slide_{i:03d}.png")
            img.save(img_path)
            slide_image_paths.append(img_path)

            audio_path = os.path.join(tmp_dir, f"audio_{i:03d}.mp3")
            generate_tts_audio(slide.narration, audio_path)
            audio_paths.append(audio_path)

        output_filename = f"{job.session_id}_{job.topic_index}.mp4"
        output_path = str(GENERATED_VIDEOS_DIR / output_filename)

        assemble_video(slides, slide_image_paths, audio_paths, output_path)

        job.video_path = output_path
        job.status = "completed"

    except Exception as e:
        job.status = "failed"
        job.error = str(e)
    finally:
        if tmp_dir:
            import shutil
            shutil.rmtree(tmp_dir, ignore_errors=True)
