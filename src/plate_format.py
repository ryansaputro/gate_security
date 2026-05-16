"""
Indonesian Plate Format Corrector
Format: [A-Z]{1,2} [0-9]{1,4} [A-Z]{1,3}
Example: B 1234 XYZ, AB 12 C, D 1 ABC

Handles OCR misreads by checking position context:
- Position 1 (prefix): MUST be letters -> fix digits that look like letters
- Position 2 (middle): MUST be digits -> fix letters that look like digits  
- Position 3 (suffix): MUST be letters -> fix digits that look like letters
"""

# Digit -> Letter (when position expects letter)
DIGIT_TO_LETTER = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '3': 'E',
    '4': 'A',
    '5': 'S',
    '6': 'G',
    '7': 'T',
    '8': 'B',
    '9': 'G',
}

# Letter -> Digit (when position expects digit)
LETTER_TO_DIGIT = {
    'O': '0',
    'Q': '0',
    'D': '0',
    'I': '1',
    'L': '1',
    'Z': '2',
    'E': '3',
    'A': '4',
    'S': '5',
    'G': '6',
    'T': '7',
    'B': '8',
    'g': '9',
}


def fix_to_letter(char):
    """Convert char to letter if it's a digit"""
    if char.isalpha():
        return char
    return DIGIT_TO_LETTER.get(char, char)


def fix_to_digit(char):
    """Convert char to digit if it's a letter"""
    if char.isdigit():
        return char
    return LETTER_TO_DIGIT.get(char, char)


def format_plate(raw_text):
    """
    Parse raw OCR text and apply Indonesian plate format correction.
    
    Format: PREFIX(1-2 letters) + NUMBER(1-4 digits) + SUFFIX(1-3 letters)
    
    Returns formatted plate string or None if can't parse.
    """
    # Remove all non-alphanumeric
    text = ''.join(c for c in raw_text.upper() if c.isalnum())
    
    if len(text) < 4:
        return None

    # Strategy: try to split into [letters][digits][letters]
    # Find where digits start and end
    
    # Method 1: Use regex to find pattern
    import re
    
    # Try strict match first: letters + digits + letters
    match = re.match(r'^([A-Z]{1,2})(\d{1,4})([A-Z]{1,3})$', text)
    if match:
        prefix, number, suffix = match.groups()
        return f"{prefix} {number} {suffix}"
    
    # Method 2: If no clean match, apply position-based correction
    # Assume: first 1-2 chars = prefix, last 1-3 chars = suffix, middle = number
    
    # Find first digit position (start of number section)
    first_digit = -1
    for i, c in enumerate(text):
        if c.isdigit() or c in LETTER_TO_DIGIT:
            first_digit = i
            break
    
    # Find last digit position (end of number section)  
    last_digit = -1
    for i in range(len(text) - 1, -1, -1):
        if text[i].isdigit() or (text[i].isalpha() and text[i] in LETTER_TO_DIGIT and i > first_digit):
            last_digit = i
            break

    # If we can't find digit section, try heuristic split
    if first_digit == -1:
        # All letters/ambiguous - assume first 1-2 are prefix, try to find numbers
        if len(text) >= 5:
            prefix_len = 1 if len(text) <= 6 else 2
            suffix_len = min(3, max(1, len(text) - prefix_len - 1))
            number_len = len(text) - prefix_len - suffix_len
            
            prefix = text[:prefix_len]
            middle = text[prefix_len:prefix_len + number_len]
            suffix = text[prefix_len + number_len:]
            
            prefix = ''.join(fix_to_letter(c) for c in prefix)
            middle = ''.join(fix_to_digit(c) for c in middle)
            suffix = ''.join(fix_to_letter(c) for c in suffix)
            
            # Validate middle is now all digits
            if middle and all(c.isdigit() for c in middle):
                return f"{prefix} {middle} {suffix}"
        return None

    # Split based on detected positions
    # Prefix: everything before first_digit
    prefix_raw = text[:first_digit] if first_digit > 0 else text[0:1]
    
    # Find where suffix starts (first letter after the digit section)
    suffix_start = len(text)
    for i in range(len(text) - 1, first_digit, -1):
        if text[i].isalpha() and not text[i] in ('O', 'I', 'L', 'Z', 'S', 'B', 'G'):
            suffix_start = i
        elif text[i].isalpha():
            # Ambiguous char - check if followed by more letters
            remaining = text[i:]
            if all(c.isalpha() for c in remaining):
                suffix_start = i
                break
    
    # Simple heuristic: last 1-3 chars are suffix (letters or digit-that-looks-like-letter)
    suffix_raw = ""
    number_end = len(text)
    for i in range(len(text) - 1, first_digit - 1, -1):
        c = text[i]
        if c.isalpha() or (c.isdigit() and c in DIGIT_TO_LETTER):
            suffix_raw = c + suffix_raw
            number_end = i
            if len(suffix_raw) >= 3:
                break
        else:
            break
    # But suffix must have at least one real letter or letter-like digit
    if suffix_raw and not any(c.isalpha() or c in DIGIT_TO_LETTER for c in suffix_raw):
        suffix_raw = ""
        number_end = len(text)
    
    if first_digit == 0:
        prefix_raw = text[0]
        first_digit = 1
    
    number_raw = text[first_digit:number_end]
    
    # Apply corrections
    prefix = ''.join(fix_to_letter(c) for c in prefix_raw)[:2]
    number = ''.join(fix_to_digit(c) for c in number_raw)[:4]
    suffix = ''.join(fix_to_letter(c) for c in suffix_raw)[:3]
    
    # Validate
    if not prefix or not number:
        return None
    if not all(c.isalpha() for c in prefix):
        return None
    if not all(c.isdigit() for c in number):
        return None
    if suffix and not all(c.isalpha() for c in suffix):
        suffix = ''.join(c for c in suffix if c.isalpha())
    
    result = f"{prefix} {number}"
    if suffix:
        result += f" {suffix}"
    
    return result


# Test
if __name__ == "__main__":
    tests = [
        "B1234XYZ",    # clean
        "8l234XY2",    # 8->B, l->1, 2->Z (suffix)
        "D1O3ABC",     # O->0 in number
        "AB12C",       # short
        "B1234",       # no suffix
        "81234XY",     # 8->B prefix
        "D1234A8C",    # 8->B in suffix
        "01234ABC",    # 0->O prefix
        "BK1Z89AG",   # Z->2 in number
    ]
    for t in tests:
        result = format_plate(t)
        print(f"  {t:12s} -> {result}")
