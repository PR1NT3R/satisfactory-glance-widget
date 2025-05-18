from flask import Flask, jsonify, send_file
from pyfactorybridge import API
from dotenv import load_dotenv
import pyfactorybridge
import platform
import socket
import sys
import os

app = Flask(__name__)

def get_env(name, default=None, output_type="str", if_none="None"):
    if os.getenv(name) == None or os.getenv(name) == '':
        if if_none != "None":
            print(if_none)
            sys.exit(1)
        return default
    else:
        try:
            if output_type == "str":
                return str(os.getenv(name))
            else:
                return int(os.getenv(name))
        except:
            return os.getenv(name)


SATISFACTORY_ENV_FILE_PATH = None
if SATISFACTORY_ENV_FILE_PATH == None or SATISFACTORY_ENV_FILE_PATH == '':
    load_dotenv()
else:
    load_dotenv(SATISFACTORY_ENV_FILE_PATH)

SATISFACTORY_SERVER_TOKEN = get_env('SATISFACTORY_SERVER_TOKEN', "str", if_none="Please specify the server token!")
SATISFACTORY_SERVER_IP = get_env('SATISFACTORY_SERVER_IP', "str", if_none="Please specify the server ip!")
SATISFACTORY_SERVER_PORT = get_env('SATISFACTORY_SERVER_PORT', "str", if_none="Please specify the server port!")

SATISFACTORY_SERVE_IMAGE_BOOL = get_env('SATISFACTORY_SERVE_IMAGE_BOOL', "false")
if SATISFACTORY_SERVE_IMAGE_BOOL.lower() == "true":
    SATISFACTORY_WINDOWS_IMAGE_PATH = get_env('SATISFACTORY_WINDOWS_IMAGE_PATH', if_none="Please specify a windows image path!")
    SATISFACTORY_LINUX_IMAGE_PATH = get_env('SATISFACTORY_LINUX_IMAGE_PATH', if_none="Please specify a linux/macos image path!")

SATISFACTORY_CHECK_SERVER_TIMEOUT = get_env('SATISFACTORY_CHECK_SERVER_TIMEOUT', output_type="int")
SATISFACTORY_IMAGE_URL_ENDPOINT = get_env('SATISFACTORY_IMAGE_URL_ENDPOINT', "/image")
SATISFACTORY_PARSED_API_URL_ENDPOINT = get_env('SATISFACTORY_PARSED_API_URL_ENDPOINT', "/")

def is_server_reachable(host, port, timeout=1):
    """Check if the server is reachable by attempting a socket connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, int(port)))
        sock.close()
        return result == 0  # 0 means connection successful
    except Exception as e:
        # print(f"Socket error: {e}")
        return False

@app.route(SATISFACTORY_PARSED_API_URL_ENDPOINT)
def index():
    if os.getenv('CHECK_SERVER_TIMEOUT') == None or os.getenv('CHECK_SERVER_TIMEOUT') == '':
        reachable = is_server_reachable(SATISFACTORY_SERVER_IP, SATISFACTORY_SERVER_PORT)
    else:
        reachable = is_server_reachable(SATISFACTORY_SERVER_IP, SATISFACTORY_SERVER_PORT, SATISFACTORY_CHECK_SERVER_TIMEOUT)
    if reachable:
        try:
            satisfactory = API(address=f"{SATISFACTORY_SERVER_IP}:{SATISFACTORY_SERVER_PORT}", token=SATISFACTORY_SERVER_TOKEN)
            if satisfactory.get_server_health()["health"] != "healthy":
                health = False
            health = True

            server_game_state = satisfactory.query_server_state()["serverGameState"]
            try:
                milestone = server_game_state["activeSchematic"].split("/")[-1].split("_")[-2]
            except:
                milestone = "None"
            try:
                phase = server_game_state["gamePhase"].split("_")[-1].split("'")[0]
            except:
                phase = "None"

            paused = server_game_state["isGamePaused"]

            try:
                time_difference = server_game_state["totalGameDuration"]
                relative_time = f"{int(time_difference // 3600):02}:{int((time_difference % 3600) // 60):02}:{int(time_difference % 60):02}"
                hours_on_save = relative_time
            except:
                hours_on_save = "N/A"

            try:
                players = f"{server_game_state['numConnectedPlayers']}/{server_game_state['playerLimit']}"
            except:
                players = "N/A"

        except pyfactorybridge.exceptions.ServerError:
            # print("A")
            health = False
            players = "N/A"
            hours_on_save = "N/A"
            phase = "N/A"
            milestone = "N/A"
            paused = True
    else:
        health = False
        players = "N/A"
        hours_on_save = "N/A"
        phase = "N/A"
        milestone = "N/A"
        paused = True

    result = {
        "healthy": health,
        "players": players,
        "hours_on_save": hours_on_save,
        "phase": phase,
        "milestone": milestone,
        "paused": paused
    }
    return jsonify(result)

@app.route(SATISFACTORY_IMAGE_URL_ENDPOINT)
def serve_image():
    if SATISFACTORY_SERVE_IMAGE_BOOL.lower() == "true":
        # Determine the correct file path for the image, this is because I sometimes like to debug on my windows machine and run "in produciton" on my linux machine
        if platform.system() == 'Windows':
            image_path = SATISFACTORY_WINDOWS_IMAGE_PATH
        else:  # POSIX
            image_path = SATISFACTORY_LINUX_IMAGE_PATH
        
        # Check if the image is present at the specified file path
        if os.path.isfile(image_path):
            return send_file(image_path, mimetype='image/jpeg')
        else:
            return f"Error: Image not found at {image_path}", 404
    else:
        return "Warning: image serving is disabled", 404

if __name__ == "__main__":
    SATISFACTORY_BIND_IP = get_env('SATISFACTORY_BIND_IP', "0.0.0.0")
    SATISFACTORY_BIND_PORT = get_env('SATISFACTORY_BIND_PORT', 6052, "int")
    
    app.run(host=SATISFACTORY_BIND_IP, port=SATISFACTORY_BIND_PORT, debug=True)