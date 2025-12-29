import instaloader
from telegram import Bot, InputMediaPhoto, InputMediaVideo
import os, json, shutil, time

# === READ FROM GITHUB SECRETS ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_JSFAVORITEGIRLS")

bot = Bot(BOT_TOKEN)

# === INSTALOADER SETTINGS ===
L = instaloader.Instaloader(
    download_videos=True,
    save_metadata=False,
    compress_json=False,
)

# === LOAD SENT HISTORY (ANTI-DUPLICATE) ===
if os.path.exists("sent.json"):
    sent = json.load(open("sent.json"))
else:
    sent = {"posts": [], "highlights": []}

# === CHANGE THIS TO YOUR TARGET IG ===
IG_USERNAME = "ying__ww"   # <----- แก้ตรงนี้ เช่น "ying_ww"

profile = instaloader.Profile.from_username(L.context, IG_USERNAME)

# ==========================
# 🔥 SEND POSTS / REELS / ALBUMS
# ==========================
for post in profile.get_posts():

    if post.shortcode in sent["posts"]:
        continue

    print(f"📌 Sending post: {post.shortcode}")

    L.download_post(post, target=post.shortcode)

    file_paths = sorted(os.listdir(post.shortcode))
    media_group = []

    # ALBUM
    if len(file_paths) > 1:
        for f in file_paths:
            path = f"{post.shortcode}/{f}"
            if f.endswith(".jpg"):
                media_group.append(InputMediaPhoto(media=open(path, "rb")))
            elif f.endswith(".mp4"):
                media_group.append(InputMediaVideo(media=open(path, "rb")))

        bot.send_media_group(CHAT_ID, media_group)

    # SINGLE FILE
    else:
        f = file_paths[0]
        path = f"{post.shortcode}/{f}"

        if f.endswith(".jpg"):
            bot.send_photo(CHAT_ID, open(path, "rb"))
        elif f.endswith(".mp4"):
            bot.send_video(CHAT_ID, open(path, "rb"))

    shutil.rmtree(post.shortcode)
    sent["posts"].append(post.shortcode)
    time.sleep(2)  # prevent rate-limit


# ==========================
# ⭐ SEND HIGHLIGHTS (ONE BY ONE)
# ==========================
for highlight in profile.get_highlights():

    for item in highlight.get_items():

        uid = str(item.mediaid)

        if uid in sent["highlights"]:
            continue

        print(f"🌟 Sending highlight: {uid}")

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


# === SAVE PROGRESS ===
json.dump(sent, open("sent.json", "w"))
print("✅ DONE — next run will continue from here")
