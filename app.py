from datetime import datetime
import os
import json
from flask import Flask, render_template, redirect, url_for, request
import requests

app = Flask(__name__)

@app.route('/fromapi')
def from_api():
    # URL per ottenere i dati con il filtro e i risultati limitati a 10
    url = 'https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=2025-01-01T00:00:00.000-05:00&pubEndDate=2025-01-08T23:59:59.999-05:00&resultsPerPage=10'

    # Effettua la richiesta API
    response = requests.get(url)

    # Verifica che la richiesta sia andata a buon fine
    if response.status_code == 200:
        data = response.json()
        # Estrarre i dettagli rilevanti (CVE ID, published, description, sourceIdentifier)
        cve_data = []
        for vuln in data.get('vulnerabilities', []):
            cve = vuln['cve']
            # Estrazione dei campi
            cve_id = cve['id']
            published = cve.get('published', 'N/A')
            source_identifier = cve.get('sourceIdentifier', 'Unknown Source')
            descriptions = cve.get('descriptions', [])
            description_en = next((desc['value'] for desc in descriptions if desc['lang'] == 'en'), 'No description available')
            # Aggiungi ai dati
            cve_data.append({
                'id': cve_id,
                'published': published,
                'sourceIdentifier': source_identifier,
                'description': description_en
            })
    else:
        cve_data = []  # Lista vuota in caso di errore
    print("Data loaded from API")
    # Passa i dati al template
    return render_template('index.html', cve_data=cve_data)


@app.route('/')
def from_file():
    # Percorso del file JSON nella cartella static
    json_path = os.path.join(app.static_folder, 'cve.json')

    try:
        # Legge i dati dal file JSON
        with open(json_path, 'r') as file:
            data = json.load(file)

        # Estrarre i dettagli rilevanti (CVE ID, published, description, sourceIdentifier)
        cve_data = []
        for vuln in data.get('vulnerabilities', []):
            cve = vuln['cve']
            cve_id = cve['id']
            published = cve.get('published', 'N/A')
            source_identifier = cve.get('sourceIdentifier', 'Unknown Source')
            descriptions = cve.get('descriptions', [])
            description_en = next((desc['value'] for desc in descriptions if desc['lang'] == 'en'), 'No description available')
            cve_data.append({
                'id': cve_id,
                'published': published,
                'sourceIdentifier': source_identifier,
                'description': description_en
            })
    except FileNotFoundError:
        cve_data = []  # Lista vuota se il file non esiste
    print("Data loaded from file")
    # Passa i dati al template
    return render_template('index.html', cve_data=cve_data)



@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/register')
def register():
    return render_template('register.html')

@app.route('/add_cve', methods=['GET', 'POST'])
def add_cve():
    if request.method == 'POST':
        # Estrai i dati dal form
        cve_id = request.form.get('cve_id')
        source_identifier = request.form.get('source_identifier')
        description = request.form.get('description')
        published = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Timestamp corrente

        # Simula il salvataggio (qui puoi aggiungere codice per salvare nel database in seguito)
        print(f"CVE ID: {cve_id}, Source Identifier: {source_identifier}, Description: {description}, Published: {published}")

        # Redirigi alla home page o a un'altra pagina
        return redirect(url_for('from_file'))

    return render_template('add_cve.html')


if __name__ == '__main__':
    app.run(debug=True)
