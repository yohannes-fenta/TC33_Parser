# parser_app/tc33_definitions.py

class Field:
    """Represents a single field within a TCR."""

    def __init__(self, name, start, length, data_format, description=""):
        self.name = name
        self.start = start  # 1-based position from documentation
        self.length = length
        self.data_format = data_format
        self.description = description
        self.python_start = start - 1  # 0-based for Python slicing
        self.python_end = self.python_start + length  # 0-based for Python slicing (exclusive end)

    def __repr__(self):
        return f"Field(name='{self.name}', start={self.start}, length={self.length}, format='{self.data_format}')"


class TCRDefinition:
    """Base class for TCR definitions."""

    def __init__(self, tcr_type, tcr_qualifier, tcr_sequence, application_code, fields):
        self.tcr_type = tcr_type  # Transaction Code (e.g., '33')
        self.tcr_qualifier = tcr_qualifier  # Transaction Code Qualifier (e.g., '0')
        self.tcr_sequence = tcr_sequence  # Transaction Component Sequence Number (e.g., '0', '1', '4')
        self.application_code = application_code  # e.g., 'HEDR', 'TRLR', 'CP01'
        self.fields = {field.name: field for field in fields}  # Dictionary for easy lookup

    def __repr__(self):
        return (f"{self.__class__.__name__}(tcr_type='{self.tcr_type}', "
                f"tcr_qualifier='{self.tcr_qualifier}', tcr_sequence='{self.tcr_sequence}', "
                f"application_code='{self.application_code}')")

    def get_field_value(self, line: str, field_name: str):
        """
        Extracts the value of a specific field from a raw TCR line.
        Handles padding with spaces if the line is shorter than expected field end.
        Converts numeric fields to int/float and returns stripped strings for alphanumeric.
        """
        field = self.fields.get(field_name)
        if not field:
            raise ValueError(
                f"Field '{field_name}' not defined for {self.__class__.__name__}.")

        # Ensure the line is long enough, pad with spaces if necessary
        if len(line) < field.python_end:
            line = line.ljust(field.python_end, ' ')

        value = line[field.python_start:field.python_end]

        if field.data_format in ['UN', 'N']:  # Unpacked Numeric or Numeric
            stripped_value = value.strip()
            if not stripped_value:
                return 0  # Treat empty numeric fields as 0
            try:
                # Handle implied decimals if necessary (this would be specific to field description)
                # For now, assume integer or float based on presence of decimal point in value
                if '.' in stripped_value:
                    return float(stripped_value)
                return int(stripped_value)
            except ValueError:
                # print(f"Warning: Could not convert '{value}' to number for field '{field_name}'")
                return 0 # Return 0 or None for non-numeric content in numeric fields
        elif field.data_format in ['AN', 'ANS', 'DX']:  # Alphanumeric, Alphanumeric Special, or Display Hexadecimal
            return value.strip()
        else:
            return value.strip() # Default for other formats


# --- TCR Definitions based on Chapter 11.txt ---
# Note: Filler fields are included for accurate byte length representation as per doc.

# TC 33.A - TCR 0 Capture - File Header (HEDR)
TCR_HEADER = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='HEDR',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code - Header', 17, 4, 'AN', 'Static value set to HEDR.'),
        Field('Capture File Number', 21, 4, 'UN', 'The file number assigned by the VIC.'),
        Field('Capture Creation Date', 25, 8, 'UN', 'The date when the file was created by the VIC.'),
        Field('Reserved', 33, 136, 'AN', 'This field is reserved; space-filled.'), # Positions 33-168
    ]
)

# TC 33.A - TCR 0 Capture - File Trailer (TRLR)
TCR_TRAILER = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='TRLR',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code - Trailer', 17, 4, 'AN', 'Static value set to TRLR.'),
        Field('Capture File Number', 21, 4, 'UN', 'The file number assigned by the VIC.'),
        Field('Capture Creation Date', 25, 8, 'UN', 'The date when the file was created by the VIC.'),
        Field('Total Transaction Count', 33, 9, 'UN', 'The count includes all capture transaction records for the entire capture file.'),
        Field('Total Transaction Amount', 42, 20, 'UN', 'Contains the hash total of all transaction amounts within the file.'),
        Field('Reserved', 62, 107, 'AN', 'This field is reserved; space-filled.'), # Positions 62-168
    ]
)

