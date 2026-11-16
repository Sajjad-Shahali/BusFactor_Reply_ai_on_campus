"""Interface language (English / Italiano).

`t("English text")` returns the Italian text when Italian is selected and the English text otherwise
(or when a string has no translation yet), so a missing entry never breaks a page. Only the interface
is translated: decision cards, questions and feedback stay in the language of the project documents,
the demo data or the model, and answers can be written in any language (grammar never lowers a score).
"""
from __future__ import annotations

import threading

LANGS = {"en": "English", "it": "Italiano"}
# Streamlit runs each session's script in its own thread: a thread-local keeps one session's language from leaking
# into another session of the same server process. set_lang() is called at the start of every run.
_state = threading.local()


def set_lang(code: str) -> None:
    _state.lang = code if code in LANGS else "en"


def get_lang() -> str:
    return getattr(_state, "lang", "en")


def t(text: str) -> str:
    return IT.get(text, text) if get_lang() == "it" else text


IT = {
    # sidebar
    "Your grade is shared. Your understanding shouldn't be isolated.":
        "Il voto è condiviso. La comprensione non dovrebbe essere isolata.",
    "Project": "Progetto",
    " · synthetic demo": " · demo sintetica",
    "DEMO DATA — synthetic": "DATI DEMO — sintetici",
    "Fictional project, members, answers and consent.": "Progetto, membri, risposte e consensi fittizi.",
    "Who are you? (demo identity switch, not a login)": "Chi sei? (cambio identità demo, non un login)",
    "Who are you?": "Chi sei?",
    "Showing only this member's answers · no login yet": "Mostra solo le risposte di questo membro · nessun login",
    "Signed in with an access code": "Accesso con codice personale",
    "Your access code": "Il tuo codice di accesso",
    "Unlock": "Sblocca",
    "That code does not match.": "Il codice non corrisponde.",
    "Too many attempts. Wait 30 seconds.": "Troppi tentativi. Attendi 30 secondi.",
    "Ask the project creator for your personal code.": "Chiedi il tuo codice personale a chi ha creato il progetto.",
    "Enter your access code in the sidebar to continue.":
        "Inserisci il tuo codice di accesso nella barra laterale per continuare.",
    "Go to": "Vai a",
    "Overview": "Panoramica",
    "1. Project Setup": "1. Impostazione progetto",
    "2. Private Check": "2. Verifica privata",
    "3. Team Coverage": "3. Copertura del team",
    "4. Teach Each Other": "4. Insegnatevi a vicenda",
    "5. Defense Retest": "5. Nuovo test",
    "6. Evidence & Limits": "6. Evidenze e limiti",
    "The demo at a glance": "La demo in sintesi",
    "Key decisions and sources": "Decisioni chiave e fonti",
    "Your own questions": "Le tue domande",
    "Who can explain what": "Chi sa spiegare cosa",
    "Peer-teaching missions": "Missioni di insegnamento tra pari",
    "New question, no hints": "Nuova domanda, senza aiuti",
    "Sources, log, limits": "Fonti, registro, limiti",
    "Reset demo data": "Ripristina dati demo",
    "Restores the synthetic demo to its starting point (coverage 1/5). Everything done in the demo is lost. "
    "Your own projects are not touched.":
        "Riporta la demo sintetica al punto di partenza (copertura 1/5). Tutto ciò che hai fatto nella demo va "
        "perso. I tuoi progetti non vengono toccati.",
    "Reset the demo now": "Ripristina la demo ora",
    # grading mode line
    "Live model grading: formative feedback that can be wrong, never an official grade.":
        "Valutazione con modello reale: feedback formativo che può essere sbagliato, mai un voto ufficiale.",
    "Offline demo keyword rubric on synthetic data: a stand-in, not a validated grader.":
        "Rubrica offline a parole chiave su dati sintetici: un sostituto, non un valutatore validato.",
    "Offline: questions come from templates and answers wait for human review, with no automatic scores.":
        "Offline: le domande vengono da modelli e le risposte aspettano la revisione umana, senza punteggi automatici.",
    # stepper / generic
    "Setup": "Impostazione", "Check": "Verifica", "Coverage": "Copertura", "Teach": "Insegna", "Retest": "Nuovo test",
    "Evidence": "Evidenze",
    "not measurable": "non misurabile", "covered": "coperto",
    "{a} of {b} confirmed decisions have been assessed": "{a} su {b} decisioni confermate sono state valutate",
    " · {n} not confirmed yet, so not counted": " · {n} non ancora confermate, quindi non contate",
    # status pills
    "Covered": "Coperta", "Single point of failure": "Punto singolo di fallimento",
    "No explainer yet": "Nessuno sa spiegarla", "Not assessed": "Non valutata", "Verified": "Verificata",
    "Needs review": "Da rivedere", "No source": "Senza fonte", "Waiting for consent": "In attesa di consenso",
    "Accepted": "Accettata", "Retest not passed yet": "Nuovo test non ancora superato",
    "Transfer verified": "Trasferimento verificato", "Ask the TA": "Chiedi al tutor",
    "Demonstrated": "Dimostrata", "Needs practice": "Da esercitare",
    "Not scored: needs human review": "Non valutata: serve revisione umana", "Not confirmed": "Non confermata",
    "Owner check · no hints": "Verifica del responsabile · senza aiuti",
    # overview
    "Synthetic demo": "Demo sintetica", "Your project": "Il tuo progetto",
    "You split the work.<br><em>Don't split the understanding.</em>":
        "Avete diviso il lavoro.<br><em>Non dividete la comprensione.</em>",
    "BusFactor finds the project decisions only one teammate can explain, sets up peer teaching between teammates, "
    "and checks with a new question that the knowledge really moved.":
        "BusFactor trova le decisioni di progetto che sa spiegare un solo compagno, organizza l'insegnamento tra "
        "compagni e verifica con una nuova domanda che la conoscenza sia davvero passata.",
    "Decision coverage": "Copertura delle decisioni", "Single points of failure": "Punti singoli di fallimento",
    "Teaching missions": "Missioni di insegnamento", "Decisions verified": "Decisioni verificate",
    "quotes checked on their page": "citazioni controllate nella loro pagina",
    "<b>+{n}</b> since start": "<b>+{n}</b> dall'inizio", "started at {a}/{b}": "partita da {a}/{b}",
    "<b>−{n}</b> since start": "<b>−{n}</b> dall'inizio",
    "<b class=\"bad\">need a second explainer</b>": "<b class=\"bad\">serve un secondo che sappia spiegare</b>",
    "{n} proposed · {v} verified": "{n} proposte · {v} verificate",
    "Find the decisions": "Trova le decisioni", "Ask privately": "Chiedi in privato",
    "Spot the risk": "Individua il rischio", "Teach each other": "Insegnatevi a vicenda",
    "Check again": "Verifica di nuovo", "Done": "Fatto", "Up next": "Prossimo", "Waiting": "In attesa",
    "{n} of {m} cards verified against the report": "{n} schede su {m} verificate rispetto al report",
    "{n} decisions have private answers": "{n} decisioni hanno risposte private",
    "{n} decisions depended on one person": "{n} decisioni dipendevano da una persona",
    "{n} mission(s) accepted by both people": "{n} missione/i accettata/e da entrambe le persone",
    "{n} transfer(s) verified · coverage {a} → {b}": "{n} trasferimento/i verificato/i · copertura {a} → {b}",
    "Demo story": "Storia della demo",
    "All numbers come from the synthetic demo data and update live as you use the app.":
        "Tutti i numeri vengono dai dati demo sintetici e si aggiornano mentre usi l'app.",
    "All numbers come from this project's stored, consented evidence.":
        "Tutti i numeri vengono dalle evidenze salvate e consentite di questo progetto.",
    # setup page
    "Project Setup": "Impostazione del progetto",
    "The key decisions of the project. Each one is linked to the exact page it comes from.":
        "Le decisioni chiave del progetto. Ognuna è collegata alla pagina esatta da cui proviene.",
    "Start a new project": "Avvia un nuovo progetto",
    "Create project": "Crea progetto", "Project title": "Titolo del progetto", "Course": "Corso",
    "Team members, one name per line": "Membri del team, un nome per riga",
    "Project report (PDF, Markdown or text)": "Report del progetto (PDF, Markdown o testo)",
    "Team members ({n})": "Membri del team ({n})", "Add member": "Aggiungi membro",
    "Add a member (name)": "Aggiungi un membro (nome)", "Add decisions": "Aggiungi decisioni",
    "Add decision": "Aggiungi decisione", "Decision (what the team chose)": "Decisione (cosa ha scelto il team)",
    "Decisions": "Decisioni", "Confirmed": "Confermate", "Confirm card": "Conferma scheda",
    "Owner (who made this decision)": "Responsabile (chi ha preso la decisione)",
    "not declared": "non dichiarato", "Delete this project": "Elimina questo progetto",
    "Delete project": "Elimina progetto",
    "Type the project title to confirm": "Scrivi il titolo del progetto per confermare",
    "Access codes": "Codici di accesso", "Turn on access codes": "Attiva i codici di accesso",
    "Issue new codes": "Emetti nuovi codici",
    "Access codes are off: anyone using this app can switch to any member and read that member's answers. Turn them "
    "on before real students use it.":
        "I codici di accesso sono disattivati: chiunque usi l'app può passare a qualsiasi membro e leggerne le "
        "risposte. Attivali prima che lo usino studenti reali.",
    "This project uses access codes. Each member unlocks their own answers with a personal code; the review queue "
    "needs the reviewer code.":
        "Questo progetto usa i codici di accesso. Ogni membro sblocca le proprie risposte con un codice personale; "
        "la coda di revisione richiede il codice del revisore.",
    "New codes replace the old ones: everyone must unlock again. Type the project title to confirm.":
        "I nuovi codici sostituiscono i vecchi: tutti dovranno sbloccare di nuovo. Scrivi il titolo del progetto per "
        "confermare.",
    "Save these access codes now. They are shown only once and cannot be recovered.":
        "Salva ora questi codici di accesso. Vengono mostrati una sola volta e non si possono recuperare.",
    "Member": "Membro", "Access code": "Codice di accesso", "Reviewer code": "Codice del revisore",
    "I have saved the codes": "Ho salvato i codici",
    # private check
    "Private Check": "Verifica privata",
    "Questions about decisions you didn't make. Your answers and feedback are shown only to you as the selected "
    "member; there is no login yet, so anyone using this app can switch identity.":
        "Domande su decisioni che non hai preso tu. Risposte e feedback sono mostrati solo a te come membro "
        "selezionato; non c'è ancora un login, quindi chiunque usi l'app può cambiare identità.",
    "Questions about decisions you didn't make. Your answers and feedback are shown only to you after you unlock "
    "your account with your access code.":
        "Domande su decisioni che non hai preso tu. Risposte e feedback sono mostrati solo a te dopo aver sbloccato "
        "il tuo account con il codice di accesso.",
    "Scores are practice feedback, not grades. You can answer in English or Italian; grammar and language never "
    "lower the score.":
        "I punteggi sono feedback di allenamento, non voti. Puoi rispondere in inglese o in italiano; grammatica e "
        "lingua non abbassano mai il punteggio.",
    "My consent": "Il mio consenso", "Save my consent": "Salva il mio consenso",
    "I agree to be assessed (private questions and retests)":
        "Accetto di essere valutato (domande private e nuovi test)",
    "I am willing to mentor a teammate": "Sono disponibile a fare da mentore a un compagno",
    "I am willing to learn from a teammate": "Sono disponibile a imparare da un compagno",
    "Allow a human reviewer to read my answers that the model could not score (without my name)":
        "Permetto a un revisore umano di leggere le mie risposte che il modello non ha potuto valutare (senza il "
        "mio nome)",
    "Get my questions": "Ottieni le mie domande", "Start owner check": "Avvia la verifica del responsabile",
    "Verify a decision you own": "Verifica una decisione di cui sei responsabile",
    "To answer ({n})": "Da rispondere ({n})", "Answered ({n})": "Risposte ({n})",
    "Nothing open. Get new questions above.": "Niente da fare. Ottieni nuove domande qui sopra.",
    "Your answer": "La tua risposta", "Submit": "Invia",
    "You have not agreed to be assessed, so BusFactor will not ask or score you.":
        "Non hai accettato di essere valutato, quindi BusFactor non ti farà domande né ti assegnerà punteggi.",
    # coverage
    "Team Coverage": "Copertura del team",
    "How many decisions at least two of you can explain. Only counts are shown, never names or scores.":
        "Quante decisioni almeno due di voi sanno spiegare. Si mostrano solo conteggi, mai nomi o punteggi.",
    "Before": "Prima", "Now": "Ora", "when the project started": "all'avvio del progetto",
    "no change yet": "nessun cambiamento", "decisions only one person can explain": "decisioni che sa spiegare "
    "una sola persona",
    "{n} can explain it": "{n} sanno spiegarla", "Next:": "Prossimo passo:",
    "The ring fills as more decisions get a second person who can explain them.":
        "L'anello si riempie man mano che più decisioni hanno una seconda persona che sa spiegarle.",
    "Export": "Esporta",
    "Download team report (Markdown)": "Scarica il report del team (Markdown)",
    "Download decisions (CSV)": "Scarica le decisioni (CSV)",
    "The exports contain counts only: no names, answers or scores.":
        "Le esportazioni contengono solo conteggi: niente nomi, risposte o punteggi.",
    # missions
    "Teach Each Other": "Insegnatevi a vicenda",
    "For each decision only one person can explain, a teammate who understands it teaches one who doesn't.":
        "Per ogni decisione che sa spiegare una sola persona, un compagno che la capisce la insegna a uno che non la "
        "capisce.",
    "Find knowledge silos and propose missions": "Trova i silos di conoscenza e proponi missioni",
    "No missions yet. Press the button above.": "Ancora nessuna missione. Premi il pulsante qui sopra.",
    "Mentor": "Mentore", "Learner": "Studente",
    "You accepted. Waiting for the other person.": "Hai accettato. In attesa dell'altra persona.",
    "I agree to take part as {role}": "Accetto di partecipare come {role}",
    "Reminder: the teaching session for {d} was agreed {n} days ago. Do it, then take the retest (page 5).":
        "Promemoria: la sessione di insegnamento per {d} è stata concordata {n} giorni fa. Fatela, poi fai il nuovo "
        "test (pagina 5).",
    "Follow-up check due: you passed the retest for {d} {n} days ago. One new question shows whether it stuck.":
        "Verifica di richiamo in scadenza: hai superato il nuovo test per {d} {n} giorni fa. Una nuova domanda "
        "mostra se è rimasto.",
    # retest
    "Defense Retest": "Nuovo test",
    "After the teaching session, answer a new question on your own. No hints are available here.":
        "Dopo la sessione di insegnamento, rispondi da solo a una nuova domanda. Qui non ci sono aiuti.",
    "You have no teaching mission as a learner.": "Non hai nessuna missione come studente.",
    "Start a new independent question": "Avvia una nuova domanda indipendente",
    "Start the follow-up check": "Avvia la verifica di richiamo",
    # evidence
    "Evidence & Limits": "Evidenze e limiti",
    "Where every decision comes from, what the agent did, and what it can't do.":
        "Da dove viene ogni decisione, cosa ha fatto l'agente e cosa non può fare.",
    "Sources": "Fonti", "Action log": "Registro azioni", "Abstentions & blocked": "Astensioni e blocchi",
    "Limits": "Limiti", "Review queue": "Coda di revisione", "None yet.": "Nessuno per ora.",
    "Answers the model could not score wait here for a human. A reviewer sees only answers from members who agreed "
    "to human review, and never their names.":
        "Le risposte che il modello non ha potuto valutare aspettano qui una persona. Il revisore vede solo le "
        "risposte dei membri che hanno accettato la revisione umana, mai i loro nomi.",
    "Enter the reviewer code to open the queue.": "Inserisci il codice del revisore per aprire la coda.",
    "Nothing is waiting for review.": "Niente in attesa di revisione.",
    "Score": "Punteggio", "Feedback for the member (optional)": "Feedback per il membro (facoltativo)",
    "Save review": "Salva revisione", "Answer": "Risposta", "A good answer covers:": "Una buona risposta copre:",
    "Review saved.": "Revisione salvata.",
}

