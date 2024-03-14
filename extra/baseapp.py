from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import socket

app = Flask(__name__)

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
        "Domain": domain,
        "Server IP": ip,
        "Location": "N/A",  # You can use IP geolocation APIs to get this information
        "ASN": "N/A",
        "ISP": "N/A",
        "Organization": "N/A"
    }

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

@app.route('/')
def analyze_website():
    url = request.args.get('url')

    if not url:
        return jsonify({"error": "URL parameter is required"}), 400

    try:
        response = requests.get(url)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 400

    domain_info = get_domain_info(url)
    subdomain_info = get_subdomain_info(response.content)

    return jsonify({
        "Domain Information": domain_info,
        "Subdomain Information": subdomain_info
    })

if __name__ == '__main__':
    app.run(debug=True)
