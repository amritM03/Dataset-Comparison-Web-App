from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
RESULTS_FOLDER = "results"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULTS_FOLDER, exist_ok=True)


def clear_folder(folder):
    """Remove old files before saving new ones"""
    for f in os.listdir(folder):
        os.remove(os.path.join(folder, f))


def read_file(file_path):
    try:
        if file_path.endswith(".csv"):
            return pd.read_csv(file_path)
        elif file_path.endswith((".xls", ".xlsx")):
            return pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html")


# 🔹 Get headers from uploaded files
@app.route("/get_headers", methods=["POST"])
def get_headers():
    try:
        clear_folder(UPLOAD_FOLDER)

        file1 = request.files.get("file1")
        file2 = request.files.get("file2")

        headers_file1, headers_file2 = [], []

        if file1:
            filepath1 = os.path.join(UPLOAD_FOLDER, secure_filename(file1.filename))
            file1.save(filepath1)
            df1 = read_file(filepath1)
            if df1 is not None:
                headers_file1 = df1.columns.tolist()

        if file2:
            filepath2 = os.path.join(UPLOAD_FOLDER, secure_filename(file2.filename))
            file2.save(filepath2)
            df2 = read_file(filepath2)
            if df2 is not None:
                headers_file2 = df2.columns.tolist()

        return jsonify({
            "file1_headers": headers_file1,
            "file2_headers": headers_file2
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# 🔹 Compare and create Excel with 4 sheets
@app.route("/compare", methods=["POST"])
def compare():
    try:
        file1_name = request.form.get("file1_name")
        file2_name = request.form.get("file2_name")

        unique_col1 = request.form.get("unique_column_file1")
        unique_col2 = request.form.get("unique_column_file2")
        compare_col1 = request.form.get("compare_column_file1")
        compare_col2 = request.form.get("compare_column_file2")

        file1_path = os.path.join(UPLOAD_FOLDER, file1_name)
        file2_path = os.path.join(UPLOAD_FOLDER, file2_name)

        df1 = read_file(file1_path)
        df2 = read_file(file2_path)

        if df1 is None or df2 is None:
            return jsonify({"error": "Could not read one of the files"}), 400

        merged = pd.merge(
            df1[[unique_col1, compare_col1]],
            df2[[unique_col2, compare_col2]],
            left_on=unique_col1,
            right_on=unique_col2,
            how="outer",
            indicator=True
        )

        # Sheets
        matched = merged[
            (merged["_merge"] == "both") &
            (merged[compare_col1] == merged[compare_col2])
        ]

        partially_matched = merged[
            (merged["_merge"] == "both") &
            (merged[compare_col1] != merged[compare_col2])
        ]

        sheet1_unmatched = merged[merged["_merge"] == "left_only"]
        sheet2_unmatched = merged[merged["_merge"] == "right_only"]

        # Save results in single Excel file
        result_file = os.path.join(RESULTS_FOLDER, f"comparison_result_{uuid.uuid4().hex}.xlsx")
        with pd.ExcelWriter(result_file, engine="openpyxl") as writer:
            matched.to_excel(writer, sheet_name="Matched", index=False)
            partially_matched.to_excel(writer, sheet_name="Partially_Matched", index=False)
            sheet1_unmatched.to_excel(writer, sheet_name="Sheet_1_UnMatched", index=False)
            sheet2_unmatched.to_excel(writer, sheet_name="Sheet_2_UnMatched", index=False)

        return send_file(result_file, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)





