import base64
import json
import os
import socket
import threading

class ChatClient:
    HELP_MSG = """  
    /help - display all commands
    /list - list all files on the server
    /download - download a file from the server
    /upload - upload a file to the server
    /exit - terminate the program
    """

    def __init__(self, host, port):
        self.HOST = host
        self.PORT = port
        self.CLIENT_DIR_BASE = "CLIENT_MEDIA"
        self.MAX_MESSAGE_SIZE = 2 ** 20
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self.client_socket.connect((self.HOST, self.PORT))
        print(f"Client connected to {self.HOST}:{self.PORT}")

        username = input("Enter username: ")
        room = input("Enter room: ")

        connect_message = {
            "message_type": "connect",
            "payload": {
                "name": username,
                "room": room
            }
        }

        self.client_socket.send(json.dumps(connect_message).encode('utf-8'))

        return username, room

    def send_msg(self, text):
        message = {
            "message_type": "message",
            "payload": {
                "text": text
            }
        }
        self.client_socket.send(json.dumps(message).encode('utf-8'))

    def send_file(self, path, name):
        with open(path, "rb") as file:
            content = base64.b64encode(file.read()).decode('utf-8')

        upload_file_message = {
            "message_type": "upload",
            "payload": {
                "file_name": name,
                "file_content": content,
            }
        }

        self.client_socket.send(json.dumps(upload_file_message).encode('utf-8'))

    def download(self, payload, username):
        CLIENT_FILES_DIR = f"{self.CLIENT_DIR_BASE}_{username}"

        name = payload.get("file_name")
        content = payload.get("file_content")

        if not os.path.exists(CLIENT_FILES_DIR):
            os.makedirs(CLIENT_FILES_DIR)

        with open(os.path.join(CLIENT_FILES_DIR, name), "wb") as file:
            file.write(base64.b64decode(content))

        print(f"\nFile {name} was downloaded successfully.")

    def list_client_media(self, folder_path):
        files = []

        for filename in os.listdir(folder_path):
            if os.path.isfile(os.path.join(folder_path, filename)):
                files.append(filename)

        return files

    def list_server_media(self, payload):
        server_media = payload.get("media", [])

        if server_media:
            print("\nAvailable server media:")

            for i, name in enumerate(server_media, start=1):
                print(f"{i}. {name}")
        else:
            print("\nNo files available on the server.")

    def get_server_media(self):
        files_list_request = {
            "message_type": "server_media",
            "payload": {}
        }

        self.client_socket.send(json.dumps(files_list_request).encode('utf-8'))

    def get_server_file(self, name):
        download_file_request = {
            "message_type": "download",
            "payload": {
                "file_name": name
            }
        }

        self.client_socket.send(json.dumps(download_file_request).encode('utf-8'))

    def get_server_message(self, payload):
        message = payload.get("message")
        print(f"\n{message}")

    def get_room_message(self, payload):
        message = payload.get("message")
        sender = payload.get("sender")
        print(f"\n{sender}: {message}")

    def receive_messages(self):
        while True:
            message = self.client_socket.recv(self.MAX_MESSAGE_SIZE).decode('utf-8')

            if not message:
                break

            try:
                message_dict = json.loads(message)
                message_type = message_dict.get("message_type")
                payload = message_dict.get("payload")

                if message_type == "connect_ack":
                    self.get_server_message(payload)
                elif message_type == "notification":
                    self.get_server_message(payload)
                elif message_type == "message":
                    self.get_room_message(payload)
                elif message_type == "file":
                    self.download(payload, self.username)
                elif message_type == "server_media":
                    self.list_server_media(payload)

            except json.JSONDecodeError:
                print(f"\n{message}")

    def upload(self):
        file_path = input("Enter the absolute path to the file to upload: ").replace("\"", "")

        if not os.path.isfile(file_path):
            print(f"No such file at {file_path}.")
            return

        try:
            file_name = os.path.basename(file_path)
            self.send_file(file_path, file_name)
        except Exception as e:
            print(f"An error occurred during upload: {e}")

    def run(self):
        self.username, self.room = self.connect()

        print(self.HELP_MSG)

        receive_thread = threading.Thread(target=self.receive_messages)
        receive_thread.daemon = True
        receive_thread.start()

        while True:
            text = input().strip().lower()

            if text == '/help':
                print(self.HELP_MSG)
            elif text == '/exit':
                break
            elif text == '/upload':
                self.upload()
            elif text == '/list':
                self.get_server_media()
            elif text == '/download':
                file_name = input("Enter the name of the file to download: ")
                self.get_server_file(file_name)
            else:
                self.send_msg(text)

        self.client_socket.close()

if __name__ == "__main__":
    HOST = '127.0.0.1'
    PORT = 8080

    chat_client = ChatClient(HOST, PORT)
    chat_client.run()