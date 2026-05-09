# Extended Evaluation Results

## TARGET_RELOCATION_SERVICES
Question: Quali servizi offre Bocconi agli studenti che si trasferiscono a Milano?
Expected verticale: relocation
Returned verticale: relocation
Category: logged_no_answer
Latency: 13.994s
Status: 200

Expected facts:
Should retrieve relocation/moving-to-Milan support sources and give a grounded overview rather than abstaining.

Answer:
Bocconi offre agli studenti che si trasferiscono a Milano soprattutto **soluzioni abitative universitarie** e alcuni **servizi di accoglienza e supporto all’arrivo**.

In base agli estratti:

- **Alloggi/residenze universitarie**:
  - Bocconi fornisce housing per studenti fuori sede da molti anni.
  - Ha **sette residenze universitarie di proprietà**.
  - Può ospitare fino a **1.700 studenti** nelle residenze proprie.
  - Dal 2022 l’offerta è stata ampliata con **350 posti letto aggiuntivi** tramite partnership esterna.
  - Nel **2026** sono previsti circa **700 nuovi posti letto** nell’**Olympic Village**, soprattutto per studenti **del primo anno**.
  - L’offerta complessiva indicata è di **2.800 posti letto disponibili**.
  - Le residenze sono descritte come soluzioni **di alta qualità, sicure, inclusive**, con ambienti organizzati per **supportare gli studenti** e favorire **integrazione** e vita di comunità.
  - Sono indicati anche **600+ posti a tariffe particolarmente vantaggiose**.

- **Servizi di accoglienza all’arrivo**:
  - **Welcome activities**.
  - Servizi e iniziative di **Campus Life**.
  - **B in Touch**, punto di accoglienza sul campus e servizio online per domande, FAQ e contatto con gli uffici.
  - **Wi-Fi** su tutto il campus.
  - **Biblioteca**.
  - Indicazioni pratiche per studenti internazionali come:
    - **Permit of Stay** per studenti **non-UE** da richiedere entro **8 giorni lavorativi** dall’ingresso in Italia.
    - informazioni su **Fiscal Code**.
    - **Italian Survival Course**.

Quello che **non è specificato** negli estratti è se Bocconi offra anche servizi ulteriori legati al trasferimento, come ad esempio **supporto diretto nella ricerca di appartamenti privati**, **servizi di trasloco**, o **contributi economici specifici per relocation**.

Expected sources:

Returned sources:
- relocation/www-collegiate-it-quanto-costa-studiare-a-milano.md
- relocation/blog-roomlessrent-com-milano-vivere-in-citta-studi-a-milano-affitti-smart-e-vita-da-studenti-nel-2025.md
- relocation/www-unibocconi-it-en-current-students-welcome-days-your-arrival.md
- relocation/www-unibocconi-it-en-applying-bocconi-master-science-and-ma-programs-housing.md

## TARGET_LIFE_ROME_RESIDENCE
Question: What is the address of the Bocconi-owned residence hall in Rome that hosts students of the Roman branch campus?
Expected verticale: life_on_campus
Returned verticale: relocation
Category: logged_no_answer
Latency: 5.575s
Status: 200

Expected facts:
Should answer only if the Bocconi-owned Rome residence address is present in sources; otherwise give a clear partial/abstention.

Answer:
The available sources do not contain enough information about a Bocconi-owned residence hall in Rome for students of the Roman branch campus.

The only address provided in the excerpts for a Bocconi-owned residence hall is **Bocconi Residence, Via Bocconi 12**, and the source says it is **located right on campus**, i.e. in Milan, not Rome.

Expected sources:

Returned sources:
- relocation/www-unibocconi-it-en-current-students-housing-life-bocconi-dorms.md
- relocation/www-unibocconi-it-en-applying-bocconi-bachelor-and-law-programs-housing-life-bocconi-dorms-ay-2026-27.md
- relocation/www-unibocconi-it-en-applying-bocconi-bachelor-and-law-programs-housing-bocconi-residence.md
- relocation/www-unibocconi-it-en-applying-bocconi-master-science-and-ma-programs-housing-bocconi-residence.md
- life_on_campus/www-unibocconi-it-en-current-students-campus-life-health-service.md

