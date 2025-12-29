import instaloader
from telegram import Bot
import os, json, shutil

# อ่าน token และ chat id จาก secrets
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_JSFAVORITEGIRLS")

bot = Bot(BOT_TOKEN)

# ตั้งค่า instaloader
L = instaloader.Instaloader(
    download_videos=True,
    save_metadata=False,
    compress_json=False
)

# ถ้ามีโพสต์ที่ส่งแล้ว จะไม่ส่งซ้ำ
sent = json.load(open("sent.json")) if os.path.exists("sent.json") else []

# ชื่อ IG ที่ต้องการให้บอทติดตาม
IG_USERNAME = "ying__ww"    # เปลี่ยนเป็น IG เป้าหมายของคุณได้

profile = instaloader.Profile.from_username(L.context, IG_USERNAME)

for post in profile.get_posts():
    if post.shortcode in sent:
        continue

    L.download_post(post, target=post.shortcode)

    for f in os.listdir(post.shortcode):
        path = f"{post.shortcode}/{f}"

        if f.endswith(".jpg"):
            bot.send_photo(CHAT_ID, open(path, "rb"), caption=f"📸 @{IG_USERNAME}")

        elif f.endswith(".mp4"):
            bot.send_video(CHAT_ID, open(path, "rb"), caption=f"🎬 @{IG_USERNAME}")

    shutil.rmtree(post.shortcode)
    sent.append(post.shortcode)
    break

json.dump(sent, open("sent.json", "w"))
