# parser_app/views.py

import os
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from .forms import UploadFileForm
from .services import parse_tc33_file
import io
import tempfile # Import for temporary files

def generate_raw_transactions_excel(parsed_data):
    """
    Generates a single-sheet Excel file containing all transactions from the parsed data.
    A 'Card ID' column is added to each transaction for later processing.

    Args:
        parsed_data (dict): The dictionary returned by parse_tc33_file.

    Returns:
        tuple: A BytesIO buffer containing the Excel file and an error message (or None).
    """
    header = parsed_data.get('header')
    trailer = parsed_data.get('trailer')
    transactions_by_message_id = parsed_data.get('transactions', {})

    if not transactions_by_message_id:
        return None, "No valid transactions found to generate raw Excel file."

    output = io.BytesIO()
    all_transactions = []

    # Flatten all transactions into a single list
    for msg_id, tcr_list in transactions_by_message_id.items():
        card_id = 'UNKNOWN'
        combined_transaction_data = {}
        combined_transaction_data['Message Identifier'] = msg_id

        for tcr_info in tcr_list:
            tcr_def_name_prefix = tcr_info.get('tcr_definition_name', '').replace('_TCR', '_TCR_')
            prefixed_fields = {
                f"{tcr_def_name_prefix}_{k}": v
                for k, v in tcr_info.get('parsed_fields', {}).items()
            }
            combined_transaction_data.update(prefixed_fields)

            # Identify Card ID from the CP01_TCR1 record
            if tcr_info.get('tcr_definition_name') == 'CP01_TCR1':
                current_card_id = tcr_info.get('parsed_fields', {}).get('Card ID')
                if current_card_id:
                    card_id = current_card_id.strip().upper()

        # Add a dedicated 'Card ID' column for easy filtering in the next step
        combined_transaction_data['Card ID'] = card_id
        all_transactions.append(combined_transaction_data)

    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Sheet 1: Summary based on Header/Trailer
            summary_data = []
            if header:
                for key, value in header.get('parsed_fields', {}).items():
                    summary_data.append({'Category': 'Header', 'Field': key, 'Value': value})
            if trailer:
                for key, value in trailer.get('parsed_fields', {}).items():
                    summary_data.append({'Category': 'Trailer', 'Field': key, 'Value': value})

            if summary_data:
                # MODIFICATION: Convert all data to string type to prevent scientific notation.
                df_summary = pd.DataFrame(summary_data).astype(str)
                df_summary.to_excel(writer, sheet_name='Total Amount and Count', index=False)

            # Sheet 2: All transactions compiled into one sheet
            if all_transactions:
                # MODIFICATION: Convert all data to string type to prevent scientific notation.
                df_all = pd.DataFrame(all_transactions).astype(str)
                df_all.to_excel(writer, sheet_name='All Transactions', index=False)
            else:
                 pd.DataFrame([{"Message": "No transactions data found."}]).to_excel(writer, sheet_name='All Transactions', index=False)

    except Exception as e:
        return None, f"An error occurred while generating the raw Excel file: {e}"

    output.seek(0)
    return output, None

