<img width="300" height="512" alt="DigitAIR" src="https://github.com/user-attachments/assets/1e9a23a8-a4c2-46bd-b907-5d0fec6c5426" />

## Descrizione del progetto
Il controllo della qualità dell’aria rappresenta una delle priorità ambientali più importanti del nostro tempo. Con l’intensificarsi dell’urbanizzazione, 
dell’industrializzazione e dei cambiamenti climatici, il monitoraggio preciso e tempestivo degli inquinanti atmosferici è diventato fondamentale per la tutela della
salute pubblica e la sostenibilità ambientale.  
Per affrontare questa sfida, l’evoluzione tecnologica degli ultimi decenni ha reso possibile lo sviluppo di sistemi di monitoraggio più capillari e
in grado di fornire i dati in tempo reale. Nel contesto territoriale pugliese, il progetto **"DigitAIR"** è stato sviluppato per superare i limiti dei tradizionali 
sistemi di monitoraggio, grazie all’implementazione di tecnologie innovative come l’Internet of Things (IoT) e l’Intelligenza Artificiale (AI).
Il progetto è stato concepito con un’architettura che consente la realizzazione di una rete di monitoraggio ad alta densità, offrendo una soluzione integrata, 
intuitiva, economicamente sostenibile e capace di garantire la massima trasparenza dei dati.  
Un aspetto fondamentale della soluzione proposta riguarda lo sviluppo di un sistema di visualizzazione dei dati accessibile a tutti. La piattaforma, caratterizzata da
un’interfaccia intuitiva e user-friendly, offre strumenti di visualizzazione intuitivi, mappe interattive per ogni inquinante e funzionalità di analisi storica
dei dati, rendendo le informazioni ambientali comprensibili e utilizzabili anche da utenti non specializzati. Particolare attenzione è stata dedicata al settore
accademico e alla pubblica amministrazione: per gli studenti universitari, i ricercatori e gli enti pubblici non solo è garantito l’accesso gratuito dei dati
raccolti consultando le mappe, ma anche l’utilizzo di funzionalità avanzate di simulazione. Queste includono modelli predittivi per valutare l’impatto 
attuale e futuro dell’inquinamento sulla salute e strumenti per stimare la riduzione degli inquinanti in seguito ad interventi di forestazione urbana.

---

## Architettura del sistema
Il sistema è progettato con un approccio modulare per garantire robustezza,scalabilità e manutenibilità, suddividendo le responsabilità tra Edge Device,
Front-end Web e Back-end, il quale è stato sviluppato secondo un’architettura a microservizi per favorire indipendenza dei componenti.

<img width="2083" height="915" alt="Architettura" src="https://github.com/user-attachments/assets/30c6c601-d99f-47ed-bbdf-bec2b0797d4c" />

Le principali componenti in cui si articola in sistema sono:  
#### User Service
Il microservizio User Service gestisce gli utenti del sistema, occupandosi di registrazione, autenticazione, gestione degli account e dei domini affiliati 
da parte dell’Admin. Utilizza token JWT per garantire un accesso sicuro alle risorse e interagisce con il Notification Service per l’invio di email.

#### Notification
Il microservizio gestisce l’invio delle email e comunica con il microservizio UserService tramite il protocollo AMQP, implementato con RabbitMQ.

#### Smartbox
La Smartbox è un dispositivo basato su ESP32 DevKit-C con sensori per il rilevamento degli inquinanti. Il microcontrollore, connesso alla rete, pubblica 
sul relativo topic le misure al minuto 50 di ogni ora affichè vengano salvate su un microservizio registrato al broker MQTT e gestisce eventuali disconnessioni
o malfunzionamenti tramite messaggi e API dedicate.

#### Device Indexer
Il microservizio Device Indexer mantiene il registro dei dispositivi, traccia lo stato di connessione, riceve e inoltra le misurazioni al Data Processor. 
Inoltre espone API per la gestione dei dispositivi e la loro disconnessione in caso di anomalie.

#### Data Processor
Il Data Processor si occupa direttamente del post processing dei dati, della generazione delle immagini e della gestione delle simulazioni. Esegue interpolazioni 
per generare mappe di distribuzione degli inquinanti e supporta simulazioni ambientali e sanitarie, fornendo inoltre API per l’accesso alle immagini e metriche.

#### Client per simulazioni
Un client Python simula l’invio concorrente di misurazioni da più dispositivi, generando dati realistici basati sulla distribuzione geografica delle province pugliesi.

#### Gateway
I microservizi sono stati connessi al frontend utilizzando KrakenD, un gateway con configurazione basata su JSON

#### Frontend
L’interfaccia web permette agli utenti di visualizzare le mappe degli inquinanti sull’intero territorio pugliese o, a scelta, solo su Lecce. In base al ruolo, gli utenti
possono eseguire simulazioni, mentre la gestione dell’applicazione è riservata esclusivamente all’Admin.

---

Di seguito viene fornita una descrizione dettagliata della componente implementata nella repository corrente.
## Device Processor
Il microservizio si occupa dell’elaborazione dei dati grezzi sia utilizzando tecniche classiche che algoritmi di intelligenza artificiale.
- ricevere i dati via AMPQ da indexer
- interpolare i dati per ricavare le mappe
- eseguire le simulazioni richieste dall’utente

#### Recezione dei dati
I dati vengono ricevuti via Celery tramite AMPQ. Alla recezione il microservizio salva i dati, con l’orario associato arrotondato all’ora intera successiva

#### Interpolazione dei dati
Ogni ora vengono recuperati i dati dell’ora precedente e viene eseguito, mediante un regressore gaussiano non parametrico, un processo di interpolazione
che ricava dai punti di misura, una distribuzione più densa di inquinante. La griglia di dati viene quindi utilizzata per ricavare un’immagine. Il microservizio 
si occupa di salvare in memoria l’immagine e, nel DB, i metadati dell’immagine (path, timestamp ecc.). Viene quindi esposta un’API che viene chiamata lato frontend per il recupero dell’immagine.

#### Simulazioni
Vengono messe a disposizione anche delle API per eseguire delle simulazioni. In particolare è possibile:
- simulare l’assorbimento di un numero di alberi definito dall’utente
- simulare l’impatto dell’inquinamento atmosferico sulla salute pubblica

Nella prima un numero di alberi, una data e delle coordinate (che rappresentano i due estremi di un rettangolo geografico) vengono fornite dall’utente.
Lo stesso algoritmo che esegue l’interpolazione degli inquinanti calcola una predizione sui valori di inquinanti assorbiti dal gruppo di alberi. La griglia delle
predizioni viene poi normalizzata rispetto la media e sottratta alle predizioni degli inquinanti per la data selezionata.
Viene creata una serie di immagini, compresse in un archivio, che l’utente scarica sulla propria macchina.  
Nella simulazione in ambito health, l’utente può visualizzare una mappa che evidenzia le aree in cui l’inquinamento atmosferico ha il maggiore impatto
sulla salute, sulla base delle misurazioni più recenti degli inquinanti. Inoltre, è possibile generare la stessa mappa per una data futura, utilizzando le predizioni
di un modello di rete neurale precedentemente addestrato.

#### Metriche ed Healthcheck
In aggiunta, il microservizio espone un’API che traccia a livello temporale il valore dell’inquinante su tutta la puglia, ed un’API per controllare lo stato di
connessione del microservizio.
