#!/usr/bin/env python3
"""
SixDot Braille - Bidirectional 6-dot braille translator

A lightweight braille translator that converts standard text to 6-dot braille and back.
Supports uncontracted (Grade 1) braille including letters, numbers, and basic punctuation.
"""

import sys
import argparse
import re
from typing import Dict, Optional, Union

# ============================================================================
# BRAILLE MAPPINGS
# ============================================================================

# Letter to Braille mapping (a-z)
LETTER_TO_BRAILLE: Dict[str, str] = {
    'a': '⠁', 'b': '⠃', 'c': '⠉', 'd': '⠙', 'e': '⠑',
    'f': '⠋', 'g': '⠛', 'h': '⠓', 'i': '⠊', 'j': '⠚',
    'k': '⠅', 'l': '⠇', 'm': '⠍', 'n': '⠝', 'o': '⠕',
    'p': '⠏', 'q': '⠟', 'r': '⠗', 's': '⠎', 't': '⠞',
    'u': '⠥', 'v': '⠧', 'w': '⠺', 'x': '⠭', 'y': '⠽', 'z': '⠵',
}

# Punctuation mapping
PUNCTUATION_TO_BRAILLE: Dict[str, str] = {
    ' ': ' ',      # space
    '.': '⠲',     # period
    ',': '⠂',     # comma
    '?': '⠦',     # question mark
    '!': '⠖',     # exclamation
    ';': '⠆',     # semicolon
    ':': '⠒',     # colon
    "'": '⠄',     # apostrophe
    '"': '⠦⠄',   # quotation mark (opening and closing same in basic)
    '(': '⠐⠦',   # opening parenthesis
    ')': '⠐⠴',   # closing parenthesis
    '-': '⠤',     # hyphen/dash
    '/': '⠌',     # slash
}

# Number mapping (0-9 using a-j patterns)
NUMBER_TO_BRAILLE: Dict[str, str] = {
    '1': '⠁', '2': '⠃', '3': '⠉', '4': '⠙', '5': '⠑',
    '6': '⠋', '7': '⠛', '8': '⠓', '9': '⠊', '0': '⠚'
}

# Reverse mappings for decoding
BRAILLE_TO_LETTER: Dict[str, str] = {v: k for k, v in LETTER_TO_BRAILLE.items()}
BRAILLE_TO_PUNCTUATION: Dict[str, str] = {v: k for k, v in PUNCTUATION_TO_BRAILLE.items()}
BRAILLE_TO_NUMBER: Dict[str, str] = {v: k for k, v in NUMBER_TO_BRAILLE.items()}

# Special symbols
NUMBER_SIGN = '⠼'      # Dots 3,4,5,6 - indicates following characters are numbers
CAPITAL_SIGN = '⠠'     # Dot 6 - indicates following letter is capital (for future use)

# Combine all braille patterns for quick lookup
ALL_BRAILLE_TO_CHAR: Dict[str, str] = {
    **BRAILLE_TO_LETTER,
    **BRAILLE_TO_PUNCTUATION,
    **BRAILLE_TO_NUMBER
}


# ============================================================================
# CORE TRANSLATION FUNCTIONS
# ============================================================================

def text_to_braille(text: str, use_capital_sign: bool = False) -> str:
    """
    Convert standard text to 6-dot braille.
    
    Args:
        text: Input text to convert
        use_capital_sign: If True, add capital sign (⠠) before capital letters
    
    Returns:
        Braille string using Unicode braille patterns
    
    Examples:
        >>> text_to_braille("Hello 123")
        '⠓⠑⠇⠇⠕ ⠼⠁⠃⠉'
        >>> text_to_braille("Hello 123", use_capital_sign=True)
        '⠠⠓⠑⠇⠇⠕ ⠼⠁⠃⠉'
    """
    result = []
    in_number = False
    i = 0
    
    while i < len(text):
        char = text[i]
        
        # Handle digits
        if char.isdigit():
            if not in_number:
                result.append(NUMBER_SIGN)
                in_number = True
            result.append(NUMBER_TO_BRAILLE[char])
            i += 1
            continue
        
        # Handle letters
        if char.isalpha():
            if in_number:
                in_number = False
            
            # Handle capitalization
            if use_capital_sign and char.isupper():
                result.append(CAPITAL_SIGN)
            
            result.append(LETTER_TO_BRAILLE[char.lower()])
            i += 1
            continue
        
        # Handle punctuation and other characters
        if in_number:
            in_number = False
        
        # Look up punctuation
        if char in PUNCTUATION_TO_BRAILLE:
            result.append(PUNCTUATION_TO_BRAILLE[char])
        elif char == '\n':
            result.append('\n')
        elif char == '\t':
            result.append(' ' * 4)  # Convert tabs to spaces
        else:
            # For unsupported characters, preserve them as-is
            result.append(char)
        
        i += 1
    
    return ''.join(result)