def generate_summary_from_excel_file(excel_file_path):
    """
    Reads a temporary Excel file, separates transactions into new sheets based on the
    'Card ID' column, and returns a new Excel file in-memory.

    Args:
        excel_file_path (str): The file path to the temporary Excel file.

    Returns:
        tuple: A BytesIO buffer containing the final summary Excel file and an error message (or None).
    """
    try:
        # MODIFICATION: Read all data as strings (dtype=str) to preserve formatting and prevent scientific notation.
        df = pd.read_excel(excel_file_path, sheet_name='All Transactions', dtype=str)
        if 'Card ID' not in df.columns:
            return None, "The source Excel file is missing the required 'Card ID' column."

    except FileNotFoundError:
        return None, f"Temporary file could not be found at path: {excel_file_path}."
    except Exception as e:
        return None, f"An error occurred while reading the temporary Excel file: {e}"

    # Filter the DataFrame based on the 'Card ID' column
    # The data types are already strings, so they will be written correctly.
    visa_transactions = df[df['TCRDefinition_Card ID'] == 'VI']
    mastercard_transactions = df[df['TCRDefinition_Card ID'] == 'MC']
    jcb_transactions = df[df['TCRDefinition_Card ID'] == 'JC']
    diners_club_transactions = df[df['TCRDefinition_Card ID'] == 'DC']
    amex_transactions = df[df['TCRDefinition_Card ID'] == 'AX']
    discover_transactions = df[df['TCRDefinition_Card ID'] == 'DI']

    known_ids = ['VI', 'MC', 'JC', 'DC', 'AX', 'DI']
    other_transactions = df[~df['TCRDefinition_Card ID'].isin(known_ids)]

    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Attempt to copy the summary sheet from the source file to the new file
            try:
                # MODIFICATION: Read all data as strings here as well for consistency.
                df_summary = pd.read_excel(excel_file_path, sheet_name='Total Amount and Count', dtype=str)
                df_summary.to_excel(writer, sheet_name='Total Amount and Count', index=False)
            except Exception:
                # If the summary sheet doesn't exist or fails to copy, we can ignore it
                pass

            # Write each filtered DataFrame to a new sheet in the final Excel file
            if not visa_transactions.empty:
                visa_transactions.to_excel(writer, sheet_name='VISA Transactions', index=False)
            if not mastercard_transactions.empty:
                mastercard_transactions.to_excel(writer, sheet_name='Mastercard Transactions', index=False)
            if not jcb_transactions.empty:
                jcb_transactions.to_excel(writer, sheet_name='JCB Transactions', index=False)
            if not diners_club_transactions.empty:
                diners_club_transactions.to_excel(writer, sheet_name='Diners Club Transactions', index=False)
            if not amex_transactions.empty:
                amex_transactions.to_excel(writer, sheet_name='AX Transactions', index=False)
            if not discover_transactions.empty:
                discover_transactions.to_excel(writer, sheet_name='Discover Transactions', index=False)
            if not other_transactions.empty:
                other_transactions.to_excel(writer, sheet_name='Other Transactions', index=False)

    except Exception as e:
        return None, f"An error occurred while writing the final summary Excel file: {e}"

    output.seek(0)
    return output, None


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read().decode('utf-8', errors='ignore')

            # 1. Parse the uploaded text file content
            parsed_data = parse_tc33_file(file_content)
            if not parsed_data.get('transactions'):
                return HttpResponseBadRequest("No valid TC-33 transaction records found in the uploaded file.")

            # 2. Generate the intermediate Excel file with all transactions in one sheet
            raw_excel_buffer, error = generate_raw_transactions_excel(parsed_data)
            if error:
                return HttpResponseBadRequest(f"Failed to generate intermediate data: {error}")

            temp_file_path = None
            try:
                # 3. Save this intermediate file temporarily to disk
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as temp_f:
                    temp_file_path = temp_f.name
                    temp_f.write(raw_excel_buffer.getvalue())

                # 4. Generate the final summary Excel by reading the temporary file
                summary_excel_buffer, error = generate_summary_from_excel_file(temp_file_path)
                if error:
                    return HttpResponseBadRequest(f"Failed to generate summary file: {error}")

            finally:
                # 5. Crucially, ensure the temporary file is deleted after use
                if temp_file_path and os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

            # 6. Return the final summary file as the HTTP response
            response = HttpResponse(
                summary_excel_buffer.getvalue(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename="tc33_summary_by_card.xlsx"'
            return response

        else:
            return HttpResponseBadRequest("Invalid form submission. Please check your file.")
    else:
        form = UploadFileForm()
    return render(request, 'parser_app/upload.html', {'form': form})