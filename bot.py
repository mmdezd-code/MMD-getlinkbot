"""
ربات تبدیل فایل به لینک دانلود مستقیم
پشتیبانی از فایل تا 4 گیگابایت با MTProto
"""

import asyncio
import logging
import os
import tempfile
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

# ══════════════════════════════════════
API_ID   = 32879233
API_HASH = "93cba81a0ce5698c4ec11a22d0e84d74"
BOT_TOKEN = "8901790954:AAEbgwVIE_1yM9OEF9kufCvMYnV-7wXTgeU"
# ══════════════════════════════════════

logging.basicConfig(format="%(asctime)s | %(levelname)s | %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

app = Client("filebot_session", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)


def human_size(size: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} TB"


def upload_to_0x0(file_path: str, filename: str) -> str | None:
    try:
        with open(file_path, "rb") as f:
            resp = requests.post("https://0x0.st", files={"file": (filename, f)}, timeout=600)
        if resp.status_code == 200:
            return resp.text.strip()
        return None
    except Exception as e:
        logger.error(f"Upload error: {e}")
        return None


def make_progress(status_msg, loop):
    last = [0]

    async def progress(current, total):
        pct = current * 100 // total
        if pct - last[0] >= 10:
            last[0] = pct
            bar = "▓" * (pct // 10) + "░" * (10 - pct // 10)
            try:
                asyncio.run_coroutine_threadsafe(
                    status_msg.edit_text(f"⬇️ دانلود...\n[{bar}] {pct}%\n{human_size(current)} / {human_size(total)}"),
                    loop
                )
            except:
                pass

    return progress


@app.on_message(filters.command("start") & filters.private)
async def cmd_start(client, message: Message):
    await message.reply_text(
        "👋 سلام!\n\n"
        "📤 هر فایلی بفرست، لینک دانلود مستقیم بهت میدم.\n"
        "✅ پشتیبانی از فایل تا **4 گیگابایت**",
        parse_mode="markdown"
    )


@app.on_message(
    filters.private & (
        filters.document | filters.video | filters.audio |
        filters.photo | filters.voice | filters.animation | filters.video_note
    )
)
async def handle_file(client: Client, message: Message):
    # شناسایی فایل
    if message.document:
        filename = message.document.file_name or "file"
        file_size = message.document.file_size or 0
    elif message.video:
        filename = message.video.file_name or "video.mp4"
        file_size = message.video.file_size or 0
    elif message.audio:
        filename = message.audio.file_name or "audio.mp3"
        file_size = message.audio.file_size or 0
    elif message.photo:
        filename = "photo.jpg"
        file_size = message.photo.file_size or 0
    elif message.voice:
        filename = "voice.ogg"
        file_size = message.voice.file_size or 0
    elif message.animation:
        filename = "animation.gif"
        file_size = message.animation.file_size or 0
    elif message.video_note:
        filename = "video_note.mp4"
        file_size = message.video_note.file_size or 0
    else:
        return

    status = await message.reply_text("⏳ در حال دریافت فایل...")
    loop = asyncio.get_event_loop()

    with tempfile.TemporaryDirectory() as tmpdir:
        local_path = os.path.join(tmpdir, filename)

        try:
            await client.download_media(
                message,
                file_name=local_path,
                progress=make_progress(status, loop)
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await client.download_media(message, file_name=local_path)
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status.edit_text("❌ خطا در دریافت فایل.")
            return

        if not os.path.exists(local_path):
            await status.edit_text("❌ دانلود ناموفق بود.")
            return

        actual_size = os.path.getsize(local_path)
        await status.edit_text(f"⬆️ آپلود روی سرور...\n📦 {human_size(actual_size)}")

        link = upload_to_0x0(local_path, filename)

    if link:
        await status.edit_text(
            f"✅ *آپلود موفق!*\n\n"
            f"📎 نام: `{filename}`\n"
            f"📦 حجم: {human_size(actual_size)}\n\n"
            f"🔗 *لینک دانلود مستقیم:*\n{link}",
            parse_mode="markdown"
        )
    else:
        await status.edit_text("❌ خطا در آپلود. دوباره امتحان کن.")


if __name__ == "__main__":
    logger.info("🤖 ربات شروع کرد...")
    app.run()
