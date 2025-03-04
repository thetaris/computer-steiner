# Frachtbriefe mit AI

## Notebook

Das Notebook `Frachtbriefe.ipynb` kann mit Jupyter Lab gestartet werden und erfordert die folgenden Vorbereitungen:

1. Die Datei `.anthropic_key` muss im aktuellen Verzeichnis gespeichert sein
2. Die Python requirements müssen installiert werden `pip install -r requirements.txt` (Derzeit nur eine)

## Report erstellen

Mit dem Start des Python programms `compare.py` erstellt den Report in folgenden Schritten:

1. Die Dateien aus dem Verzeichnis `/output` wurden im Notebook erstellt
2. Die Referenzergebnisse liegen im Verzeichnis `/reference`
3. Der Report wird im HTML Format ins Verzeichnis `/reports` geschrieben.