# Documentazione Sicurezza delle Architetture Orientate ai Servizi

# CVE Tracker

- Studente: Visci Nicolas

Il progetto ha previsto la realizzazione di una Web app che permette la visualizzazione tramite l'API del National Institute of Standards and Technology (NIST), delle prime 50 CVE pubblicate nel 2025. Tramite autenticazione con Token JWT, è permesso aggiungere nuove CVE.
La sicurezza del servizio implementato è garantita dall'utilizzo di Protocollo HTTPS, sul quale i dati viaggiano cifrati, e l'utilizzo di Token JWT per garantire l'autenticità degli utenti.

## Principali Tecnologie utilizzate

- MySQL Database
- PyCharm / Python
- HTML / CSS /Javascript
- Flask
- Ngrok

## Architettura del servizio

L'architettura REST è uno stile architetturale per progettare servizi web. Si basa su principi e vincoli che garantiscono semplicità, scalabilità e interoperabilità tra sistemi.

## Passi per l'installazione - Da completare

- Installazione requirements
- Configurare MySQL Database 
- Avviare server ngrok
- Avviare web app

## Configurazione ambiente - Ngrok

Ngrok è uno strumento che consente di esporre server o applicazioni in esecuzione localmente su internet tramite un tunnel sicuro. 
È particolarmente utile durante lo sviluppo per testare servizi.

Caratteristiche principali:
- Fornisce un URL pubblico, accessibile da qualsiasi dispositivo connesso a internet, che inoltra le richieste al server locale.
- Supporta connessioni HTTPS, garantendo che i dati inviati attraverso il tunnel siano protetti durante il transito.
- Semplice da configurare e funziona senza modificare il firewall o la rete.

<h3>ISTRUZIONI PER INSTALLARE E CONFIGURARE NGROK:</h3>

1. Visitare il sito: https://ngrok.com/ e registrarsi.
 
Dopo la registrazione su ngrok, viene fornito un Authtoken (un codice alfanumerico unico). Questo token serve per autenticare l'utente e abilitare l'accesso alle funzionalità di ngrok, come l'utilizzo di URL persistenti o altre opzioni avanzate.

2. Scaricare l'eseguibile ngrok.exe ed aggiungerlo alle variabili d'ambiente in modo da poter eseguire i comandi successivi senza problemi:
  - Aggiungere il percorso di ngrok.exe manualmente alle variabili di ambiente Path,
  - in alternativa, aprire il prompt dei comandi windows e digitare
    `setx /M PATH "%PATH%;<PATH_TO_NGROK>"`  ad esempio :
    `setx /M PATH "%PATH%;C:\tools\ngrok"`

3. Dopo aver aggiunto ngrok alle variabili d'ambiente, configurarlo con il token ottenuto durante la fase di registrazione, eseguire quindi il seguente comando:
`ngrok config add-authtoken <YOUR_AUTHTOKEN>`

4. Per avviare il servizio di esposizione sulla porta 5000 eseguire sul prompt:
`ngrok http 5000`

5. Una volta avviato il servizio si otterrà una schermata tipo:
   
![ngrok](https://github.com/user-attachments/assets/983735e3-da4f-46e0-b1ac-f2dd26a12d3c)
   
<b>ATTENZIONE:</b> Ogni volta che ngrok viene stoppato, bisogna rieseguire il comando dell <b>punto 4</b>

## Configurazione MySQL Database - Da completare

Descrizione breve di MySQL

<b> QUERY </b>
descrizione di QUERY

<h3> CONFIGURAZIONE DATABASE:</h3>
1. 



## Flask

Flask è un framework web leggero, più precisamente un microframework, open-source per il linguaggio di programmazione Python. È progettato per facilitare la creazione di applicazioni web, offrendo gli strumenti di base necessari per gestire richieste HTTP, routing, gestione delle sessioni e rendering di template.

Flask è particolarmente utile per:

- <b>Sviluppare API web:</b> grazie alla sua semplicità e flessibilità è molto usato per costruire API RESTful.
- <b>Creare siti web dinamici:</b> Consente di generare pagine web dinamiche, interagendo con il database, gestendo la logica di business e rendendo il contenuto personalizzato per gli utenti.

Vantaggi nell'utilizzo di Flask

- <b>Flessibilità:</b> Essendo un microframework, Flask non impone una struttura rigida e consente agli sviluppatori di scegliere le librerie o gli strumenti che meglio si adattano al progetto. È possibile aggiungere facilmente estensioni per funzionalità come la gestione delle sessioni, la convalida dei moduli e l'autenticazione.

- <b>Scalabilità:</b> Sebbene sia un framework leggero, Flask è abbastanza scalabile per supportare applicazioni più complesse. Può essere utilizzato per progetti di piccole dimensioni così come per applicazioni più grandi, con una gestione del codice che resta relativamente semplice.

## Diagramma delle Architetture - Da completare

## Controlli di Sicurezza - Da completare

- SQL Injection

- Cross-Site Scripting (XSS)

- Sicurezza dei Cookie

## Fonti e Riferimenti

- ngrok - https://ngrok.com/

- Flask - https://flask.palletsprojects.com/en/stable/

- JWT - https://www.ionos.it/digitalguide/siti-web/programmazione-del-sito-web/json-web-token-jwt/