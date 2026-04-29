import asyncio
import websockets
import json
import os

connected = {}

async def handler(ws):
    client_id = None
    try:
        msg = await ws.recv()
        data = json.loads(msg)
        if data.get("type") == "register":
            client_id = data["id"]
            connected[client_id] = ws
            print(f"[+] {client_id} connected")
        else:
            await ws.send(json.dumps({"error": "First message must be register"}))
            return

        async for msg in ws:
            data = json.loads(msg)
            target = data.get("to")
            if target in connected:
                await connected[target].send(json.dumps(data))
            else:
                await ws.send(json.dumps({"error": f"{target} not connected"}))
    except Exception as e:
        pass
    finally:
        if client_id:
            del connected[client_id]
            print(f"[-] {client_id} disconnected")

async def main():
    port = int(os.environ.get("PORT", 8765))
    print(f"[*] Relay server started on port {port}")
    async with websockets.serve(handler, "0.0.0.0", port):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
