import xml.etree.ElementTree as ET
import os
import shutil


def clean_text(data):
    """Zet bytes om naar leesbare ASCII-tekst."""
    data = data.strip(b'\x00\x01\xff \xfe\xfd')
    if not data:
        return ""

    cleaned_bytes = bytearray()
    for b in data:
        if 32 <= b <= 126:
            cleaned_bytes.append(b)
        else:
            break

    try:
        return cleaned_bytes.decode("ascii").strip()
    except UnicodeDecodeError:
        return ""


# ==========================================
# SPECIFIEKE PARSERS PER MODULE
# ==========================================

def parse_vmbgpod(memory_hex, module_type, caption):
    """
    Specifieke parser voor VMBGPOD en VMBGPOD-2 (Glasspanels).
    Genereert standaard de 32 knoppen/kanalen zoals gedefinieerd in de XML-structuur.
    """
    default_channels = [f"Drukknop {i}" for i in range(1, 33)]

    if not memory_hex:
        return default_channels

    try:
        memory = bytes.fromhex(memory_hex)
    except ValueError:
        return default_channels

    # Hier kun je eventueel extra geheugen-analyser logica toevoegen
    # als je specifieke custom labels uit het geheugen wilt uitlezen.
    channels = []
    for i in range(1, 33):
        channels.append(f"Drukknop {i}")

    return channels


def parse_vmb1rys(memory_hex, module_type, caption):
    """Specifieke parser voor VMB1RYS (6 kanalen)."""
    try:
        memory = bytes.fromhex(memory_hex)
    except ValueError:
        return []

    channels = []
    ch1_name = clean_text(memory[234:250]) if len(memory) >= 250 else ""
    if not ch1_name:
        ch1_name = "Extern relais"

    channels.append(ch1_name)
    channels.extend([
        "Virtueel relais",
        "Virtueel relais",
        "Virtueel relais",
        "Virtueel relais",
        "Externe ingang"
    ])
    return channels


def parse_vmbpir_20(memory_hex, module_type, caption):
    """
    Specifieke parser voor VMBPIR-20.
    Standaard 7/8 vaste functies (zoals zichtbaar in VelbusLink).
    """
    default_names = [
        "Uitgang donker",
        "Uitgang licht",
        "Beweging 1",
        "Uitgang beweging 1 (lichtafh.)",
        "Beweging 2",
        "Uitgang beweging 2 (lichtafh.)",
        "Output afwezigheid"
    ]

    try:
        memory = bytes.fromhex(memory_hex)
        custom_names = []
        for offset in range(256, len(memory) - 15, 16):
            txt = clean_text(memory[offset:offset + 16])
            if txt and txt not in custom_names and not txt.startswith("VMBPIR"):
                custom_names.append(txt)

        channels = []
        for i in range(7):
            if i < len(custom_names) and custom_names[i]:
                channels.append(custom_names[i])
            else:
                channels.append(default_names[i])
        return channels

    except ValueError:
        return default_names


def parse_vmbpirm(memory_hex, module_type, caption):
    """Specifieke parser voor VMBPIRM."""
    return [
        "Uitgang donker",
        "Uitgang licht",
        "Beweging 1",
        "Uitgang beweging 1 (lichtafh.)",
        "Beweging 2",
        "Uitgang beweging 2 (lichtafh.)",
        "Output afwezigheid"
    ]


def parse_vmbpiro_10(memory_hex, module_type, caption):
    """Specifieke parser voor VMBPIRO-10."""
    try:
        memory = bytes.fromhex(memory_hex)
        temp_name = clean_text(memory[80:96]) if len(memory) >= 96 else ""
        if not temp_name:
            temp_name = "Buitentemp."
    except ValueError:
        temp_name = "Buitentemp."

    return [
        temp_name,
        "Uitgang donker",
        "Uitgang licht",
        "Beweging 1",
        "Uitgang beweging 1 (lichtafh.)",
        "Beweging 2",
        "Uitgang beweging 2 (lichtafh.)",
        "Output afwezigheid"
    ]


def parse_vmbmeteo(memory_hex, module_type, caption):
    """Specifieke parser voor VMBMETEO (Weerstation module)."""
    return [
        "Vorst alarm",
        "Hitte alarm",
        "Regen alarm",
        "Dageraad alarm",
        "Schemer alarm",
        "Zon alarm",
        "Wind alarm",
        "Storm alarm",
        "Outdoor temp.",
        "Rainfall",
        "Illuminance",
        "Wind speed"
    ]


