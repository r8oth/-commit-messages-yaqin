import subprocess
import re
import os
from datetime import datetime
import requests
import time

# ===== إعدادات المشروع =====
project_path = r"C:\Users\ZEUS\Desktop\yaqeen nori zamel"
os.chdir(project_path)

log_file = "commit_log.txt"

# ===== إعدادات التليجرام =====
use_telegram = True
bot_token = "8655043920:AAHs1uenSdo5P0c-OSY_FNLxA4g9euSZ8J8"
chat_id = "784582542"


def send_telegram(message):
    if not use_telegram:
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message
    }

    try:
        response = requests.post(url, data=data, timeout=10)

        if response.status_code != 200:
            print("❌ Telegram HTTP Error:", response.status_code)
            print(response.text)
        else:
            result = response.json()
            if not result.get("ok"):
                print("❌ Telegram API Error:", result)

    except Exception as e:
        print("❌ Telegram exception:", e)


def get_git_diff():
    result = subprocess.run(
        ["git", "diff", "-U0"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="ignore"
    )
    return result.stdout


def analyze_diff(diff):
    files_changes = {}
    hunk_pattern = re.compile(r'^@@ -(\d+),?\d* \+(\d+),?\d* @@')

    current_file = None
    old_line = 0
    new_line = 0

    for line in diff.splitlines():

        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                current_file = parts[2][2:]

                if current_file == "commit_log.txt":
                    current_file = None
                    continue

                files_changes[current_file] = []

        hunk = hunk_pattern.match(line)
        if hunk:
            old_line = int(hunk.group(1))
            new_line = int(hunk.group(2))
            continue

        if current_file is None:
            continue

        if line.startswith("-") and not line.startswith("---"):
            files_changes[current_file].append({
                "type": "change",
                "old_line": old_line,
                "old_content": line[1:].strip(),
                "new_content": None
            })
            old_line += 1

        elif line.startswith("+") and not line.startswith("+++"):
            if files_changes[current_file] and files_changes[current_file][-1]["new_content"] is None:
                files_changes[current_file][-1]["new_content"] = line[1:].strip()
                files_changes[current_file][-1]["new_line"] = new_line
            else:
                files_changes[current_file].append({
                    "type": "add",
                    "new_line": new_line,
                    "new_content": line[1:].strip()
                })

            new_line += 1

        else:
            old_line += 1
            new_line += 1

    return files_changes


def build_detailed_message(changes):
    messages = []

    for file, change_list in changes.items():
        for change in change_list:

            if change.get("type") == "change" and change.get("new_content"):
                messages.append(
                    f"✏️ {file}\n"
                    f"Line {change['old_line']} قبل:\n{change['old_content']}\n"
                    f"Line {change.get('new_line','?')} بعد:\n{change['new_content']}"
                )

            elif change.get("type") == "add":
                messages.append(
                    f"➕ {file} | Line {change['new_line']} إضافة:\n{change['new_content']}"
                )

    return "\n\n".join(messages[:20])


def git_add_and_commit(message):
    subprocess.run(["git", "add", "."], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    subprocess.run(
        ["git", "commit", "-m", message],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def save_log(message):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now()} - {message}\n")
        
        # ===== المراقبة =====

print("🚀 Auto-commit running...")

last_diff = ""

while True:
    try:
        diff = get_git_diff()

        if not diff or diff == last_diff:
            time.sleep(3)
            continue

        last_diff = diff

        changes = analyze_diff(diff)

        if changes:
            message = build_detailed_message(changes)

            git_add_and_commit("Auto commit")
            save_log(message)

            send_telegram(f"🔔 Changes detected:\n\n{message}")

            print("✅ Commit sent")

        time.sleep(2)

    except KeyboardInterrupt:
        print("🛑 Stopped")
        break

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(2)
print("اتمنا عجبكم المشروع وشكراالطالبة يقين نوري زامل 😁")