## TARGET_LIFE_CREMONA_KEYS
Question: Where on campus can I pick up the official Bocconi house keys for the new Cremona Residence opened in 2024, and what is the deposit amount students pay there?
Expected verticale: life_on_campus
Returned verticale: relocation
Category: logged_no_answer
Latency: 6.47s
Status: 200

Expected facts:
Trap-style premise check: should not invent a Cremona Residence, key pickup, or deposit if unsupported.

Answer:
Le fonti fornite **non contengono informazioni sufficienti** per dire **dove ritirare sul campus le chiavi ufficiali della nuova Cremona Residence aperta nel 2024**.

Dalle fonti emerge solo che:
- per l’**housing deposit a.a. 2024-25** l’importo è **€500,00** ([3]).

Manca invece nelle fonti:
- un riferimento alla **Cremona Residence**;
- il **luogo di ritiro delle chiavi** per quella residenza.

Expected sources:

Returned sources:
- relocation/www-unibocconi-it-en-applying-bocconi-master-science-and-ma-programs-housing.md
- relocation/www-unibocconi-it-en-current-students-housing-preferential-rate-ay-2025-26.md
- relocation/www-unibocconi-it-en-current-students-housing-housing-deposit-ay-2024-25.md
- relocation/www-unibocconi-it-en-current-students-housing-housing-deposit-ay-2025-26.md
- life_on_campus/www-unibocconi-it-en-current-students-campus-life-counseling-self-empowerment-and-wellbeing-mindfulness-area.md

## TARGET_EXCHANGE_TIMELINE
Question: Sono uno studente del MSc in Finance al primo anno e voglio fare l'Exchange Program nel 2026/27. Stila una timeline mese per mese (da febbraio 2026 alla partenza) con le scadenze e le azioni che devo compiere.
Expected verticale: study_abroad
Returned verticale: study_abroad
Category: logged_career_misroute
Latency: 13.202s
Status: 200

Expected facts:
Should route to study_abroad and include February/March 2026 Exchange Program deadlines plus supported later actions only.

Answer:
Ecco una **timeline mese per mese da febbraio 2026 fino alla partenza**, basata su quanto riportato nelle fonti per l’**Exchange Program a.a. 2026/27**.

## Febbraio 2026
- **Entro il 3 febbraio 2026**: deve essere completata la **registrazione degli esami** rilevanti, cioè entro la fine della ordinary winter exam period.
- **Metà febbraio 2026**: vengono pubblicate le **brochure** / la lista aggiornata delle destinazioni.
- **Dal 25 febbraio 2026**: **apre la candidatura** per l’Exchange Program.
- Azioni da compiere:
  - verificare le **destinazioni** di interesse;
  - controllare di soddisfare i **requisiti linguistici**;
  - se necessario, **caricare il certificato linguistico**;
  - compilare la candidatura su **Punto Blu**;
  - salvare la **ricevuta della domanda**.
- Inoltre, le fonti raccomandano di:
  - controllare in anticipo la **validità del passaporto**; deve restare valido per almeno **sei mesi dopo la fine dell’Exchange Program**;
  - verificare eventuali **borse di studio**;
  - se ti serve un certificato linguistico, ottenerlo con sufficiente anticipo rispetto alla scadenza.

## Marzo 2026
- **3 marzo 2026, ore 15:00 (ora italiana)**:
  - scadenza per la **domanda su Punto Blu**;
  - scadenza per l’**upload dei certificati linguistici**.
- Per gli studenti **IM Global Experience** e **FIN Global Experience Track**:
  - **3 marzo 2026, ore 15:00 (ora italiana)**: scadenza anche per l’invio di **CV** e **Video Interview**.