IT.update({
    # accessibility / coverage verdict
    "Text version of the map": "Versione testuale della mappa",
    "3D map of the decisions and who can explain them (text version below)":
        "Mappa 3D delle decisioni e di chi sa spiegarle (versione testuale qui sotto)",
    "Nothing has been assessed yet.": "Ancora nulla è stato valutato.",
    "Members can take a private check on the Private Check page.":
        "I membri possono fare una verifica privata nella pagina Verifica privata.",
    "1 decision depends on one person.": "1 decisione dipende da una sola persona.",
    "{n} decisions depend on one person.": "{n} decisioni dipendono da una sola persona.",
    "No decision depends on one person.": "Nessuna decisione dipende da una sola persona.",
    "Next: open Teach Each Other and propose missions.":
        "Prossimo passo: apri Insegnatevi a vicenda e proponi le missioni.",
    "Keep it fresh: practise a new 'what if' before the defense.":
        "Tienila allenata: esercitati su un nuovo «e se» prima della discussione.",
    "<b>+1</b> decision covered": "<b>+1</b> decisione coperta",
    "<b>+{n}</b> decisions covered": "<b>+{n}</b> decisioni coperte",
    "It is not confirmed or has no verified source, so it is not counted.":
        "Non è confermata o non ha una fonte verificata, quindi non viene contata.",
    "Review it in Project Setup.": "Rivedila in Impostazione progetto.",
    # empty states
    "No decisions yet": "Ancora nessuna decisione",
    "Add the project's key decisions below: each quote is checked against your document.":
        "Aggiungi qui sotto le decisioni chiave del progetto: ogni citazione viene controllata nel tuo documento.",
    "Nothing to answer right now": "Niente a cui rispondere ora",
    "Choose up to two decisions above and press \u201cGet my questions\u201d.":
        "Scegli fino a due decisioni qui sopra e premi «Ottieni le mie domande».",
    "No missions yet": "Ancora nessuna missione",
    "Press the button above and BusFactor pairs a mentor with a learner for every decision only one person can "
    "explain.":
        "Premi il pulsante qui sopra e BusFactor abbina un mentore a uno studente per ogni decisione che sa spiegare "
        "una sola persona.",
    "You have no teaching mission as a learner": "Non hai nessuna missione come studente",
    "A retest opens after a mentor and you both accept a mission on the Teach Each Other page.":
        "Il nuovo test si apre dopo che tu e un mentore accettate una missione nella pagina Insegnatevi a vicenda.",
    "Go to Teach Each Other": "Vai a Insegnatevi a vicenda",
    "Nothing is waiting for review": "Niente in attesa di revisione",
    "When a member who agreed to human review has an answer the model could not score, it appears here.":
        "Quando un membro che ha accettato la revisione umana ha una risposta che il modello non ha potuto valutare, "
        "compare qui.",
    # retest, simulator
    "Independent check · no hints": "Verifica indipendente · senza aiuti",
    "Attempt {n} of {m}": "Tentativo {n} di {m}", "Attempt {n}": "Tentativo {n}",
    "Defense simulator": "Simulatore di discussione",
    "A mock oral: a random question on one of your project's decisions, no hints. Practice only: it never changes "
    "team coverage.":
        "Un'interrogazione di prova: una domanda casuale su una decisione del tuo progetto, senza aiuti. Solo "
        "allenamento: non cambia mai la copertura del team.",
    "Ask me a question": "Fammi una domanda", "Send answer": "Invia risposta",
    "You have not agreed to be assessed, so the simulator is not available.":
        "Non hai accettato di essere valutato, quindi il simulatore non è disponibile.",
    "{n} answered in the simulator": "{n} risposte nel simulatore", "Result": "Risultato",
    # course material
    "Course material (optional)": "Materiale del corso (facoltativo)",
    "Lecture notes or slides of the course. When nobody can explain a decision, BusFactor points to the page that "
    "talks about it instead of a generic message.":
        "Appunti o slide del corso. Quando nessuno sa spiegare una decisione, BusFactor indica la pagina che ne parla "
        "invece di un messaggio generico.",
    "Add course files (PDF, Markdown or text)": "Aggiungi file del corso (PDF, Markdown o testo)",
    "Add course material": "Aggiungi materiale del corso",
    "Where your course material talks about it:": "Dove il materiale del corso ne parla:", "page": "pagina",
    "Download team report (PDF)": "Scarica il report del team (PDF)",
})


