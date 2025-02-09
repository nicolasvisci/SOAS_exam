from datetime import timedelta
import datetime
import os
import json
import requests
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, get_flashed_messages, session
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity, decode_token, \
    jwt_required
from flask import flash
from utils import *

app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')  # Usa un valore di fallback se non trovato
app.config['JWT_TOKEN_LOCATION'] = [os.getenv('JWT_TOKEN_LOCATION', 'cookies')]
app.config['JWT_ACCESS_COOKIE_NAME'] = os.getenv('JWT_ACCESS_COOKIE_NAME', 'access_token_cookie')
app.config['JWT_COOKIE_SECURE'] = os.getenv('JWT_COOKIE_SECURE', 'False').lower() == 'true'  # Converti stringa in bool
app.config['JWT_COOKIE_CSRF_PROTECT'] = os.getenv('JWT_COOKIE_CSRF_PROTECT', 'False').lower() == 'true'

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

@app.route('/fromapi')
def from_api():
    # URL per ottenere i dati con il filtro e i risultati limitati a 10
    url = 'https://services.nvd.nist.gov/rest/json/cves/2.0/?pubStartDate=2025-01-01T00:00:00.000-05:00&pubEndDate=2025-01-08T23:59:59.999-05:00&resultsPerPage=50'

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
    # Passa i dati al template
    return render_template('index.html', cve_data=cve_data)


@app.route('/add_cve', methods=['GET', 'POST'])
def add_cve():

    token = request.cookies.get('access_token_cookie')

    if not token:
        flash("Devi effettuare il login per accedere a questa pagina.", "danger")
        return redirect(url_for('login'))

    try:
        decode_token(token)  # Decodifica e verifica il token JWT
    except Exception as e:
        flash("Sessione scaduta. Effettua nuovamente il login.", "warning")
        return redirect(url_for('login'))

    verify_jwt_in_request()  # Verifica il token
    user = get_jwt_identity()  # Ottieni l'email dal token

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

    return render_template('add_cve.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')

    elif request.method == 'POST':
        # Verifica se la richiesta contiene dati JSON o form-data
        if request.content_type == 'application/json':
            data = request.get_json()  # JSON
        else:
            data = request.form  # Form-data

        email = data.get('email')
        password = data.get('password')

        if not email or not password:
            return jsonify({'message': 'Email e password obbligatorie'}), 400

        cursor = db.cursor(dictionary=True)

        # Controllo se l'email esiste già (uso query parametrizzate per prevenire SQL Injection)
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            cursor.close()
            return jsonify({'message': 'Email già registrata'}), 409

        # Hash della password
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        # Inserimento del nuovo utente
        cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed_password))
        db.commit()
        cursor.close()

        flash("Registrazione completata")
        return redirect(url_for('login'))
    

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':

        # Verifica se c'è un token nel cookie
        token = request.cookies.get('access_token_cookie')

        if token:
            try:
                # Decodifica il token per verificarne la validità
                decoded_token = decode_token(token)
                if decoded_token:
                    # Se il token è valido, reindirizza alla dashboard
                    return redirect(url_for('dashboard'))
            except Exception as e:
                flash("Sessione scaduta. Effettua nuovamente il login.")
                # Se il token non è valido, non fare nulla e lascia l'utente sulla pagina di login

    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and bcrypt.check_password_hash(user['password_hash'], password):
            access_token = create_access_token(identity=email, expires_delta=timedelta(days=1))
            flash("Accesso riuscito")
            response = make_response(redirect(url_for('dashboard')))  # ⬅️ Reindirizzamento
            response.set_cookie('access_token_cookie', access_token, httponly=True)
            return response
        else:
            flash("Credenziali non valide")  # 🔥 Usa flash() invece della sessione
            return redirect(url_for('login'))  # 🔄 Redirect senza messaggio nell'URL

    return render_template('login.html')

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('access_token_cookie', '', expires=0, httponly=True)
    flash("Logout effettuato con successo")
    return response


@app.route('/dashboard')
def dashboard():
    try:
        verify_jwt_in_request()  # Verifica il token
        user = get_jwt_identity()  # Ottieni l'email dal token

        return render_template('dashboard.html', user=user)
    except Exception as e:

        flash("Errore access_token_cookie. Effettua nuovamente il login.")
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
