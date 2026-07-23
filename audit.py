import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION ET STYLE PROPRE (FOND BLANC & TIMES NEW ROMAN)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Audit FSSC 22000",
    page_icon="🛡️",
    layout="wide"
)

st.markdown("""
<style>
    /* Fond blanc et police Times New Roman globale */
    .stApp {
        background-color: #FFFFFF !important;
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }
    
   import streamlit as st
import pandas as pd
import plotly.express as px
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION ET STYLE PROPRE
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Audit FSSC 22000",
    page_icon="🛡️",
    layout="wide"
)

# NOUVEAU CSS : Empêche le bug de l'écran blanc lié au mode sombre de l'ordinateur
st.markdown("""
<style>
    /* Fond blanc global */
    .stApp {
        background-color: #FFFFFF !important;
    }
    
    /* Forcer TOUT le texte en noir pour éviter le bug du mode sombre */
    .stApp, p, span, div, h1, h2, h3, h4, h5, h6, label, li {
        font-family: "Times New Roman", Times, serif !important;
        color: #000000 !important;
    }

    /* Exception : Garder le texte du bouton en blanc pour quil soit lisible */
    div.stButton > button, div.stButton > button * {
        background-color: #000000 !important;
        color: #FFFFFF !important;
        font-family: "Times New Roman", Times, serif !important;
        font-weight: bold !important;
        border-radius: 4px !important;
    }
    div.stButton > button:hover {
        background-color: #333333 !important;
        color: #FFFFFF !important;
        border: 1px solid #000000 !important;
    }
</style>
""", unsafe_allow_html=True)

# Connexion Google Sheets ou secours CSV local
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    use_gsheets = True
except Exception:
    use_gsheets = False

LOCAL_FILE = "resultats_audit_qualite.csv"

# -----------------------------------------------------------------------------
# 2. STRUCTURES DE DONNÉES
# -----------------------------------------------------------------------------
STRUCTURE = {
    "El Mazraa": ["Charcuterie", "Surgelé", "Abattoir Dinde", "Petfood", "Co-produit", "Croquette"],
    "Dick": ["Abattoir Poulet"],
    "Essanawbar": ["Plats Cuisinés"]
}

ACTIVITES = {
    "Charcuterie": ["Préparation", "Cuisson", "Conditionnement"],
    "Surgelé": ["Activité 1", "Activité 2", "Activité 3"],
    "Abattoir Dinde": ["Activité 1", "Activité 2", "Activité 3"],
    "Petfood": ["Activité 1", "Activité 2", "Activité 3"],
    "Co-produit": ["Activité 1", "Activité 2", "Activité 3"],
    "Croquette": ["Activité 1", "Activité 2", "Activité 3"],
    "Abattoir Poulet": ["Activité 1", "Activité 2", "Activité 3"],
    "Plats Cuisinés": ["Activité 1", "Activité 2", "Activité 3"]
}

QUESTIONS_PERSONNEL = {
    "1. Vision et mission": [
        "Connaissez-vous la politique de votre entreprise en matière de la sécurité des aliments ?",
        "Avez-vous reçu des connaissances sur la vision et la mission de l'entreprise ?",
        "Pouvez-vous m'expliquer la vision et la mission de l'entreprise ?",
        "Savez-vous que l'entreprise dispose des certifications qualité ?",
        "Vos responsables vous communiquent-ils les attentes en matière de sécurité des aliments ?"
    ],
    "2. Personnel": [
        "Avez-vous suivi une sensibilisation en matière de sécurité des aliments lors des 2 derniers mois ?",
        "Êtes-vous favorisé(e) à la mise en place d'outils (boîte à suggestions) pour signaler les problèmes ?",
        "Connaissez-vous les règles relatives aux droits au travail ?",
        "Utilisez-vous des gants lorsque vous touchez les aliments ?",
        "Respectez-vous les protocoles de lavage des mains avant de manipuler les aliments ?",
        "Respectez-vous les règles concernant le non-port des bijoux, vernis et faux ongles ?",
        "Respectez-vous l'interdiction de manger, fumer ou cracher au sein de l'unité ?",
        "Utilisez-vous le masque lorsque vous manipulez les aliments ?",
        "Respectez-vous les instructions de travail au sein de votre atelier ?",
        "Avez-vous été formé à la sécurité des aliments les 2 derniers mois ?",
        "Êtes-vous prêt à participer à des programmes de sensibilisation sur la sécurité des aliments ?"
    ],
    "3. Cohérence": [
        "Connaissez-vous vos responsabilités en matière de sécurité des aliments ?",
        "Avez-vous reçu une formation seulement sur vos responsabilités ?",
        "Vous sentez-vous valorisé après avoir présenté vos observations concernant la sécurité des aliments ?",
        "Les affiches ou mémentos sont-elles compréhensibles ?",
        "Êtes-vous favorisé à ce que des instructions soient affichées dans chaque atelier ?",
        "Êtes-vous consulté lors de l'élaboration des protocoles et instructions sur la sécurité des aliments ?",
        "Participez-vous à des réunions sur la qualité des aliments ?"
    ],
    "4. Adaptabilité": [
        "Êtes-vous convoqué à des réunions d'information en cas de changements ou d'évolutions ?",
        "Vous adaptez-vous facilement aux changements ?",
        "Vous sentez-vous à l'aise d'arrêter la ligne si vous constatez un risque pour la qualité ?",
        "Avez-vous suivi une formation à la suite des nouvelles évolutions (matériel, instructions) ?",
        "Avez-vous été informé des procédures d'urgence à suivre en cas d'incident ?"
    ],
    "5. Conscience des dangers et des risques": [
        "Avez-vous reçu une formation sur la gestion des risques et des dangers ?",
        "Savez-vous ce qu'est la contamination croisée ?",
        "Comprenez-vous comment les aliments peuvent être contaminés (physique, chimique, microbio) ?",
        "Êtes-vous en mesure d'identifier les risques dans votre environnement de travail ?",
        "Signalez-vous immédiatement tout incident ou contamination potentielle ?",
        "Respectez-vous les instructions de travail visant à limiter la contamination croisée ?"
    ]
}

QUESTIONS_RESPONSABLES = {
    "1. Vision et mission": [
        "Q1.1 : La direction démontre-t-elle son engagement envers la sécurité des aliments ?",
        "Q1.2 : L'importance de la politique et les objectifs sont-ils communiqués et appliqués ?",
        "Q1.3 : La direction encourage-t-elle activement l'amélioration continue ?",
        "Q2.1 : Les attentes sont-elles communiquées de manière claire quotidiennement ?",
        "Q2.2 : Des formations sont-elles organisées pour s'assurer de la compréhension ?",
        "Q2.3 : Les communications sont-elles régulières et adaptées ?",
        "Q2.4 : La communication est-elle suivie d'une évaluation d'efficacité ?",
        "Q3.1 : La vision et la mission sont-elles affichées et intégrées ?",
        "Q3.2 : Les employés reçoivent-ils une présentation lors de leur intégration ?",
        "Q3.3 : Des rappels de la vision/mission sont-ils régulièrement partagés ?",
        "Q3.4 : L’entreprise a-t-elle évalué récemment l'adhésion à la mission/vision ?"
    ],
    "2. Personnel": [
        "Q7.1 : Existe-t-il un canal formel pour signaler les préoccupations ?",
        "Q7.2 : L'environnement encourage-t-il l'expression libre des inquiétudes ?",
        "Q7.3 : Les alertes ont-elles été suivies d'actions correctives ?",
        "Q7.4 : Chaque collaborateur est-il conscient de l'impact de ses signalements ?",
        "Q8.1 : Avez-vous une mission clairement définie en sécurité des aliments ?",
        "Q8.2 : Appliquez-vous les bonnes pratiques et participez-vous aux réunions qualité ?",
        "Q8.3 : Avez-vous été formé(e) les 12 derniers mois ?",
        "Q9.1 : Existe-t-il des indicateurs de performance dédiés ?",
        "Q9.2 : Le suivi intègre-t-il les non-conformités et réclamations clients ?",
        "Q9.3 : Les audits évaluent-ils ces performances ?"
    ],
    "3. Cohérence": [
        "Q4.1 : Les employés participent-ils à l'amélioration des procédures ?",
        "Q4.2 : Les suggestions sont-elles valorisées et intégrées ?",
        "Q4.3 : Les instructions sont-elles testées en conditions réelles ?",
        "Q5.1 : Les documents sont-ils clairs, à jour et accessibles ?",
        "Q5.2 : La documentation aide-t-elle à prendre les bonnes décisions ?",
        "Q5.3 : Existe-t-il des supports visuels de compréhension ?",
        "Q5.4 : Les documents facilitent-ils la conformité ?",
        "Q6.1 : Les modifications de procédures sont-elles communiquées ?",
        "Q6.2 : Y a-t-il un mécanisme formel pour proposer des améliorations ?",
        "Q6.3 : Y a-t-il une formation pour contribuer aux protocoles ?",
        "Q6.4 : Les retours d’audit sont-ils analysés avec les opérateurs ?",
        "Q6.5 : L’implication des employés est-elle mesurée ?"
    ],
    "4. Adaptabilité": [
        "Q10.1 : Votre organisation fait-elle une veille réglementaire ?",
        "Q10.2 : Existe-t-il une procédure de gestion du changement ?",
        "Q10.3 : Utilisez-vous les retours d'expérience ?",
        "Q10.4 : Des formations sont-elles organisées lors de nouveaux procédés ?",
        "Q10.5 : Avez-vous un plan de gestion de crise ?",
        "Q11.1 : Les décisions intègrent-elles les exigences FSSC ?",
        "Q11.2 : Les responsables sont-ils formés à la prise de décision ?",
        "Q11.3 : Les attentes sont-elles revues en cas de changement ?",
        "Q12.1 : L’entreprise a-t-elle une stratégie documentée d'urgence ?",
        "Q12.2 : Les rôles et responsabilités sont-ils clairement définis ?",
        "Q12.3 : Les retours d’expérience améliorent-ils la stratégie ?",
        "Q12.4 : Des simulations de crise sont-elles réalisées ?"
    ],
    "5. Conscience des dangers et des risques": [
        "Q13.1 : Existe-t-il une procédure pour analyser les quasi-accidents ?",
        "Q13.2 : Les collaborateurs sont-ils encouragés à identifier les risques ?",
        "Q13.3 : Les analyses permettent-elles des actions préventives ?",
        "Q13.4 : Les actions mises en place sont-elles évaluées ?",
        "Q14.1 : L’entreprise évalue-t-elle l'engagement du personnel ?",
        "Q14.2 : Les responsables montrent-ils l’exemple ?",
        "Q14.3 : Les comportements non conformes sont-ils corrigés ?"
    ]
}

# -----------------------------------------------------------------------------
# 3. INTERFACE
# -----------------------------------------------------------------------------
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("Évaluation de la Culture Sécurité des Aliments")
st.markdown("---")

# CORRECTION DU SESSION STATE : Gestion sécurisée du message de succès
if st.session_state.get('audit_success', False):
    st.success("✅ Audit enregistré avec succès !")
    st.session_state['audit_success'] = False  # Réinitialisation manuelle

tab_form, tab_dash = st.tabs(["📋 Saisie de l'Audit", "📊 Statistiques & Histogrammes"])

with tab_form:
    st.subheader("1. Paramétrage de l'audit")
    
    col1, col2 = st.columns(2)
    with col1:
        evaluateur = st.text_input("Nom de l'évaluateur :")
        societe = st.selectbox("Société :", list(STRUCTURE.keys()))
    
    with col2:
        secteur = st.selectbox("Secteur :", STRUCTURE[societe])
        activite = st.selectbox("Activité spécifique :", ACTIVITES[secteur])
        profil = st.selectbox("Profil audité :", ["Personnel", "Responsable"])

    if st.button("🚀 Commencer l'audit avec ces paramètres"):
        if not evaluateur:
            st.error("Veuillez saisir le nom de l'évaluateur avant de commencer.")
        else:
            st.session_state['audit_started'] = True
            st.session_state['params'] = {
                "evaluateur": evaluateur,
                "societe": societe,
                "secteur": secteur,
                "activite": activite,
                "profil": profil
            }

    st.markdown("---")

    if st.session_state.get('audit_started', False):
        p = st.session_state['params']
        st.info(f"Audit en cours : {p['societe']} > {p['secteur']} > {p['activite']} | Profil : {p['profil']}")
        
        current_questions = QUESTIONS_PERSONNEL if p['profil'] == "Personnel" else QUESTIONS_RESPONSABLES
        options = ["Oui (100%)", "En partie (50%)", "Non (0%)"]
        dim_scores = {}

        with st.form("formulaire_questions", clear_on_submit=True):
            st.subheader("2. Questionnaire FSSC 22000")
            
            for dim_name, q_list in current_questions.items():
                st.markdown(f"**{dim_name.upper()}**")
                numeric_scores = []
                for idx, q_text in enumerate(q_list):
                    ans = st.radio(f"{idx+1}. {q_text}", options, index=0, horizontal=True, key=f"{dim_name}_{idx}")
                    val = 100 if ans == "Oui (100%)" else (50 if ans == "En partie (50%)" else 0)
                    numeric_scores.append(val)
                dim_scores[dim_name] = sum(numeric_scores) / len(numeric_scores)
                st.markdown("<br>", unsafe_allow_html=True)
            
            commentaires = st.text_area("Remarques et Observations :")
            submitted = st.form_submit_button("💾 Enregistrer les résultats")

            if submitted:
                score_global = sum(dim_scores.values()) / len(dim_scores)

                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Evaluateur": p["evaluateur"],
                    "Societe": p["societe"],
                    "Secteur": p["secteur"],
                    "Activite": p["activite"],
                    "Profil": p["profil"],
                    "Score_Global_%": round(score_global, 1),
                    "Vision_Mission_%": round(dim_scores.get("1. Vision et mission", 0), 1),
                    "Personnel_%": round(dim_scores.get("2. Personnel", 0), 1),
                    "Coherence_%": round(dim_scores.get("3. Cohérence", 0), 1),
                    "Adaptabilite_%": round(dim_scores.get("4. Adaptabilité", 0), 1),
                    "Conscience_Risques_%": round(dim_scores.get("5. Conscience des dangers et des risques", 0), 1),
                    "Remarques": commentaires
                }

                saved = False
                df_entry = pd.DataFrame([entry])

                if use_gsheets:
                    try:
                        df_existing = conn.read(ttl="0")
                        if df_existing is None or df_existing.empty:
                            df_updated = df_entry
                        else:
                            df_updated = pd.concat([df_existing, df_entry], ignore_index=True)
                        conn.update(data=df_updated)
                        saved = True
                    except Exception as e:
                        print(f"Erreur GSheets : {e}")
                        pass
                
                if not saved:
                    if not os.path.exists(LOCAL_FILE):
                        df_entry.to_csv(LOCAL_FILE, index=False)
                    else:
                        df_entry.to_csv(LOCAL_FILE, mode='a', header=False, index=False)

                st.session_state['audit_started'] = False
                st.session_state['audit_success'] = True
                st.rerun()

with tab_dash:
    st.subheader("Analyse des Performances")

    df = None
    if use_gsheets:
        try:
            df = conn.read(ttl="0")
        except Exception:
            pass
            
    if df is None or df.empty:
        if os.path.exists(LOCAL_FILE):
            df = pd.read_csv(LOCAL_FILE)

    if df is None or df.empty or "Societe" not in df.columns:
        st.info("Aucune donnée enregistrée pour le moment ou fichier vide.")
    else:
        st.markdown("**Filtrer les données :**")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            filter_soc = st.selectbox("Sélectionner la Société :", df["Societe"].unique())
        with c_f2:
            secteurs_dispo = df[df["Societe"] == filter_soc]["Secteur"].unique()
            if len(secteurs_dispo) > 0:
                filter_sec = st.selectbox("Sélectionner le Secteur :", secteurs_dispo)
            else:
                filter_sec = None

        if filter_sec is None:
            st.warning("Aucun secteur trouvé pour cette société.")
        else:
            df_filtered = df[(df["Societe"] == filter_soc) & (df["Secteur"] == filter_sec)]

            if df_filtered.empty:
                st.warning("Aucun audit réalisé pour ce croisement.")
            else:
                st.markdown(f"### Histogramme : Dimensions par Activité ({filter_soc} - {filter_sec})")
                
                dimensions_cols = [
                    "Vision_Mission_%", "Personnel_%", "Coherence_%", 
                    "Adaptabilite_%", "Conscience_Risques_%"
                ]
                
                # Vérifier que toutes les colonnes requises existent dans le DataFrame
                cols_presentes = [col for col in dimensions_cols if col in df_filtered.columns]
                
                df_grouped = df_filtered.groupby("Activite")[cols_presentes].mean().reset_index()
                
                df_melted = df_grouped.melt(
                    id_vars="Activite", 
                    value_vars=cols_presentes,
                    var_name="Dimension", 
                    value_name="Score Moyen (%)"
                )

                # Correction du str.replace pour éviter les avertissements
                df_melted["Dimension"] = df_melted["Dimension"].str.replace("_%", "", regex=False).str.replace("_", " ", regex=False)

                fig = px.bar(
                    df_melted, 
                    x="Activite", 
                    y="Score Moyen (%)", 
                    color="Dimension", 
                    barmode="group",
                    color_discrete_sequence=["#1E3A8A", "#059669", "#D97706", "#DC2626", "#7C3AED"]
                )
                fig.update_layout(
                    plot_bgcolor="white",
                    paper_bgcolor="white",
                    font=dict(family="Times New Roman", size=14, color="black"),
                    yaxis=dict(range=[0, 100], gridcolor="#E2E8F0"),
                    legend_title_text="Dimensions FSSC 22000"
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("---")
                st.markdown("### Tableau des données brutes filtrées")
                st.dataframe(df_filtered)
