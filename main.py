from flask import Flask, jsonify, send_file
from pyfactorybridge import API
from dotenv import load_dotenv
import pyfactorybridge
import platform
import socket
import os

app = Flask(__name__)

SATISFACTORY_ENV_FILE_PATH = None

if SATISFACTORY_ENV_FILE_PATH == None or SATISFACTORY_ENV_FILE_PATH == '':
    load_dotenv()
else:
    load_dotenv(SATISFACTORY_ENV_FILE_PATH)

SATISFACTORY_SERVER_TOKEN = os.getenv('SATISFACTORY_TOKEN')
SATISFACTORY_SERVER_IP = os.getenv('SATISFACTORY_IP')
SATISFACTORY_SERVER_PORT = os.getenv('SATISFACTORY_PORT')

SATISFACTORY_WINDOWS_IMAGE_PATH = str(os.getenv('WINDOWS_IMAGE_PATH'))
SATISFACTORY_LINUX_IMAGE_PATH = str(os.getenv('LINUX_IMAGE_PATH'))

try:
    SATISFACTORY_CHECK_SERVER_TIMEOUT = int(os.getenv('CHECK_SERVER_TIMEOUT'))
except:
    SATISFACTORY_CHECK_SERVER_TIMEOUT = None

SATISFACTORY_IMAGE_URL_ENDPOINT = str(os.getenv('IMAGE_URL_ENDPOINT'))
SATISFACTORY_PARSED_API_URL_ENDPOINT = str(os.getenv('PARSED_API_URL_ENDPOINT'))

if SATISFACTORY_IMAGE_URL_ENDPOINT == None or SATISFACTORY_IMAGE_URL_ENDPOINT == '':
    SATISFACTORY_IMAGE_URL_ENDPOINT = "/image"
if SATISFACTORY_PARSED_API_URL_ENDPOINT == None or SATISFACTORY_PARSED_API_URL_ENDPOINT == '':
    SATISFACTORY_PARSED_API_URL_ENDPOINT = "/"

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

if __name__ == "__main__":
    
    if os.getenv('SATISFACTORY_BIND_IP') == None or os.getenv('SATISFACTORY_BIND_IP') == '':
        SATISFACTORY_BIND_IP = "0.0.0.0"
    else:
        SATISFACTORY_BIND_IP = str(os.getenv('SATISFACTORY_BIND_IP'))

    if os.getenv('SATISFACTORY_BIND_PORT') == None or  os.getenv('SATISFACTORY_BIND_PORT') == '':
        SATISFACTORY_BIND_PORT = 6052
    else:
        SATISFACTORY_BIND_PORT = int(os.getenv('SATISFACTORY_BIND_PORT'))
    
    app.run(host=SATISFACTORY_BIND_IP, port=SATISFACTORY_BIND_PORT, debug=True)