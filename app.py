import pandas as pd
from flask import Flask, render_template, request, send_file, jsonify
import io
import concurrent.futures

app = Flask(_name_)
combined_df = {}
sheet_names = []

def read_file(file):
    filename = file.filename
    if filename.endswith('.xlsx') or filename.endswith('.xls'):
        return pd.read_excel(file, dtype=str)
    elif filename.endswith('.csv'):
        return pd.read_csv(file, dtype=str)
    elif filename.endswith('.tsv') or filename.endswith('.txt'):
        return pd.read_csv(file, sep='\t', dtype=str)
    else:
        raise ValueError("Unsupported file format")

def process_files(file1, file2, unique_column1, unique_column2, column_to_compare1, column_to_compare2):
    try:
        df1 = read_file(file1)
        df2 = read_file(file2)

        df1[unique_column1] = df1[unique_column1].str.strip().str.lstrip('0')
        df2[unique_column2] = df2[unique_column2].str.strip().str.lstrip('0')

        df1.set_index(unique_column1, inplace=True)
        df2.set_index(unique_column2, inplace=True)

        if column_to_compare1 not in df1.columns or column_to_compare2 not in df2.columns:
            return "Error: No common columns found for comparison.", None

        # Convert both columns to float for comparison
        df1[column_to_compare1] = df1[column_to_compare1].astype(float)
        df2[column_to_compare2] = df2[column_to_compare2].astype(float)

        common_index = df1.index.intersection(df2.index)
        unique_index_df1 = df1.index.difference(df2.index)
        unique_index_df2 = df2.index.difference(df1.index)

        differing_rows = df1.loc[common_index, column_to_compare1] != df2.loc[common_index, column_to_compare2]

        differing_df = df1.loc[common_index][differing_rows]
        identical_df = df1.loc[common_index][~differing_rows]
        unmatched_df1 = df1.loc[unique_index_df1]
        unmatched_df2 = df2.loc[unique_index_df2]

        differing_ = pd.DataFrame(differing_df)
        identical_ = pd.DataFrame(identical_df)
        totallyunmatched_1 = pd.DataFrame(unmatched_df1)
        totallyunmatched_2 = pd.DataFrame(unmatched_df2)

        if not differing_.empty:
            differing_[unique_column1] = differing_.index
        if not identical_.empty:
            identical_[unique_column1] = identical_.index
        if not totallyunmatched_1.empty:
            totallyunmatched_1[unique_column1] = totallyunmatched_1.index
        if not totallyunmatched_2.empty:
            totallyunmatched_2[unique_column2] = totallyunmatched_2.index

        def move_columns_to_end(df, unique_col, compare_col):
            cols = df.columns.tolist()
            if unique_col in cols:
                cols.remove(unique_col)
            if compare_col in cols:
                cols.remove(compare_col)
            cols.append(unique_col)
            if compare_col in df.columns:
                cols.append(compare_col)
            return df[cols]

        if not differing_.empty:
            differing_ = move_columns_to_end(differing_, unique_column1, column_to_compare1)
        if not identical_.empty:
            identical_ = move_columns_to_end(identical_, unique_column1, column_to_compare1)
        if not totallyunmatched_1.empty:
            totallyunmatched_1 = move_columns_to_end(totallyunmatched_1, unique_column1, column_to_compare1)
        if not totallyunmatched_2.empty:
            totallyunmatched_2 = move_columns_to_end(totallyunmatched_2, unique_column2, column_to_compare2)

        combined_df = {
            'Matched': identical_,
            'Partially_Matched': differing_,
            'Sheet_1_UnMatched': totallyunmatched_1,
            'Sheet_2_UnMatched': totallyunmatched_2
        }
        sheet_names = ['Matched', 'Partially_Matched', 'Sheet_1_UnMatched', 'Sheet_2_UnMatched']

        return None, (combined_df, sheet_names)

    except Exception as e:
        return str(e), None

@app.route('/', methods=['GET', 'POST'])
def index():
    global combined_df, sheet_names

    if request.method == 'POST':
        try:
            file1 = request.files['file1']
            file2 = request.files['file2']
            unique_column1 = request.form['unique_column1']
            unique_column2 = request.form['unique_column2']
            column_to_compare1 = request.form['columns_to_compare1']
            column_to_compare2 = request.form['columns_to_compare2']

            if file1 and file2:
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(process_files, file1, file2, unique_column1, unique_column2, column_to_compare1, column_to_compare2)
                    error, result = future.result()
                
                if error:
                    return f"Error: {error}", 500

                global combined_df, sheet_names
                combined_df, sheet_names = result

                return render_template('index.html', sheets_available=True)

        except Exception as e:
            return f"Error: {str(e)}", 500

    return render_template('index.html', sheets_available=False)

@app.route('/get_headers', methods=['POST'])
def get_headers():
    try:
        file1 = request.files.get('file1')
        file2 = request.files.get('file2')

        if not file1 or not file2:
            return jsonify({'error': 'Both files are required.'}), 400

        headers = {}
        df1 = read_file(file1)
        df2 = read_file(file2)

        headers['file1'] = df1.columns.tolist() if not df1.empty else []
        headers['file2'] = df2.columns.tolist() if not df2.empty else []

        return jsonify(headers)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/download')
def download():
    try:
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            for sheet_name, df in combined_df.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)

        output.seek(0)
        return send_file(output, as_attachment=True, download_name='comparison_output.xlsx')

    except Exception as e:
        return f"Error: {str(e)}", 500
     

if _name_ == '_main_':
    app.run(debug=True)
