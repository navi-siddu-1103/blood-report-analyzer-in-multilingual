from flask import Flask, request, jsonify
from flask_cors import CORS
import PyPDF2
from PIL import Image
import pytesseract
import io
import re
import os

app = Flask(__name__)
CORS(app)

# Blood parameter reference ranges
REFERENCE_RANGES = {
    'hemoglobin': {'min': 12, 'max': 16, 'unit': 'g/dL', 'reverse': False},
    'wbc': {'min': 4000, 'max': 11000, 'unit': '/μL', 'reverse': False},
    'rbc': {'min': 4.5, 'max': 5.5, 'unit': 'M/μL', 'reverse': False},
    'platelets': {'min': 150000, 'max': 400000, 'unit': '/μL', 'reverse': False},
    'glucose': {'min': 70, 'max': 100, 'unit': 'mg/dL', 'reverse': False},
    'cholesterol': {'min': 0, 'max': 200, 'unit': 'mg/dL', 'reverse': False},
    'hdl': {'min': 40, 'max': 999, 'unit': 'mg/dL', 'reverse': True},
    'ldl': {'min': 0, 'max': 100, 'unit': 'mg/dL', 'reverse': False},
    'triglycerides': {'min': 0, 'max': 150, 'unit': 'mg/dL', 'reverse': False},
    'creatinine': {'min': 0.7, 'max': 1.3, 'unit': 'mg/dL', 'reverse': False}
}

# Multi-language parameter names
PARAMETER_NAMES = {
    'hemoglobin': {
        'english': 'Hemoglobin',
        'hindi': 'हीमोग्लोबिन',
        'kannada': 'ಹಿಮೋಗ್ಲೋಬಿನ್'
    },
    'wbc': {
        'english': 'WBC Count',
        'hindi': 'WBC काउंट',
        'kannada': 'WBC ಎಣಿಕೆ'
    },
    'rbc': {
        'english': 'RBC Count',
        'hindi': 'RBC काउंट',
        'kannada': 'RBC ಎಣಿಕೆ'
    },
    'platelets': {
        'english': 'Platelet Count',
        'hindi': 'प्लेटलेट काउंट',
        'kannada': 'ಪ್ಲೇಟ್ಲೆಟ್ ಎಣಿಕೆ'
    },
    'glucose': {
        'english': 'Blood Glucose',
        'hindi': 'रक्त शर्करा',
        'kannada': 'ರಕ್ತದ ಸಕ್ಕರೆ'
    },
    'cholesterol': {
        'english': 'Total Cholesterol',
        'hindi': 'कुल कोलेस्ट्रॉल',
        'kannada': 'ಒಟ್ಟು ಕೊಲೆಸ್ಟರಾಲ್'
    },
    'hdl': {
        'english': 'HDL Cholesterol',
        'hindi': 'HDL कोलेस्ट्रॉल',
        'kannada': 'HDL ಕೊಲೆಸ್ಟರಾಲ್'
    },
    'ldl': {
        'english': 'LDL Cholesterol',
        'hindi': 'LDL कोलेस्ट्रॉल',
        'kannada': 'LDL ಕೊಲೆಸ್ಟರಾಲ್'
    },
    'triglycerides': {
        'english': 'Triglycerides',
        'hindi': 'ट्राइग्लिसराइड्स',
        'kannada': 'ಟ್ರೈಗ್ಲಿಸರೈಡ್ಸ್'
    },
    'creatinine': {
        'english': 'Creatinine',
        'hindi': 'क्रिएटिनिन',
        'kannada': 'ಕ್ರಿಯೇಟಿನೈನ್'
    }
}

