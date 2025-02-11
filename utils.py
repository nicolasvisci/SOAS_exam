import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()  # Carica variabili d'ambiente dal file .env

# Impostazioni per la connessione a MySQL
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

cursor = db.cursor()