# --- CP01 TCRs ---
# TC 33.A - CP 01 TCR 0 Transaction Data
CP01_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'This TCR group code identifies a group of related Transaction Component Records (TCR0 through TCRE). This field has a static value of CP01.'),
        Field('Message Identifier', 21, 15, 'AN', 'A unique message identifier that links a specific capture record among multiple capture records being submitted for a single transaction.'),
        Field('Transaction Identifier', 36, 15, 'AN', 'A unique value that Visa assigns to each transaction and returns to the acquirer in the authorization response.'),
        Field('Retrieval Reference Number', 51, 12, 'AN', 'An identification number assigned by the processing entity that is used with other data elements to identify and track messages related to a given cardholder transaction.'),
        Field('Account Number', 63, 16, 'AN', 'This field contains an issuer-assigned number or a payment token that identifies a cardholder\'s account.'),
        Field('Account Number Extension', 79, 3, 'AN', 'This field is used for account numbers or tokens greater than 16 digits. It contains a 3-digit extension of the account number or token.'),
        Field('Expiration Date', 82, 4, 'AN', 'This field contains an account number or token expiration date in the following format: YYMM.'),
        Field('Purchase Date', 86, 4, 'UN', 'Date the purchase transaction was made (MMDD) based on Greenwich mean time (GMT).'),
        Field('Authorization Date', 90, 4, 'AN', 'The actual date that the request for the authorization was made based on GMT. Format: MMDD.'),
        Field('Decimal Positions Indicator', 94, 2, 'AN', 'Indicates decimal positions of all amount fields.'),
        Field('Authorized Amount', 96, 12, 'UN', 'Amount the issuer originally authorized. This field is formatted based on currency exponents.'),
        Field('Authorization Currency Code', 108, 3, 'AN', 'Currency code of the authorized source amount. ISO numeric currency code.'),
        Field('Total Authorized Amount', 111, 12, 'UN', 'Total authorized amount of the transaction including taxes and miscellaneous fees less reversals.'),
        Field('Source Amount', 123, 12, 'UN', 'This field contains the purchase value in transaction currency.'),
        Field('Source Currency Code', 135, 3, 'AN', 'Currency code used in the transaction. Valid currency ISO numeric code.'),
        Field('Tip Amount', 138, 12, 'UN', 'This field contains the tip amount.'),
        Field('Action Code', 150, 2, 'AN', 'This field contains the action code of the capture transaction.'),
        Field('Service Identifier', 152, 2, 'AN', 'This field contains the code used to identify the type of service.'),
        Field('Acquiring Identifier', 154, 6, 'UN', 'The field contains the Acquiring Identifier used in the authorization.'),
        Field('Message Reason Code', 160, 4, 'AN', 'This field contains the Message Reason Code.'),
        Field('Additional Authorization Indicator', 164, 1, 'N', 'This field will contain one of these values: 1 (Partial authorization), 2 (Estimated authorization), 3 (Both partial and estimated).'),
        Field('Domestic Switch ID', 165, 4, 'AN', 'This field will contain a CyberSource generated ID for domestic switches when complying with country routing mandates.'), # Positions 165-168
    ]
)

# TC 33.A - CP 01 TCR 1 Additional Data
CP01_TCR1 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='1',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 1.'),
        Field('Capture Date', 5, 4, 'UN', 'The date when the merchant intends to process the capture file (MMDD) in the merchant local time.'),
        Field('Authorization Code', 9, 6, 'AN', 'A code that an issuer, its authorizing processor, or Stand-In Processing (STIP) provides to indicate approval of a transaction.'),
        Field('POS Entry Mode', 15, 2, 'AN', 'A V.I.P. System field indicating the method by which a point-of-transaction terminal obtains and transmits the cardholder information.'),
        Field('Card Acceptor ID', 17, 15, 'ANS', 'Code that identifies the card acceptor operating the POS terminal.'),
        Field('Terminal ID', 32, 8, 'ANS', 'Code that identifies the card acceptor terminal.'),
        Field('Mail/Phone/Electronic Commerce and Payment Indicator', 40, 1, 'AN', 'Indicates transaction performed by mail order, telephone, or electronic commerce.'),
        Field('Unattended Acceptance Terminal Indicator', 41, 1, 'AN', 'Indicates type of unattended terminal.'),
        Field('AVS Response Code', 42, 1, 'AN', 'Contains the response to an Address Verification Service (AVS) request.'),
        Field('Authorization Source Code', 43, 1, 'AN', 'This field identifies who provided the authorization response.'),
        Field('Purchase Identifier Format', 44, 1, 'AN', 'Indicates the format of additional identifying information for purchases.'),
        Field('Purchase Identifier', 45, 25, 'AN', 'Identifies the purchase to the issuer and cardholder.'),
        Field('Card ID', 70, 2, 'AN', 'Code used to identify the card brand used for payment (VI, MC, JC, DC, AX, DI).'), # Positions 70-71
        Field('Point-of-Service Condition Code', 72, 2, 'AN', 'Code identifying transaction conditions at the point of sale or point of service.'),
        Field('Processing Code', 74, 6, 'AN', 'Code used to identify the type of transaction.'),
        Field('Network ID', 80, 4, 'AN', 'Contains a code that specifies the network used for transmission of the transaction.'),
        Field('Authorization Response Code', 84, 2, 'AN', 'The authorization code provided by the issuer when a transaction is approved.'),
        Field('Validation Code', 86, 4, 'AN', 'A unique value that Visa includes as part of authorization response.'),
        Field('Market-Specific Authorization Data Indicator', 90, 1, 'AN', 'Code indicating the industry for which market-specific authorization data was included.'),
        Field('Product ID', 91, 2, 'AN', 'This field will contain Product ID.'),
        Field('Program ID', 93, 6, 'AN', 'Program identifier. Available for US domestic transactions when provided by issuer.'),
        Field('CVV2 Result Code', 99, 1, 'AN', 'Card Verification Value 2 (CVV2) is the verification result for card-not-present transactions.'),
        Field('Authorization Characteristics Indicator', 100, 1, 'AN', 'Code used by the acquirer to request CPS qualification as returned in the original authorization response.'),
        Field('POS Terminal Capability', 101, 1, 'AN', 'Indicates the capability of the point-of-sale (POS) terminal to obtain an authorization and process transaction data.'),
        Field('Cardholder ID Method', 102, 1, 'AN', 'Indicates method used to identify cardholder (e.g., signature or Personal Identification Number [PIN]).'),
        Field('Request ID', 103, 26, 'AN', 'Unique Request Record ID assigned by Visa for each transaction.'),
        Field('Electronic Commerce Goods Indicator', 129, 2, 'AN', 'This field indicates the type of goods that were purchased on the Internet.'),
        Field('Fee Program Indicator', 131, 3, 'AN', 'This field contains an interchange reimbursement fee program indicator (FPI).'),
        Field('Service Development Field', 134, 1, 'AN', 'Indicates type of commerce.'),
        Field('Account Selection', 135, 1, 'AN', 'Indicates type of account (savings, checking, etc.).'),
        Field('POS Environment', 136, 1, 'AN', 'A recurring transaction indicator.'),
        Field('Time of Purchase', 137, 4, 'UN', 'Indicates time the purchase was made. Format is HHMM.'),
        Field('Batch Request ID', 141, 26, 'AN', 'This field contains batch request ID.'),
        Field('Spend Qualified Indicator', 167, 1, 'AN', 'This field indicates whether the account is Spend Qualified.'),
        Field('CAVV Results Code', 168, 1, 'AN', 'This field will contain the CAVV results code from the response message.'), # Position 168
    ]
)

