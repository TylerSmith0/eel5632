import requests

if __name__ == "__main__":
    data = {
        "id": "123",
        "type": "TEST",
        "spot": "",
        "key": "123"
    }
    url = "http://eel5632.tylersmith.us/data/sensor/123"
    # url = "http://127.0.0.1:5000/data/sensor/123"
    resp = requests.post(url, json=data)
    print(resp.content)