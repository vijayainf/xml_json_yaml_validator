import os
import json
import yaml
import xml.etree.ElementTree as ET
import re
import difflib

# -------------------- Helpers --------------------
def remove_unicode_symbols(text):
    return re.sub(r'[^\x00-\x7F]+', '', text)

# -------------------- JSON Functions --------------------
def validate_json(content):
    try:
        json.loads(content)
        return True
    except json.JSONDecodeError:
        return False

def fix_json(content):
    content = remove_unicode_symbols(content)
    content = content.replace('\r\n', '\n')  # Normalize line endings

    # Insert missing commas intelligently
    content = re.sub(
        r'(?<=[0-9truefalsenull\"\'])(\s*)(?=\s*\"[^\"]+\"\s*:)',
        ',\n',
        content,
        flags=re.IGNORECASE
    )

    try:
        obj = json.loads(content)
    except json.JSONDecodeError as e:
        raise ValueError(f"Cannot auto-fix JSON: {e}")

    return json.dumps(obj, indent=2)

def wrap_json_in_array(fixed_content):
    try:
        obj = json.loads(fixed_content)
        if not isinstance(obj, list):
            return json.dumps([obj], indent=2)
        else:
            return fixed_content
    except Exception as e:
        print(f" Error wrapping JSON into array: {e}")
        return fixed_content

# -------------------- YAML Functions --------------------
def validate_yaml(content):
    try:
        yaml.safe_load(content)
        return True
    except yaml.YAMLError:
        return False

def fix_yaml(content):
    content = remove_unicode_symbols(content)
    lines = content.splitlines()
    fixed_lines = []
    for line in lines:
        if line.strip():
            line = line.replace('\t', '    ')  # Replace tabs with spaces
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)

# -------------------- XML Functions --------------------
def validate_xml(content):
    try:
        ET.fromstring(content)
        return True
    except ET.ParseError:
        return False

def fix_xml(content):
    content = remove_unicode_symbols(content)
    if not content.startswith("<?xml"):
        content = '<?xml version="1.0" encoding="UTF-8"?>\n' + content

    if not re.search(r'</\w+>$', content.strip()):
        root_tag = re.search(r'<(\w+)', content)
        if root_tag:
            root = root_tag.group(1)
            content += f"\n</{root}>"

    return content

# -------------------- Diff Preview --------------------
def preview_diff_and_confirm(original, fixed):
    diff = difflib.unified_diff(
        original.splitlines(),
        fixed.splitlines(),
        fromfile='Original',
        tofile='Fixed',
        lineterm=''
    )

    diff_output = '\n'.join(diff)
    if not diff_output.strip():
        print(" No differences detected. No need to save.")
        return False

    print("\n--- Differences Detected ---")
    print(diff_output)
    print("\nSave the fixed file? (y/n): ", end='')
    choice = input().strip().lower()

    return choice == 'y'

# -------------------- Main Validator --------------------
def detect_file_type(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.json', '.yaml', '.yml', '.xml']:
        return ext.replace('.', '')  # 'json', 'yaml', 'yml', 'xml'

    # Auto-detect based on file content
    with open(file_path, 'r', encoding='utf-8') as f:
        first_line = f.readline().strip()
        if first_line.startswith('{') or first_line.startswith('['):
            return 'json'
        elif first_line.startswith('<?xml') or first_line.startswith('<'):
            return 'xml'
        else:
            return 'yaml'

def save_fixed_file(original_path, fixed_content):
    base, ext = os.path.splitext(original_path)
    fixed_path = f"{base}_fixed{ext}"
    with open(fixed_path, 'w', encoding='utf-8') as f:
        f.write(fixed_content)
    print(f" Fixed file saved at: {fixed_path}")

def validate_and_fix_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    file_type = detect_file_type(file_path)

    if file_type == 'json':
        print("Detected: JSON")
        if validate_json(content):
            print("JSON is valid.")
            # Ask if the user wants to wrap the valid JSON in an array
            wrap_choice = input("Wrap JSON into an array [ ]? (y/n): ").strip().lower()
            if wrap_choice == 'y':
                fixed = wrap_json_in_array(content)
                save_fixed_file(file_path, fixed)
            else:
                print(" No changes made to the file.")
        else:
            print(" JSON is invalid. Fixing...")
            fixed = fix_json(content)
            if preview_diff_and_confirm(content, fixed):
                wrap_choice = input("Wrap JSON into an array [ ]? (y/n): ").strip().lower()
                if wrap_choice == 'y':
                    fixed = wrap_json_in_array(fixed)
                save_fixed_file(file_path, fixed)
            else:
                print(" File not saved.")

    elif file_type in ['yaml', 'yml']:
        print("Detected: YAML")
        if validate_yaml(content):
            print(" YAML is valid.")
        else:
            print(" YAML is invalid. Fixing...")
            fixed = fix_yaml(content)
            if preview_diff_and_confirm(content, fixed):
                save_fixed_file(file_path, fixed)
            else:
                print("❌ File not saved.")

    elif file_type == 'xml':
        print("Detected: XML")
        if validate_xml(content):
            print(" XML is valid.")
        else:
            print(" XML is invalid. Fixing...")
            fixed = fix_xml(content)
            if preview_diff_and_confirm(content, fixed):
                save_fixed_file(file_path, fixed)
            else:
                print(" File not saved.")

    else:
        print("❌ Unsupported file type.")

# -------------------- Main Entry --------------------
def main():
    file_path = input("Enter path to your JSON/YAML/XML file: ").strip()
    if not os.path.isfile(file_path):
        print(" File not found.")
        return

    validate_and_fix_file(file_path)

if __name__ == "__main__":
    main()
