# 🏗️ AI Construction Measurement Extractor

A powerful, AI-driven application for extracting structured measurement data from construction images with support for bulk processing, multiple output formats, and enhanced parsing capabilities.

## ✨ Features

### 🔍 Advanced OCR & Parsing
- **Google Cloud Vision OCR** - Fast, accurate text extraction
- **OpenAI Vision Enhancement** - Intelligent parsing for complex measurements
- **Pattern Recognition** - Supports various measurement formats (feet-inches, decimals, areas)
- **Smart Room Detection** - Automatic room identification from filenames and content

### 📁 Bulk Processing
- **Multi-Image Upload** - Process dozens of images simultaneously
- **ZIP File Support** - Upload compressed archives of construction images
- **Progress Tracking** - Real-time processing status and estimated completion
- **Concurrent Processing** - Multi-threaded processing for speed

### 📊 Structured Output
- **Multiple Formats** - Text, JSON, CSV, and individual files
- **Standardized Format** - Consistent measurement structure across all outputs
- **Download Packages** - Convenient ZIP files with all results
- **Comprehensive Reports** - Detailed analysis with statistics

### 🔐 Secure & Configurable
- **Encrypted Credentials** - Secure storage of API keys and credentials
- **Environment Configuration** - Flexible settings via environment variables
- **Error Handling** - Robust error recovery and detailed logging

## 📋 Expected Output Format

The system extracts measurements in this standardized format:

```
Room: Bedroom - subroom
  Height: 8'
  Measurements:
    Walls:
      - Area: 183.88 SF
      - Total (Walls & Ceiling): 232.87 SF
    Ceiling:
      - Area: 49.00 SF
    Floor:
      - Area: 49.00 SF
      - Perimeter: 20.94 LF
      - Flooring: 5.44 SY
    Ceiling Perimeter:
      - Length: 37.49 LF
    Door:
      - Dimensions: 2'6" X 6'8"
      - Opens into: ENTRY_FOYER
      - Dimensions: 2' X 6'8"
      - Opens into: Exterior
    Missing Wall:
      - Dimensions: 4'6 5/8" X 8'
      - Opens into: BEDROOM
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Credentials

#### Google Cloud Platform (Required)
1. Create a GCP project and enable Vision API
2. Create a service account and download the JSON key
3. Either:
   - **Secure Method**: Encrypt your credentials
     ```bash
     python secure_credentials.py encrypt gcp-vision-key.json
     ```
   - **Simple Method**: Set environment variable
     ```bash
     export GOOGLE_APPLICATION_CREDENTIALS=./gcp-vision-key.json
     ```

#### OpenAI API (Optional - for enhanced parsing)
1. Get API key from [OpenAI Platform](https://platform.openai.com/api-keys)
2. Add to `.env` file:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```

### 3. Configure Environment

Copy `.env.example` to `.env` and update:

```bash
cp .env.example .env
# Edit .env with your settings
```

### 4. Run the Application

```bash
python measurement_app.py
```

Visit http://localhost:7860 to access the web interface.

## 🧪 Testing

Test the system with sample data:

```bash
python test_measurement_extraction.py
```

This creates test images and verifies all functionality.

## 📖 Usage Guide

### Single Image Processing

1. Go to the **"Single Image"** tab
2. Upload a construction measurement image
3. Click **"Extract Measurements"**
4. View results in both text and JSON formats

### Bulk Processing

1. Go to the **"Bulk Processing"** tab
2. Upload multiple images or ZIP files
3. Configure options:
   - **OpenAI Enhancement**: Enable for complex parsing
   - **Output Formats**: Choose text, JSON, CSV, or individual files
4. Click **"Process All Images"**
5. Download the results package when complete

### Supported File Formats

- **Images**: JPG, JPEG, PNG, BMP, TIFF
- **Archives**: ZIP files containing images
- **Max Size**: 10MB per file

## 📁 Project Structure

