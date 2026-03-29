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
    data = {"chat_id": chat_id, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print("❌ Telegram send error:", e)


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

        # Detect file
        if line.startswith("diff --git"):
            parts = line.split()
            if len(parts) >= 3:
                current_file = parts[2][2:]
                files_changes[current_file] = []

        # Detect hunk
        hunk = hunk_pattern.match(line)
        if hunk:
            old_line = int(hunk.group(1))
            new_line = int(hunk.group(2))
            continue

        if current_file is None:
            continue

        # Removed line
        if line.startswith("-") and not line.startswith("---"):
            files_changes[current_file].append({
                "type": "remove",
                "line": old_line,
                "content": line[1:]
            })
            old_line += 1

        # Added line
        elif line.startswith("+") and not line.startswith("+++"):
            files_changes[current_file].append({
                "type": "add",
                "line": new_line,
                "content": line[1:]
            })
            new_line += 1

        else:
            old_line += 1
            new_line += 1

    return files_changes


def generate_commit_message(changes):
    messages = []

    for file, actions in changes.items():
        for action in actions:
            if action["type"] == "add":
                messages.append(f"Add in {file} (line {action['line']})")
            elif action["type"] == "remove":
                messages.append(f"Remove in {file} (line {action['line']})")

    if not messages:
        messages.append("Update code")

    # remove duplicates
    messages = list(dict.fromkeys(messages))
    return " | ".join(messages)


def git_add_and_commit(commit_message):
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", commit_message])


def save_log(commit_message, changes):
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"\n==== Commit at {datetime.now()} ====\n")
        f.write(f"Commit message: {commit_message}\n")

        for file, actions in changes.items():
            f.write(f"\n📄 File: {file}\n")
            for action in actions:
                if action["type"] == "add":
                    f.write(f"  [+] Line {action['line']}: {action['content']}\n")
                elif action["type"] == "remove":
                    f.write(f"  [-] Line {action['line']}: {action['content']}\n")

        f.write("\n")


# ===== المراقبة المستمرة =====
print("🚀 Auto-commit monitor started... Press Ctrl+C to stop.")

last_diff_snapshot = None
last_sent_commit_message = ""

while True:
    try:
        diff_text = get_git_diff()

        if diff_text and diff_text != last_diff_snapshot:
            last_diff_snapshot = diff_text

            changes = analyze_diff(diff_text)

            if changes:
                commit_message = generate_commit_message(changes)
                if commit_message != last_sent_commit_message:
                    send_telegram(f"🔹 New commit created:\n{commit_message}")
                    last_sent_commit_message = commit_message

                    git_add_and_commit(commit_message)
                    save_log(commit_message, changes)

                print("\n🔹 Suggested commit message:\n")
                print(commit_message)
                print("\n✅ Commit has been created automatically")
                print(f"📚 All commit details saved to {log_file}")

        time.sleep(5)

    except KeyboardInterrupt:
        print("\n🛑 Auto-commit monitor stopped by user.")
        break

    except Exception as e:
        print("❌ Error:", e)
        time.sleep(5)
