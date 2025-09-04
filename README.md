File Comparator Web Application

A web-based tool built with Python, Flask, and Pandas to compare two tabular data files and generate a detailed Excel report highlighting:
  ✅ Matched Records
  ✅ Partially Matched Records
  ✅ Unmatched Records from each file
This tool simplifies comparing datasets such as .csv, .tsv, .txt, or Excel files and provides an intuitive web interface for easy use.

🚀 Features:
    -->Compare two files based on selected unique identifiers
    -->Select columns to compare between the files
    -->Supports .xlsx, .xls, .csv, .tsv, and .txt file formats
    -->Download comparison results as a structured multi-sheet Excel report
    -->Clean, responsive web interface using HTML, CSS, and JavaScript
    -->Fast processing using Python and Pandas

🛠️ Tech Stack
    -Python 3.x
    -Flask (web framework)
    -Pandas (data processing)
    -xlsxwriter (Excel report generation)
    -HTML, CSS, JavaScript (frontend)

📂 Project Structure:
├── app.py              # Main Flask application  
├── index.html          # Frontend web interface (Jinja template)  
├── requirements.txt    # Python dependencies  
└── README.md           # Project documentation

🧑‍💻 Getting Started:
1. Install Dependencies
      -->pip install -r requirements.txt
2. Run the Application
      -->python app.py
3. Access the Web Interface
      -->Open your browser and visit: https://dataset-comparison-web-app.onrender.com/
   
💡 How to Use
   -->Upload two supported files using the web interface
   -->Select unique identifier columns for each file
   -->Select columns to compare
   -->Submit the form to process the files
   -->Download the generated Excel report containing the comparison results

📦 Output Details
The generated Excel file contains the following sheets:
    -->Matched — Records where comparison columns match
    -->Partially_Matched — Records with mismatched comparison columns for matching unique IDs
    -->Sheet_1_UnMatched — Records present in File 1 but not in File 2
    -->Sheet_2_UnMatched — Records present in File 2 but not in File 1

🌟 Future Enhancements
  -->Enhanced error handling and validations
  -->Progress indicators for large files
  -->Deployment to cloud platforms (Heroku, AWS)
  -->Support for additional file formats and delimiters

Simple. Reliable. Efficient File Comparison Tool for Everyday Use.
