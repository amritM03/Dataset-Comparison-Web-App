import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = "uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "tsv"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def read_file(file_path):
    ext = file_path.rsplit(".", 1)[1].lower()
    try:
        if ext in ["xlsx", "xls"]:
            return pd.read_excel(file_path, engine="openpyxl")
        elif ext == "csv":
            return pd.read_csv(file_path)
        elif ext == "tsv":
            return pd.read_csv(file_path, sep="\t")
        else:
            return None
    except Exception as e:
        print(f"Error reading file {file_path}: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_headers", methods=["POST"])
def get_headers():
    file1 = request.files.get("file1")
    file2 = request.files.get("file2")

    headers = {"file1_headers": [], "file2_headers": []}

    if file1 and allowed_file(file1.filename):
        file1_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file1.filename))
        file1.save(file1_path)
        df1 = read_file(file1_path)
        if df1 is not None:
            headers["file1_headers"] = list(df1.columns)

    if file2 and allowed_file(file2.filename):
        file2_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file2.filename))
        file2.save(file2_path)
        df2 = read_file(file2_path)
        if df2 is not None:
            headers["file2_headers"] = list(df2.columns)

    return jsonify(headers)


@app.route("/compare", methods=["POST"])
def compare():
    try:
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")

        unique_col1 = request.form.get("unique_column_file1")
        unique_col2 = request.form.get("unique_column_file2")
        compare_col1 = request.form.get("compare_column_file1")
        compare_col2 = request.form.get("compare_column_file2")

        if not all([file1, file2, unique_col1, unique_col2, compare_col1, compare_col2]):
            return jsonify({"error": "All fields are required"}), 400

        # Save files
        file1_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file1.filename))
        file2_path = os.path.join(app.config["UPLOAD_FOLDER"], secure_filename(file2.filename))
        file1.save(file1_path)
        file2.save(file2_path)

        df1 = read_file(file1_path)
        df2 = read_file(file2_path)

        if df1 is None or df2 is None:
            return jsonify({"error": "Could not read one of the files"}), 400

        # Merge data on unique keys
        merged = pd.merge(
            df1[[unique_col1, compare_col1]],
            df2[[unique_col2, compare_col2]],
            left_on=unique_col1,
            right_on=unique_col2,
            how="outer",
            suffixes=("_file1", "_file2")
        )

        # Categorize results
        matched = merged[(merged[compare_col1] == merged[compare_col2]) & merged[compare_col1].notna()]
        partially_matched = merged[(merged[compare_col1] != merged[compare_col2]) & merged[unique_col1].notna() & merged[unique_col2].notna()]
        sheet1_unmatched = merged[merged[unique_col2].isna()]  # in File1, not in File2
        sheet2_unmatched = merged[merged[unique_col1].isna()]  # in File2, not in File1

        # Save to Excel with 4 sheets
        output_path = os.path.join(app.config["UPLOAD_FOLDER"], "comparison_result.xlsx")
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            matched.to_excel(writer, sheet_name="Matched", index=False)
            partially_matched.to_excel(writer, sheet_name="Partially_Matched", index=False)
            sheet1_unmatched.to_excel(writer, sheet_name="Sheet_1_UnMatched", index=False)
            sheet2_unmatched.to_excel(writer, sheet_name="Sheet_2_UnMatched", index=False)

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)