def braille_to_text(braille: str, preserve_numbers: bool = True) -> str:
    """
    Convert 6-dot braille back to standard text.
    
    Args:
        braille: Braille string to decode
        preserve_numbers: If True, decode number sign sequences as digits
    
    Returns:
        Plain text string
    
    Examples:
        >>> braille_to_text("⠓⠑⠇⠇⠕ ⠼⠁⠃⠉")
        'hello 123'
    """
    result = []
    in_number = False
    i = 0
    
    while i < len(braille):
        char = braille[i]
        
        # Handle number sign
        if preserve_numbers and char == NUMBER_SIGN:
            in_number = True
            i += 1
            continue
        
        # Handle numbers
        if in_number and char in BRAILLE_TO_NUMBER:
            result.append(BRAILLE_TO_NUMBER[char])
            in_number = False
            i += 1
            continue
        
        # Handle punctuation and spaces
        if char in BRAILLE_TO_PUNCTUATION:
            result.append(BRAILLE_TO_PUNCTUATION[char])
            in_number = False
            i += 1
            continue
        
        # Handle letters
        if char in BRAILLE_TO_LETTER:
            result.append(BRAILLE_TO_LETTER[char])
            in_number = False
            i += 1
            continue
        
        # Handle capital sign (skip it for now, just uppercase next letter)
        if char == CAPITAL_SIGN:
            i += 1
            if i < len(braille) and braille[i] in BRAILLE_TO_LETTER:
                result.append(BRAILLE_TO_LETTER[braille[i]].upper())
            else:
                # If no letter follows, just append the capital sign as is
                result.append(CAPITAL_SIGN)
            in_number = False
            i += 1
            continue
        
        # Handle line breaks and unknown characters
        if char == '\n':
            result.append('\n')
        elif char not in ALL_BRAILLE_TO_CHAR:
            result.append(char)
        
        in_number = False
        i += 1
    
    return ''.join(result)


def is_valid_braille(braille: str) -> bool:
    """
    Check if a string contains only valid 6-dot braille characters.
    
    Args:
        braille: String to validate
    
    Returns:
        True if all characters are valid braille patterns
    """
    valid_characters = set(ALL_BRAILLE_TO_CHAR.keys()) | {NUMBER_SIGN, CAPITAL_SIGN, ' ', '\n', '\t'}
    return all(char in valid_characters for char in braille)


def detect_language(text: str) -> str:
    """
    Detect whether input is text or braille based on character patterns.
    
    Args:
        text: Input string to analyze
    
    Returns:
        'braille' if input appears to be braille, 'text' otherwise
    """
    if not text:
        return 'text'
    
    braille_chars = set(ALL_BRAILLE_TO_CHAR.keys()) | {NUMBER_SIGN, CAPITAL_SIGN}
    braille_count = sum(1 for char in text if char in braille_chars)
    text_count = len(text) - braille_count
    
    # If more than 30% of non-space characters are braille patterns, treat as braille
    non_space_chars = [c for c in text if c != ' ']
    if not non_space_chars:
        return 'text'
    
    braille_ratio = braille_count / len(non_space_chars)
    return 'braille' if braille_ratio > 0.3 else 'text'


def smart_convert(text: str, auto_detect: bool = True) -> Dict[str, Union[str, bool]]:
    """
    Smart conversion that auto-detects input type.
    
    Args:
        text: Input text or braille
        auto_detect: If True, auto-detect direction
    
    Returns:
        Dictionary with 'result', 'direction', and 'success' keys
    """
    direction = None
    result = None
    success = False
    
    if auto_detect:
        direction = detect_language(text)
    else:
        # Default to text-to-braille
        direction = 'text'
    
    try:
        if direction == 'braille':
            result = braille_to_text(text)
        else:
            result = text_to_braille(text)
        success = True
    except Exception as e:
        result = str(e)
        success = False
    
    return {
        'result': result,
        'direction': direction,
        'success': success
    }


