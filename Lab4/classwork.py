import socket
import signal
import sys
import threading
import json

HOST = '127.0.0.1'
PORT = 8081

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)
print(f"Server is listening on {HOST}:{PORT}")

def handle_request(client_socket):
    request_data = client_socket.recv(1024).decode('utf-8')
    print(f"Received Request:\n{request_data}")

    method, path = parse_request(request_data)

    response_content, status_code = route_request(path)

    response = f'HTTP/1.1 {status_code} OK\nContent-Type: text/html\n\n{response_content}'
    client_socket.send(response.encode('utf-8'))

    client_socket.close()

def parse_request(request_data):
    request_lines = request_data.split('\n')
    method, path, _ = request_lines[0].strip().split()
    return method, path

def route_request(path):
    routes = {
        '/': home_page,
        '/about': about_page,
        '/contacts': contacts_page,
        '/products': products_page,
    }

    if path.startswith('/product/'):
        return product_page(path)

    return routes.get(path, not_found_page)()

def home_page():
    return 'Home page. Welcome!', 200

def about_page():
    return 'About page.', 200

def contacts_page():
    return 'Contacts: (+373) 00 000 000\nLocation: Moldova', 200

def products_page():
    with open("products.json", "r") as file:
        json_data = json.load(file)

    products = json_data.get("products", [])
    response_content = ''

    for product_nr, product in enumerate(products, start=1):
        response_content += f"<a href=\"/product/{product_nr}\">Product: {product_nr}</a><br>"
        response_content += "<ul>"
        for key, value in product.items():
            response_content += f"<li>{key}: {value}</li><br>"
        response_content += "</ul><br>"

    return response_content, 200

def product_page(path):
    product_nr = int(path.replace("/product/", ""))
    with open("products.json", "r") as file:
        json_data = json.load(file)

    products = json_data.get("products", [])
    response_content = ''

    if 0 < product_nr <= len(products):
        product = products[product_nr - 1]
        response_content += f"Product: {product_nr}<br>"
        response_content += "<ul>"
        for key, value in product.items():
            response_content += f"<li>{key}: {value}</li><br>"
        response_content += "</ul><br>"
        status_code = 200
    else:
        response_content = '404 Not Found'
        status_code = 404

    return response_content, status_code

def not_found_page():
    return '404 Not Found', 404

def signal_handler(sig, frame):
    print("\nShutting down the server...")
    server_socket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

while True:
    client_socket, client_address = server_socket.accept()
    print(f"Accepted connection from {client_address[0]}:{client_address[1]}")

    client_handler = threading.Thread(target=handle_request, args=(client_socket,))
    client_handler.start()
