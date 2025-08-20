import requests

url = "http://127.0.0.1:8000/upload-pdf/"  # Update to match your FastAPI route
file_path = r"C:/Users/Unam/Downloads/dummy.pdf"

with open(file_path, "rb") as f:
    files = {"file": ("dummy.pdf", f, "application/pdf")}
    response = requests.post(url, files=files)

print("Status code:", response.status_code)
try:
    print("Response JSON:", response.json())
except Exception:
    print("Response Text:", response.text)