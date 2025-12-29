import instaloader
from telegram import Bot, Update, InputMediaPhoto, InputMediaVideo
from telegram.ext import Updater, CommandHandler
import os, json, shutil, time

BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = Bot(BOT_TOKEN)

L = instaloader.Instaloader(download_videos=True, save_metadata=False, compress_json=False)


# ---------- LOAD DATA ----------
targets = json.load(open("targets.json")) if os.path.exists("targets.json") else {
    "targets": {},
    "summary_chat": None,
    "command_thread": 1,
    "summary_thread": 2
}

sent = json.load(open("sent.json")) if os.path.exists("sent.json") else {"posts": {}}



# ---------- COMMANDS ----------
def add_ig(update: Update, context):
    msg = update.message

    # รับเฉพาะใน topic คำสั่ง
    if msg.message_thread_id != targets["command_thread"]:
        return

    if len(context.args) != 1:
        msg.reply_text("ใช้แบบนี้:\n/เพิ่ม <ไอจี>\n/addig <instagram>")
        return

    ig = context.args[0].lower()
    chat_id = targets["summary_chat"]

    # สร้าง topic ใหม่ตามชื่อ IG
    resp = bot.create_forum_topic(chat_id=chat_id, name=ig)
    thread_id = resp.message_thread_id

    targets["targets"][ig] = {
        "chat_id": chat_id,
        "thread_id": thread_id
    }

    json.dump(targets, open("targets.json","w"))

    msg.reply_text(f"เพิ่ม {ig} สำเร็จ ✔\nหัวข้อใหม่: {ig}")



def del_ig(update: Update, context):
    msg = update.message

    if msg.message_thread_id != targets["command_thread"]:
        return

    if len(context.args) != 1:
        msg.reply_text("ใช้แบบนี้:\n/ลบ <ไอจี>\n/delig <instagram>")
        return

    ig = context.args[0].lower()

    if ig not in targets["targets"]:
        msg.reply_text(f"{ig} ไม่มีในระบบ ❌")
        return

    del targets["targets"][ig]
    json.dump(targets, open("targets.json","w"))

    msg.reply_text(f"ลบ {ig} แล้ว ✔")



def show_id(update: Update, context):
    update.message.reply_text(f"chat_id = {update.message.chat_id}")



def help_cmd(update: Update, context):
    text = (
        "📌 คำสั่งบอท (ไทย/อังกฤษ)\n\n"
        "/เพิ่ม <ig>\n/addig <ig>\n ➜ เพิ่มบัญชี IG และสร้างหัวข้อใหม่\n\n"
        "/ลบ <ig>\n/delig <ig>\n ➜ ลบบัญชี IG ออกจากระบบ\n\n"
        "/สถานะ\n/status\n ➜ ดูสรุปการทำงานล่าสุด\n"
    )
    update.message.reply_text(text)



# ---------- SEND DASHBOARD ----------
def dashboard():
    chat_id = targets["summary_chat"]
    thread_id = targets["summary_thread"]

    lines = ["📊 สรุปผลการทำงานล่าสุด\n"]

    for ig, data in targets["targets"].items():
        total_sent = len(sent["posts"].get(ig, []))
        lines.append(f"{ig:<15} ส่งแล้ว {total_sent} โพสต์")

    bot.send_message(chat_id, "\n".join(lines), message_thread_id=thread_id)



# ---------- SEND POSTS ----------
def send_ig_posts(ig):
    chat_id = targets["targets"][ig]["chat_id"]
    thread_id = targets["targets"][ig]["thread_id"]

    if ig not in sent["posts"]:
        sent["posts"][ig] = []

    profile = instaloader.Profile.from_username(L.context, ig)
    new_count = 0

    for post in profile.get_posts():
        if post.shortcode in sent["posts"][ig]:
            continue

        L.download_post(post, target=post.shortcode)
        files = sorted(os.listdir(post.shortcode))
        media_group = []

        if len(files) > 1:
            # อัลบั้ม
            for f in files:
                path = f"{post.shortcode}/{f}"
                if f.endswith(".jpg"):
                    media_group.append(InputMediaPhoto(open(path, "rb")))
                elif f.endswith(".mp4"):
                    media_group.append(InputMediaVideo(open(path, "rb")))
            bot.send_media_group(chat_id, media_group, message_thread_id=thread_id)

        else:
            f = files[0]
            path = f"{post.shortcode}/{f}"
            if f.endswith(".jpg"):
                bot.send_photo(chat_id, open(path, "rb"), message_thread_id=thread_id)
            elif f.endswith(".mp4"):
                bot.send_video(chat_id, open(path, "rb"), message_thread_id=thread_id)

        shutil.rmtree(post.shortcode)
        sent["posts"][ig].append(post.shortcode)
        new_count += 1
        time.sleep(2)  # กัน rate limit

    json.dump(sent, open("sent.json","w"))

    return new_count



# ---------- AUTO RUN ----------
def worker():
    for ig, data in targets["targets"].items():
        send_ig_posts(ig)

    dashboard()



# ---------- MAIN ----------
def main():
    updater = Updater(BOT_TOKEN)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler(["addig", "เพิ่ม"], add_ig))
    dp.add_handler(CommandHandler(["delig", "ลบ"], del_ig))
    dp.add_handler(CommandHandler(["status", "สถานะ"], lambda u, c: dashboard()))
    dp.add_handler(CommandHandler(["id", "ไอดี"], show_id))
    dp.add_handler(CommandHandler(["help", "ช่วยเหลือ"], help_cmd))

    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    if targets["summary_chat"] is None:
        print("⚠ กรุณาตั้งค่า summary_chat ใน targets.json ก่อน")
    worker()  # GitHub Actions เรียกตอนรัน
    main()
