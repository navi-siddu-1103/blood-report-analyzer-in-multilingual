# Blood Report Analyzer - Deployment Guide

A comprehensive blood report analyzer with multi-lingual support (English, Hindi, Kannada) that analyzes blood reports from PDF/image files and provides health recommendations.

## Features

✅ **Multi-lingual Interface** - English, Hindi (हिंदी), and Kannada (ಕನ್ನಡ)
✅ **File Upload Support** - Analyze PDF and image files (JPG, PNG)
✅ **Manual Entry** - Enter blood parameters manually
✅ **Comprehensive Analysis** - Analyzes 10+ blood parameters
✅ **Health Recommendations** - Personalized suggestions based on results
✅ **Beautiful UI** - Modern, responsive design matching reference images

## Project Structure

```
blood-report-analyzer/
├── backend/
│   ├── app.py                 # Flask backend application
│   └── requirements.txt       # Python dependencies
├── frontend/
│   └── index.html            # Frontend HTML application
└── README.md                 # This file
```

## Prerequisites

### Backend Requirements
- Python 3.8 or higher
- Tesseract OCR (for image text extraction)

### Frontend Requirements
- Modern web browser
- Web server (optional, for production)

## Installation Steps

### 1. Install Tesseract OCR

#### On Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install tesseract-ocr
```

#### On macOS:
```bash
brew install tesseract
```

#### On Windows:
Download and install from: https://github.com/UB-Mannheim/tesseract/wiki

### 2. Set Up Python Backend

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Backend Server

```bash
# Make sure you're in the backend directory with venv activated
python app.py
```

The backend API will start on `http://localhost:5000`

### 4. Set Up Frontend

The frontend can be served in multiple ways:

#### Option A: Simple Python HTTP Server
```bash
# Navigate to frontend directory
cd frontend

# Start simple HTTP server
python3 -m http.server 8080
```

Access at: `http://localhost:8080`

#### Option B: Using Live Server (VS Code Extension)
1. Open `index.html` in VS Code
2. Right-click and select "Open with Live Server"

#### Option C: Direct File Access
Simply open `index.html` in your browser (note: file upload may have CORS restrictions)

## API Endpoints

### 1. Analyze File Upload
**Endpoint:** `POST /api/analyze-file`

**Form Data:**
- `file`: Blood report file (PDF/Image)
- `language`: Language preference (english/hindi/kannada)

**Response:**
```json
{
  "parameters": [
    {
      "name": "Hemoglobin",
      "value": 13.5,
      "range": "12-16 g/dL",
      "status": "normal"
    }
  ],
  "recommendations": ["..."],
  "overallStatus": "Good Health",
  "abnormalCount": 2
}
```

### 2. Analyze Manual Entry
**Endpoint:** `POST /api/analyze-manual`

**JSON Body:**
```json
{
  "hemoglobin": 13.5,
  "wbc": 9500,
  "rbc": 4.8,
  "platelets": 220000,
  "glucose": 145,
  "cholesterol": 225,
  "hdl": 35,
  "ldl": 160,
  "triglycerides": 185,
  "creatinine": 1.0,
  "language": "english"
}
```

### 3. Health Check
**Endpoint:** `GET /api/health`

## Connecting Frontend to Backend

If your frontend is served from a different port than the backend, you'll need to update the API endpoints in `index.html`:

```javascript
// Find and update the API base URL
const API_BASE_URL = 'http://localhost:5000';
```

Then update the fetch calls to use this base URL:

```javascript
// For file upload
fetch(`${API_BASE_URL}/api/analyze-file`, {...})

// For manual entry
fetch(`${API_BASE_URL}/api/analyze-manual`, {...})
```

## Blood Parameters Analyzed

| Parameter | Normal Range | Unit |
|-----------|-------------|------|
| Hemoglobin | 12-16 | g/dL |
| WBC Count | 4000-11000 | /μL |
| RBC Count | 4.5-5.5 | M/μL |
| Platelet Count | 150000-400000 | /μL |
| Blood Glucose | 70-100 | mg/dL |
| Total Cholesterol | < 200 | mg/dL |
| HDL Cholesterol | > 40 | mg/dL |
| LDL Cholesterol | < 100 | mg/dL |
| Triglycerides | < 150 | mg/dL |
| Creatinine | 0.7-1.3 | mg/dL |