# Multi-language recommendations
RECOMMENDATIONS = {
    'glucose_high': {
        'english': '🍎 Diet: Reduce sugar intake and focus on a low-glycemic diet to manage blood glucose levels',
        'hindi': '🍎 आहार: रक्त शर्करा को नियंत्रित करने के लिए चीनी का सेवन कम करें और कम ग्लाइसेमिक आहार पर ध्यान दें',
        'kannada': '🍎 ಆಹಾರ: ರಕ್ತದ ಗ್ಲೂಕೋಸ್ ಮಟ್ಟವನ್ನು ನಿರ್ವಹಿಸಲು ಸಕ್ಕರೆ ಸೇವನೆಯನ್ನು ಕಡಿಮೆ ಮಾಡಿ'
    },
    'cholesterol_high': {
        'english': '🥗 Nutrition: Increase intake of omega-3 fatty acids and fiber-rich foods to lower cholesterol',
        'hindi': '🥗 पोषण: कोलेस्ट्रॉल कम करने के लिए ओमेगा-3 फैटी एसिड और फाइबर युक्त खाद्य पदार्थों का सेवन बढ़ाएं',
        'kannada': '🥗 ಪೋಷಣೆ: ಕೊಲೆಸ್ಟರಾಲ್ ಕಡಿಮೆ ಮಾಡಲು ಒಮೆಗಾ-3 ಮತ್ತು ಫೈಬರ್ ಸಮೃದ್ಧ ಆಹಾರಗಳನ್ನು ಹೆಚ್ಚಿಸಿ'
    },
    'hdl_low': {
        'english': '🏃 Exercise: Engage in at least 30 minutes of moderate aerobic exercise daily to improve HDL cholesterol',
        'hindi': '🏃 व्यायाम: HDL कोलेस्ट्रॉल बढ़ाने के लिए रोजाना कम से कम 30 मिनट की मध्यम एरोबिक एक्सरसाइज करें',
        'kannada': '🏃 ವ್ಯಾಯಾಮ: HDL ಕೊಲೆಸ್ಟರಾಲ್ ಸುಧಾರಿಸಲು ದಿನಕ್ಕೆ 30 ನಿಮಿಷಗಳ ವ್ಯಾಯಾಮ ಮಾಡಿ'
    },
    'medication': {
        'english': '💊 Medication: Consult your doctor about potential treatments',
        'hindi': '💊 दवा: संभावित उपचार के बारे में अपने डॉक्टर से परामर्श लें',
        'kannada': '💊 ಔಷಧಿ: ಸಂಭವನೀಯ ಚಿಕಿತ್ಸೆಯ ಬಗ್ಗೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ'
    },
    'weight': {
        'english': '⚖️ Weight: Maintain healthy body weight through balanced diet and regular physical activity',
        'hindi': '⚖️ वजन: संतुलित आहार और नियमित शारीरिक गतिविधि के माध्यम से स्वस्थ शरीर का वजन बनाए रखें',
        'kannada': '⚖️ ತೂಕ: ಸಮತೋಲಿತ ಆಹಾರ ಮತ್ತು ನಿಯಮಿತ ದೈಹಿಕ ಚಟುವಟಿಕೆಯ ಮೂಲಕ ಆರೋಗ್ಯಕರ ತೂಕವನ್ನು ನಿರ್ವಹಿಸಿ'
    },
    'lifestyle': {
        'english': '🚭 Lifestyle: Avoid smoking and limit alcohol consumption',
        'hindi': '🚭 जीवनशैली: धूम्रपान से बचें और शराब का सेवन सीमित करें',
        'kannada': '🚭 ಜೀವನಶೈಲಿ: ಧೂಮಪಾನವನ್ನು ತಪ್ಪಿಸಿ ಮತ್ತು ಮದ್ಯಪಾನವನ್ನು ಸೀಮಿತಗೊಳಿಸಿ'
    },
    'followup': {
        'english': '🔄 Follow-up: Repeat tests after 3 months',
        'hindi': '🔄 फॉलो-अप: 3 महीने बाद टेस्ट दोहराएं',
        'kannada': '🔄 ಅನುಸರಣೆ: 3 ತಿಂಗಳ ನಂತರ ಪರೀಕ್ಷೆಗಳನ್ನು ಪುನರಾವರ್ತಿಸಿ'
    },
    'hemoglobin_low': {
        'english': '🥩 Diet: Increase iron-rich foods like spinach, red meat, and legumes',
        'hindi': '🥩 आहार: पालक, लाल मांस और दालों जैसे आयरन युक्त खाद्य पदार्थों का सेवन बढ़ाएं',
        'kannada': '🥩 ಆಹಾರ: ಪಾಲಕ್, ಕೆಂಪು ಮಾಂಸ ಮತ್ತು ದಾಳಿಗಳಂತಹ ಕಬ್ಬಿಣದ ಆಹಾರವನ್ನು ಹೆಚ್ಚಿಸಿ'
    }
}

