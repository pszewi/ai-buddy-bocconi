# Extended Evaluation Results

## 03
Question: Confrontando i bus diretti da Malpensa a Milano Centrale tra i vettori documentati (Autostradale/Malpensa Bus Express, Terravision, Flibco, FlixBus): qual è il prezzo di partenza più basso indicato per ciascun vettore?
Expected verticale: relocation
Returned verticale: relocation
Category: computational
Latency: 11.057s
Status: 200

Expected facts:
Il prezzo di partenza più basso documentato per i bus diretti Malpensa - Milano Centrale è, a regime: Autostradale/Malpensa Bus Express ~10 EUR (online); Terravision ~10 EUR (online, talvolta da 8 EUR in promo); Flibco da ~9.99 EUR; FlixBus da ~9.99 EUR (varia per data e fascia oraria). Tutti e quattro i vettori partono da prezzi nel range 8-12 EUR a tratta in advance booking.

Answer:
Per i collegamenti diretti documentati verso **Milano Centrale**, il **prezzo di partenza più basso indicato** è:

- **Autostradale / Malpensa Bus Express**: **da 8 euro**  
  - Nell’estratto compare anche un link promozionale con **“Da 4,99€ a persona”** per il bus T1/T2 ↔ Stazione Centrale.
- **Terravision**: **da 6 euro**  
  - Il testo dice: **“a partire da 6-10 euro”**.
- **Flibco**: **da circa 8 euro**  
  - Il testo dice: **“a partire da circa 8-10 euro”**.
- **FlixBus**: **da circa 6 euro**  
  - Però l’estratto dice solo che collega Malpensa con varie città e che i prezzi variano per rotta; **non specifica in modo esplicito un collegamento diretto Malpensa–Milano Centrale**.

Quindi, tra i valori riportati negli estratti, il più basso è:
- **4,99€** per **Autostradale** se si considera il prezzo del link promozionale riportato nell’estratto;
- altrimenti, nei testi descrittivi principali, i più bassi sono **6€** per **Terravision** e **circa 6€** per **FlixBus**.

Expected sources:

Returned sources:
- relocation/www-aeroporto-net-aeroporto-milano-malpensa-collegamenti-aeroporto-milano-malpensa.md
- relocation/www-aeroporto-net-aeroporto-milano-linate-collegamenti-aeroporto-milano-linate.md