# ============================================================================
# FILE HANDLING FUNCTIONS
# ============================================================================

def convert_file(input_file: str, output_file: str, to_braille: bool = True) -> None:
    """
    Convert an entire file from text to braille or vice versa.
    
    Args:
        input_file: Path to input file
        output_file: Path to output file
        to_braille: If True, convert text to braille; if False, convert braille to text
    """
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if to_braille:
        result = text_to_braille(content)
    else:
        result = braille_to_text(content)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(result)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def print_braille_dot_pattern(braille_char: str) -> None:
    """
    Print the dot pattern of a braille character for visualization.
    
    Args:
        braille_char: A single braille character
    """
    # Braille dot patterns (1-6) mapping
    # This is a simplified visual representation
    patterns = {
        '⠁': [1], '⠃': [1,2], '⠉': [1,4], '⠙': [1,4,5], '⠑': [1,5],
        '⠋': [1,2,4], '⠛': [1,2,4,5], '⠓': [1,2,5], '⠊': [2,4], '⠚': [2,4,5],
        '⠅': [1,3], '⠇': [1,2,3], '⠍': [1,3,4], '⠝': [1,3,4,5], '⠕': [1,3,5],
        '⠏': [1,2,3,4], '⠟': [1,2,3,4,5], '⠗': [1,2,3,5], '⠎': [2,3,4], '⠞': [2,3,4,5],
        '⠥': [1,3,6], '⠧': [1,2,3,6], '⠺': [2,4,5,6], '⠭': [1,3,4,6], '⠽': [1,3,4,5,6], '⠵': [1,3,5,6]
    }
    
    if braille_char not in patterns:
        print(f"No pattern data for {braille_char}")
        return
    
    dots = patterns[braille_char]
    grid = [
        ['●' if 1 in dots else '○', '●' if 4 in dots else '○'],
        ['●' if 2 in dots else '○', '●' if 5 in dots else '○'],
        ['●' if 3 in dots else '○', '●' if 6 in dots else '○']
    ]
    
    for row in grid:
        print(f"  {row[0]}   {row[1]}")


def get_version() -> str:
    """Return the current version of the software."""
    return "1.0.0"


# ============================================================================
# INTERACTIVE MODE
# ============================================================================

def interactive_mode() -> None:
    """Run an interactive session for continuous conversion."""
    print("\n" + "=" * 60)
    print(" SixDot Braille - Interactive Mode")
    print("=" * 60)
    print("Commands:")
    print("  :mode text    - Convert text to braille (default)")
    print("  :mode braille - Convert braille to text")
    print("  :auto         - Auto-detect input type")
    print("  :quit or :q   - Exit interactive mode")
    print("  :help         - Show this help")
    print("-" * 60)
    
    mode = "text"  # 'text' or 'braille' or 'auto'
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.startswith(':'):
                cmd = user_input.lower()
                if cmd in [':quit', ':q', ':exit']:
                    print("Goodbye!")
                    break
                elif cmd == ':help':
                    print("\nCommands:")
                    print("  :mode text    - Convert text to braille")
                    print("  :mode braille - Convert braille to text")
                    print("  :auto         - Auto-detect input type")
                    print("  :quit         - Exit")
                elif cmd == ':mode text':
                    mode = "text"
                    print("Mode: Text → Braille")
                elif cmd == ':mode braille':
                    mode = "braille"
                    print("Mode: Braille → Text")
                elif cmd == ':auto':
                    mode = "auto"
                    print("Mode: Auto-detect")
                else:
                    print(f"Unknown command: {cmd}")
                continue
            
            # Perform conversion
            if mode == "auto":
                result_dict = smart_convert(user_input)
                print(f"\n[{result_dict['direction']} → {'braille' if result_dict['direction'] == 'text' else 'text'}]")
                print(result_dict['result'])
            elif mode == "text":
                print(text_to_braille(user_input))
            else:  # braille mode
                print(braille_to_text(user_input))
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


# ============================================================================
# MAIN CLI ENTRY POINT
# ============================================================================