def analyze_status(param_name, value):
    """Determine if a parameter value is normal, high, or low"""
    ref = REFERENCE_RANGES.get(param_name)
    if not ref:
        return 'normal'
    
    if ref['reverse']:
        # For HDL cholesterol (higher is better)
        return 'normal' if value >= ref['min'] else 'low'
    else:
        if value < ref['min']:
            return 'low'
        elif value > ref['max']:
            return 'high'
        else:
            return 'normal'

def generate_recommendations(parameters, language='english'):
    """Generate health recommendations based on abnormal parameters"""
    recommendations = []
    abnormal_params = [p for p in parameters if p['status'] != 'normal']
    
    for param in abnormal_params:
        param_key = param['key']
        status = param['status']
        
        if param_key == 'glucose' and status == 'high':
            recommendations.append(RECOMMENDATIONS['glucose_high'][language])
        
        if param_key in ['cholesterol', 'ldl', 'triglycerides'] and status == 'high':
            if RECOMMENDATIONS['cholesterol_high'][language] not in recommendations:
                recommendations.append(RECOMMENDATIONS['cholesterol_high'][language])
        
        if param_key == 'hdl' and status == 'low':
            recommendations.append(RECOMMENDATIONS['hdl_low'][language])
        
        if param_key == 'hemoglobin' and status == 'low':
            recommendations.append(RECOMMENDATIONS['hemoglobin_low'][language])
    
    # Add general recommendations
    if len(abnormal_params) > 0:
        recommendations.append(RECOMMENDATIONS['medication'][language])
        recommendations.append(RECOMMENDATIONS['weight'][language])
        recommendations.append(RECOMMENDATIONS['lifestyle'][language])
        recommendations.append(RECOMMENDATIONS['followup'][language])
    
    return recommendations