# TC 33.A - CP 01 TCR 2 Billing and Shipping
CP01_TCR2 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='2',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 2.'),
        Field('Bill to Last Name', 5, 60, 'ANS', 'This field contains billing last name.'),
        Field('Bill to First Name', 65, 60, 'ANS', 'This field contains billing first name.'),
        Field('Bill to Postal Code', 125, 11, 'ANS', 'This field contains billing postal code.'),
        Field('Ship to Postal Code', 136, 20, 'ANS', 'This field contains postal code of the location the item is being shipped to.'),
        Field('Ship to State/Province Code', 156, 3, 'ANS', 'This field contains shipping state/province code of the location being shipped to.'),
        Field('Ship from Postal Code', 159, 10, 'ANS', 'This field contains shipping from postal code of the location being shipped from.'), # Positions 159-168
    ]
)

# TC 33.A - CP 01 TCR 3 Billing and Shipping (Cont'd)
CP01_TCR3 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='3',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 3.'),
        Field('Ship to Country Code', 5, 3, 'AN', 'This field contains the shipping country code.'), # Positions 5-7, important for TCR9 logic
        Field('Address Line 1', 8, 40, 'ANS', 'This field contains billing address line 1.'),
        Field('Address Line 2', 48, 40, 'ANS', 'This field contains billing address line 2.'),
        Field('City', 88, 50, 'ANS', 'This field contains billing city.'),
        Field('State', 138, 20, 'ANS', 'This field contains billing state.'),
        Field('Billing Country Code', 158, 3, 'AN', 'This field will contain the billing country code.'),
        Field('Reserved', 161, 8, 'AN', 'This field is reserved; space-filled.'), # Positions 161-168
    ]
)

# TC 33.A - CP 01 TCR 4 Merchant Data
CP01_TCR4 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='4',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 4.'),
        Field('Merchant Name', 5, 25, 'ANS', 'This field contains the Merchant Name.'),
        Field('Merchant Street Address', 30, 60, 'ANS', 'This field contains Merchant Street Address.'),
        Field('Merchant City', 90, 13, 'ANS', 'This field contains Merchant City.'),
        Field('Merchant State/Province', 103, 3, 'ANS', 'This field contains Merchant State/Province Code.'),
        Field('Merchant Country', 106, 3, 'AN', 'This field contains Merchant Country Code.'),
        Field('Merchant Postal Code', 109, 9, 'ANS', 'This field contains Merchant Postal Code.'),
        Field('Merchant Phone Number', 118, 15, 'ANS', 'This field contains Merchant Phone Number.'),
        Field('Merchant URL', 133, 30, 'ANS', 'This field contains Merchant URL.'),
        Field('Merchant Category Code', 163, 4, 'AN', 'This field contains the Merchant Category Code (MCC).'),
        Field('Reserved', 167, 2, 'AN', 'This field is reserved; space-filled.'), # Positions 167-168
    ]
)

# TC 33.A - CP 01 TCR 5 Installment Payment (Added based on Chapter 11.txt details)
CP01_TCR5 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='5',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 5.'),
        Field('Installment Payment Count', 5, 3, 'UN', 'Number of payments in an installment plan.'),
        Field('Installment Payment Frequency', 8, 1, 'AN', 'Frequency of installment payments (D=Daily, W=Weekly, M=Monthly).'),
        Field('Installment Payment Amount', 9, 12, 'UN', 'Amount of each installment payment.'),
        Field('Installment First Payment Date', 21, 6, 'UN', 'Date of the first installment payment (YYMMDD).'),
        Field('Installment Grace Period Duration', 27, 3, 'UN', 'Duration of the grace period before the first payment.'),
        Field('Installment Grace Period Duration Type', 30, 1, 'AN', 'Unit of grace period (D=Days, W=Weeks, M=Months).'),
        Field('Installment Transaction ID', 31, 15, 'AN', 'Unique ID for the installment transaction.'),
        Field('Reserved', 46, 123, 'AN', 'This field is reserved; space-filled.'), # Positions 46-168
    ]
)


