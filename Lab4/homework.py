import socket
from bs4 import BeautifulSoup

def parse_products_html(html_content):
    products_list = []

    soup = BeautifulSoup(html_content, 'html.parser')

    # Find all <ul> tags containing product information
    ul_tags = soup.find_all('ul')

    for ul_tag in ul_tags:
        product_dict = {}
        li_tags = ul_tag.find_all('li')
        for li in li_tags:
            key, value = li.get_text().split(': ', 1)
            if key and value:
                product_dict[key] = value
        products_list.append(product_dict)

    return products_list

def send_tcp_request(url, port, endpoint):
    try:
        with socket.create_connection((url, port)) as s:
            s.settimeout(2)

            request = f"GET {endpoint} HTTP/1.1\r\nHost: {url}\r\n\r\n"
            s.send(request.encode())

            if "product" in endpoint:
                print(parse_products_html(s.recv(2048).decode("utf-8")))
            else:
                print(s.recv(2048).decode("utf-8"))

    except Exception as e:
        print(f"Error: {str(e)}")

def main():
    url = "127.0.0.1"
    port = 8081

    endpoints = ["/products", "/product/1", "/product/2", "/", "/contacts", "/about"]

    for endpoint in endpoints:
        send_tcp_request(url, port, endpoint)

if __name__ == "__main__":
    main()
