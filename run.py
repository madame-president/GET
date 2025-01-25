from flask import Flask, request, render_template, jsonify
import pandas as pd
from data import get_transaction_data, get_live_price
from processing import processing
from dataframe import convert_to_dataframe
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
from dotenv import load_dotenv
import base64

load_dotenv()

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_address = request.form.get('bitcoin_address')
        user_email = request.form.get('email')

        if not user_address or not user_email:
            return jsonify({"error": "Bitcoin address and email are required"}), 400

        raw_data = get_transaction_data(user_address)
        if not raw_data:
            return jsonify({"error": "No transaction data found for the address"}), 404

        processed_data = processing(raw_data, user_address)
        df = convert_to_dataframe(processed_data, get_live_price(), user_address)

        filename = f"address_statement_{user_address}.xlsx"
        df.to_excel(filename, index=False)

        send_email_with_attachment(user_email, filename)

        return jsonify({"message": "Report generated and sent successfully"}), 200

    return render_template('index.html')

def send_email_with_attachment(user_email, filename):
    message = Mail(
        from_email="norma@normaescobar.com",
        to_emails=user_email,
        subject="Your Bitcoin Address Report",
        html_content="Please find your Bitcoin address report attached."
    )

    with open(filename, 'rb') as f:
        file_data = f.read()

    encoded_file = base64.b64encode(file_data).decode()

    attached_file = Attachment(
        FileContent(encoded_file),
        FileName(filename),
        FileType('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
        Disposition('attachment')
    )
    message.attachment = attached_file

    try:
        sg = SendGridAPIClient(os.getenv('SENDGRID_API_KEY'))  # Load API key from environment
        response = sg.send(message)
        print(f"Email sent with status code: {response.status_code}")
    except Exception as e:
        print(f"Error sending email: {e}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)