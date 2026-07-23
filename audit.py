import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & DESIGN CSS (BLANC, PROFESSIONNEL & ÉPURÉ)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Audit FSSC 22000",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    /* Fond 100% blanc et typographie sombre */
    html, body, .stApp {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* Boutons principaux */
    .stButton>button {
        background-color: #0F172A !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 10px 24px !important;
        border: none !important;
        width: 100%;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #334155 !important;
    }

    /* Style des titres */
    h1, h2, h3 {
        color: #0F172A !important;
    }
    
    /* Séparateurs subtils */
    hr {
        border-color: #E2E8F0 !important;
    }
</style>
""", unsafe_allow_html=True)

try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    use_gsheets = True
except Exception:
    use_gsheets = False

LOCAL_FILE = "resultats_audit_qualite.csv"

# -----------------------------------------------------------------------------
# 2. HIERARCHIE : SOCIÉTÉS -> SECTEURS -> ACTIVITÉS
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

# -----------------------------------------------------------------------------
# 3. DICTIONNAIRES DES QUESTIONS
# -----------------------------------------------------------------------------
QUESTIONS_PERSONNEL = {
    "1. Vision et mission": [
        "Connaissez-vous la politique de votre entreprise en matière de la sécurité des aliments ?",
        "Avez-vous reçu des connaissances sur la vision et la mission de l'entreprise ?",
        "Pouvez-vous me expliquer la vision et la mission de l'entreprise ?",
        "Savez-vous que l'entreprise dispose des certifications qualité ?",
        "Vos responsables vous communiquent-ils les attentes en matière de sécurité des aliments ?"
    ],
    "2. Personnel": [
        "Avez-vous suivi un sensibilisation en matière de sécurité des aliments lors des 2 derniers mois ?",
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
        "Q1.1 : La direction démontre-t-elle son engagement envers la sécurité des aliments (politique, objectifs, ressources) ?",
        "Q1.2 : L'importance de la politique et les objectifs sont-ils communiqués, compris et appliqués ?",
        "Q1.3 : La direction encourage-t-elle activement l'amélioration continue via formations/événements ?",
        "Q2.1 : Les attentes sont-elles communiquées de manière claire quotidiennement à tous ?",
        "Q2.2 : Des formations sont-elles organisées pour s'assurer que les employés comprennent ces attentes ?",
        "Q2.3 : Les communications (réunions, affichage) sont-elles régulières et adaptées ?",
        "Q2.4 : La communication est-elle suivie d'une évaluation pour mesurer son efficacité ?",
        "Q3.1 : La vision et la mission sont-elles affichées, communiquées et intégrées dans les activités ?",
        "Q3.2 : Les employés reçoivent-ils une présentation de la vision lors de leur intégration ?",
        "Q3.3 : Des rappels de la vision/mission sont-ils régulièrement partagés ?",
        "Q3.4 : L’entreprise a-t-elle évalué récemment la compréhension des employés à la mission/vision ?"
    ],
    "2. Personnel": [
        "Q7.1 : Existe-t-il un canal formel pour signaler les préoccupations, connu de tous ?",
        "Q7.2 : L'environnement encourage-t-il l'expression libre des inquiétudes ?",
        "Q7.3 : Les alertes des 6 derniers mois ont-elles été suivies d'actions correctives ?",
        "Q7.4 : Chaque collaborateur est-il conscient de l'impact de ses signalements sur la sécurité ?",
        "Q8.1 : Avez-vous une mission clairement définie en sécurité des aliments ?",
        "Q8.2 : Appliquez-vous les bonnes pratiques et participez-vous aux réunions qualité ?",
        "Q8.3 : Avez-vous été formé(e) les 12 derniers mois et sensibilisé vos collègues ?",
        "Q9.1 : Existe-t-il des indicateurs de performance dédiés, suivis et communiqués ?",
        "Q9.2 : Le suivi intègre-t-il les non-conformités, alertes et réclamations clients ?",
        "Q9.3 : Les audits évaluent-ils ces performances et les écarts sont-ils analysés ?"
    ],
    "3. Cohérence": [
        "Q4.1 : Les employés participent-ils à la création et l'amélioration des procédures ?",
        "Q4.2 : Les suggestions des employés sont-elles valorisées et intégrées ?",
        "Q4.3 : Les instructions sont-elles testées en conditions réelles avec les opérateurs ?",
        "Q5.1 : Les documents sont-ils clairs, à jour et facilement accessibles ?",
        "Q5.2 : La documentation aide-t-elle à prendre les bonnes décisions en cas d'imprévu ?",
        "Q5.3 : Existe-t-il des supports visuels pour soutenir la compréhension ?",
        "Q5.4 : Les documents sont-ils conçus pour faciliter la conformité ?",
        "Q6.1 : Les employés participent-ils à l'amélioration des procédures ?",
        "Q6.2 : Y a-t-il un mécanisme formel encourageant à proposer des améliorations ?",
        "Q6.3 : Y a-t-il une formation pour contribuer à l’amélioration des protocoles ?",
        "Q6.4 : Les retours d’audit sont-ils analysés avec les opérateurs ?",
        "Q6.5 : L’implication des employés dans l’amélioration est-elle suivie et mesurée ?"
    ],
    "4. Adaptabilité": [
        "Q10.1 : Votre organisation fait-elle une veille sur les évolutions réglementaires ?",
        "Q10.2 : Existe-t-il une procédure de gestion du changement évaluant les risques ?",
        "Q10.3 : Utilisez-vous les retours d'expérience pour améliorer vos pratiques ?",
        "Q10.4 : Des formations sont-elles organisées lors de l'introduction de nouveaux procédés ?",
        "Q10.5 : Avez-vous un plan de continuité ou de gestion de crise ?",
        "Q11.1 : Les décisions opérationnelles intègrent-elles systématiquement les exigences FSSC ?",
        "Q11.2 : Les responsables sont-ils formés à prendre des décisions conformes ?",
        "Q11.3 : Les attentes sont-elles régulièrement revues en cas de changement ?",
        "Q12.1 : L’entreprise a-t-elle une stratégie documentée pour les situations d’urgence ?",
        "Q12.2 : Les rôles et responsabilités sont-ils clairement définis et formés ?",
        "Q12.3 : Les retours d’expérience sont-ils utilisés pour améliorer la stratégie ?",
        "Q12.4 : Des exercices ou simulations de crise sont-ils réalisés ?"
    ],
    "5. Conscience des dangers et des risques": [
        "Q13.1 : Existe-t-il une procédure pour signaler et analyser les quasi-accidents ?",
        "Q13.2 : Les collaborateurs sont-ils encouragés à identifier les risques ?",
        "Q13.3 : Les analyses des quasi-accidents permettent-elles des actions correctives ?",
        "Q13.4 : Les actions mises en place sont-elles suivies et évaluées ?",
        "Q14.1 : L’entreprise dispose-t-elle d’un système pour évaluer l’engagement du personnel ?",
        "Q14.2 : Les responsables montrent-ils l’exemple et soutiennent-ils le signalement ?",
        "Q14.3 : Les comportements non conformes sont-ils rapidement corrigés ?"
    ]
}

# -----------------------------------------------------------------------------
# 4. INTERFACE UTILISATEUR
# -----------------------------------------------------------------------------
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)

st.title("Évaluation de la Culture Sécurité des Aliments")
st.markdown("---")

tab_form, tab_dash = st.tabs(["📋 Saisie de l'Audit", "📊 Statistiques & Histogrammes"])

# --- ONGLET 1 : FORMULAIRE EN CASCADE ---
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

    # APPARITION DU QUESTIONNAIRE SEULEMENT SI LE BOUTON A ÉTÉ CLIQUÉ
    if st.session_state.get('audit_started', False):
        p = st.session_state['params']
        st.info(f"**Audit en cours :** {p['societe']} > {p['secteur']} > {p['activite']} | Profil : {p['profil']}")
        
        current_questions = QUESTIONS_PERSONNEL if p['profil'] == "Personnel" else QUESTIONS_RESPONSABLES
        options = ["Oui (100%)", "En partie (50%)", "Non (0%)"]
        dim_scores = {}

        with st.form("formulaire_questions", clear_on_submit=True):
            st.subheader("2. Questionnaire FSSC 22000")
            
            for dim_name, q_list in current_questions.items():
                st.markdown(f"**{dim_name.upper()}**")
                numeric_scores = []
                for idx, q_text in enumerate(q_list):
                    ans = st.radio(f"{idx+1}. {q_text}", options, horizontal=True, key=f"{dim_name}_{idx}")
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
                if use_gsheets:
                    try:
                        df_existing = conn.read(ttl="0")
                        df_updated = pd.concat([df_existing, pd.DataFrame([entry])], ignore_index=True)
                        conn.update(data=df_updated)
                        saved = True
                    except Exception:
                        pass
                
                if not saved:
                    df_e = pd.DataFrame([entry])
                    if not os.path.exists(LOCAL_FILE):
                        df_e.to_csv(LOCAL_FILE, index=False)
                    else:
                        df_e.to_csv(LOCAL_FILE, mode='a', header=False, index=False)

                st.success("✅ Audit enregistré avec succès !")
                st.session_state['audit_started'] = False # Cache le formulaire après enregistrement

# --- ONGLET 2 : DASHBOARD STATISTIQUES ---
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

    if df is None or df.empty:
        st.info("Aucune donnée enregistrée pour le moment.")
    else:
        # 1. Filtres pour cibler une société et un secteur
        st.markdown("**Filtrer les données :**")
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            filter_soc = st.selectbox("Sélectionner la Société :", df["Societe"].unique())
        with c_f2:
            secteurs_dispo = df[df["Societe"] == filter_soc]["Secteur"].unique()
            filter_sec = st.selectbox("Sélectionner le Secteur :", secteurs_dispo)

        # Filtrage du dataframe
        df_filtered = df[(df["Societe"] == filter_soc) & (df["Secteur"] == filter_sec)]

        if df_filtered.empty:
            st.warning("Aucun audit réalisé pour ce croisement.")
        else:
            st.markdown(f"### Histogramme : Dimensions par Activité ({filter_soc} - {filter_sec})")
            
            # Préparation des données pour l'histogramme groupé
            dimensions_cols = [
                "Vision_Mission_%", "Personnel_%", "Coherence_%", 
                "Adaptabilite_%", "Conscience_Risques_%"
            ]
            
            # Moyenne des scores par activité et par dimension
            df_grouped = df_filtered.groupby("Activite")[dimensions_cols].mean().reset_index()
            
            # Transformation ("Melt") pour Plotly
            df_melted = df_grouped.melt(
                id_vars="Activite", 
                value_vars=dimensions_cols,
                var_name="Dimension", 
                value_name="Score Moyen (%)"
            )

            # Nettoyage des noms de dimensions pour la légende
            df_melted["Dimension"] = df_melted["Dimension"].str.replace("_%", "").str.replace("_", " ")

            # Création de l'histogramme avec Plotly
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
                yaxis=dict(range=[0, 100], gridcolor="#E2E8F0"),
                legend_title_text="Dimensions FSSC 22000"
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("---")
            st.markdown("### Tableau des données brutes filtrées")
            st.dataframe(df_filtered)