# ---- plain-language labels, guidance, session checklist, privacy, log (HCI pass)
IT.update({
    "Only 1 can explain it": "Solo 1 sa spiegarla", "2+ can explain it": "In 2+ sanno spiegarla",
    "Nobody can explain it yet": "Nessuno sa ancora spiegarla", "Retest: try again": "Nuovo test: riprova",
    "Confirmed: can explain it": "Confermato: sa spiegarla", "Confirmed: you can explain it": "Confermato: sai spiegarla",
    "Decisions only 1 person can explain": "Decisioni che sa spiegare 1 sola persona",
    "Since the start": "Dall'inizio",
    # pill tooltips
    "Only one member has shown they can explain this decision. If they are absent, nobody can defend it.":
        "Solo un membro ha dimostrato di saper spiegare questa decisione. Se è assente, nessuno può difenderla.",
    "At least two members have shown they can explain this decision, so the team does not depend on one person.":
        "Almeno due membri hanno dimostrato di saper spiegare questa decisione, quindi il team non dipende da una "
        "sola persona.",
    "Members were checked, but nobody has shown they can explain this decision yet.":
        "I membri sono stati verificati, ma nessuno ha ancora dimostrato di saper spiegare questa decisione.",
    "Nobody has answered a question on this decision yet. That is unknown, not failed.":
        "Nessuno ha ancora risposto a una domanda su questa decisione. È sconosciuto, non fallito.",
    "The learner explained the decision on a new question, with no hints.":
        "Lo studente ha spiegato la decisione su una nuova domanda, senza aiuti.",
    "The last retest answer was not complete. The learner can try a new question.":
        "L'ultima risposta del nuovo test non era completa. Lo studente può provare con una nuova domanda.",
    "The grader was not sure, so a person has to look at this answer.":
        "Il valutatore non era sicuro, quindi una persona deve guardare questa risposta.",
    # your next step
    "Your next step": "Il tuo prossimo passo", "Progress: step {n} of 6": "Avanzamento: passo {n} di 6",
    "Add and confirm the project's key decisions first.": "Aggiungi e conferma prima le decisioni chiave del progetto.",
    "Open Project Setup": "Apri Impostazione progetto", "Open Private Check": "Apri Verifica privata",
    "Open Teach Each Other": "Apri Insegnatevi a vicenda", "Open Defense Retest": "Apri Nuovo test",
    "Agree to be assessed to start your private check. You can withdraw at any time.":
        "Accetta di essere valutato per iniziare la verifica privata. Puoi ritirarti in qualsiasi momento.",
    "A teaching session on {d} is waiting for your OK.": "Una sessione di insegnamento su {d} aspetta il tuo OK.",
    "Hold your teaching session on {d}, then tick the steps off.":
        "Tieni la sessione di insegnamento su {d}, poi spunta i passaggi.",
    "Take your retest on {d}: a new question, no hints.": "Fai il nuovo test su {d}: una nuova domanda, senza aiuti.",
    "Follow-up check due on {d}: one new question shows whether it stuck.":
        "Verifica di richiamo su {d}: una nuova domanda mostra se è rimasto.",
    "You have {n} question(s) waiting for your answer.": "Hai {n} domanda/e in attesa di risposta.",
    "Take your private check: two short questions on decisions you did not make.":
        "Fai la verifica privata: due brevi domande su decisioni che non hai preso tu.",
    "{n} decision(s) can only be explained by one person: set up teaching sessions.":
        "{n} decisione/i sa spiegare una sola persona: organizza le sessioni di insegnamento.",
    "You are up to date. Practise with the defense simulator before the oral.":
        "Sei in pari. Allenati con il simulatore prima della discussione.",
    "Start the guided tour": "Avvia il tour guidato", "Decisions at a glance": "Decisioni in sintesi",
    "Show the 3D map (optional)": "Mostra la mappa 3D (facoltativa)",
    # private check
    "Questions about decisions you didn't make. Your answers and feedback are private to you.":
        "Domande su decisioni che non hai preso tu. Risposte e feedback sono privati.",
    "Show you can explain your own decision": "Dimostra di saper spiegare la tua decisione",
    "Start my question": "Avvia la mia domanda", "Your own decision · no hints": "La tua decisione · senza aiuti",
    "Solo question · no hints": "Domanda singola · senza aiuti",
    "Checking your answer…": "Controllo la tua risposta…", "Preparing a question…": "Preparo una domanda…",
    "Reading your report with the model… this can take a minute.":
        "Leggo il tuo report con il modello… può volerci un minuto.",
    "Your draft is saved while you move around. After you send it, you cannot edit it.":
        "La bozza viene salvata mentre ti sposti. Dopo l'invio non puoi modificarla.",
    "Not there yet. Ask your mentor to go through it again, then try a new question.":
        "Non ci sei ancora. Chiedi al mentore di rivederla con te, poi prova una nuova domanda.",
    # teaching session
    "Set up teaching sessions": "Organizza le sessioni di insegnamento",
    "Your teaching session": "La vostra sessione di insegnamento", "Conversation starters": "Spunti di conversazione",
    "Session held. The learner can take the retest now.": "Sessione svolta. Lo studente può fare il nuovo test.",
    "We held the session: tick everything": "Abbiamo fatto la sessione: spunta tutto",
    "Hold your teaching session first, then come back for the retest.":
        "Fate prima la sessione di insegnamento, poi torna per il nuovo test.",
    "We already did the session": "Abbiamo già fatto la sessione",
    # privacy panel
    "Who can see what?": "Chi può vedere cosa?",
    "Your answers, scores and feedback": "Le tue risposte, i punteggi e il feedback",
    "Only you, after you enter your access code.": "Solo tu, dopo aver inserito il codice di accesso.",
    "Only you (in this demo anyone can switch member, so it is synthetic data).":
        "Solo tu (in questa demo chiunque può cambiare membro, quindi sono dati sintetici).",
    "Team coverage and the exports": "Copertura del team ed esportazioni",
    "Everyone in the team, as counts only: no names, answers or scores.":
        "Tutto il team, solo come conteggi: niente nomi, risposte o punteggi.",
    "A teaching session": "Una sessione di insegnamento",
    "Only the mentor and the learner until both accept; then the team sees that it exists.":
        "Solo il mentore e lo studente finché entrambi accettano; poi il team vede che esiste.",
    "Answers the model could not score": "Risposte che il modello non ha potuto valutare",
    "A reviewer, and only if you agreed; never with your name.": "Un revisore, e solo se hai accettato; mai con il tuo nome.",
    "The action log": "Il registro delle azioni",
    "Shared project steps and your own steps; never another member's answers.":
        "Passaggi condivisi del progetto e i tuoi; mai le risposte di un altro membro.",
    # sidebar
    "View as": "Visualizza come", "Demo identity switch, not a login.": "Cambio identità demo, non un login.",
    "Demo identity switch, not a login: anyone can pick any member.":
        "Cambio identità demo, non un login: chiunque può scegliere qualsiasi membro.",
    "Keep me signed in on this device (7 days)": "Resta connesso su questo dispositivo (7 giorni)",
    "Adds a private token to this page's link. Anyone who has the link can open your answers until it expires, so "
    "do not share it.":
        "Aggiunge un token privato al link di questa pagina. Chiunque abbia il link può aprire le tue risposte "
        "finché non scade: non condividerlo.",
    "Sign out": "Esci", "Larger text": "Testo più grande",
    # log
    "Show technical details": "Mostra i dettagli tecnici", "Time": "Ora", "Who": "Chi", "What happened": "Cosa è successo",
    "Action": "Azione", "Detail": "Dettaglio",
    "The synthetic demo was loaded.": "È stata caricata la demo sintetica.",
    "A project was created.": "È stato creato un progetto.", "A member was added to the project.": "È stato aggiunto un membro al progetto.",
    "A decision card was added.": "È stata aggiunta una scheda decisione.",
    "A decision card was confirmed.": "È stata confermata una scheda decisione.",
    "Access codes were issued.": "Sono stati emessi i codici di accesso.",
    "Course material was added.": "È stato aggiunto materiale del corso.",
    "Your consent choices were saved.": "Le tue scelte di consenso sono state salvate.",
    "Decisions were chosen for your private check.": "Sono state scelte le decisioni per la tua verifica privata.",
    "A question was prepared for you.": "È stata preparata una domanda per te.",
    "A decision was skipped: it is not confirmed or has no source.":
        "Una decisione è stata saltata: non è confermata o non ha una fonte.",
    "A decision was skipped: nothing new to ask.": "Una decisione è stata saltata: niente di nuovo da chiedere.",
    "A question on your own decision was prepared.": "È stata preparata una domanda sulla tua decisione.",
    "Your answer was recorded and assessed.": "La tua risposta è stata registrata e valutata.",
    "A request for the answer was handled (no answer given in a check).":
        "Una richiesta della risposta è stata gestita (nessuna risposta data in una verifica).",
    "An answer addressed to the grader was not scored.": "Una risposta rivolta al valutatore non è stata valutata.",
    "Teaching sessions were worked out from the coverage.": "Le sessioni di insegnamento sono state ricavate dalla copertura.",
    "Teaching sessions were saved.": "Le sessioni di insegnamento sono state salvate.",
    "Someone agreed to take part in a teaching session.": "Qualcuno ha accettato di partecipare a una sessione di insegnamento.",
    "Both people agreed to a teaching session.": "Entrambe le persone hanno accettato una sessione di insegnamento.",
    "Steps of a teaching session were ticked off.": "Sono stati spuntati dei passaggi di una sessione di insegnamento.",
    "A new retest question was prepared.": "È stata preparata una nuova domanda per il nuovo test.",
    "A retest answer was recorded and assessed.": "Una risposta al nuovo test è stata registrata e valutata.",
    "The retest result was applied to the mission.": "Il risultato del nuovo test è stato applicato alla missione.",
    "A request for the answer was refused in the retest.": "Una richiesta della risposta è stata rifiutata nel nuovo test.",
    "A retest answer addressed to the grader was not scored.":
        "Una risposta al nuovo test rivolta al valutatore non è stata valutata.",
    "A follow-up question was opened.": "È stata aperta una domanda di richiamo.",
    "A defense-simulator question was prepared.": "È stata preparata una domanda per il simulatore.",
    "A simulator answer was recorded (practice only).": "Una risposta del simulatore è stata registrata (solo allenamento).",
    "A request for the answer was refused in the simulator.": "Una richiesta della risposta è stata rifiutata nel simulatore.",
    "A simulator answer addressed to the grader was not scored.":
        "Una risposta del simulatore rivolta al valutatore non è stata valutata.",
    "A reviewer scored an answer.": "Un revisore ha valutato una risposta.",
    "Team coverage was recorded.": "La copertura del team è stata registrata.",
})


