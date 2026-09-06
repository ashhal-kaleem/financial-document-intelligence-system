import pymupdf

def generate_pdf():
    doc = pymupdf.open()
    
    # Page 1: Consolidated Statements of Operations
    page1 = doc.new_page()
    page1.insert_text((50, 40), "CONSOLIDATED STATEMENTS OF OPERATIONS - APPLE INC.", fontsize=14)
    page1.insert_text((50, 60), "Fiscal Year Ended September 28, 2024 and September 30, 2023 (in millions)", fontsize=10)
    
    table1 = (
        "Table 1 - Consolidated Operations:\n"
        "Total net sales: 2024 = $391,035 million | 2023 = $383,285 million\n"
        "Products net sales: 2024 = $294,866 million | 2023 = $298,085 million\n"
        "Services net sales: 2024 = $96,169 million | 2023 = $85,200 million\n"
        "Total cost of sales: 2024 = $210,352 million | 2023 = $214,137 million\n"
        "Gross margin: 2024 = $180,683 million | 2023 = $169,148 million\n"
        "Research and development: 2024 = $31,370 million | 2023 = $29,915 million\n"
        "Selling, general and administrative: 2024 = $26,097 million | 2023 = $24,932 million\n"
        "Total operating expenses: 2024 = $57,467 million | 2023 = $54,847 million\n"
        "Operating income: 2024 = $123,216 million | 2023 = $114,301 million\n"
        "Net income: 2024 = $93,736 million | 2023 = $96,995 million\n"
        "Diluted earnings per share (GAAP): 2024 = $6.08 | 2023 = $6.13"
    )
    page1.insert_text((50, 85), table1, fontsize=9)
    page1.insert_text(
        (50, 260),
        "Note 1 - Segment Performance:\n"
        "Services revenue reached an all-time record of $96,169 million, driven by growth in advertising, cloud services, and payment services.\n"
        "Americas segment revenue was $163,553 million, Europe was $99,576 million, and Greater China was $66,952 million.",
        fontsize=9
    )

    # Page 2: Consolidated Balance Sheets & Debt Footnotes
    page2 = doc.new_page()
    page2.insert_text((50, 40), "CONSOLIDATED BALANCE SHEETS - APPLE INC.", fontsize=14)
    page2.insert_text((50, 60), "As of September 28, 2024 (in millions, except number of shares)", fontsize=10)

    table2 = (
        "Table 2 - Consolidated Balance Sheet:\n"
        "Cash and cash equivalents: 2024 = $29,942 million | 2023 = $29,965 million\n"
        "Marketable securities: 2024 = $35,227 million | 2023 = $31,590 million\n"
        "Accounts receivable, net: 2024 = $33,410 million | 2023 = $29,508 million\n"
        "Total current assets: 2024 = $153,086 million | 2023 = $143,566 million\n"
        "Property, plant and equipment, net: 2024 = $45,246 million | 2023 = $43,715 million\n"
        "Total assets: 2024 = $364,980 million | 2023 = $352,583 million\n"
        "Current Liabilities - Term debt: 2024 = $10,912 million | 2023 = $9,822 million\n"
        "Non-current Liabilities - Term debt: 2024 = $95,786 million | 2023 = $95,281 million\n"
        "Total liabilities: 2024 = $308,030 million | 2023 = $290,437 million\n"
        "Total shareholders equity: 2024 = $56,950 million | 2023 = $62,146 million"
    )
    page2.insert_text((50, 85), table2, fontsize=9)
    page2.insert_text(
        (50, 260),
        "Note 6 - Commercial Paper & Financing Activities:\n"
        "During fiscal 2024, the Company repurchased $94.6 billion of common stock and paid cash dividends of $15.2 billion.\n"
        "The Company's effective tax rate for fiscal 2024 was 15.4% compared to 14.7% in fiscal 2023.",
        fontsize=9
    )

    doc.save("tests/sample_apple_10k.pdf")
    doc.close()
    print("Successfully generated tests/sample_apple_10k.pdf")

if __name__ == "__main__":
    generate_pdf()
