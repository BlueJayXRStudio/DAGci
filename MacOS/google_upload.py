"""
testing google drive upload
"""
import sys, os, _bootstrap
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from dotenv import load_dotenv
from pathlib import Path

this_path = Path(__file__).resolve()
load_dotenv(this_path.parent.parent / "envs/gcp.env")
FOLDER_ID = os.getenv("FOLDER_ID")

# Load your JSON credential file
creds = service_account.Credentials.from_service_account_file(
    this_path.parent.parent / "envs/gcp.json",
    scopes=["https://www.googleapis.com/auth/drive"]
)

service = build("drive", "v3", credentials=creds)

# results = service.files().list(
#     q=f"'{FOLDER_ID}' in parents",
#     fields="files(id, name)",
#     supportsAllDrives=True,
#     includeItemsFromAllDrives=True
# ).execute()
# print(results)

file_metadata = {
    "name": "apk1.zip",
    "parents": [FOLDER_ID]
}

media = MediaFileUpload(this_path.parent.parent / "Android/builds/app.zip", resumable=True)

file = service.files().create(
    body=file_metadata,
    media_body=media,
    fields="id",
    supportsAllDrives=True # REQUIRED for Shared Drives
).execute()

print("Uploaded file ID:", file["id"])

service.permissions().create(
    fileId=file["id"],
    body={"role": "reader", "type": "anyone"},
    supportsAllDrives=True
).execute()

print("Public download link:")
print(f"https://drive.google.com/uc?id={file['id']}&export=download")
