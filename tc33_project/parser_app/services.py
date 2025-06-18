# parser_app/services.py

import io
from collections import defaultdict

from .tc33_definitions import (
    TCRDefinition,
    Field,
    TCR_HEADER, TCR_TRAILER,
    CP01_TCR0, CP01_TCR1, CP01_TCR2, CP01_TCR3, CP01_TCR4, CP01_TCR5, CP01_TCR6, CP01_TCR7, CP01_TCR8, CP01_TCR9_GENERIC, CP01_TCRA, CP01_TCRB,
    CP01_TCR9_COL, CP01_TCR9_JPN, CP01_TCR9_MEX, # Specific TCR9 definitions for contextual use
    CP02_TCR0, CP02_TCR1,
    CP03_TCR0, CP03_TCR1, CP03_TCR4,
    CP04_TCR0, CP04_TCR1,
    CP05_TCR0,
    CP06_TCR0, CP06_TCR1,
    CP07_TCR0, CP07_TCR8,
    CP08_TCR0,
    CP09_TCR0, CP09_TCR4,
    CP10_TCR0,
    CP12_TCR0,
    TCR_DEFINITIONS
)

# Centralized mapping for TCR lookup (Application Code, Sequence Number) -> TCRDefinition
TCR_LOOKUP_MAP = {
    (def_obj.application_code, def_obj.tcr_sequence): def_obj
    for key, def_obj in TCR_DEFINITIONS.items()
    if isinstance(key, tuple) and len(key) == 2 and not key[0].endswith('_TCR9')
}