def extract_text_from_pdf(file_content):
    """Extract text from PDF file"""
    try:
        pdf_file = io.BytesIO(file_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text
    except Exception as e:
        print(f"Error extracting PDF text: {e}")
        return ""

def extract_text_from_image(file_content):
    """Extract text from image using OCR"""
    try:
        image = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(image)
        return text
    except Exception as e:
        print(f"Error extracting image text: {e}")
        return ""

def parse_blood_report(text):
    """Parse blood report text to extract parameter values"""
    data = {}
    
    # Common patterns for blood parameters
    patterns = {
        'hemoglobin': r'(?:hemoglobin|hb|hgb)[\s:]*(\d+\.?\d*)',
        'wbc': r'(?:wbc|white blood cell|leucocyte)[\s:]*(\d+)',
        'rbc': r'(?:rbc|red blood cell|erythrocyte)[\s:]*(\d+\.?\d*)',
        'platelets': r'(?:platelet|plt)[\s:]*(\d+)',
        'glucose': r'(?:glucose|blood sugar|fasting glucose)[\s:]*(\d+\.?\d*)',
        'cholesterol': r'(?:total cholesterol|cholesterol total)[\s:]*(\d+\.?\d*)',
        'hdl': r'(?:hdl|hdl cholesterol)[\s:]*(\d+\.?\d*)',
        'ldl': r'(?:ldl|ldl cholesterol)[\s:]*(\d+\.?\d*)',
        'triglycerides': r'(?:triglyceride|tg)[\s:]*(\d+\.?\d*)',
        'creatinine': r'(?:creatinine|creat)[\s:]*(\d+\.?\d*)'
    }
    
    text_lower = text.lower()
    
    for param, pattern in patterns.items():
        match = re.search(pattern, text_lower)
        if match:
            try:
                value = float(match.group(1))
                data[param] = value
            except:
                pass
    
    return data

@app.route('/api/analyze-file', methods=['POST'])
def analyze_file():
    """Analyze blood report from uploaded file (PDF or Image)"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['file']
        language = request.form.get('language', 'english')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        file_content = file.read()
        file_extension = file.filename.rsplit('.', 1)[1].lower()
        
        # Extract text based on file type
        if file_extension == 'pdf':
            text = extract_text_from_pdf(file_content)
        elif file_extension in ['jpg', 'jpeg', 'png']:
            text = extract_text_from_image(file_content)
        else:
            return jsonify({'error': 'Unsupported file format'}), 400
        
        # Parse blood report data
        parsed_data = parse_blood_report(text)
        
        if not parsed_data:
            # Return sample data if parsing fails
            return jsonify({'warning': 'Could not parse report, returning sample data', 
                          'data': get_sample_analysis(language)}), 200
        
        # Analyze the data
        result = analyze_manual_data(parsed_data, language)
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error analyzing file: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyze-manual', methods=['POST'])
def analyze_manual():
    """Analyze manually entered blood report data"""
    try:
        data = request.json
        language = data.get('language', 'english')
        
        # Extract parameter values
        param_values = {
            'hemoglobin': float(data.get('hemoglobin', 0)),
            'wbc': int(data.get('wbc', 0)),
            'rbc': float(data.get('rbc', 0)),
            'platelets': int(data.get('platelets', 0)),
            'glucose': int(data.get('glucose', 0)),
            'cholesterol': int(data.get('cholesterol', 0)),
            'hdl': int(data.get('hdl', 0)),
            'ldl': int(data.get('ldl', 0)),
            'triglycerides': int(data.get('triglycerides', 0)),
            'creatinine': float(data.get('creatinine', 0))
        }
        
        result = analyze_manual_data(param_values, language)
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error analyzing manual data: {e}")
        return jsonify({'error': str(e)}), 500

def analyze_manual_data(param_values, language='english'):
    """Analyze blood parameter values and generate report"""
    parameters = []
    
    for param_key, value in param_values.items():
        if param_key in REFERENCE_RANGES:
            ref = REFERENCE_RANGES[param_key]
            status = analyze_status(param_key, value)
            
            # Format range string
            if ref['reverse']:
                range_str = f"> {ref['min']} {ref['unit']}"
            else:
                range_str = f"{ref['min']}-{ref['max']} {ref['unit']}"
            
            parameters.append({
                'key': param_key,
                'name': PARAMETER_NAMES[param_key]['english'],
                'nameHindi': PARAMETER_NAMES[param_key]['hindi'],
                'nameKannada': PARAMETER_NAMES[param_key]['kannada'],
                'value': value,
                'range': range_str,
                'status': status
            })
    
    # Generate recommendations
    recommendations = generate_recommendations(parameters, language)
    
    # Calculate overall health status
    abnormal_count = sum(1 for p in parameters if p['status'] != 'normal')
    
    overall_status = {
        'english': 'Excellent Health',
        'hindi': 'उत्कृष्ट स्वास्थ्य',
        'kannada': 'ಅತ್ಯುತ್ತಮ ಆರೋಗ್ಯ'
    }
    
    if abnormal_count >= 3:
        overall_status = {
            'english': 'Moderate Risk - Action Required',
            'hindi': 'मध्यम जोखिम - कार्रवाई आवश्यक',
            'kannada': 'ಮಧ್ಯಮ ಅಪಾಯ - ಕ್ರಮ ಅಗತ್ಯವಿದೆ'
        }
    elif abnormal_count > 0:
        overall_status = {
            'english': 'Good Health - Minor Attention Needed',
            'hindi': 'अच्छा स्वास्थ्य - मामूली ध्यान की आवश्यकता',
            'kannada': 'ಉತ್ತಮ ಆರೋಗ್ಯ - ಸ್ವಲ್ಪ ಗಮನ ಅಗತ್ಯವಿದೆ'
        }
    
    return {
        'parameters': parameters,
        'recommendations': recommendations,
        'overallStatus': overall_status[language],
        'abnormalCount': abnormal_count
    }

def get_sample_analysis(language='english'):
    """Return sample blood report analysis"""
    sample_values = {
        'hemoglobin': 13.5,
        'wbc': 9500,
        'rbc': 4.8,
        'platelets': 220000,
        'glucose': 145,
        'cholesterol': 225,
        'hdl': 35,
        'ldl': 160,
        'triglycerides': 185,
        'creatinine': 1.0
    }
    return analyze_manual_data(sample_values, language)

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'message': 'Blood Report Analyzer API is running'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)