def main() -> None:
    """Main command-line interface entry point."""
    parser = argparse.ArgumentParser(
        description="SixDot Braille Translator - Convert text to 6-dot braille and back",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s "Hello World"              # Text to braille
  %(prog)s --decode "⠓⠑⠇⠇⠕"       # Braille to text
  %(prog)s --interactive              # Interactive mode
  %(prog)s --capital "Hello"          # Preserve capitalization
  %(prog)s --file input.txt output.brl # Convert file
        """
    )
    
    parser.add_argument(
        'text', nargs='?',
        help='Text to translate (if not using --file or --interactive)'
    )
    parser.add_argument(
        '-d', '--decode', action='store_true',
        help='Decode braille to text'
    )
    parser.add_argument(
        '-c', '--capital', action='store_true',
        help='Use capital sign (⠠) for uppercase letters (text to braille only)'
    )
    parser.add_argument(
        '-i', '--interactive', action='store_true',
        help='Start interactive mode'
    )
    parser.add_argument(
        '-f', '--file', nargs=2, metavar=('INPUT', 'OUTPUT'),
        help='Convert file (input output)'
    )
    parser.add_argument(
        '-a', '--auto', action='store_true',
        help='Auto-detect input type (text or braille)'
    )
    parser.add_argument(
        '-v', '--version', action='store_true',
        help='Show version information'
    )
    parser.add_argument(
        '--validate', metavar='BRAILLE',
        help='Validate if a string contains valid braille characters'
    )
    
    args = parser.parse_args()
    
    # Show version
    if args.version:
        print(f"SixDot Braille v{get_version()}")
        return
    
    # Validate mode
    if args.validate:
        valid = is_valid_braille(args.validate)
        print(f"Valid braille: {'Yes' if valid else 'No'}")
        return
    
    # Interactive mode
    if args.interactive:
        interactive_mode()
        return
    
    # File conversion mode
    if args.file:
        try:
            convert_file(args.file[0], args.file[1], to_braille=not args.decode)
            print(f"Successfully converted {args.file[0]} → {args.file[1]}")
        except Exception as e:
            print(f"Error converting file: {e}", file=sys.stderr)
            sys.exit(1)
        return
    
    # Single string conversion
    if not args.text:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.auto:
            result_dict = smart_convert(args.text)
            print(result_dict['result'])
        elif args.decode:
            result = braille_to_text(args.text)
            print(result)
        else:
            result = text_to_braille(args.text, use_capital_sign=args.capital)
            print(result)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


# ============================================================================
# SELF-TEST
# ============================================================================

def run_self_test() -> bool:
    """Run a self-test to verify the translator works correctly."""
    print("Running self-test...")
    
    test_cases = [
        ("hello", "⠓⠑⠇⠇⠕"),
        ("Hello", "⠓⠑⠇⠇⠕"),
        ("HELLO", "⠓⠑⠇⠇⠕"),
        ("123", "⠼⠁⠃⠉"),
        ("Hello 123", "⠓⠑⠇⠇⠕ ⠼⠁⠃⠉"),
        ("a1b2c3", "⠁⠼⠁⠃⠼⠃⠉⠼⠉"),
        ("Hello, world!", "⠓⠑⠇⠇⠕⠂ ⠺⠕⠗⠇⠙⠖"),
        ("test?", "⠞⠑⠎⠞⠦"),
    ]
    
    all_passed = True
    
    for text, expected_braille in test_cases:
        result = text_to_braille(text)
        if result != expected_braille:
            print(f"❌ FAIL: '{text}' → '{result}' (expected '{expected_braille}')")
            all_passed = False
        else:
            # Test round-trip
            decoded = braille_to_text(result)
            if decoded.lower() != text.lower():
                print(f"❌ FAIL Round-trip: '{text}' → '{result}' → '{decoded}'")
                all_passed = False
            else:
                print(f"✅ PASS: '{text}' → '{result}'")
    
    # Test capital sign
    capital_test = text_to_braille("Hello", use_capital_sign=True)
    if capital_test == "⠠⠓⠑⠇⠇⠕":
        print(f"✅ PASS: Capital sign test → '{capital_test}'")
    else:
        print(f"❌ FAIL: Capital sign test → '{capital_test}' (expected '⠠⠓⠑⠇⠇⠕')")
        all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
    else:
        print("\n⚠️ Some tests failed!")
    
    return all_passed


if __name__ == "__main__":
    # Run self-test if module is executed directly
    if len(sys.argv) == 1:
        run_self_test()
    else:
        main()