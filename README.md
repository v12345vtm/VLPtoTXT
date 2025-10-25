# Velbus VLP naar TXT Export Tool

In vroegere versies van **VelbusLink** bestond er een handige functie om een `.vlp`-project te **exporteren naar PDF**.  
Deze functie is in de huidige versies verdwenen — maar dit script biedt een alternatief!

In plaats van een PDF, zet deze tool je **Velbus-project (.vlp)** om naar een **gestructureerd .txt-bestand**.  
Zo kun je de gegevens:
- eenvoudig verwerken met andere software,
- afdrukken om met pen en papier notities bij te voegen,
- of aan de klant bezorgen als naslagwerk.

---

## 🧠 Functieoverzicht

Het script leest het `.vlp`-bestand (Velbus XML-structuur) en schrijft een overzicht van alle modules, kanalen en instellingen naar een eenvoudig te lezen `.txt`-bestand.

---

## ⚙️ Gebruik

Pas de onderstaande configuratie aan met het pad naar jouw `.vlp`-bestand en het gewenste `.txt`-uitvoerbestand:

```python
# ==============================================================================
# --- Configuration ---
# NOTE: Update these paths to match the location of your XML file and desired output.
INPUT_FILE = r"C:\Users\v12345vtm\Documents\MyProject.vlp"
OUTPUT_FILE = r"C:\Users\v12345vtm\Documents\MyProject_vlp.txt"
# ---------------------

if __name__ == "__main__":
    process_velbus_xml(INPUT_FILE, OUTPUT_FILE)