## Features Demonstration

### 1. Language Selection
- Click the language dropdown in the header
- Select from English, हिंदी, or ಕನ್ನಡ
- Entire interface updates instantly

### 2. File Upload
- Click "Upload Blood Report" card
- Drag and drop or click to select file
- Supports PDF, JPG, PNG formats
- OCR extracts text from images
- PDF text extraction for PDF files

### 3. Manual Entry
- Click "Manual Entry" card
- Fill in blood parameter values
- All fields are required
- Click "Analyze" to generate report

### 4. Results Display
- Overall health status card
- Comprehensive parameter table with color-coded status
- Personalized health recommendations
- Multi-lingual support for all sections

## Troubleshooting

### Issue: Tesseract not found
**Solution:** Ensure Tesseract is installed and added to PATH
```bash
# Check if tesseract is installed
tesseract --version
```

### Issue: CORS errors
**Solution:** Make sure Flask-CORS is installed and backend is running
```bash
pip install flask-cors
```

### Issue: File upload fails
**Solution:** 
1. Check file size (max 16MB by default)
2. Ensure file format is supported (PDF, JPG, PNG)
3. Check backend logs for errors

### Issue: OCR accuracy is low
**Solution:**
1. Use high-quality scans/images
2. Ensure good lighting and contrast
3. Consider manually entering values if OCR fails

## Production Deployment

### Backend Deployment (using Gunicorn)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Frontend Deployment

#### Using Nginx:
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    root /path/to/frontend;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Using Docker

**Dockerfile for Backend:**
```dockerfile
FROM python:3.9-slim

RUN apt-get update && apt-get install -y tesseract-ocr

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app.py .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "5000:5000"
    
  frontend:
    image: nginx:alpine
    volumes:
      - ./frontend:/usr/share/nginx/html
    ports:
      - "80:80"
```

## Environment Variables

Create a `.env` file in the backend directory:

```env
FLASK_ENV=production
FLASK_DEBUG=False
MAX_CONTENT_LENGTH=16777216  # 16MB
SECRET_KEY=your-secret-key-here
```

## Security Considerations

1. **File Upload Security:**
   - Validate file types
   - Limit file sizes
   - Scan uploaded files for malware

2. **Data Privacy:**
   - Don't store uploaded reports
   - Use HTTPS in production
   - Implement user authentication if needed

3. **API Security:**
   - Add rate limiting
   - Implement API keys
   - Use CORS properly

## Testing

### Test Backend API:

```bash
# Test health endpoint
curl http://localhost:5000/api/health

# Test manual analysis
curl -X POST http://localhost:5000/api/analyze-manual \
  -H "Content-Type: application/json" \
  -d '{
    "hemoglobin": 13.5,
    "wbc": 9500,
    "rbc": 4.8,
    "platelets": 220000,
    "glucose": 95,
    "cholesterol": 180,
    "hdl": 50,
    "ldl": 90,
    "triglycerides": 120,
    "creatinine": 1.0,
    "language": "english"
  }'
```

## Support & Contact

For issues and questions:
- Check existing issues on GitHub
- Create a new issue with detailed description
- Include error logs and screenshots

## License

This project is open source and available under the MIT License.

## Disclaimer

⚠️ **Medical Disclaimer:** This tool is for informational purposes only and should not be used as a substitute for professional medical advice, diagnosis, or treatment. Always consult with a qualified healthcare provider for medical concerns.

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## Future Enhancements

- [ ] Support for more blood parameters
- [ ] PDF report generation
- [ ] Email report functionality
- [ ] User accounts and history
- [ ] Mobile app versions
- [ ] More language support
- [ ] Advanced AI-based analysis
- [ ] Integration with hospital systems

---

**Version:** 1.0.0
**Last Updated:** 2025-01-03