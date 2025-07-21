# Secure Credential Storage Guide for GCP Vision API

## 🔒 Security Methods (From Most to Least Secure)

### 1. **Encrypted Local Storage** (Recommended for Development)

**Best for**: Development environments, local testing, personal projects

```bash
# Install encryption dependencies
pip install cryptography

# Encrypt your credentials
python secure_credentials.py encrypt gcp-vision-key.json

# Test decryption
python secure_credentials.py test
```

**How it works**:
- Encrypts JSON file with password-based encryption (PBKDF2 + Fernet)
- Stores encrypted data in `.credentials/` directory
- Original JSON file can be safely deleted
- Password required each time (or use environment variable)

**Setup Steps**:
1. Download your GCP service account JSON file
2. Run: `python secure_credentials.py encrypt gcp-vision-key.json`
3. Enter a strong password when prompted
4. Delete the original JSON file
5. Test with: `python secure_credentials.py test`

### 2. **Environment Variables with Base64 Encoding**

**Best for**: CI/CD pipelines, Docker containers, cloud deployments

```bash
# Encode your JSON file to base64
base64 -i gcp-vision-key.json -o gcp-encoded.txt

# Set environment variable (Linux/Mac)
export GCP_CREDENTIALS_BASE64="$(cat gcp-encoded.txt)"

# Set environment variable (Windows PowerShell)
$env:GCP_CREDENTIALS_BASE64=(Get-Content gcp-encoded.txt -Raw)
```

**Add to your .env file**:
```env
GCP_CREDENTIALS_BASE64=ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsC...
```

### 3. **Cloud Secret Managers** (Production Recommended)

#### AWS Secrets Manager
```python
import boto3
import json

def get_gcp_credentials_from_aws():
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId='gcp-vision-credentials')
    credentials = json.loads(response['SecretString'])
    
    # Write to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials, f)
        return f.name
```

#### Azure Key Vault
```python
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential
import json
import tempfile

def get_gcp_credentials_from_azure():
    credential = DefaultAzureCredential()
    client = SecretClient(vault_url="https://your-keyvault.vault.azure.net/", credential=credential)
    
    secret = client.get_secret("gcp-vision-credentials")
    credentials = json.loads(secret.value)
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials, f)
        return f.name
```

#### Google Secret Manager (Ironic but effective)
```python
from google.cloud import secretmanager
import json
import tempfile

def get_gcp_credentials_from_gcp():
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/your-project/secrets/gcp-vision-credentials/versions/latest"
    
    response = client.access_secret_version(request={"name": name})
    credentials = json.loads(response.payload.data.decode("UTF-8"))
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials, f)
        return f.name
```

### 4. **HashiCorp Vault** (Enterprise)

```python
import hvac
import json
import tempfile

def get_gcp_credentials_from_vault():
    client = hvac.Client(url='https://vault.company.com')
    client.token = os.environ['VAULT_TOKEN']
    
    response = client.secrets.kv.v2.read_secret_version(
        path='gcp-vision-credentials',
        mount_point='secret'
    )
    
    credentials = response['data']['data']
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(credentials, f)
        return f.name
```

### 5. **Docker Secrets** (Container Environments)

```dockerfile
# Dockerfile
FROM python:3.9
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    build: .
    secrets:
      - gcp-credentials
    environment:
      - GOOGLE_APPLICATION_CREDENTIALS=/run/secrets/gcp-credentials

secrets:
  gcp-credentials:
    file: ./gcp-vision-key.json
```

## 🚫 What NOT to Do

### ❌ Never Do These:
1. **Commit credentials to Git**
   ```bash
   # This is VERY BAD
   git add gcp-vision-key.json
   git commit -m "Added API keys"
   ```

2. **Hardcode credentials in source code**
   ```python
   # This is TERRIBLE
   credentials = {
       "type": "service_account",
       "project_id": "my-project",
       "private_key_id": "abc123...",
       # ... rest of the key
   }
   ```

3. **Store in unencrypted cloud storage**
   ```bash
   # Don't do this
   aws s3 cp gcp-vision-key.json s3://public-bucket/
   ```

4. **Email or message credentials**
   - Never send credentials via email, Slack, Teams, etc.
   - Use secure sharing methods only

## 🛡️ Security Best Practices

### 1. **Principle of Least Privilege**
Create service accounts with minimal required permissions:

