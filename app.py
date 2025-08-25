import os
import pandas as pd
from flask import Flask, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# Function to read Excel safely
def read_file(filepath):
    try:
        if filepath.endswith(".xlsx"):
            return pd.read_excel(filepath, engine="openpyxl")
        elif filepath.endswith(".csv"):
            return pd.read_csv(filepath)
        else:
            return None
    except Exception as e:
        print(f"Error reading file {filepath}: {e}")
        return None


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/get_headers", methods=["POST"])
def get_headers():
    try:
        file1 = request.files.get("file1")
        file2 = request.files.get("file2")

        headers_file1, headers_file2 = [], []

        if file1:
            filepath1 = os.path.join(UPLOAD_FOLDER, secure_filename(file1.filename))
            file1.save(filepath1)
            df1 = read_file(filepath1)
            if df1 is not None:
                headers_file1 = df1.columns.astype(str).tolist()

        if file2:
            filepath2 = os.path.join(UPLOAD_FOLDER, secure_filename(file2.filename))
            file2.save(filepath2)
            df2 = read_file(filepath2)
            if df2 is not None:
                headers_file2 = df2.columns.astype(str).tolist()

        return jsonify({
            "file1_headers": headers_file1,
            "file2_headers": headers_file2
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/compare", methods=["POST"])
def compare():
    try:
        file1 = request.files["file1"]
        file2 = request.files["file2"]

        unique_col1 = request.form["unique_column_file1"]
        unique_col2 = request.form["unique_column_file2"]
        compare_col1 = request.form["compare_column_file1"]
        compare_col2 = request.form["compare_column_file2"]

        # Save files
        filepath1 = os.path.join(UPLOAD_FOLDER, secure_filename(file1.filename))
        filepath2 = os.path.join(UPLOAD_FOLDER, secure_filename(file2.filename))
        file1.save(filepath1)
        file2.save(filepath2)

        df1 = read_file(filepath1)
        df2 = read_file(filepath2)

        if df1 is None or df2 is None:
            return jsonify({"error": "Error reading one of the files."}), 400

        # Ensure key columns are strings for matching
        df1[unique_col1] = df1[unique_col1].astype(str)
        df2[unique_col2] = df2[unique_col2].astype(str)

        # Merge on unique IDs
        merged = pd.merge(
            df1[[unique_col1, compare_col1]],
            df2[[unique_col2, compare_col2]],
            left_on=unique_col1, right_on=unique_col2,
            how="outer", indicator=True
        )

        # Sheets
        matched = merged[(merged[compare_col1] == merged[compare_col2]) & (merged["_merge"] == "both")]
        partially = merged[(merged[compare_col1] != merged[compare_col2]) & (merged["_merge"] == "both")]
        only_file1 = merged[merged["_merge"] == "left_only"]
        only_file2 = merged[merged["_merge"] == "right_only"]

        # Save results
        output_path = os.path.join(UPLOAD_FOLDER, "comparison_result.xlsx")
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            matched.to_excel(writer, index=False, sheet_name="Matched")
            partially.to_excel(writer, index=False, sheet_name="Partially_Matched")
            only_file1.to_excel(writer, index=False, sheet_name="Sheet_1_UnMatched")
            only_file2.to_excel(writer, index=False, sheet_name="Sheet_2_UnMatched")

        return send_file(output_path, as_attachment=True)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True)





