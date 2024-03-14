from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import socket

app = Flask(__name__)
socketio = SocketIO(app)

# Function to get domain information
def get_domain_info(url):
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    try:
        ip = socket.gethostbyname(domain)
    except socket.gaierror:
        ip = "Unknown"

    # You can implement logic to retrieve other domain information like ASN, ISP, etc.
    # This might require using external APIs or libraries
    
    return {
        "ip": ip,
        "isp": "N/A",  # Placeholder, you can replace this with actual ISP information
        "organization": "N/A",  # Placeholder, you can replace this with actual organization information
        "asn": "N/A",  # Placeholder, you can replace this with actual ASN information
        "location": "N/A"  # Placeholder, you can replace this with actual location information
    }

# Function to get subdomain information
def get_subdomain_info(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')

    # Extracting subdomains, external stylesheets, javascripts, images, iframe sources, and anchor tag references
    subdomains = set()
    stylesheets = set()
    javascripts = set()
    images = set()
    iframes = set()
    anchors = set()

    for tag in soup.find_all(["a", "img", "link", "script", "iframe"]):
        if tag.name == "a" and tag.get("href"):
            anchors.add(tag.get("href"))
        elif tag.name == "img" and tag.get("src"):
            images.add(tag.get("src"))
        elif tag.name == "link" and tag.get("rel") == ["stylesheet"] and tag.get("href"):
            stylesheets.add(tag.get("href"))
        elif tag.name == "script" and tag.get("src"):
            javascripts.add(tag.get("src"))
        elif tag.name == "iframe" and tag.get("src"):
            iframes.add(tag.get("src"))

    return {
        "Subdomains": list(subdomains),
        "Stylesheets": list(stylesheets),
        "Javascripts": list(javascripts),
        "Images": list(images),
        "Iframes": list(iframes),
        "Anchors": list(anchors)
    }

# Function to get asset domains
def get_asset_domains(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    asset_domains = {
        "javascripts": set(),
        "stylesheets": set(),
        "images": set(),
        "iframes": set(),
        "anchors": set()
    }

    for tag in soup.find_all(["script", "link", "img", "iframe", "a"]):
        if tag.name == "script" and tag.get("src"):
            asset_domains["javascripts"].add(tag.get("src"))
        elif tag.name == "link" and tag.get("rel") == ["stylesheet"] and tag.get("href"):
            asset_domains["stylesheets"].add(tag.get("href"))
        elif tag.name == "img" and tag.get("src"):
            asset_domains["images"].add(tag.get("src"))
        elif tag.name == "iframe" and tag.get("src"):
            asset_domains["iframes"].add(tag.get("src"))
        elif tag.name == "a" and tag.get("href"):
            asset_domains["anchors"].add(tag.get("href"))

    return {
        "javascripts": list(asset_domains["javascripts"]),
        "stylesheets": list(asset_domains["stylesheets"]),
        "images": list(asset_domains["images"]),
        "iframes": list(asset_domains["iframes"]),
        "anchors": list(asset_domains["anchors"])
    }

# WebSocket endpoint
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('message')
def handle_message(message):
    if 'url' in message:
        url = message['url']
        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            emit('message', {'error': str(e)})
            return

        # Extracting domain information
        domain_info = get_domain_info(url)

        # Extracting subdomain information
        subdomain_info = get_subdomain_info(response.content)

        # Extracting asset domains
        asset_domains = get_asset_domains(response.content)

        # Constructing the output
        output = {
            "info": domain_info,
            "subdomains": subdomain_info["Subdomains"],
            "asset_domains": asset_domains
        }

        emit('message', {'data': output})

    elif 'operation' in message:
        operation = message['operation']
        if operation == 'get_info':
            url = message.get('url')
            if url:
                domain_info = get_domain_info(url)
                emit('message', {'data': {'info': domain_info}})
            else:
                emit('message', {'error': 'URL is missing'})

        elif operation == 'get_subdomains':
            url = message.get('url')
            if url:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    emit('message', {'error': str(e)})
                    return

                subdomain_info = get_subdomain_info(response.content)
                emit('message', {'data': {'subdomains': subdomain_info["Subdomains"]}})
            else:
                emit('message', {'error': 'URL is missing'})

        elif operation == 'get_asset_domains':
            url = message.get('url')
            if url:
                try:
                    response = requests.get(url)
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    emit('message', {'error': str(e)})
                    return

                asset_domains = get_asset_domains(response.content)
                emit('message', {'data': {'asset_domains': asset_domains}})
            else:
                emit('message', {'error': 'URL is missing'})

        else:
            emit('message', {'error': 'Invalid operation'})

    else:
        emit('message', {'error': 'Invalid message format. Message must contain "url" or "operation" attribute.'})

@app.route('/')
def index():
    return "Hello, this is a WebSocket server."

if __name__ == '__main__':
    socketio.run(app, debug=True)
