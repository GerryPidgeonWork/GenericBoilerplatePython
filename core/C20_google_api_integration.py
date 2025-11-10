# ====================================================================================================
# C20_google_api_integration.py
# ----------------------------------------------------------------------------------------------------
# Provides Google Drive API authentication and file operations.
#
# Purpose:
#   - Authenticate with the Google Drive API using OAuth 2.0.
#   - Upload, download, and list files on Google Drive.
#   - Support uploading Pandas DataFrames as CSV without saving locally.
#
# Notes:
#   - Requires credentials/credentials.json (OAuth 2.0 client secret).
#   - On first run, a browser window will open to grant access.
#   - Token is cached in credentials/token.json for reuse.
#
# ----------------------------------------------------------------------------------------------------
# Author:       Gerry Pidgeon
# Created:      2025-11-10
# Project:      GenericBoilerplatePython
# ====================================================================================================


# ====================================================================================================
# 1. SYSTEM IMPORTS
# ----------------------------------------------------------------------------------------------------
# Add parent directory to sys.path so this module can import other "core" packages.
# ====================================================================================================
import sys
from pathlib import Path

# --- Standard block for all modules ---
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))     # Add project root so /core/ is importable from anywhere
sys.dont_write_bytecode = True                                      # Prevent creation of __pycache__ folders

# ====================================================================================================
# 2. PROJECT IMPORTS
# ----------------------------------------------------------------------------------------------------
# Bring in standard libraries and settings from the central import hub.
# Typically used to import core utilities like C03_logging_handler or C01_set_file_paths.
# ====================================================================================================
from core.C00_set_packages import *                                 # Imports all universal packages
from core.C01_set_file_paths import PROJECT_ROOT, LOGS_DIR          # Access project root and log directory
from core.C03_logging_handler import get_logger, log_exception      # Unified logging utilities

# --- Initialise logger ---
logger = get_logger(__name__)

# Other required packages
from core.C01_set_file_paths import GDRIVE_CREDENTIALS_FILE, GDRIVE_TOKEN_FILE
from core.C02_system_processes import user_download_folder
from core.C09_io_utils import MediaIoBaseDownload

# ====================================================================================================
# 3. CONSTANTS
# ----------------------------------------------------------------------------------------------------
SCOPES = ['https://www.googleapis.com/auth/drive']