# TC 33.A - CP 01 TCR 6 Gateway Data
CP01_TCR6 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='6',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 6.'),
        Field('Cardholder Authentication Verification Value', 5, 20, 'ANS', 'This field contains the Cardholder Authentication Verification Value (CAVV).'),
        Field('Network Transaction Identifier', 25, 15, 'AN', 'This field contains the Network Transaction Identifier.'),
        Field('Message Integrity Check Value', 40, 20, 'DX', 'This field contains the Message Integrity Check Value (MICV).'),
        Field('Transaction Security Level', 60, 2, 'AN', 'This field contains the transaction security level.'),
        Field('Transaction ID for 3D Secure', 62, 28, 'ANS', 'This field contains the transaction ID for 3D Secure.'),
        Field('Program Protocol', 90, 2, 'AN', 'This field contains the Program Protocol.'),
        Field('Directory Server Transaction ID', 92, 28, 'ANS', 'This field contains the Directory Server Transaction ID.'),
        Field('Reserved', 120, 49, 'AN', 'This field is reserved; space-filled.'), # Positions 120-168
    ]
)

# TC 33.A - CP 01 TCR 7 Gateway Data (Cont'd)
CP01_TCR7 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='7',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 7.'),
        Field('Processor Supplied Data', 5, 164, 'ANS', 'This field contains data supplied by the processor.'), # Positions 5-168
    ]
)

# TC 33.A - CP 01 TCR 8 Supplemental Data (Added based on Chapter 11.txt details)
CP01_TCR8 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='8',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 8.'),
        Field('Transaction Type Indicator', 5, 1, 'AN', 'Indicates specific transaction type (e.g., Recurring, Installment).'),
        Field('Recurring Transaction Indicator', 6, 1, 'AN', 'Indicates if transaction is part of a recurring series.'),
        Field('Payment Facilitator ID', 7, 11, 'AN', 'Identifier for the payment facilitator.'),
        Field('Sub-Merchant ID', 18, 15, 'AN', 'Identifier for the sub-merchant.'),
        Field('Reserved', 33, 136, 'AN', 'This field is reserved; space-filled.'), # Positions 33-168
    ]
)

# TC 33.A - CP 01 TCR 9 Intra-Country Data - (Generic/Placeholder for various countries)
# The actual country-specific TCR9s will be used based on context
CP01_TCR9_GENERIC = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='9',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 9.'),
        Field('Intra-Country Data', 5, 164, 'ANS', 'Generic field for country-specific data.'), # Positions 5-168
    ]
)

# CP01 TCR9 (Country-specific variants - defined for specific field layouts if known)
# Note: These are example structures, actual fields based on full Chapter 11.txt pages for each country
CP01_TCR9_COL = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='9',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 9.'),
        Field('National Data Country Code', 5, 3, 'AN', 'Colombia Country Code (170).'), # Positions 5-7
        Field('Payment Method', 8, 2, 'AN', 'Payment Method (e.g., "01" for Cash, "02" for Cheque).'),
        Field('Taxable Amount', 10, 12, 'UN', 'Taxable Amount.'),
        Field('Tax Amount', 22, 12, 'UN', 'Tax Amount.'),
        Field('Non-Taxable Amount', 34, 12, 'UN', 'Non-Taxable Amount.'),
        Field('Installment Count', 46, 3, 'N', 'Number of installments.'),
        Field('Merchant Industry', 49, 4, 'AN', 'Merchant Industry.'),
        Field('Discount Amount', 53, 12, 'UN', 'Discount Amount.'),
        Field('Invoice Number', 65, 20, 'AN', 'Invoice Number.'),
        Field('POS System Trace Audit Number', 85, 6, 'AN', 'POS System Trace Audit Number.'),
        Field('Cashback Amount', 91, 12, 'UN', 'Cashback Amount.'),
        Field('Reserved', 103, 66, 'AN', 'Reserved; space-filled.'), # Positions 103-168
    ]
)

CP01_TCR9_JPN = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='9',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 9.'),
        Field('JCN Purchase Plan Code', 5, 2, 'AN', 'Japan Card Network Purchase Plan Code.'),
        Field('JCN Purchase Plan Amount', 7, 12, 'UN', 'Japan Card Network Purchase Plan Amount.'),
        Field('JCN Purchase Plan Tax Amount', 19, 12, 'UN', 'Japan Card Network Purchase Plan Tax Amount.'),
        Field('Reserved', 31, 138, 'AN', 'Reserved; space-filled.'), # Positions 31-168
    ]
)

CP01_TCR9_MEX = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='9',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 9.'),
        Field('Mexico Installment Indicator', 5, 1, 'AN', 'Indicator for installment payments (M = Monthly, etc.).'),
        Field('Mexico Installment Number', 6, 2, 'N', 'Number of installments.'),
        Field('Mexico Coupon Code', 8, 4, 'AN', 'Coupon Code used in Mexico.'),
        Field('Mexico Cashback Amount', 12, 12, 'UN', 'Cashback Amount in Mexico.'),
        Field('Reserved', 24, 145, 'AN', 'Reserved; space-filled.'), # Positions 24-168
    ]
)

# TC 33.A - CP 01 TCR A Currency Conversion (Added)
CP01_TCRA = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='A',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value A.'),
        Field('Currency Conversion Rate', 5, 12, 'UN', 'Rate used for currency conversion.'),
        Field('Original Currency Amount', 17, 12, 'UN', 'Amount in original currency.'),
        Field('Original Currency Code', 29, 3, 'AN', 'Original ISO numeric currency code.'),
        Field('Converted Amount', 32, 12, 'UN', 'Amount after conversion.'),
        Field('Converted Currency Code', 44, 3, 'AN', 'Converted ISO numeric currency code.'),
        Field('Reserved', 47, 122, 'AN', 'This field is reserved; space-filled.'), # Positions 47-168
    ]
)