# ---- remaining interface strings
IT.update({
    "{n} new question(s) below.": "{n} nuova/e domanda/e qui sotto.",
    "No new questions for these decisions.": "Nessuna nuova domanda per queste decisioni.",
    "Choose up to 2 decisions to be checked on": "Scegli fino a 2 decisioni su cui essere verificato",
    "Why": "Perché", "What If": "E se", "Transfer": "Trasferimento",
    "Only you can change these, and you can withdraw at any time. Withdrawing removes your answers from the team's "
    "coverage.":
        "Solo tu puoi modificarli e puoi ritirarti in qualsiasi momento. Ritirarti toglie le tue risposte dalla "
        "copertura del team.",
    "In the demo, consent is synthetic.": "Nella demo il consenso è sintetico.",
    "Owning a decision is not proof you can defend it. One independent question, no hints: only a full answer lets "
    "you mentor a teammate on it.":
        "Essere responsabili di una decisione non prova che sai difenderla. Una domanda indipendente, senza aiuti: "
        "solo una risposta completa ti permette di fare da mentore a un compagno.",
    "Both people must accept the mission before the retest.": "Entrambe le persone devono accettare la missione prima del nuovo test.",
    "You have not agreed to be assessed, so the retest is not available.":
        "Non hai accettato di essere valutato, quindi il nuovo test non è disponibile.",
    "Your answer to the last question was recorded": "La tua risposta all'ultima domanda è stata registrata",
    "New situation": "Nuova situazione",
    "Mission status: **{status}** · team coverage now {cov}": "Stato della missione: **{status}** · copertura del team ora {cov}",
    "You explained {d} on a new question, with no hints. Team coverage went up.":
        "Hai spiegato {d} su una nuova domanda, senza aiuti. La copertura del team è aumentata.",
    "New question passed. Team coverage is now {cov}.": "Nuova domanda superata. La copertura del team è ora {cov}.",
    "This project has no members yet. Add the team in **1. Project Setup** first.":
        "Questo progetto non ha ancora membri. Aggiungi prima il team in **1. Impostazione progetto**.",
    "The people in this mission are shown only to them until both accept.":
        "Le persone di questa missione sono mostrate solo a loro finché entrambi non accettano.",
    "Shared project steps, plus your own private steps. Other members' checks, consents and retests are never shown "
    "here, and answers and scores are never written to the log.":
        "Passaggi condivisi del progetto più i tuoi passaggi privati. Verifiche, consensi e nuovi test degli altri "
        "membri non sono mai mostrati qui, e risposte e punteggi non vengono mai scritti nel registro.",
    "Scores are practice feedback, not grades. A score from the model can be wrong.":
        "I punteggi sono feedback di allenamento, non voti. Un punteggio del modello può essere sbagliato.",
    "One correct answer shows someone explained one decision on one day, not that they'll remember it.":
        "Una risposta corretta mostra che qualcuno ha spiegato una decisione un giorno, non che la ricorderà.",
    "Decision Coverage is a prototype indicator, not a validated metric.":
        "La copertura delle decisioni è un indicatore di prototipo, non una metrica validata.",
    "In the synthetic demo, answers are scored offline with a keyword rubric on made-up data, as a stand-in for the "
    "model. A score of 2 also needs explained reasoning and the scenario's own conclusion.":
        "Nella demo sintetica le risposte sono valutate offline con una rubrica a parole chiave su dati inventati, "
        "al posto del modello. Un punteggio di 2 richiede anche un ragionamento spiegato e la conclusione propria "
        "dello scenario.",
    "In your own projects without the live model, nothing is scored automatically: answers wait for human review. "
    "With the model, unsure or inconsistent grades also go to human review.":
        "Nei tuoi progetti senza il modello reale nulla viene valutato automaticamente: le risposte aspettano la "
        "revisione umana. Con il modello, anche i voti incerti o incoerenti vanno alla revisione umana.",
    "Answers that try to instruct the grader are never scored. The app cannot stop anyone from using an outside AI "
    "tool.":
        "Le risposte che cercano di istruire il valutatore non vengono mai valutate. L'app non può impedire a nessuno "
        "di usare uno strumento di IA esterno.",
    "No source means no assessment. A decision is assessed only after a member confirms it.":
        "Senza fonte non c'è valutazione. Una decisione viene valutata solo dopo la conferma di un membro.",
    "If nobody can explain a decision, the app points to the course material or the TA.":
        "Se nessuno sa spiegare una decisione, l'app indica il materiale del corso o il tutor.",
    "In a small team even totals can identify people, so the team view shows only counts per decision.":
        "In un piccolo team anche i totali possono identificare le persone, quindi la vista del team mostra solo "
        "conteggi per decisione.",
    "No course given": "Nessun corso indicato", "source": "fonte", "no document yet": "ancora nessun documento",
    "Next step": "Prossimo passo",
    "Add the team members below. Each member then opts in to assessment on the Private Check page.":
        "Aggiungi i membri del team qui sotto. Ogni membro accetta poi la valutazione nella pagina Verifica privata.",
    "Add the project's key decisions: by hand (each quote is checked) or with the live model.":
        "Aggiungi le decisioni chiave del progetto: a mano (ogni citazione viene controllata) o con il modello reale.",
    "Decisions are confirmed. Members can now take private checks and owners their owner checks.":
        "Le decisioni sono confermate. I membri possono ora fare le verifiche private e i responsabili la loro verifica.",
    "A new project is added next to the existing ones; nothing is deleted. Members start with every consent off. Only "
    "upload documents you are allowed to share.":
        "Un nuovo progetto viene aggiunto accanto a quelli esistenti; nulla viene eliminato. I membri iniziano con "
        "ogni consenso disattivato. Carica solo documenti che puoi condividere.",
    "No members yet.": "Ancora nessun membro.",
    "Each member opts in for themselves on the Private Check page.":
        "Ogni membro accetta per sé nella pagina Verifica privata.",
    "This project has no document, so no decision can be source-checked. Start a new project with its report.":
        "Questo progetto non ha documenti, quindi nessuna decisione può essere controllata sulla fonte. Avvia un "
        "nuovo progetto con il suo report.",
    "Propose decisions with the live model": "Proponi decisioni con il modello reale",
    "Copy the quote word for word from the document; it is checked against that page.":
        "Copia la citazione parola per parola dal documento; viene controllata in quella pagina.",
    "Rationale (why, in the team's words)": "Motivazione (perché, con le parole del team)",
    "Rejected alternatives (comma-separated)": "Alternative scartate (separate da virgola)",
    "Document": "Documento", "Page": "Pagina", "Exact quote from that page": "Citazione esatta da quella pagina",
    "Added, but the quote was not found on that page, so it can never be assessed. Check the page number and the "
    "exact wording.":
        "Aggiunta, ma la citazione non è stata trovata in quella pagina, quindi non potrà mai essere valutata. "
        "Controlla il numero di pagina e la formulazione esatta.",
    "No verified source: the quote is not on the cited page, so this decision is never assessed.":
        "Nessuna fonte verificata: la citazione non è nella pagina indicata, quindi questa decisione non viene mai "
        "valutata.",
    "Proposed: not assessed until a member checks the quote and confirms it.":
        "Proposta: non valutata finché un membro non controlla la citazione e la conferma.",
    "Add members first: only a member can confirm a decision.":
        "Aggiungi prima i membri: solo un membro può confermare una decisione.",
    "Deletes this project's decisions, members, answers, missions and log. It cannot be undone. Other projects and "
    "the demo are not affected.":
        "Elimina decisioni, membri, risposte, missioni e registro di questo progetto. Non si può annullare. Gli altri "
        "progetti e la demo non sono toccati.",
})

