import xml.etree.ElementTree as ET
import os
import re

# ==============================================================================
# Single-Pass Velbus Configuration Extractor and Cleaner
# ==============================================================================

def process_velbus_xml(xml_file_path: str, output_file_path: str):
    """
    Parses the Velbus configuration XML file, extracts Module data,
    and performs all subsequent cleaning and filtering steps in memory
    before writing the final, cleaned output to a single text file.

    Args:
        xml_file_path (str): The path to the input XML file (*.vlp).
        output_file_path (str): The path for the final output text file.
    """
    # 1. Read and Parse the XML content
    try:
        print(f"Reading XML from: {xml_file_path}")
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except FileNotFoundError:
        print(f"Error: The input file was not found at {xml_file_path}")
        return
    except ET.ParseError as e:
        print(f"Error parsing XML content: {e}")
        print("Please ensure the input file contains valid XML.")
        return
    except Exception as e:
        print(f"An error occurred during file reading or parsing: {e}")
        return

    all_module_blocks = []
    modules_element = root.find('Modules')

    if modules_element is None:
        print("Warning: Could not find the <Modules> element in the XML.")
        return

    # 2. Iterate and Extract Data
    for module in modules_element.findall('Module'):
        # --- Extraction ---
        module_type = module.get('type')
        address_hex = module.get('address', '')

        caption_element = module.find('Caption')
        caption_text = caption_element.text.strip() if caption_element is not None and caption_element.text else 'N/A (No Caption)'

        snapshot_element = module.find('Memory')
        snapshot_hex = snapshot_element.text.strip() if snapshot_element is not None and snapshot_element.text else 'N/A'

        # --- Hex Address to Decimal Conversion ---
        address_dec = 'ERROR: Invalid Address'
        try:
            hex_parts = address_hex.split(',')
            decimal_parts = [str(int(part.strip(), 16)) for part in hex_parts]
            address_dec = ','.join(decimal_parts)
        except (TypeError, ValueError):
            pass # Keep default error message

        # --- Snapshot Hex to Printable ASCII Conversion ---
        snapshot_ascii_converted = 'N/A'
        if snapshot_hex != 'N/A' and snapshot_hex and len(snapshot_hex) % 2 == 0:
            try:
                snapshot_bytes = bytes.fromhex(snapshot_hex)
                ascii_list = [chr(byte) if 32 <= byte <= 126 else '.' for byte in snapshot_bytes]
                snapshot_ascii_converted = "".join(ascii_list)
            except ValueError:
                snapshot_ascii_converted = 'Error: Non-hex characters'
        elif snapshot_hex != 'N/A' and len(snapshot_hex) % 2 != 0:
             snapshot_ascii_converted = f'Error: Odd length ({len(snapshot_hex)})'

        # --- Initial Formatting (Equivalent to output of original parse_velbus_xml) ---
        initial_lines = []
        initial_lines.append(f"Module : {module_type} {address_dec}")
        initial_lines.append(f"Address :  {address_dec}")
        initial_lines.append(f"Modulenaam : {caption_text}")
        initial_lines.append(f"Ascii : \r\n{snapshot_ascii_converted}")
        initial_lines.append("________________________")

        # Combine lines for subsequent processing
        module_block_raw = '\n'.join(initial_lines)
        all_module_blocks.append(module_block_raw)

    # 3. Post-Processing (All steps from 'deel2' combined)

    # Combine all raw blocks into one large text
    raw_output_text = "\n".join(all_module_blocks)

    # --- Step 3a: Split lines wider than 240 chars ---
    temp_lines = []
    max_len_240 = 240
    for line in raw_output_text.splitlines():
        if not line.strip(): # Skip empty lines
            continue
        # Only split if the line is not a block-separator line
        if not line.startswith("___"):
            for i in range(0, len(line), max_len_240):
                temp_lines.append(line[i:i + max_len_240])
        else:
             temp_lines.append(line)

    # --- Step 3b: Split non-header lines wider than 16 chars ---
    split_16_lines = []
    max_len_16 = 16
    for line in temp_lines:
        # skip splitting if line contains 'Module', 'Modulenaam', 'Address' or '___'
        if "Module" in line or "Modulenaam" in line or "Address" in line or "___" in line:
            split_16_lines.append(line)
            continue

        # otherwise, break into chunks of max_len_16
        for i in range(0, len(line), max_len_16):
            split_16_lines.append(line[i:i + max_len_16])


    # --- Step 3c: Clean Dots and Remove fully dotted lines ---
    cleaned_lines_dots = []
    for line in split_16_lines:
        chars = list(line)
        # Step 1 — replace any pattern .X. → ...
        for i in range(1, len(chars) - 1):
            if chars[i - 1] == '.' and chars[i + 1] == '.' and chars[i] != '.':
                chars[i] = '.'

        cleaned_line = ''.join(chars)

        # Step 2 — skip lines that are 15 or 16 dots long
        if cleaned_line.strip('.') == '' and len(cleaned_line) in (15, 16):
            continue

        cleaned_lines_dots.append(cleaned_line)

    cleaned_text_dots = '\n'.join(cleaned_lines_dots)


    # --- Step 3d: Final Module-based Cleaning/Filtering ('superclean') ---
    final_blocks = []
    # Split into module blocks by lines of underscores
    blocks = re.split(r'\n_{4,}\s*\n', cleaned_text_dots.strip(), flags=re.MULTILINE)

    for block in blocks:
        if not block.strip():
            continue

        lines = block.splitlines()
        module_name = None
        module_name_line_index = -1

        # Find Modulenaam line
        for idx, line in enumerate(lines):
            if line.strip().lower().startswith("modulenaam"):
                module_name = line.split(":", 1)[1].strip() if ":" in line else ""
                module_name_line_index = idx
                break

        if module_name_line_index == -1:
            final_blocks.append("\n".join(lines))
            continue

        # Normalize module name for substring matching
        name_clean = re.sub(r'[^A-Za-z0-9]', '', module_name).lower()

        new_lines = []
        for idx, line in enumerate(lines):
            stripped = line.strip()

            # Always keep Modulenaam line
            if idx == module_name_line_index:
                new_lines.append(line)
                continue

            # Replace any line containing "Ascii" with blank line
            if "ascii" in stripped.lower():
                new_lines.append("")
                continue

            # Remove lines that are only dots/whitespace or empty after strip
            if not stripped or re.fullmatch(r'[.\s]*', line):
                continue

            # Normalize line for substring check
            line_clean = re.sub(r'[^A-Za-z0-9]', '', line).lower()

            # Remove lines that are substring of module name
            if line_clean and line_clean in name_clean:
                continue

            new_lines.append(line)

        final_blocks.append("\n".join(new_lines))


    # 4. Write the results to the output file
    final_output_content = "\n________________________\n".join(final_blocks)

    try:
        with open(output_file_path, 'w', encoding='utf-8') as outfile:
            outfile.write(final_output_content)

        print(f"\n✅ Successfully processed and cleaned {len(modules_element.findall('Module'))} modules.")
        print(f"Output written to: {output_file_path}")

    except Exception as e:
        print(f"An error occurred while writing the output file: {e}")


# ==============================================================================
# --- Configuration ---
# NOTE: Update these paths to match the location of your XML file and desired output.
INPUT_FILE = r"C:\Users\v12345vtm\Documents\MyProject.vlp"
OUTPUT_FILE = r"C:\Users\v12345vtm\Documents\MyProject_vlp.txt"
# ---------------------

if __name__ == "__main__":
    process_velbus_xml(INPUT_FILE, OUTPUT_FILE)