```bash
# Only grant Vision API access
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:vision-ocr@PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/vision.cloudVisionAPIUser"
```

### 2. **Credential Rotation**
```bash
# Rotate credentials regularly
gcloud iam service-accounts keys create new-key.json \
    --iam-account=vision-ocr@PROJECT_ID.iam.gserviceaccount.com

# Delete old keys
gcloud iam service-accounts keys delete KEY_ID \
    --iam-account=vision-ocr@PROJECT_ID.iam.gserviceaccount.com
```

### 3. **Monitor Usage**
- Enable audit logging for service account usage
- Set up billing alerts for unexpected API usage
- Monitor for unusual access patterns

### 4. **Network Security**
```python
# Restrict API access by IP if possible
from google.oauth2 import service_account
from google.auth.transport.requests import Request

credentials = service_account.Credentials.from_service_account_file(
    'path/to/credentials.json',
    scopes=['https://www.googleapis.com/auth/cloud-vision']
)

# Add IP restrictions in GCP Console
```

## 🔧 Implementation in Your App

### Method 1: Encrypted Storage
```python
# In your config.py
from secure_credentials import get_secure_credentials

class Config:
    @property
    def gcp_credentials_path(self):
        return get_secure_credentials()
```

### Method 2: Environment Variables
```python
# In your config.py
import os
import json
import tempfile
import base64

class Config:
    @property
    def gcp_credentials_path(self):
        # Try base64 encoded credentials first
        encoded = os.environ.get('GCP_CREDENTIALS_BASE64')
        if encoded:
            decoded = base64.b64decode(encoded)
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                f.write(decoded.decode())
                return f.name
        
        # Fallback to file path
        return os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
```

### Method 3: Cloud Secret Manager
```python
# In your config.py
class Config:
    @property
    def gcp_credentials_path(self):
        if os.environ.get('CLOUD_ENVIRONMENT') == 'aws':
            return get_gcp_credentials_from_aws()
        elif os.environ.get('CLOUD_ENVIRONMENT') == 'azure':
            return get_gcp_credentials_from_azure()
        else:
            return os.environ.get('GOOGLE_APPLICATION_CREDENTIALS')
```

## 🧪 Testing Security

Use the provided test script to verify your security setup:

```bash
# Test all security methods
python test_gcp_ocr.py

# Test with real image
python test_gcp_ocr.py path/to/construction/image.jpg

# Test specific security method
python -c "
from secure_credentials import get_secure_credentials
print('Secure credentials test:', get_secure_credentials() is not None)
"
```

## 🚨 Security Incident Response

### If Credentials Are Compromised:

1. **Immediate Actions**:
   ```bash
   # Disable the service account immediately
   gcloud iam service-accounts disable vision-ocr@PROJECT_ID.iam.gserviceaccount.com
   
   # Delete all keys for the service account
   gcloud iam service-accounts keys list --iam-account=vision-ocr@PROJECT_ID.iam.gserviceaccount.com
   gcloud iam service-accounts keys delete KEY_ID --iam-account=vision-ocr@PROJECT_ID.iam.gserviceaccount.com
   ```

2. **Investigation**:
   - Check audit logs for unauthorized usage
   - Review billing for unexpected charges
   - Scan code repositories for accidentally committed credentials

3. **Recovery**:
   ```bash
   # Create new service account
   gcloud iam service-accounts create new-vision-ocr --display-name="New Vision OCR Service"
   
   # Grant minimal permissions
   gcloud projects add-iam-policy-binding PROJECT_ID \
       --member="serviceAccount:new-vision-ocr@PROJECT_ID.iam.gserviceaccount.com" \
       --role="roles/vision.cloudVisionAPIUser"
   
   # Create new key
   gcloud iam service-accounts keys create new-credentials.json \
       --iam-account=new-vision-ocr@PROJECT_ID.iam.gserviceaccount.com
   ```

## 📋 Security Checklist

- [ ] Credentials are encrypted or stored in secure secret manager
- [ ] Original JSON file is deleted from local machine
- [ ] `.gitignore` includes credential patterns
- [ ] Service account has minimal required permissions
- [ ] Audit logging is enabled
- [ ] Billing alerts are configured
- [ ] Credential rotation schedule is established
- [ ] Team knows incident response procedures
- [ ] Regular security reviews are scheduled

## 🔗 Additional Resources

- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Google Cloud IAM Best Practices](https://cloud.google.com/iam/docs/using-iam-securely)