# TC 33.A - CP 01 TCR B Additional Gateway Data (Added)
CP01_TCRB = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='B',
    application_code='CP01',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value B.'),
        Field('Gateway Reference ID', 5, 20, 'AN', 'Reference ID assigned by the gateway.'),
        Field('Gateway Transaction Time', 25, 6, 'UN', 'Time of transaction at gateway (HHMMSS).'),
        Field('Gateway Transaction Date', 31, 8, 'UN', 'Date of transaction at gateway (YYYYMMDD).'),
        Field('Reserved', 39, 130, 'AN', 'This field is reserved; space-filled.'), # Positions 39-168
    ]
)


# --- CP02 TCRs (EMV Data) ---
# TC 33.A - CP 02 TCR 0 EMV Data
CP02_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP02',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP02.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links EMV data to transaction).'),
        Field('Application Interchange Profile', 36, 4, 'DX', 'Application Interchange Profile (AIP).'),
        Field('Dedicated File Name', 40, 32, 'DX', 'Dedicated File Name (DF name).'),
        Field('Terminal Capabilities', 72, 6, 'DX', 'Terminal Capabilities.'),
        Field('Terminal Country Code', 78, 4, 'DX', 'Terminal Country Code (ISO 3166-1 numeric).'),
        Field('Transaction Currency Code', 82, 4, 'DX', 'Transaction Currency Code (ISO 4217 numeric).'),
        Field('Transaction Date', 86, 6, 'DX', 'Transaction Date (YYMMDD).'),
        Field('Transaction Type', 92, 2, 'DX', 'Transaction Type.'),
        Field('Unpredictable Number', 94, 8, 'DX', 'Unpredictable Number.'),
        Field('Amount Authorized (Binary)', 102, 12, 'DX', 'Amount Authorized, Binary (8 bytes).'),
        Field('Amount Other (Binary)', 114, 12, 'DX', 'Amount Other, Binary (8 bytes).'),
        Field('Application Transaction Counter', 126, 4, 'DX', 'Application Transaction Counter (ATC).'),
        Field('Cryptogram', 130, 16, 'DX', 'Cryptogram (Application Cryptogram - AC).'),
        Field('Cryptogram Information Data', 146, 2, 'DX', 'Cryptogram Information Data (CID).'),
        Field('Issuer Application Data', 148, 32, 'DX', 'Issuer Application Data (IAD).'), # Positions 148-179 -> Corrected to fit 168:
        # Assuming IAD is shorter or split if it actually runs past 168
        Field('Issuer Application Data (part 1)', 148, 21, 'DX', 'Issuer Application Data (IAD) part 1.'), # Positions 148-168
    ]
)

CP02_TCR1 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='1',
    application_code='CP02',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 1.'),
        Field('Terminal Verification Results', 5, 10, 'DX', 'Terminal Verification Results (TVR).'),
        Field('Transaction Status Information', 15, 4, 'DX', 'Transaction Status Information (TSI).'),
        Field('Cardholder Verification Method Results', 19, 6, 'DX', 'Cardholder Verification Method (CVM) Results.'),
        Field('Issuer Authentication Data', 25, 32, 'DX', 'Issuer Authentication Data (ARPC).'),
        Field('Cryptogram Version Number', 57, 2, 'DX', 'Cryptogram Version Number.'),
        Field('Terminal Type', 59, 2, 'DX', 'Terminal Type.'),
        Field('Terminal Capabilities (part 2)', 61, 2, 'DX', 'Terminal Capabilities, continuation.'),
        Field('Dedicated File Name (part 2)', 63, 10, 'DX', 'Dedicated File Name, continuation.'),
        Field('Filler', 73, 96, 'AN', 'Reserved; space-filled.'), # Positions 73-168
    ]
)

# CP02_TCR2 to CP02_TCRB would follow a similar pattern if defined in Chapter 11.txt
# For brevity and assuming primary focus on core details, not all sub-TCRs for CP02 are exhaustively listed.
# If required, these can be added by precise extraction from Chapter 11.txt

# --- CP03 TCRs (Lodging Summary & Additional Amounts) ---
# TC 33.A - CP 03 TCR 0 Default Data (Common fields for CP03 group)
CP03_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP03',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP03.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links lodging data to transaction).'),
        Field('Lodging Property Type', 36, 2, 'AN', 'Type of lodging property (e.g., Hotel, Motel).'),
        Field('Lodging Chain Code', 38, 3, 'AN', 'Chain code for the lodging property.'),
        Field('Lodging Property ID', 41, 11, 'AN', 'Property identifier for the lodging establishment.'),
        Field('Check-in Date', 52, 8, 'UN', 'Check-in date (YYYYMMDD).'),
        Field('Check-out Date', 60, 8, 'UN', 'Check-out date (YYYYMMDD).'),
        Field('Total Room Nights', 68, 3, 'UN', 'Total number of room nights.'),
        Field('Room Rate', 71, 12, 'UN', 'Daily room rate.'),
        Field('Reserved', 83, 86, 'AN', 'Reserved; space-filled.'), # Positions 83-168
    ]
)