def parse_generic_module(memory_hex, module_type, caption):
    """Algemene/fallback parser voor overige modules."""
    names = []
    if not memory_hex:
        return names
    try:
        byte_data = bytes.fromhex(memory_hex)
    except ValueError:
        return names

    parts = byte_data.split(b'\xff')

    ignore_strings = [module_type, caption]
    if module_type:
        ignore_strings.append(module_type.replace('-', ''))
        ignore_strings.append(module_type.replace('-', ' '))

    for part in parts:
        part = part.strip(b'\x00\x01\xff ')
        if not part:
            continue

        if not all(32 <= b <= 126 for b in part):
            continue

        chunks = []
        if len(part) > 16:
            for i in range(0, len(part), 16):
                chunks.append(part[i:i + 16])
        else:
            chunks.append(part)

        for chunk in chunks:
            chunk = chunk.strip(b'\x00\x01\xff ')
            if not chunk:
                continue
            try:
                name = chunk.decode('ascii').strip()
            except UnicodeDecodeError:
                continue
            if not name:
                continue
            if any(name.lower() == ign.lower() for ign in ignore_strings if ign):
                continue
            if "cntr alarm" in name.lower():
                continue
            if not any(c.isalnum() for c in name):
                continue
            if len(name) < 2:
                continue
            if name not in names:
                names.append(name)

    return names


def extract_channel_names(memory_hex, module_type, caption):
    """Routering naar de specifieke parser per moduletype."""
    mod_upper = module_type.upper()

    if mod_upper in ["VMBGPOD", "VMBGPOD-2"]:
        return parse_vmbgpod(memory_hex, module_type, caption)
    elif mod_upper == "VMB1RYS":
        return parse_vmb1rys(memory_hex, module_type, caption)
    elif mod_upper == "VMBPIR-20":
        return parse_vmbpir_20(memory_hex, module_type, caption)
    elif mod_upper == "VMBPIRM":
        return parse_vmbpirm(memory_hex, module_type, caption)
    elif mod_upper == "VMBPIRO-10":
        return parse_vmbpiro_10(memory_hex, module_type, caption)
    elif mod_upper == "VMBMETEO":
        return parse_vmbmeteo(memory_hex, module_type, caption)
    else:
        return parse_generic_module(memory_hex, module_type, caption)


# ==========================================
# HOOFDPROGRAMMA
# ==========================================

def convert_vlp_to_txt(input_file_path, output_file_path):
    base_name, ext = os.path.splitext(input_file_path)
    if ext.lower() != '.xml':
        xml_copy_path = base_name + '.xml'
        try:
            shutil.copy2(input_file_path, xml_copy_path)
            print(f"✅ Kopie van de invoer opgeslagen als: {xml_copy_path}")
        except Exception as e:
            print(f"⚠️ Fout bij het maken van de XML-kopie: {e}")

    try:
        tree = ET.parse(input_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Fout bij het inlezen van het bestand: {e}")
        return

    root_name = os.path.basename(input_file_path)
    output_lines = [root_name]

    modules = root.findall('.//Module')
    if not modules:
        print("Geen <Module> elementen gevonden in het bestand.")
        return

    for i, module in enumerate(modules):
        is_last_module = (i == len(modules) - 1)
        module_prefix = "`-- " if is_last_module else "|-- "
        child_prefix = "    " if is_last_module else "|   "

        module_type = module.get('type', 'Onbekend')
        address_hex_full = module.get('address', '0')
        build = module.get('build', 'N/A')

        caption_element = module.find('Caption')
        caption = caption_element.text.strip() if caption_element is not None and caption_element.text else module_type

        address_hex = address_hex_full.split(',')[0]
        try:
            address_dec = int(address_hex, 16)
        except ValueError:
            address_dec = address_hex

        output_lines.append(f"{module_prefix}{module_type} (Addr: {address_dec}, Type: {module_type}, Build: {build})")

        memory_element = module.find('Memory')
        if memory_element is not None and memory_element.text:
            memory_hex = memory_element.text.strip()
            channel_names = extract_channel_names(memory_hex, module_type, caption)

            if not channel_names:
                channel_names = [f"CH{j + 1}" for j in range(8)]

            for ch in range(len(channel_names)):
                channel_name = channel_names[ch]
                is_last_ch = (ch == len(channel_names) - 1)
                ch_prefix = "`-- " if is_last_ch else "|-- "
                output_lines.append(f"{child_prefix}{ch_prefix}CH{ch + 1}: {channel_name}")

    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(output_lines))
        print(f"✅ Succes! De configuratie is opgeslagen in: {output_file_path}")
        if hasattr(os, "startfile"):
            os.startfile(output_file_path)
    except Exception as e:
        print(f"Fout bij het schrijven naar het bestand: {e}")


if __name__ == "__main__":
    INPUT_FILE = r"C:\Users\Administrator\Downloads\VLPtoTXT-main\VelbusExamples\MyProject.vlp"
    OUTPUT_TXT = r"C:\Users\Administrator\Downloads\VLPtoTXT-main\VelbusExamples\MyProject_uitvoer.txt"

    if os.path.exists(INPUT_FILE):
        convert_vlp_to_txt(INPUT_FILE, OUTPUT_TXT)
    else:
        print(f"Kan het bestand '{INPUT_FILE}' niet vinden. Controleer het pad.")