<<<<<<< Updated upstream
=======

# ---- connect a model, question source, quiz
IT.update({
    "Model: connected": "Modello: connesso", "Connect a model": "Collega un modello",
    "Model connected (this session only): {m}": "Modello collegato (solo questa sessione): {m}",
    "No model connected: questions and scoring run offline on the synthetic demo data.":
        "Nessun modello collegato: domande e punteggi funzionano offline sui dati demo sintetici.",
    "Disconnect": "Scollega", "Provider": "Fornitore", "API key": "Chiave API", "Model name": "Nome del modello",
    "Base URL": "URL di base",
    "The server already has a model configured: {m}": "Il server ha già un modello configurato: {m}",
    "Kept in this session's memory only: not saved to the database, the logs or any export.":
        "Conservata solo nella memoria di questa sessione: non viene salvata nel database, nei registri o in "
        "esportazioni.",
    "Leave empty for OpenAI. For a model on this computer use e.g. http://localhost:11434/v1 (Ollama); no key is "
    "needed then.":
        "Lascia vuoto per OpenAI. Per un modello su questo computer usa ad es. http://localhost:11434/v1 (Ollama); "
        "in quel caso non serve la chiave.",
    "I understand that the project text and my team's answers are sent to this provider to write questions and "
    "score answers.":
        "Capisco che il testo del progetto e le risposte del mio team vengono inviati a questo fornitore per scrivere "
        "domande e valutare le risposte.",
    "Connect and test": "Collega e prova",
    "The provider rejected the key (401). Check it and the model name.":
        "Il fornitore ha rifiutato la chiave (401). Controllala e controlla il nome del modello.",
    "The provider rejected the key (403). Check it and the model name.":
        "Il fornitore ha rifiutato la chiave (403). Controllala e controlla il nome del modello.",
    "Cannot reach the model API (network).": "Impossibile raggiungere l'API del modello (rete).",
    "Model rate-limited; try again shortly.": "Modello con limite di richieste; riprova tra poco.",
    "Enter an API key.": "Inserisci una chiave API.",
    "The model did not return JSON.": "Il modello non ha restituito JSON.",
    "The connection test failed.": "La prova di connessione non è riuscita.",
    "Written by the connected model": "Scritta dal modello collegato",
    "From the synthetic demo bank": "Dalla banca demo sintetica",
    "Fixed template (no model connected)": "Modello fisso (nessun modello collegato)",
    "Start a {n}-question quiz": "Avvia un quiz di {n} domande", "Quiz: question {n} of {m}": "Quiz: domanda {n} di {m}",
    "Quiz finished: {a} strong, {b} partly there, {c} not yet, out of {n}.":
        "Quiz finito: {a} solide, {b} a metà, {c} non ancora, su {n}.",
    "{n} answer(s) could not be scored automatically and wait for human review.":
        "{n} risposta/e non ha potuto essere valutata automaticamente e aspetta la revisione umana.",
    "A quiz is practice only: it never changes team coverage.":
        "Un quiz è solo allenamento: non cambia mai la copertura del team.",
})