# ====================================================================================================
# 4. AUTHENTICATION
# ----------------------------------------------------------------------------------------------------
def get_drive_service():
    """
    Authenticate with the Google Drive API using OAuth 2.0.

    This function:
      - Loads credentials from a saved token file if available.
      - If not found or expired, runs an OAuth browser flow.
      - Returns a service object for subsequent API operations.

    Returns:
        service (googleapiclient.discovery.Resource | None):
            Authenticated Google Drive API service object, or None if authentication fails.
    """
    creds = None
    if os.path.exists(GDRIVE_TOKEN_FILE):
        try:
            creds = Credentials.from_authorized_user_file(GDRIVE_TOKEN_FILE, SCOPES)
            logger.info(f"🔑 Loaded existing token: {GDRIVE_TOKEN_FILE.name}")
        except Exception as e:
            logger.warning(f"⚠️  Token load failed, re-authenticating: {e}")
            creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                logger.info("🔄 Token refreshed successfully.")
            except Exception as e:
                logger.error(f"❌ Token refresh failed: {e}")
                return None
        else:
            if not os.path.exists(GDRIVE_CREDENTIALS_FILE):
                logger.error(f"❌ Missing credentials: {GDRIVE_CREDENTIALS_FILE}")
                return None
            try:
                flow = InstalledAppFlow.from_client_secrets_file(GDRIVE_CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
                logger.info("🌐 Authenticated successfully via browser.")
            except Exception as e:
                logger.error(f"❌ OAuth error: {e}")
                return None

        try:
            with open(GDRIVE_TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
            logger.info(f"💾 Token saved: {GDRIVE_TOKEN_FILE.name}")
        except Exception as e:
            logger.warning(f"⚠️  Could not save token: {e}")

    try:
        service = build('drive', 'v3', credentials=creds)
        logger.info("✅ Google Drive API service initialised.")
        return service
    except HttpError as e:
        logger.error(f"❌ HTTP error during service build: {e}")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
    return None


# ====================================================================================================
# 5. HELPER FUNCTIONS
# ----------------------------------------------------------------------------------------------------
def find_folder_id(service, folder_name: str) -> str | None:
    """
    Find the ID of a Google Drive folder by name.

    Args:
        service (Resource): Authenticated Google Drive API service.
        folder_name (str): The name of the folder to find.

    Returns:
        str | None: Folder ID if found, otherwise None.
    """
    if not service:
        logger.error("❌ Invalid Drive service object.")
        return None

    try:
        query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
        results = service.files().list(q=query, pageSize=1, fields="files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            logger.warning(f"⚠️  Folder not found: '{folder_name}'")
            return None
        folder_id = items[0]['id']
        logger.info(f"📁 Found folder '{folder_name}' (ID: {folder_id})")
        return folder_id
    except HttpError as e:
        logger.error(f"❌ Error finding folder: {e}")
        return None


def find_file_id(service, file_name: str, in_folder_id: str | None = None) -> str | None:
    """
    Find the ID of a Google Drive file by name.

    Args:
        service (Resource): Authenticated Drive service.
        file_name (str): The file name to search for.
        in_folder_id (str | None): Optional folder ID to restrict search.

    Returns:
        str | None: File ID if found, otherwise None.
    """
    if not service:
        logger.error("❌ Invalid Drive service object.")
        return None

    try:
        query = f"name='{file_name}' and mimeType!='application/vnd.google-apps.folder' and trashed=false"
        if in_folder_id:
            query += f" and '{in_folder_id}' in parents"
        results = service.files().list(q=query, pageSize=1, fields="files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            logger.warning(f"⚠️  File not found: '{file_name}'")
            return None
        file_id = items[0]['id']
        logger.info(f"📄 Found file '{file_name}' (ID: {file_id})")
        return file_id
    except HttpError as e:
        logger.error(f"❌ Error finding file: {e}")
        return None


# ====================================================================================================
# 6. FILE OPERATIONS
# ----------------------------------------------------------------------------------------------------
def upload_file(service, local_path: Path, folder_id: str | None = None, filename: str | None = None) -> str | None:
    """
    Upload a local file to Google Drive.

    Args:
        service (Resource): Authenticated Drive service.
        local_path (Path): Local file path to upload.
        folder_id (str | None): Target folder ID (optional).
        filename (str | None): Rename uploaded file (optional).

    Returns:
        str | None: Uploaded file ID, or None if upload failed.
    """
    if not service:
        logger.error("❌ Invalid Drive service object.")
        return None
    if not local_path.exists():
        logger.error(f"❌ File not found: {local_path}")
        return None

    try:
        filename = filename or local_path.name
        metadata: dict[str, Any] = {"name": filename}
        if folder_id:
            metadata["parents"] = [folder_id]

        media = MediaFileUpload(local_path, resumable=True)
        uploaded = service.files().create(body=metadata, media_body=media, fields='id').execute()
        file_id = uploaded.get('id')
        logger.info(f"✅ Uploaded '{filename}' (ID: {file_id})")
        return file_id
    except HttpError as e:
        logger.error(f"❌ Upload error: {e}")
        return None


def upload_dataframe_as_csv(service, csv_buffer: io.StringIO, filename: str, folder_id: str | None = None) -> str | None:
    """
    Upload a Pandas DataFrame to Google Drive directly from memory as a CSV.

    Args:
        service (Resource): Authenticated Drive service.
        csv_buffer (io.StringIO): CSV data buffer from df.to_csv().
        filename (str): Desired file name (should end with '.csv').
        folder_id (str | None): Optional folder ID to upload into.

    Returns:
        str | None: File ID of uploaded CSV, or None if failed.
    """
    if not service:
        logger.error("❌ Invalid Drive service object.")
        return None

    try:
        bytes_data = io.BytesIO(csv_buffer.getvalue().encode('utf-8'))
        metadata: dict[str, Any] = {'name': filename}
        if folder_id:
            metadata['parents'] = [folder_id]

        media = MediaIoBaseUpload(bytes_data, mimetype='text/csv', resumable=True)
        uploaded = service.files().create(body=metadata, media_body=media, fields='id').execute()
        file_id = uploaded.get('id')
        logger.info(f"✅ Uploaded DataFrame as '{filename}' (ID: {file_id})")
        return file_id
    except HttpError as e:
        logger.error(f"❌ Upload error: {e}")
        return None


def download_file(service, file_id: str, local_path: Path) -> None:
    """
    Download a file from Google Drive to a local destination.

    Args:
        service (Resource): Authenticated Drive service.
        file_id (str): Google Drive file ID.
        local_path (Path): Local path where the file should be saved.
    """
    if not service:
        logger.error("❌ Invalid Drive service object.")
        return

    try:
        local_path.parent.mkdir(parents=True, exist_ok=True)
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            logger.info(f"⬇️  Download progress: {int(status.progress() * 100)}%")
        with open(local_path, 'wb') as f:
            f.write(fh.getbuffer())
        logger.info(f"✅ File saved to: {local_path}")
    except HttpError as e:
        logger.error(f"❌ Download error: {e}")


# ====================================================================================================
# 7. SELF TEST
# ----------------------------------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Standalone self-test for verifying authentication and Drive access.
    Lists up to 5 files after authenticating.
    """
    logger.info("🔍 Running C20_google_api_integration self-test...")
    service = get_drive_service()
    if service:
        try:
            results = service.files().list(pageSize=5, fields="files(id, name)").execute()
            files = results.get('files', [])
            if not files:
                logger.warning("⚠️  No files found in Google Drive.")
            else:
                for f in files:
                    logger.info(f"📄 {f['name']} (ID: {f['id']})")
        except Exception as e:
            logger.error(f"❌ Listing error: {e}")
    logger.info("✅ Google Drive API self-test complete.")