```
ai_construction_estimate/
├── src/
│   ├── models/
│   │   └── room_measurement.py      # Data models
│   ├── services/
│   │   ├── measurement/
│   │   │   ├── extraction_service.py    # Core extraction logic
│   │   │   ├── bulk_processor.py        # Bulk processing
│   │   │   └── output_formatter.py      # Output formatting
│   │   └── ocr/
│   │       └── gcp_ocr.py              # Google Cloud OCR
│   ├── core/
│   │   ├── credentials.py              # Secure credential management
│   │   └── config.py                   # Configuration
│   └── ui/
│       └── measurement_app.py          # Gradio web interface
├── measurement_app.py                  # Main launcher
├── test_measurement_extraction.py     # Test suite
├── secure_credentials.py              # Credential encryption tool
└── docs/
    ├── GCP_OCR_SETUP.md               # GCP setup guide
    └── SECURE_CREDENTIALS_GUIDE.md    # Security guide
```

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to GCP credentials | `./gcp-vision-key.json` |
| `GCP_DECRYPT_PASSWORD` | Password for encrypted credentials | - |
| `OPENAI_API_KEY` | OpenAI API key for enhancement | - |
| `OCR_SERVICE` | OCR service to use | `gcp` |
| `OCR_CONFIDENCE_THRESHOLD` | Minimum OCR confidence | `0.3` |
| `MAX_WORKERS` | Concurrent processing threads | `4` |

### Processing Options

- **Basic Extraction**: Uses pattern matching and GCP OCR
- **Enhanced Extraction**: Adds OpenAI Vision API for complex parsing
- **Bulk Processing**: Processes multiple images with progress tracking
- **Output Formats**: Text, JSON, CSV, individual JSON files

## 🔧 Advanced Features

### Room Detection

The system automatically detects room types from:

- **Filename patterns**: `bedroom_1.jpg`, `kitchen_main.png`
- **Image content**: Text found in the measurement image
- **Context clues**: Measurement types and patterns

Supported room types:
- Bedroom, Bathroom, Kitchen, Living Room, Dining Room
- Office, Closet, Hallway, Entry/Foyer, Garage
- Basement, Attic, Laundry, Utility

### Measurement Parsing

Supports various measurement formats:

- **Feet-Inches**: `10'-6"`, `8'`, `2'6"`
- **Decimal Feet**: `10.5 ft`, `8.25 feet`
- **Dimensions**: `12 x 15`, `10' x 8'`
- **Areas**: `180 SF`, `5.44 SY`
- **Linear**: `20.94 LF`

### Output Customization

- **Text Format**: Human-readable, structured format
- **JSON Format**: Machine-readable with full metadata
- **CSV Format**: Spreadsheet-compatible for analysis
- **Individual Files**: Separate JSON file per room

## 🔒 Security

### Credential Management

- **Encrypted Storage**: Credentials encrypted with password
- **Environment Variables**: Secure credential loading
- **No Hardcoding**: No credentials in source code
- **Audit Trail**: Comprehensive logging

### Data Privacy

- **Local Processing**: OCR results processed locally
- **Secure APIs**: Encrypted connections to cloud services
- **Temporary Files**: Automatic cleanup of temporary data
- **Access Control**: User-defined access restrictions

## 🛠️ Troubleshooting

### Common Issues

1. **"No GCP credentials found"**
   - Check `GOOGLE_APPLICATION_CREDENTIALS` environment variable
   - Verify credentials file exists and is valid JSON
   - Ensure GCP Vision API is enabled

2. **"OCR extraction failed"**
   - Check image quality and text visibility
   - Verify internet connection for cloud APIs
   - Try with different image formats

3. **"OpenAI parsing unavailable"**
   - Set `OPENAI_API_KEY` environment variable
   - Check API key is valid and has credits
   - Basic extraction will still work without OpenAI

4. **"Bulk processing slow"**
   - Reduce `MAX_WORKERS` if system is overloaded
   - Process smaller batches of images
   - Check internet connection speed

### Performance Tips

1. **Image Quality**: Use high-resolution, clear images
2. **File Naming**: Include room names in filenames
3. **Batch Size**: Process 10-50 images per batch for optimal speed
4. **Network**: Ensure stable internet for cloud APIs

## 📈 API Usage & Costs

### Google Cloud Vision
- **Free Tier**: 1,000 requests/month
- **Pricing**: $1.50 per 1,000 requests (next 5M)
- **Speed**: ~1-3 seconds per image

### OpenAI Vision (Optional)
- **Pricing**: ~$0.01-0.03 per image
- **Speed**: ~5-10 seconds per image
- **Value**: Enhanced parsing for complex measurements

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

1. Check the troubleshooting section above
2. Review the setup guides in the `docs/` folder
3. Run the test suite to verify installation
4. Check logs for detailed error information

---

**Built with**: Python, Gradio, Google Cloud Vision API, OpenAI API, and modern AI/ML technologies.