# ---- local command-line providers
IT.update({
    "Runs the tool already installed and logged in on this computer: no key is typed here. Use it only on your own "
    "computer, never on a shared server.":
        "Usa lo strumento già installato e con accesso effettuato su questo computer: qui non si digita nessuna chiave. "
        "Usalo solo sul tuo computer, mai su un server condiviso.",
    "Codex runs in a read-only sandbox, but it can still read files on this computer.":
        "Codex gira in una sandbox in sola lettura, ma può comunque leggere file su questo computer.",
    "(the tool's default)": "(il predefinito dello strumento)",
})

>>>>>>> Stashed changes
# sentences built by coverage.py and missions.py: matched by shape, then translated with the same placeholders
_DYNAMIC = [
    (r"^(\d+) members have each demonstrated it, so the team does not depend on one person\.$",
     "{n} members have each demonstrated it, so the team does not depend on one person.",
     "{n} membri l'hanno dimostrata, quindi il team non dipende da una sola persona."),
    (r"^Only 1 member has demonstrated it\. If they are absent, nobody can defend it\.$",
     "Only 1 member has demonstrated it. If they are absent, nobody can defend it.",
     "Solo 1 membro l'ha dimostrata. Se è assente, nessuno può difenderla."),
    (r"^Propose a teaching mission so a second member learns it\.$",
     "Propose a teaching mission so a second member learns it.",
     "Proponi una missione di insegnamento così un secondo membro la impara."),
    (r"^Members were checked, but nobody has demonstrated it yet\.$",
     "Members were checked, but nobody has demonstrated it yet.",
     "I membri sono stati verificati, ma nessuno l'ha ancora dimostrata."),
    (r"^The decision's owner can take an owner check; otherwise use the course material or ask the TA\.$",
     "The decision's owner can take an owner check; otherwise use the course material or ask the TA.",
     "Il responsabile della decisione può fare la verifica del responsabile; altrimenti usa il materiale del corso "
     "o chiedi al tutor."),
    (r"^Nobody has answered a question on it yet\. That is unknown, not failed\.$",
     "Nobody has answered a question on it yet. That is unknown, not failed.",
     "Nessuno ha ancora risposto a una domanda su di essa. È sconosciuto, non fallito."),
    (r"^Members can take a private check on it\.$", "Members can take a private check on it.",
     "I membri possono fare una verifica privata su di essa."),
    (r"^(.+) was chosen because they demonstrated (.+) and are willing to mentor; (.+) has not demonstrated it yet "
     r"and is willing to learn\.$",
     "{a} was chosen because they demonstrated {b} and are willing to mentor; {c} has not demonstrated it yet and "
     "is willing to learn.",
     "{a} è stato scelto perché ha dimostrato {b} ed è disponibile a fare da mentore; {c} non l'ha ancora "
     "dimostrata ed è disponibile a imparare."),
    (r"^Nobody has demonstrated (.+) yet, so no mentor was invented; (.+) is pointed to course material or the "
     r"TA\.$",
     "Nobody has demonstrated {a} yet, so no mentor was invented; {b} is pointed to course material or the TA.",
     "Nessuno ha ancora dimostrato {a}, quindi non è stato inventato nessun mentore; {b} viene indirizzato al "
     "materiale del corso o al tutor."),
    (r"^Nobody on the team has demonstrated this yet — review the course material for this topic or ask the TA\.$",
     "Nobody on the team has demonstrated this yet — review the course material for this topic or ask the TA.",
     "Nessuno nel team l'ha ancora dimostrata: rivedi il materiale del corso su questo argomento o chiedi al tutor."),
]
IT.update({english: italian for _, english, italian in _DYNAMIC})


def tr_dynamic(text: str) -> str:
    """Translate a sentence produced by the coverage or mission logic (numbers and names are kept)."""
    if get_lang() != "it":
        return text
    import re
    for pattern, _english, italian in _DYNAMIC:
        match = re.match(pattern, text)
        if match:
            groups = match.groups()
            if len(groups) == 1 and "{n}" in italian:
                return italian.format(n=groups[0])
            if groups:
                return italian.format(**dict(zip("abc", groups, strict=False)))
            return italian
    return text