# TC 33.A - CP 03 TCR 1 Lodging Summary
CP03_TCR1 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='1',
    application_code='CP03',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 1.'),
        Field('Lodging Folio Number', 5, 20, 'AN', 'Lodging Folio Number.'),
        Field('Lodging Check-in Date', 25, 6, 'UN', 'Lodging Check-in Date (YYMMDD).'),
        Field('Lodging Check-out Date', 31, 6, 'UN', 'Lodging Check-out Date (YYMMDD).'),
        Field('Lodging Duration', 37, 3, 'UN', 'Lodging Duration (Number of nights).'),
        Field('Lodging Rate', 40, 12, 'UN', 'Lodging Rate per night.'),
        Field('Lodging Guest Name', 52, 60, 'ANS', 'Lodging Guest Name.'),
        Field('Reserved', 112, 57, 'AN', 'Reserved; space-filled.'), # Positions 112-168
    ]
)

# TC 33.A - CP 03 TCR 4 Lodging Additional Amounts
CP03_TCR4 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='4',
    application_code='CP03',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 4.'),
        Field('Room Tax', 5, 12, 'UN', 'Room Tax Amount.'),
        Field('Misc Expenses', 17, 12, 'UN', 'Miscellaneous Expenses Amount.'),
        Field('Food & Beverage', 29, 12, 'UN', 'Food and Beverage Amount.'),
        Field('Phone Charges', 41, 12, 'UN', 'Phone Charges Amount.'),
        Field('Incidental Charges', 53, 12, 'UN', 'Incidental Charges Amount.'),
        Field('Total Additional Amounts', 65, 12, 'UN', 'Total of all additional lodging amounts.'),
        Field('Reserved', 77, 92, 'AN', 'Reserved; space-filled.'), # Positions 77-168
    ]
)

# --- CP04 TCRs (Industry-Specific Data - Passenger Transport) ---
# TC 33.A - CP 04 TCR 0 Default Data (Common fields for CP04 group)
CP04_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP04',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP04.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links transport data to transaction).'),
        Field('Airline Code', 36, 3, 'AN', 'Airline Designator Code.'),
        Field('Ticket Number', 39, 15, 'AN', 'Ticket/Document Number.'),
        Field('Travel Agency Code', 54, 8, 'AN', 'Travel Agency Code.'),
        Field('Departure Date', 62, 8, 'UN', 'Departure Date (YYYYMMDD).'),
        Field('Reserved', 70, 99, 'AN', 'Reserved; space-filled.'), # Positions 70-168
    ]
)

# TC 33.A - CP 04 TCR 1 Industry-Specific Data - Passenger Transport (Cont'd)
CP04_TCR1 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='1',
    application_code='CP04',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 1.'),
        Field('Passenger Name', 5, 30, 'ANS', 'Name of the passenger.'),
        Field('Ticket Issue Date', 35, 8, 'UN', 'Date ticket was issued (YYYYMMDD).'),
        Field('Fare Basis Code', 43, 8, 'AN', 'Fare Basis Code.'),
        Field('Origin Airport Code', 51, 3, 'AN', 'Origin Airport Code (IATA).'),
        Field('Destination Airport Code', 54, 3, 'AN', 'Destination Airport Code (IATA).'),
        Field('Flight Number', 57, 5, 'UN', 'Flight Number.'),
        Field('Class of Service', 62, 1, 'AN', 'Class of Service (e.g., F, J, Y).'),
        Field('Travel Agency Name', 63, 25, 'ANS', 'Name of the travel agency.'),
        Field('Reserved', 88, 81, 'AN', 'Reserved; space-filled.'), # Positions 88-168
    ]
)

# --- CP05 TCRs (Industry-Specific Data - Car Rental) ---
# TC 33.A - CP 05 TCR 0 Default Data (Common fields for CP05 group)
CP05_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP05',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP05.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links car rental data to transaction).'),
        Field('Rental Agreement Number', 36, 20, 'AN', 'Car Rental Agreement Number.'),
        Field('Rental Pick-up Date', 56, 8, 'UN', 'Rental Pick-up Date (YYYYMMDD).'),
        Field('Rental Return Date', 64, 8, 'UN', 'Rental Return Date (YYYYMMDD).'),
        Field('Rental Duration', 72, 3, 'UN', 'Rental Duration (Number of days).'),
        Field('Reserved', 75, 94, 'AN', 'Reserved; space-filled.'), # Positions 75-168
    ]
)

# --- CP06 TCRs (Enhanced Data - Purchasing Transaction Line Item Detail) ---
# TC 33.A - CP 06 TCR 0 Default Data (Common fields for CP06 group)
CP06_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP06',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP06.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links line item data to transaction).'),
        Field('Invoice Date', 36, 8, 'UN', 'Invoice Date (YYYYMMDD).'),
        Field('Invoice Number', 44, 20, 'AN', 'Invoice Number.'),
        Field('Purchase Order Number', 64, 20, 'AN', 'Purchase Order Number.'),
        Field('Total Discount Amount', 84, 12, 'UN', 'Total Discount Amount for the transaction.'),
        Field('Total Tax Amount', 96, 12, 'UN', 'Total Tax Amount for the transaction.'),
        Field('Shipping Cost', 108, 12, 'UN', 'Shipping Cost.'),
        Field('Duty Amount', 120, 12, 'UN', 'Duty Amount.'),
        Field('Reserved', 132, 37, 'AN', 'Reserved; space-filled.'), # Positions 132-168
    ]
)