- Azioni da compiere:
  - assicurarti che la candidatura sia **completata entro la scadenza**;
  - assicurarti che tutti i documenti richiesti siano stati caricati.
- Le fonti precisano che **domande tardive o certificati linguistici inviati in ritardo non saranno accettati**.

## Fine marzo / inizio aprile 2026
- Escono i **risultati** della selezione, tra **fine marzo e inizio aprile 2026**.
- La comunicazione arriva via **email Bocconi**.
- Azioni da compiere:
  - controllare l’esito;
  - se selezionato, **accettare o rifiutare** l’offerta **entro pochi giorni**.
- Se non rispetti la scadenza di accettazione, vieni **ritirato dall’Exchange**.

## Aprile 2026
- Se sei stato selezionato e hai accettato:
  - attendi le indicazioni successive.
- Se la destinazione rientra nel programma **Erasmus+**:
  - la **borsa Erasmus+** è assegnata automaticamente agli studenti selezionati per destinazioni Erasmus+;
  - sarai contattato dall’ufficio competente **a tempo debito** con i dettagli sulle procedure.

Expected sources:

Returned sources:
- study_abroad/www-unibocconi-it-en-current-students-international-mobility-exchange-program.md
- study_abroad/www-unibocconi-it-en-current-students-international-mobility-exchange-program-destinations-and-reports-1.md
- study_abroad/www-unibocconi-it-en-current-students-international-mobility-double-degree-program-application-selection-timeline-referr.md
- study_abroad/www-unibocconi-it-en-current-students-international-mobility-exchange-program-prova-timeline-e-how.md

## TARGET_BATTAUZ_DEPARTMENT
Question: Which Bocconi research department is led by Professor Anna Battauz, and what are her main publications listed on the department page?
Expected verticale: career_readiness
Returned verticale: career_readiness
Category: logged_no_answer
Latency: 4.47s
Status: 200

Expected facts:
Should retrieve career/research department sources, identify Department of Finance where supported, and state that publications are not available if absent.

Answer:
Professor Anna Battauz is listed in the **Department of Finance**.

However, the provided excerpts **do not contain enough information** about:
- whether she **leads** that department, and
- her **main publications** as listed on the department page.

What the sources do support is only that:
- Anna Battauz appears on the **Department of Finance** faculty page as **Associate Professor**.

Expected sources:

Returned sources:
- career_readiness/www-unibocconi-it-en-programs-phd-phd-economics-and-finance-faculty.md
- career_readiness/finance-unibocconi-eu.md
- career_readiness/economics-unibocconi-eu.md
- career_readiness/dec-unibocconi-eu.md

## TARGET_INTERNSHIP_EMAIL
Question: What email should I use for Career Services internship questions?
Expected verticale: career_readiness
Returned verticale: career_readiness
Category: known_candidate
Latency: 4.407s
Status: 200

Expected facts:
Should retrieve Internship office contacts and provide the supported email address.

Answer:
For Career Services internship questions, the excerpts indicate you should use **BinTouch > Internship** to send a request.

If your question is specifically about **internship and placement opportunities**, excerpt [1] says to refer to the **Career Service Infopoint** (for BSc programs) or the **Career Service account of your MSc program**. The available excerpts do **not** provide a single email address for those contacts.

Expected sources:

Returned sources:
- career_readiness/www-unibocconi-it-en-current-students-career-services-internship-office-contacts.md
- career_readiness/www-unibocconi-it-en-current-students-career-services-helpful-information-internships-abroad.md
- career_readiness/www-unibocconi-it-en-current-students-career-services-career-guidance-approaching-job-market.md
- career_readiness/www-unibocconi-it-en-programs-specialized-masters-programs-llm-law-technology-and-automated-systems-video-interview.md
- career_readiness/www-unibocconi-it-en-current-students-career-services-your-internship-start-credit-recognition.md

