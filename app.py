from datetime import timedelta, datetime
import time
import bleach
import re
import os
import json
import random
import requests
from flask import Flask, request, jsonify, make_response, render_template, redirect, url_for, get_flashed_messages, session, flash
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, create_access_token, verify_jwt_in_request, get_jwt_identity, decode_token, \
    jwt_required
from utils import *

app = Flask(__name__)

# Configurazione delle impostazioni per JWT (JSON Web Token) nei cookie
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'fallback_secret_key')
app.config['JWT_TOKEN_LOCATION'] = os.getenv('JWT_TOKEN_LOCATION', 'cookies')
app.config['JWT_ACCESS_COOKIE_NAME'] = os.getenv('JWT_ACCESS_COOKIE_NAME', 'access_token_cookie')
app.config['JWT_COOKIE_SECURE'] = os.getenv('JWT_COOKIE_SECURE', 'False').lower() == 'true'
app.config['JWT_COOKIE_HTTPONLY'] = os.getenv('JWT_COOKIE_HTTPONLY', 'False').lower() == 'true'
app.config['JWT_COOKIE_CSRF_PROTECT'] = os.getenv('JWT_COOKIE_CSRF_PROTECT', 'False').lower() == 'true'
app.config['JWT_COOKIE_SAMESITE'] = "Strict"

bcrypt = Bcrypt(app)
jwt = JWTManager(app)

@app.route('/')
def from_api():
    # URL per ottenere i dati relativi alle prime 50 CVE pubblicate nel 2025
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

    # Connessione al database per ottenere dati aggiuntivi da cvelist
    try:
        with db.cursor(dictionary=True) as cursor:
            cursor.execute("SELECT cveid, published, sourceIdentifier, description FROM cvelist")
            db_cve_data = cursor.fetchall()  # Ottieni tutte le righe dalla tabella cvelist
            # Aggiungi i dati del database alla lista cve_data
            for cve in db_cve_data:
                cve_data.append({
                    'id': cve['cveid'],
                    'published': cve['published'],
                    'sourceIdentifier': cve['sourceIdentifier'],
                    'description': cve['description']
                })
    except mysql.connector.Error as err:
        print(f"Errore nel recupero dei dati dal database: {err}")

    # Passa i dati al template
    return render_template('index.html', cve_data=cve_data)


@app.route('/fromfile')
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
            except Exception:
                flash("Sessione scaduta. Effettua nuovamente il login.")

    elif request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        try:
            # Connessione al database
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()

            if user and bcrypt.check_password_hash(user['password_hash'], password):

                # Genera un timestamp al momento della creazione del token
                timestamp = datetime.utcnow().isoformat()
                # Crea l'identity come combinazione di email + timestamp
                identity = f"{email}#{timestamp}"

                access_token = create_access_token(identity=identity, expires_delta=timedelta(minutes=20))
                flash("Accesso riuscito")
                response = make_response(redirect(url_for('dashboard')))  # ⬅️ Reindirizzamento
                response.set_cookie('access_token_cookie', access_token, httponly=True, secure=True, samesite="Strict", max_age=1200)
                return response
            else:
                flash("Credenziali non valide")
                return redirect(url_for('login'))
        except mysql.connector.Error as err:
            flash(f"Errore nel database: {err}", "danger")
            return redirect(url_for('login'))  # Ritorna alla pagina di login se c'è un errore con il database

    return render_template('login.html')


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

        # Verifica che la password rispetti i requisiti
        password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|<>]).{8,}$'

        if not re.match(password_pattern, password):
            flash("Controlla che la password inserita rispetti i requisiti previsti")
            return redirect(url_for('register'))
        try:
            # Connessione al database
            with db.cursor(dictionary=True) as cursor:
                # Controllo se l'email esiste già (uso query parametrizzate per prevenire SQL Injection)
                cursor.execute("SELECT email FROM users WHERE email = %s", (email,))
                if cursor.fetchone():
                    flash("Email già registrata")
                    return redirect(url_for('register'))

                # Hash della password
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

                # Inserimento del nuovo utente
                cursor.execute("INSERT INTO users (email, password_hash) VALUES (%s, %s)", (email, hashed_password))
                db.commit()

            flash("Registrazione completata")
            return redirect(url_for('login'))

        except mysql.connector.Error as err:
            # Gestione degli errori del database
            return jsonify({'message': f"Errore nel database: {err}"}), 500

@app.route('/logout')
def logout():
    response = make_response(redirect(url_for('login')))
    response.set_cookie('access_token_cookie', '', expires=0, httponly=True)
    flash("Logout effettuato con successo")
    return response


@app.route('/add_cve', methods=['GET', 'POST'])
def add_cve():

    token = request.cookies.get('access_token_cookie')

    if not token:
        flash("Devi effettuare il login per accedere a questa pagina.", "danger")
        return redirect(url_for('login'))

    try:
        verify_jwt_in_request()  # Verifico il token
    except Exception:
        flash("Sessione scaduta. Effettua nuovamente il login.", "warning")
        return redirect(url_for('login'))

    identity_token = get_jwt_identity()  # Ottiengo il token
    user_email = identity_token.split("#")[0]

    if request.method == 'POST':

        random_number = f"{random.randint(0, 99999):05d}"
        cve_id = f"CVE-2025-{random_number}"

        description = request.form.get('description')
        # Sanificazione dell'input usando bleach
        description = bleach.clean(description)  # Rimuove HTML potenzialmente pericoloso

        published = datetime.now().isoformat()  # Timestamp corrente

        try:
            # Connessione al database
            with db.cursor(dictionary=True) as cursor:
                cursor.execute("INSERT INTO cvelist (cveid, published, sourceIdentifier, description) VALUES (%s, %s, %s, %s)",(cve_id, published, user_email, description))
                db.commit()
            flash("CVE aggiunta con successo!", "success")
            return redirect(url_for('dashboard'))

        except mysql.connector.Error as err:
            flash("Si è verificato un errore. Riprova più tardi.", "danger")

    return render_template('add_cve.html', user=user_email)

@app.route('/dashboard')
def dashboard():
    try:
        verify_jwt_in_request()  # Verifica il token
        identity_token = get_jwt_identity()  # Ottiengo il token
        user = identity_token.split("#")[0]

        # Connessione al database e recupero delle CVE
        try:
            with db.cursor(dictionary=True) as cursor:
                # Query parametrizzata per evitare SQL injection
                cursor.execute("SELECT * FROM cvelist WHERE sourceIdentifier = %s", (user,))
                cve_data = cursor.fetchall()
        except mysql.connector.Error as err:
            flash(f"Errore nel database: {err}", "danger")
            return redirect(url_for('dashboard'))

        # Passa i dati al template
        return render_template('dashboard.html', user=user, cve_data=cve_data)

    except Exception:
        flash("Devi effettuare il login per accedere a questa pagina.", "danger")
        return redirect(url_for('login'))


if __name__ == '__main__':
    app.run(debug=True)