# TC 33.A - CP 06 TCR 1 Enhanced Data - Purchasing Transaction Line Item Detail
CP06_TCR1 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='1',
    application_code='CP06',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 1.'),
        Field('Line Item Sequence Number', 5, 3, 'UN', 'Line Item Sequence Number.'),
        Field('Item Description', 8, 26, 'ANS', 'Description of the item.'),
        Field('Quantity', 34, 12, 'UN', 'Quantity of the item.'),
        Field('Unit Cost', 46, 12, 'UN', 'Unit Cost of the item.'),
        Field('Item Amount', 58, 12, 'UN', 'Total Amount for the line item.'),
        Field('Discount Amount Line Item', 70, 12, 'UN', 'Discount Amount for this line item.'),
        Field('Tax Amount Line Item', 82, 12, 'UN', 'Tax Amount for this line item.'),
        Field('Product Code', 94, 12, 'AN', 'Product Code.'),
        Field('Unit of Measure', 106, 3, 'AN', 'Unit of Measure (e.g., EA for Each).'),
        Field('Tax Rate', 109, 6, 'UN', 'Tax Rate applied.'),
        Field('Debit/Credit Indicator Line Item', 115, 1, 'AN', 'Debit/Credit Indicator for Line Item (C/D).'),
        Field('Reserved', 116, 53, 'AN', 'Reserved; space-filled.'), # Positions 116-168
    ]
)


# --- CP07 TCRs (Japan's MC Additional Data / Common Payment Transaction) ---
# TC 33.A - CP 07 TCR 0 Default Data (Common fields for CP07 group)
CP07_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP07',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP07.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links CP07 data to transaction).'),
        Field('Installment Plan ID', 36, 2, 'AN', 'Installment Plan ID (e.g., for Japan specific).'),
        Field('Number of Installments', 38, 3, 'UN', 'Number of Installment Payments.'),
        Field('Reserved', 41, 128, 'AN', 'Reserved; space-filled.'), # Positions 41-168
    ]
)

# TC 33.A - CP07 TCR 8 Japan's MC Additional Data
CP07_TCR8 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='8',
    application_code='CP07',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 8.'),
        Field('Original Authorization Amount', 5, 12, 'UN', 'Original Authorization Amount.'),
        Field('Original Authorization Currency Code', 17, 3, 'AN', 'Original Authorization Currency Code.'),
        Field('Original Approval Code', 20, 6, 'AN', 'Original Approval Code.'),
        Field('Original Transaction Date', 26, 4, 'UN', 'Original Transaction Date (MMDD).'),
        Field('Original Transaction Time', 30, 6, 'UN', 'Original Transaction Time (HHMMSS).'),
        Field('Original Message Identifier', 36, 15, 'AN', 'Original Message Identifier.'),
        Field('Reserved', 51, 118, 'AN', 'Reserved; space-filled.'), # Positions 51-168
    ]
)


# --- CP08 TCRs (Discretionary Data) ---
# TC 33.A - CP 08 TCR 0 Discretionary Data - Default TCR
CP08_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP08',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP08.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links discretionary data to transaction).'),
        Field('Discretionary Data', 36, 133, 'ANS', 'Generic discretionary data field.'), # Positions 36-168
    ]
)

# --- CP09 TCRs (Cardholder Verification) ---
# TC 33.A - CP 09 TCR 0 Default Data (Common fields for CP09 group)
CP09_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP09',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP09.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links CVM data to transaction).'),
        Field('Reserved', 36, 133, 'AN', 'Reserved; space-filled.'), # Positions 36-168
    ]
)

# TC 33.A - CP 09 TCR 4 Recipient Name (Split)
CP09_TCR4 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='4',
    application_code='CP09',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 4.'),
        Field('Recipient First Name', 5, 40, 'ANS', 'Recipient First Name.'),
        Field('Recipient Last Name', 45, 40, 'ANS', 'Recipient Last Name.'),
        Field('Reserved', 85, 84, 'AN', 'Reserved; space-filled.'), # Positions 85-168
    ]
)

# --- CP10 TCRs (POS Device Information) ---
# TC 33.A - CP 10 TCR 0 Default Data (Common fields for CP10 group)
CP10_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP10',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP10.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links POS data to transaction).'),
        Field('POS Device Type', 36, 2, 'AN', 'Type of POS device (e.g., Terminal, ATM).'),
        Field('POS Device Capabilities', 38, 3, 'AN', 'Capabilities of the POS device.'),
        Field('Reserved', 41, 128, 'AN', 'Reserved; space-filled.'), # Positions 41-168
    ]
)

# --- CP12 TCRs (MCC Data - Visa Specific) ---
# TC 33.A - CP 12 TCR 0 Default Data (Common fields for CP12 group)
CP12_TCR0 = TCRDefinition(
    tcr_type='33',
    tcr_qualifier='0',
    tcr_sequence='0',
    application_code='CP12',
    fields=[
        Field('Transaction Code', 1, 2, 'UN', 'This field contains the value 33.'),
        Field('Transaction Code Qualifier', 3, 1, 'UN', 'This field contains the value 0.'),
        Field('Transaction Component Sequence Number', 4, 1, 'AN', 'This field contains the value 0.'),
        Field('Destination Identifier', 5, 6, 'UN', 'The entity to which the BASE II transaction message is sent.'),
        Field('Source Identifier', 11, 6, 'UN', 'This field contains the Visa internal identifier of the VIC.'),
        Field('TC 33 Application Code', 17, 4, 'AN', 'Static value set to CP12.'),
        Field('Message Identifier', 21, 15, 'AN', 'Message Identifier (links CP12 data to transaction).'),
        Field('Merchant Category Code (MCC)', 36, 4, 'AN', 'Merchant Category Code.'),
        Field('Merchant SIC Code', 40, 4, 'AN', 'Standard Industrial Classification Code.'),
        Field('Reserved', 44, 125, 'AN', 'Reserved; space-filled.'), # Positions 44-168
    ]
)