def parse_tc33_file(file_content: str) -> dict:
    """
    Parses the entire TC33 file content, extracting header, trailer,
    and grouping transaction component records (TCRs) by Message Identifier.

    Args:
        file_content: A string containing the full content of the TC33 file.

    Returns:
        A dictionary containing:
        - 'header': Parsed header record or None.
        - 'trailer': Parsed trailer record or None.
        - 'transactions': A dictionary where keys are Message Identifiers
                         and values are lists of parsed TCRs belonging to that transaction.
    """
    lines = file_content.splitlines()
    header = None
    trailer = None
    transactions = defaultdict(list)
    current_message_id = None
    
    current_transaction_tcr_cache = [] 
    active_transaction_cp_code = None 

    print("--- Starting TC33 File Parsing ---")

    for line_num, raw_line in enumerate(lines):
        raw_line_padded = raw_line.ljust(168, ' ') 
        raw_line_stripped = raw_line_padded.strip()
        
        if not raw_line_stripped:
            continue

        tx_code = raw_line_padded[0:2].strip()
        tx_qualifier = raw_line_padded[2:3].strip()
        seq_num = raw_line_padded[3:4].strip()
        current_line_app_code = raw_line_padded[16:20].strip()

        tcr_def = None
        
        # --- Determine TCR Definition based on parsed line data ---
        if seq_num == '0':
            key = (current_line_app_code, seq_num)
            tcr_def = TCR_LOOKUP_MAP.get(key)
            
            if tcr_def:
                if hasattr(tcr_def, 'fields') and 'Message Identifier' in tcr_def.fields:
                    try:
                        msg_id_from_tcr0 = tcr_def.get_field_value(raw_line_padded, 'Message Identifier')
                        
                        if msg_id_from_tcr0:
                            if current_message_id is None or msg_id_from_tcr0 != current_message_id:
                                print(f"DEBUG: New transaction context. Line {line_num+1}: Old MID='{current_message_id}', New MID='{msg_id_from_tcr0}'. AppCode='{current_line_app_code}'")
                                current_message_id = msg_id_from_tcr0
                                current_transaction_tcr_cache = [] 
                                active_transaction_cp_code = current_line_app_code
                            elif current_line_app_code.startswith('CP'):
                                active_transaction_cp_code = current_line_app_code
                                print(f"DEBUG: Continued transaction context. Line {line_num+1}: MID='{current_message_id}', AppCode='{current_line_app_code}'.")
                        else:
                            print(f"WARNING: Transaction TCR0 '{tcr_def.__class__.__name__}' on line {line_num+1} has an EMPTY Message Identifier. Resetting transaction context. Raw: {raw_line_stripped[:60]}...")
                            current_message_id = None 
                            current_transaction_tcr_cache = [] 
                            active_transaction_cp_code = None
                    except Exception as e:
                        print(f"ERROR: Extracting Message Identifier from {tcr_def.__class__.__name__} on line {line_num+1}: {e}. Resetting transaction context. Raw: {raw_line_stripped[:60]}...")
                        current_message_id = None 
                        current_transaction_tcr_cache = [] 
                        active_transaction_cp_code = None
                else: 
                    print(f"DEBUG: File-level record (HEDR/TRLR) found on line {line_num+1}. Resetting transaction context.")
                    current_message_id = None 
                    current_transaction_tcr_cache = []
                    active_transaction_cp_code = None
            else:
                print(f"WARNING: Unrecognized TCR0 (App Code: '{current_line_app_code}') on line {line_num+1}. Skipping record. Raw: {raw_line_stripped[:60]}...")

        elif current_message_id and active_transaction_cp_code: 
            key = (active_transaction_cp_code, seq_num)
            tcr_def = TCR_LOOKUP_MAP.get(key)

            if tcr_def is None and seq_num == '9' and active_transaction_cp_code == 'CP01':
                country_code = None
                for cached_tcr in current_transaction_tcr_cache:
                    if cached_tcr.get('tcr_definition_name') == 'CP01_TCR3':
                        country_code = cached_tcr.get('parsed_fields', {}).get('Ship to Country Code')
                        if country_code:
                            country_code = country_code.strip().upper()
                            break
                
                if country_code == 'COL':
                    tcr_def = TCR_DEFINITIONS.get('CP01_TCR9_COL')
                    print(f"DEBUG: CP01 TCR9 detected as COL for MID='{current_message_id}' on line {line_num+1}.")
                elif country_code == 'JPN':
                    tcr_def = TCR_DEFINITIONS.get('CP01_TCR9_JPN')
                    print(f"DEBUG: CP01 TCR9 detected as JPN for MID='{current_message_id}' on line {line_num+1}.")
                elif country_code == 'MEX':
                    tcr_def = TCR_DEFINITIONS.get('CP01_TCR9_MEX')
                    print(f"DEBUG: CP01 TCR9 detected as MEX for MID='{current_message_id}' on line {line_num+1}.")
                else:
                    tcr_def = CP01_TCR9_GENERIC
                    print(f"DEBUG: CP01 TCR9 detected as GENERIC for MID='{current_message_id}' on line {line_num+1}.")
            
            if not tcr_def:
                print(f"WARNING: No specific TCR definition found for active CP code '{active_transaction_cp_code}' and sequence '{seq_num}' on line {line_num+1}. Skipping record. Raw: {raw_line_stripped[:60]}...")
                continue

        else: 
            print(f"INFO: Record on line {line_num+1} skipped due to missing or invalid transaction context (no current_message_id or active_transaction_cp_code). Raw: {raw_line_stripped[:60]}...")
            continue

        # --- Process identified TCR definition and extract data ---
        parsed_fields = {}
        try:
            for field_name, field_obj in tcr_def.fields.items():
                parsed_fields[field_name] = tcr_def.get_field_value(raw_line_padded, field_name)
            
            # --- ADD THIS DEBUG PRINT FOR CARD ID ---
            if tcr_def.__class__.__name__ == 'CP01_TCR1' and 'Card ID' in parsed_fields:
                # This debug print is already in place.
                print(f"DEBUG: Line {line_num+1} - CP01_TCR1. Extracted Card ID: '{parsed_fields['Card ID']}' (Raw: '{raw_line_padded[69:71]}')")
            # --- END DEBUG PRINT ---

        except Exception as e:
            print(f"ERROR: Parsing fields for {tcr_def.__class__.__name__} on line {line_num+1}: {e}. Raw: {raw_line_stripped[:60]}...")
            continue

        tcr_info = {
            'tcr_definition_name': tcr_def.__class__.__name__,
            'tcr_type_code': tx_code,
            'tcr_qualifier': tx_qualifier,
            'tcr_sequence': seq_num,
            'application_code': tcr_def.application_code, 
            'parsed_fields': parsed_fields,
            '_raw_line': raw_line_stripped
        }

        # Store the parsed data
        if tcr_def == TCR_HEADER:
            header = tcr_info
            print(f"DEBUG: Found HEADER. Line {line_num+1}.")
        elif tcr_def == TCR_TRAILER:
            trailer = tcr_info
            print(f"DEBUG: Found TRAILER. Line {line_num+1}. Total Transaction Count: {trailer.get('parsed_fields', {}).get('Total Transaction Count')}")
        elif current_message_id: 
            transactions[current_message_id].append(tcr_info)
            current_transaction_tcr_cache.append(tcr_info)
            # --- MODIFIED DEBUG PRINT HERE ---
            print(f"DEBUG: Added {tcr_def.__class__.__name__} (Seq {seq_num}) to transaction '{current_message_id}' (Line {line_num+1}). Current TCRs in cache: {len(current_transaction_tcr_cache)}")
        else:
            print(f"INFO: Parsed transaction TCR {tcr_def.__class__.__name__} on line {line_num+1} but could not group due to missing or invalid Message Identifier. This record will not be included in transaction groups. Raw: {raw_line_stripped[:60]}...")

    print(f"--- Parsing Complete ---")
    print(f"Total unique transactions identified by Message ID: {len(transactions)}")

    return {
        'header': header,
        'trailer': trailer,
        'transactions': dict(transactions)
    }
