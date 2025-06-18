# parser_app/views.py

import os
import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseBadRequest
from django.conf import settings
from .forms import UploadFileForm
from .services import parse_tc33_file
import io

def generate_excel_file(parsed_data):
    """
    Generates a multi-sheet Excel file from parsed TC-33 records.
    Splits transactions into sheets based on Card ID (VISA, Mastercard, JCB, Diners Club, AX, Discover, Other).

    Args:
        parsed_data (dict): A dictionary containing 'header', 'trailer',
                            and 'transactions' as returned by parse_tc33_file.

    Returns:
        tuple: A tuple containing:
            - io.BytesIO: A BytesIO object containing the Excel file, or None if no data.
            - str: An error message, or None if successful.
    """
    header = parsed_data.get('header')
    trailer = parsed_data.get('trailer')
    transactions_by_message_id = parsed_data.get('transactions', {})

    if not header and not trailer and not transactions_by_message_id:
        return None, "No valid TC-33 records found to generate Excel."

    output = io.BytesIO()
    try:
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # --- Sheet 1: Total Amount and Count (Summary) ---
            summary_data = []
            if header:
                for key, value in header.get('parsed_fields', {}).items():
                    summary_data.append({'Category': 'Header', 'Field': key, 'Value': value})
            if trailer:
                for key, value in trailer.get('parsed_fields', {}).items():
                    summary_data.append({'Category': 'Trailer', 'Field': key, 'Value': value})

            if summary_data:
                df_summary = pd.DataFrame(summary_data)
                df_summary.to_excel(writer, sheet_name='Total Amount and Count', index=False)
            else:
                pd.DataFrame([{"Message": "No Header or Trailer records found."}]).to_excel(writer, sheet_name='Total Amount and Count', index=False)


            # --- Categorize Transactions by Card ID ---
            visa_transactions = []
            mastercard_transactions = []
            jcb_transactions = [] # New list for JCB
            diners_club_transactions = [] # New list for Diners Club
            amex_transactions = []
            discover_transactions = [] # New list for Discover
            other_transactions = [] # For other card IDs or transactions without a recognized CP01 TCR1

            for msg_id, tcr_list in transactions_by_message_id.items():
                card_id = 'UNKNOWN' # Default value
                
                # Flatten all TCRs for this transaction into a single dictionary
                combined_transaction_data = {}
                
                # Add Message Identifier at the start for clarity on transaction-level sheets
                combined_transaction_data['Message Identifier'] = msg_id

                for tcr_info in tcr_list:
                    # Make sure the prefix helps identify the TCR and avoid collisions
                    tcr_def_name_prefix = tcr_info.get('tcr_definition_name', '').replace('_TCR', '_TCR_') 
                    
                    # Add raw line to combined data for debugging/completeness
                    combined_transaction_data[f"{tcr_def_name_prefix}_Raw_Line"] = tcr_info.get('_raw_line')

                    # Prefix all parsed fields with TCR definition name for uniqueness
                    prefixed_fields = {
                        f"{tcr_def_name_prefix}_{k}": v 
                        for k, v in tcr_info.get('parsed_fields', {}).items()
                    }
                    combined_transaction_data.update(prefixed_fields)

                    # Check for Card ID, specifically from CP01_TCR1
                    # Note: The Card ID field is expected in CP01_TCR1 based on tc33_definitions.py
                    if tcr_info.get('tcr_definition_name') == 'CP01_TCR1':
                        current_card_id = tcr_info.get('parsed_fields', {}).get('Card ID')
                        if current_card_id:
                            card_id = current_card_id.strip().upper() # Clean and standardize

                # Assign transaction to appropriate list based on Card ID
                if card_id == 'VI':
                    visa_transactions.append(combined_transaction_data)
                elif card_id == 'MC':
                    mastercard_transactions.append(combined_transaction_data)
                elif card_id == 'JC': # JCB
                    jcb_transactions.append(combined_transaction_data)
                elif card_id == 'DC': # Diners Club
                    diners_club_transactions.append(combined_transaction_data)
                elif card_id == 'AX':
                    amex_transactions.append(combined_transaction_data)
                elif card_id == 'DI': # Discover
                    discover_transactions.append(combined_transaction_data)
                else:
                    # For transactions not fitting specific categories, add the identified Card ID for context
                    combined_transaction_data['Identified Card ID (Other)'] = card_id 
                    other_transactions.append(combined_transaction_data)

            # --- Write categorized transactions to sheets ---

            # Sheet 2: VISA Transactions
            if visa_transactions:
                df_visa = pd.DataFrame(visa_transactions)
                df_visa.to_excel(writer, sheet_name='VISA Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No VISA transactions found."}]).to_excel(writer, sheet_name='VISA Transactions', index=False)

            # Sheet 3: Mastercard Transactions
            if mastercard_transactions:
                df_mc = pd.DataFrame(mastercard_transactions)
                df_mc.to_excel(writer, sheet_name='Mastercard Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No Mastercard transactions found."}]).to_excel(writer, sheet_name='Mastercard Transactions', index=False)

            # Sheet 4: AX Transactions
            if amex_transactions:
                df_ax = pd.DataFrame(amex_transactions)
                df_ax.to_excel(writer, sheet_name='AX Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No AX transactions found."}]).to_excel(writer, sheet_name='AX Transactions', index=False)

            # Sheet 5: JCB Transactions
            if jcb_transactions:
                df_jcb = pd.DataFrame(jcb_transactions)
                df_jcb.to_excel(writer, sheet_name='JCB Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No JCB transactions found."}]).to_excel(writer, sheet_name='JCB Transactions', index=False)

            # Sheet 6: Diners Club Transactions
            if diners_club_transactions:
                df_dc = pd.DataFrame(diners_club_transactions)
                df_dc.to_excel(writer, sheet_name='Diners Club Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No Diners Club transactions found."}]).to_excel(writer, sheet_name='Diners Club Transactions', index=False)

            # Sheet 7: Discover Transactions
            if discover_transactions:
                df_di = pd.DataFrame(discover_transactions)
                df_di.to_excel(writer, sheet_name='Discover Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No Discover transactions found."}]).to_excel(writer, sheet_name='Discover Transactions', index=False)

            # Sheet 8: Other Transactions
            if other_transactions:
                df_other = pd.DataFrame(other_transactions)
                df_other.to_excel(writer, sheet_name='Other Transactions', index=False)
            else:
                pd.DataFrame([{"Message": "No Other transactions found."}]).to_excel(writer, sheet_name='Other Transactions', index=False)


    except Exception as e:
        return None, f"An error occurred while generating the Excel file: {e}"

    output.seek(0)
    return output, None


def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES['file']
            file_content = uploaded_file.read().decode('utf-8', errors='ignore')

            # Use the main parsing function from services.py
            parsed_data = parse_tc33_file(file_content)

            if not parsed_data['header'] and not parsed_data['trailer'] and not parsed_data['transactions']:
                return HttpResponseBadRequest("No valid TC-33 records found in the uploaded file.")

            # Generate Excel file using the structured parsed_data
            excel_file_buffer, error_message = generate_excel_file(parsed_data)

            if excel_file_buffer:
                response = HttpResponse(
                    excel_file_buffer.getvalue(),
                    content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                )
                response['Content-Disposition'] = 'attachment; filename="tc33_parsed_data.xlsx"'
                return response
            else:
                return HttpResponseBadRequest(f"Failed to generate Excel file: {error_message}")
        else:
            return HttpResponseBadRequest("Invalid form submission. Please check your file.")
    else:
        form = UploadFileForm()
    return render(request, 'parser_app/upload.html', {'form': form})