# Dictionary mapping (Application Code, Sequence Number) to TCRDefinition objects
# This will be used in services.py for lookups.
TCR_DEFINITIONS = {
    # Header and Trailer
    ('HEDR', '0'): TCR_HEADER,
    ('TRLR', '0'): TCR_TRAILER,

    # CP01 TCRs
    ('CP01', '0'): CP01_TCR0,
    ('CP01', '1'): CP01_TCR1,
    ('CP01', '2'): CP01_TCR2,
    ('CP01', '3'): CP01_TCR3,
    ('CP01', '4'): CP01_TCR4,
    ('CP01', '5'): CP01_TCR5,
    ('CP01', '6'): CP01_TCR6,
    ('CP01', '7'): CP01_TCR7,
    ('CP01', '8'): CP01_TCR8,
    ('CP01', '9'): CP01_TCR9_GENERIC, # Generic TCR9, will be overridden by specific country logic
    ('CP01', 'A'): CP01_TCRA,
    ('CP01', 'B'): CP01_TCRB,
    # Specific TCR9s for contextual lookup (handled in services.py directly)
    'CP01_TCR9_COL': CP01_TCR9_COL,
    'CP01_TCR9_JPN': CP01_TCR9_JPN,
    'CP01_TCR9_MEX': CP01_TCR9_MEX,

    # CP02 TCRs
    ('CP02', '0'): CP02_TCR0,
    ('CP02', '1'): CP02_TCR1,
    # Add other CP02 TCRs (2-B) if present in Chapter 11.txt with distinct fields

    # CP03 TCRs
    ('CP03', '0'): CP03_TCR0,
    ('CP03', '1'): CP03_TCR1,
    ('CP03', '4'): CP03_TCR4,

    # CP04 TCRs
    ('CP04', '0'): CP04_TCR0,
    ('CP04', '1'): CP04_TCR1,

    # CP05 TCRs
    ('CP05', '0'): CP05_TCR0,

    # CP06 TCRs
    ('CP06', '0'): CP06_TCR0,
    ('CP06', '1'): CP06_TCR1,

    # CP07 TCRs
    ('CP07', '0'): CP07_TCR0,
    ('CP07', '8'): CP07_TCR8,

    # CP08 TCRs
    ('CP08', '0'): CP08_TCR0,

    # CP09 TCRs
    ('CP09', '0'): CP09_TCR0,
    ('CP09', '4'): CP09_TCR4,

    # CP10 TCRs
    ('CP10', '0'): CP10_TCR0,

    # CP12 TCRs
    ('CP12', '0'): CP12_TCR0,
}

# This function is primarily for single-line debugging; full file parsing logic in services.py is preferred.
def parse_tc33_line(line: str):
    """
    Parses a single TC33 line and returns a dictionary of its fields.
    This function is primarily for debugging or if you need to process lines individually.
    For full file processing, use parse_tc33_file from services.py.
    """
    raw_line = line.strip()
    if not raw_line:
        return None

    # Extract common fields for initial identification
    tx_code = raw_line[0:2].strip()
    tx_qualifier = raw_line[2:3].strip()
    seq_num = raw_line[3:4].strip()
    application_code = raw_line[16:20].strip() # Relevant for TCR0s, HEDR, TRLR

    tcr_def = None

    # First, try to match using the common (application_code, sequence_number) for TCR0s
    if seq_num == '0' or application_code in ('HEDR', 'TRLR'):
        key = (application_code, seq_num)
        tcr_def = TCR_DEFINITIONS.get(key)
    else:
        # For non-TCR0s, this helper can't reliably determine the CPxx context
        # from a single line. A more advanced standalone line parser would
        # need to maintain state about the previous TCR0's application code.
        # We try a direct lookup, but it might not be accurate without context.
        # For CP01 TCR9, it's particularly complex without TCR3 context.
        key = (application_code, seq_num) # e.g., ('CP01', '1')
        tcr_def = TCR_DEFINITIONS.get(key)
        
        # Basic attempt for CP01 TCR9 based on common application code and seq_num '9'
        if not tcr_def and seq_num == '9' and application_code == 'CP01':
            # This logic for country-specific TCR9s cannot be done accurately
            # in a single-line parser without prior context (e.g., TCR3's country code).
            # Fallback to generic TCR9 or return None.
            tcr_def = CP01_TCR9_GENERIC # Default to generic if no specific lookup is possible
            

    if not tcr_def:
        # print(f"Warning: No TCR definition found for line: {raw_line[:20]}...")
        return None

    parsed_data = {
        'TCR_Type': tx_code,
        'TCR_Qualifier': tx_qualifier,
        'TCR_Sequence': seq_num,
        'Application_Code': application_code,
        'TCR_Definition_Name': tcr_def.__class__.__name__,
        'Raw_Line': raw_line
    }

    for field_name, field_def in tcr_def.fields.items():
        try:
            parsed_data[field_name] = tcr_def.get_field_value(raw_line, field_name)
        except Exception as e:
            # print(f"Error parsing field '{field_name}' in {tcr_def.__class__.__name__}: {e}")
            parsed_data[field_name] = None

    return parsed_data
