"""
Simple credential handler for encrypted GCP credentials.
"""

import os
import json
import base64
import tempfile
import logging
from pathlib import Path
from typing import Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logger = logging.getLogger(__name__)

try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    logger.warning("cryptography library not available. Cannot decrypt credentials.")


def get_gcp_credentials_path() -> Optional[str]:
    """
    Get GCP credentials file path, handling encrypted credentials.
    
    Returns:
        Path to credentials file or None if not available
    """
    # 1. Check for standard environment variable
    if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
        creds_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        if os.path.exists(creds_path):
            logger.info(f"Using GCP credentials from environment: {creds_path}")
            return creds_path
    
    # 2. Check for base64 encoded credentials in environment
    base64_creds = os.getenv('GCP_CREDENTIALS_BASE64')
    if base64_creds:
        try:
            decoded_creds = base64.b64decode(base64_creds).decode('utf-8')
            temp_file = Path(__file__).parent.parent.parent / "temp_gcp_credentials.json"
            
            with open(temp_file, 'w') as f:
                f.write(decoded_creds)
            
            logger.info("Using GCP credentials from base64 environment variable")
            return str(temp_file)
            
        except Exception as e:
            logger.error(f"Failed to decode base64 credentials: {e}")
    
    # 3. Check for encrypted credentials file
    project_root = Path(__file__).parent.parent.parent
    encrypted_file = project_root / ".credentials" / "gcp-vision-encrypted"
    
    if encrypted_file.exists():
        logger.info("Found encrypted credentials file")
        decrypted_path = _decrypt_credentials_file(encrypted_file)
        if decrypted_path:
            return decrypted_path
    
    # 4. Check for plain credentials file
    plain_file = project_root / "gcp-vision-key.json"
    if plain_file.exists():
        logger.info(f"Using plain GCP credentials: {plain_file}")
        return str(plain_file)
    
    logger.warning("No GCP credentials found")
    return None


def _decrypt_credentials_file(encrypted_file: Path) -> Optional[str]:
    """
    Decrypt encrypted credentials file.
    
    Args:
        encrypted_file: Path to encrypted credentials file
        
    Returns:
        Path to decrypted credentials file or None if failed
    """
    if not CRYPTO_AVAILABLE:
        logger.error("Cannot decrypt credentials: cryptography library not available")
        logger.info("Install with: pip install cryptography")
        return None
    
    try:
        # Read encrypted data
        with open(encrypted_file, 'r') as f:
            encrypted_data = json.load(f)
        
        salt = base64.b64decode(encrypted_data['salt'])
        encrypted_content = encrypted_data['encrypted_data']
        
        # Get decryption password from environment
        password = os.getenv('GCP_DECRYPT_PASSWORD')
        if not password:
            logger.error("GCP_DECRYPT_PASSWORD not set in environment")
            logger.info("Add to .env file: GCP_DECRYPT_PASSWORD=your_password")
            return None
        
        # Derive key from password
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        fernet = Fernet(key)
        
        # Decrypt the credentials
        encrypted_bytes = base64.b64decode(encrypted_content)
        decrypted_data = fernet.decrypt(encrypted_bytes)
        credentials_json = decrypted_data.decode('utf-8')
        
        # Write to temporary file
        temp_file = encrypted_file.parent.parent / "temp_gcp_credentials.json"
        with open(temp_file, 'w') as f:
            f.write(credentials_json)
        
        logger.info("Successfully decrypted GCP credentials")
        return str(temp_file)
        
    except Exception as e:
        logger.error(f"Failed to decrypt credentials: {e}")
        return None