import os
from flask import Flask, request, jsonify, render_template, send_file
from datetime import datetime
from zipfile import ZipFile
from datetime import datetime
import re

# Get today's date
today_date = datetime.now()

# Format it as yyyymmdd
today_date = today_date.strftime('%Y%m%d')

app = Flask(__name__)


def convert_date_format(input_date):
    # Convert string to datetime object
    date_object = datetime.strptime(input_date, '%Y%m%d')

    # Format the datetime object to the desired format
    formatted_date = date_object.strftime('%d/%m/%Y')

    return formatted_date


def process_log_file(date, log_type):
    directory_path = 'data/logs'

    # Get a list of files in the directory
    date_dirs = os.listdir(directory_path)

    processed_date_dirs = []

    for dir_name in date_dirs:
        p_ele = {}
        p_ele['dirname'] = convert_date_format(dir_name)
        p_ele['date'] = dir_name
        processed_date_dirs.append(p_ele)

    # Assuming `date` parameter is in the format 'YYYY-MM-DD'
    file_path = f'data/logs/{date}/{log_type}.txt'

    try:
        with open(file_path, 'r') as file:
            file_contents = file.readlines()
    except FileNotFoundError:
        return None  # Return None if file not found
    
    logs_dict = {}

    # Iterate over each log entry
    for log_entry in file_contents:
        # Extract datetime from the log entry
        match = re.search(r'\[(.*?)\]', log_entry)
        if match:
            datetime_str = match.group(1)
            datetime_obj = datetime.strptime(datetime_str, '%Y-%m-%dT%H:%M:%S.%f%z')

            # Use datetime as the key in the dictionary
            logs_dict[datetime_obj] = log_entry.strip()
    
    # Format timestamps as strings in 'm/d/Y h:i A' format
    log_entries = {timestamp.strftime('%m/%d/%Y %I:%M %p'): log_entry for timestamp, log_entry in logs_dict.items()}
    
    return processed_date_dirs, log_entries


@app.route('/')
def index():
    directory_path = 'data/logs'

    # Get a list of files in the directory
    date_dirs = os.listdir(directory_path)

    processed_date_dirs = []

    for dir_name in date_dirs:
        p_ele = {}
        p_ele['dirname'] = convert_date_format(dir_name)
        p_ele['date'] = dir_name
        processed_date_dirs.append(p_ele)

    print(processed_date_dirs)

    return render_template('index.html', date_dirs=processed_date_dirs)


@app.route('/logs/<date>/error')
def error_logs(date):
    result = process_log_file(date, 'error')
    if result is None:
        return render_template('error.html', error_message='File not found')
    
    processed_date_dirs, log_entries = result
    return render_template('log.html', date_dirs=processed_date_dirs, log_type='Error', log_date=date, log_entries=log_entries)

@app.route('/logs/<date>/warning')
def warning_logs(date):
    result = process_log_file(date, 'warning')
    if result is None:
        return render_template('error.html', error_message='File not found')
    
    processed_date_dirs, log_entries = result
    return render_template('log.html', date_dirs=processed_date_dirs, log_type='Warning', log_date=date, log_entries=log_entries)

@app.route('/logs/<date>/sos')
def sos_logs(date):
    result = process_log_file(date, 'sos')
    if result is None:
        return render_template('error.html', error_message='File not found')
    
    processed_date_dirs, log_entries = result
    return render_template('log.html', date_dirs=processed_date_dirs, log_type='SOS', log_date=date, log_entries=log_entries)

@app.route('/logs/<date>/debug')
def debug_logs(date):
    result = process_log_file(date, 'debug')
    if result is None:
        return render_template('error.html', error_message='File not found')
    
    processed_date_dirs, log_entries = result
    return render_template('log.html', date_dirs=processed_date_dirs, log_type='Debug', log_date=date, log_entries=log_entries)

@app.route('/logs/<date>/activity')
def user_activites(date):
    result = process_log_file(date, 'activity')
    if result is None:
        return render_template('error.html', error_message='File not found')
    
    processed_date_dirs, log_entries = result
    return render_template('log.html', date_dirs=processed_date_dirs, log_type='Activity', log_date=date, log_entries=log_entries)


@app.route('/download/<date>')
def download_directory(date):
    try:
        directory_to_zip = 'data/logs/' + date

        # Create a temporary zip file
        zip_filename = date + '-logview.zip'
        zip_path = os.path.join('tmp', zip_filename)

        with ZipFile(zip_path, 'w') as zipf:
            for root, dirs, files in os.walk(directory_to_zip):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, directory_to_zip)
                    zipf.write(file_path, arcname=arcname)
            
        # # Send the zip file as a response
        return send_file(zip_path, as_attachment=True, download_name=date + '-logview.zip')

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500  # 500 is the HTTP status code for Internal Server Error


@app.route('/receive/<logtype>', methods=['POST'])
def receive_logs(logtype):
    try:
        # Ensure the 'logs' key is present in the request
        if 'logs' not in request.files:
            return jsonify({'status': 'error', 'message': 'No log file provided'}), 400  # 400 is the HTTP status code for Bad Request

        if logtype not in ['error', 'info', 'warning', 'sos', 'debug', 'activity', 'info']:
            logtype = 'info'
        
        log_file = request.files['logs']

        # Specify the directory path
        directory_path = f'data/logs/{today_date}'

        # Check if the directory exists
        if not os.path.exists(directory_path):
            # Create the directory if it doesn't exist
            os.makedirs(directory_path)
            print(f'Directory "{directory_path}" created.')


        # Specify the directory where you want to save the log file
        save_path = os.path.join("data/logs/" + today_date, logtype + '.txt')
        log_file.save(save_path)

        # Process and store logs as needed
        # You might want to handle log storage, parsing, or any other custom logic here

        return jsonify({'status': 'success'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500  # 500 is the HTTP status code for Internal Server Error

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
