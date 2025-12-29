import instaloader
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import os, json, shutil, time

# === อ่านข้อมูลจาก Secrets ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_JSFAVORITEGIRLS")

bot = Bot(BOT_TOKEN)

# === โหลดด้วยคุณภาพสูงสุด ===
L = instaloader.Instaloader(
    download_videos=True,
    save_metadata=False,
    compress_json=False,
)

# === โหลดโพสต์ที่ส่งไปแล้ว (กันซ้ำ) ===
if os.path.exists("sent.json"):
    sent = json.load(open("sent.json"))
else:
    sent = {"posts": [], "highlights": []}

# === ✏️ แก้เป็นชื่อไอจีที่คุณต้องการ ===
IG_USERNAME = "ชื่อไอจีของคุณ"   # <---- แก้ตรงนี้อย่างเดียวก่อนรัน

profile = instaloader.Profile.from_username(L.context, IG_USERNAME)

# ==========================
# 🔥 ส่ง POSTS / REELS / ALBUMS
# ==========================
for post in profile.get_posts():

    if post.shortcode in sent["posts"]:
        continue

    L.download_post(post, target=post.shortcode)

    media_group = []
    for f in sorted(os.listdir(post.shortcode)):
        path = f"{post.shortcode}/{f}"
        if f.endswith(".jpg"):
            media_group.append(InputMediaPhoto(open(path, "rb")))
        elif f.endswith(".mp4"):
            media_group.append(InputMediaVideo(open(path, "rb")))

    # อัลบั้ม = ส่งเป็น media group
    if len(media_group) > 1:
        bot.send_media_group(CHAT_ID, media_group)
    else:
        # เดี่ยว = ส่งธรรมดา
        media = media_group[0]
        if media.media.endswith(".jpg"):
            bot.send_photo(CHAT_ID, media.media)
        else:
            bot.send_video(CHAT_ID, media.media)

    shutil.rmtree(post.shortcode)
    sent["posts"].append(post.shortcode)

    time.sleep(2)  # ป้องกันการส่งเร็วเกินไป


# ==========================
# ⭐ ส่ง HIGHLIGHTS (ทีละไฟล์)
# ==========================
for highlight in profile.get_highlights():

    for item in highlight.get_items():

        uid = str(item.mediaid)

        if uid in sent["highlights"]:
            continue

        dl_folder = f"hl_{uid}"
        L.download_storyitem(item, target=dl_folder)

        for f in sorted(os.listdir(dl_folder)):
            path = f"{dl_folder}/{f}"
            if f.endswith(".jpg"):
                bot.send_photo(CHAT_ID, open(path, "rb"))
            elif f.endswith(".mp4"):
                bot.send_video(CHAT_ID, open(path, "rb"))

        shutil.rmtree(dl_folder)
        sent["highlights"].append(uid)

        time.sleep(2)


# === บันทึกสถานะที่ส่งแล้ว ===
json.dump(sent, open("sent.json", "w"))
