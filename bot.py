aNotepad aNotepad

bot tele
Share Bookmark Save Copy
VPNBook
import json
import os
import asyncio
import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from asyncio import Lock
from dotenv import load_dotenv

# Load biến môi trường từ .env
load_dotenv("env.txt")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Cấu hình
FILE_PATH = "accounts.txt"
LOG_PATH = "used_log.txt"
QUOTA_PATH = "user_quota.json"
MAX_PER_DAY = 5

# Lock để xử lý đồng bộ
lock = Lock()

# Load quota từ file
def load_quota():
    if os.path.exists(QUOTA_PATH):
        with open(QUOTA_PATH, 'r') as f:
            return json.load(f)
    return {}

# Lưu quota vào file
def save_quota(quota):
    with open(QUOTA_PATH, 'w') as f:
        json.dump(quota, f)

# Reset quota theo ngày
def reset_daily_quota(quota):
    today = datetime.date.today().isoformat()
    for user_id in list(quota.keys()):
        if quota[user_id]["date"] != today:
            quota[user_id] = {"count": 0, "date": today}
    return quota

# Lấy tài khoản đầu tiên trong file
def get_next_account():
    with open(FILE_PATH, "r") as file:
        lines = file.readlines()

    if not lines:
        return None

    account = lines[0].strip()

    with open(FILE_PATH, "w") as file:
        file.writelines(lines[1:])  # Ghi lại các dòng còn lại

    return account

# Ghi log người dùng
def log_user(user_id, username, account):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{now}] {user_id} ({username}): {account}\n"
    with open(LOG_PATH, "a") as log_file:
        log_file.write(log_line)

# Lệnh /acc
async def acc_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    username = update.effective_user.username or "NoUsername"

    async with lock:
        quota = load_quota()
        quota = reset_daily_quota(quota)

        if user_id not in quota:
            quota[user_id] = {"count": 0, "date": datetime.date.today().isoformat()}

        if quota[user_id]["count"] >= MAX_PER_DAY:
            await update.message.reply_text("Bạn đã nhận tối đa 5 tài khoản hôm nay.")
            return

        account = get_next_account()
        if not account:
            await update.message.reply_text("Hết tài khoản!")
            return

        quota[user_id]["count"] += 1
        save_quota(quota)
        log_user(user_id, username, account)

        await update.message.reply_text(f"Tài khoản của bạn: {account}")

# Lệnh /check
async def check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    async with lock:
        quota = load_quota()
        quota = reset_daily_quota(quota)

        user_data = quota.get(user_id, {"count": 0})
        remaining = MAX_PER_DAY - user_data.get("count", 0)

        await update.message.reply_text(f"Bạn còn {remaining} lượt nhận tài khoản hôm nay.")

# Khởi động bot
async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("acc", acc_handler))
    app.add_handler(CommandHandler("check", check_handler))

    print("Bot đang chạy...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
