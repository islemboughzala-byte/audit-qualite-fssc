import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# -----------------------------------------------------------------------------
# 1. CONFIGURATION ET STYLES VISUELS (CSS)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Audit Culture Qualité FSSC 22000",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #059669 100%);
        padding: 26px;
        border-radius: 12px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 2.1rem;
        margin-bottom: 6px;
    }
    .main-header p {
        color: #E2E8F0 !important;
        font-size: 1.05rem;
        margin: 0;
    }
    .stButton>button {
        background: linear-gradient(90deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        border-radius: 10px !important;
        padding: 12px 28px !important;
        border: none !important;
        width: 100%;
        box-shadow: 0 4px 10px rgba(5, 150, 105, 0.3);
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(5, 150, 105, 0.4);
    }
</style>
""", unsafe_allow_html=True)

# Connexion à Google Sheets (avec secours fichier local CSV)
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    use_gsheets = True
except Exception:
    use_gsheets = False

LOCAL_FILE = "resultats_audit_qualite.csv"

# -----------------------------------------------------------------------------
# 2. DICTIONNAIRES COMPLETS DES QUESTIONS (34 Personnel + 52 Responsables)
# -----------------------------------------------------------------------------
QUESTIONS_PERSONNEL = {
    "1. Vision et Mission": [
        "Connaissez-vous la politique de votre entreprise en matière de la sécurité des aliments ?",
        "Avez-vous reçu des connaissances sur la vision et la mission de l'entreprise ?",
        "Pouvez-vous me expliquer la vision et la mission de l'entreprise ?",
        "Savez-vous que l'entreprise dispose des certifications qualité ?",
        "Vos responsables vous communiquent-ils les attentes en matière de sécurité des aliments ?"
    ],
    "2. Personnel": [
        "Avez-vous suivi un sensibilisation en matière de sécurité des aliments lors des 2 derniers mois ?",
        "Êtes-vous favorisé(e) à la mise en place d'outils (interne, boîte à suggestions) pour signaler les problèmes ?",
        "Connaissez-vous les règles relatives aux droits au travail ?",
        "Utilisez-vous des gants lorsque vous touchez les aliments ?",
        "Respectez-vous les protocoles de lavage des mains avant de manipuler les aliments ?",
        "Respectez-vous les règles concernant le non-port des bijoux, des vernis à ongles et des faux ongles ?",
        "Respectez-vous l'interdiction de manger au sein de l'unité, ainsi que de fumer ou de cracher ?",
        "Utilisez-vous le masque lorsque vous manipulez les aliments ?",
        "Respectez-vous les instructions de travail au sein de votre atelier ?",
        "Avez-vous été formé à la sécurité des aliments les 2 derniers mois ?",
        "Êtes-vous prêt à participer à des programmes de sensibilisation et de formation sur la sécurité des aliments ?"
    ],
    "3. Cohérence": [
        "Connaissez-vous vos responsabilités en matière de sécurité des aliments ?",
        "Avez-vous reçu une formation seulement sur vos responsabilités ?",
        "Vous sentez-vous valorisé après avoir présenté vos observations concernant la sécurité des aliments ?",
        "Les affiches ou mémentos sont-elles compréhensibles ?",
        "Êtes-vous favorisé à ce que des instructions soient affichées ou en couleur dans chaque atelier ?",
        "Êtes-vous consulté lors de l'élaboration des protocoles et des instructions sur la sécurité des aliments ?",
        "Participez-vous à des réunions sur la qualité des aliments ?"
    ],
    "4. Adaptabilité": [
        "Êtes-vous convoqué à des réunions d'information en cas de changements ou d'évolutions ?",
        "Vous adaptez-vous facilement aux changements ?",
        "Vous sentez-vous à l'aise d'arrêter la ligne chaque fois que vous constatez quelque chose qui pourrait nuire à la qualité ?",
        "Avez-vous suivi une formation à la suite des nouvelles évolutions (matériel, nouvelles instructions) ?",
        "Avez-vous été informé des procédures d'urgence à suivre en cas d'incident ?"
    ],
    "5. Connaissance des Dangers et Risques": [
        "Avez-vous reçu une formation sur la gestion des risques et des dangers ?",
        "Savez-vous ce qu'est la contamination croisée ?",
        "Comprenez-vous comment les aliments peuvent être contaminés par des agents physiques, chimiques, microbiologiques ou allergènes ?",
        "Êtes-vous en mesure d'identifier les risques liés à la sécurité des aliments dans votre environnement de travail ?",
        "Signalez-vous immédiatement tout incident ou toute contamination potentielle des aliments ?",
        "Respectez-vous les instructions de travail visant à limiter la contamination croisée ?"
    ]
}

QUESTIONS_RESPONSABLES = {
    "1. Vision et Mission": [
        "Q1.1 : La direction démontre-t-elle son engagement envers la sécurité des aliments (politique, objectifs, ressources) ?",
        "Q1.2 : L'importance de la politique et les objectifs sont-ils communiqués, compris et appliqués par l'ensemble du personnel ?",
        "Q1.3 : La direction encourage-t-elle activement l'amélioration continue de la culture via formations/événements ?",
        "Q2.1 : Les attentes relatives à la sécurité des aliments sont-elles communiquées de manière claire et quotidienne ?",
        "Q2.2 : Des formations sont-elles organisées régulièrement pour s'assurer de la compréhension des attentes ?",
        "Q2.3 : Les communications (réunions, affichages, formations) sont-elles régulières et adaptées aux différents niveaux ?",
        "Q2.4 : La communication est-elle suivie d'une évaluation pour mesurer son efficacité (sondages, évaluations) ?",
        "Q3.1 : La vision et la mission sont-elles affichées, communiquées et intégrées dans les documents et activités ?",
        "Q3.2 : Les employés reçoivent-ils une présentation de la vision et mission lors de leur intégration ?",
        "Q3.3 : Des rappels de la vision/mission sont-ils régulièrement partagés lors de réunions/briefings ?",
        "Q3.4 : L'entreprise a-t-elle évalué récemment la compréhension et l'adhésion des employés à la mission/vision ?"
    ],
    "2. Personnel": [
        "Q7.1 : Existe-t-il un canal formel pour signaler les préoccupations (registre, application, boîte dédiée) connu de tous ?",
        "Q7.2 : L'environnement encourage-t-il l'expression libre des inquiétudes sans crainte ?",
        "Q7.3 : Les alertes signalées au cours des 6 derniers mois ont-elles été suivies d'actions correctives concrètes ?",
        "Q7.4 : Chaque collaborateur est-il conscient de l'impact direct de sa performance individuelle sur la sécurité des aliments ?",
        "Q8.1 : Avez-vous une mission clairement définie et êtes-vous conscient de l'impact de vos actions quotidiennes ?",
        "Q8.2 : Appliquez-vous systématiquement les bonnes pratiques et participez-vous aux réunions qualité ?",
        "Q8.3 : Avez-vous été formé(e) les 12 derniers mois et contribué à sensibiliser vos collègues ?",
        "Q9.1 : Existe-t-il des indicateurs de performance dédiés suivis à fréquence régulière et communiqués ?",
        "Q9.2 : Le suivi de performance intègre-t-il la mesure des non-conformités, alertes et réclamations clients ?",
        "Q9.3 : Les audits évaluent-ils ces performances et les écarts constatés sont-ils analysés ?"
    ],
    "3. Cohérence": [
        "Q4.1 : Les employés participent-ils à la création, mise à jour et amélioration des procédures ?",
        "Q4.2 : Les suggestions des employés sont-elles valorisées, prises en compte et intégrées ?",
        "Q4.3 : Les instructions de travail sont-elles testées en conditions réelles avec les opérateurs avant validation ?",
        "Q5.1 : Les documents sont-ils clairs, régulièrement à jour, communiqués et facilement accessibles ?",
        "Q5.2 : La documentation aide-t-elle les employés à prendre les bonnes décisions en cas d'imprévu ?",
        "Q5.3 : Existe-t-il des supports visuels ou simplifiés pour soutenir la compréhension ?",
        "Q5.4 : Les documents sont-ils conçus pour faciliter la conformité plutôt que complexifier les tâches ?",
        "Q6.1 : Les employés participent-ils à l'amélioration des procédures et les modifications sont-elles communiquées ?",
        "Q6.2 : Y a-t-il un mécanisme formel encourageant les employés à proposer des améliorations ?",
        "Q6.3 : Y a-t-il une formation spécifique permettant aux employés de contribuer à l'amélioration des protocoles ?",
        "Q6.4 : Les retours d'audit ou de production sont-ils analysés avec les opérateurs ?",
        "Q6.5 : L'implication des employés dans l'amélioration est-elle suivie et mesurée ?"
    ],
    "4. Adaptabilité": [
        "Q10.1 : Votre organisation met-elle en place une veille pour anticiper les évolutions réglementaires ou sectorielles ?",
        "Q10.2 : Existe-t-il une procédure de gestion du changement intégrée permettant d'évaluer systématiquement les risques ?",
        "Q10.3 : Utilisez-vous les retours d'expérience pour améliorer vos pratiques et maintenir le plan de gestion de crise ?",
        "Q10.4 : Des formations/réunions sont-elles organisées lors de l'introduction de nouveaux procédés ou exigences ?",
        "Q10.5 : Avez-vous un plan de continuité ou de gestion de crise lié à la sécurité des aliments ?",
        "Q11.1 : Les décisions opérationnelles intègrent-elles systématiquement les exigences de sécurité des aliments ?",
        "Q11.2 : Les responsables sont-ils formés et sensibilisés à prendre des décisions conformes ?",
        "Q11.3 : Les décisions prises et les attentes sont-elles régulièrement revues et communiquées ?",
        "Q12.1 : L'entreprise dispose-t-elle d'une stratégie documentée pour gérer les situations d'urgence ?",
        "Q12.2 : Les rôles et responsabilités sont-ils clairement définis et les collaborateurs formés ?",
        "Q12.3 : Les retours d'expérience sont-ils utilisés pour améliorer la stratégie FSSC 22000 ?",
        "Q12.4 : Des exercices ou des simulations de crise sont-ils réalisés régulièrement ?"
    ],
    "5. Connaissance des Dangers et Risques": [
        "Q13.1 : Existe-t-il une procédure documentée pour signaler, enregistrer et analyser les quasi-accidents ?",
        "Q13.2 : Les collaborateurs sont-ils formés et encouragés à identifier et signaler les risques ?",
        "Q13.3 : Les analyses des quasi-accidents permettent-elles de mettre en œuvre des actions préventives efficaces ?",
        "Q13.4 : Les actions mises en place sont-elles suivies et évaluées pour prévenir la récurrence ?",
        "Q14.1 : L'entreprise dispose-t-elle d'un système pour promouvoir, suivre et évaluer l'engagement du personnel ?",
        "Q14.2 : Les responsables montrent-ils l'exemple et soutiennent-ils le signalement des risques ?",
        "Q14.3 : Les comportements non conformes sont-ils corrigés et les initiatives positives valorisées ?"
    ]
}

# -----------------------------------------------------------------------------
# 3. EN-TÊTE DE L'APPLICATION
# -----------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>Évaluation de la Culture Sécurité des Aliments</h1>
    <p>Référentiel FSSC 22000 / ISO 22000 — Grille d'Évaluation Opérateurs & Responsables</p>
</div>
""", unsafe_allow_html=True)

tab_form, tab_dash = st.tabs(["📋 Saisie du Questionnaire", "📊 Dashboard & Statistiques Globales"])

# -----------------------------------------------------------------------------
# ONGLET 1 : SAISIE DU QUESTIONNAIRE
# -----------------------------------------------------------------------------
with tab_form:
    st.subheader("📝 Formulaire d'Évaluation Terrain")
    
    with st.form("audit_form_full", clear_on_submit=True):
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            evaluateur = st.text_input("Nom / Matricule Évaluateur", placeholder="Ex: Mohamed Ben Ali")
        with col_m2:
            profil = st.selectbox("Profil Évalué", ["Personnel / Opérateur", "Responsable / Cadre"])
        with col_m3:
            atelier = st.selectbox("Atelier / Secteur", ["Préparation", "Cuisson", "Conditionnement", "Stockage & Logistique", "Laboratoire / Qualité", "Direction"])

        st.markdown("---")
        
        # Choix du dictionnaire selon le profil
        current_questions = QUESTIONS_PERSONNEL if profil == "Personnel / Opérateur" else QUESTIONS_RESPONSABLES
        
        st.info(f"💡 Vous remplissez la grille pour : **{profil}** ({sum(len(q) for q in current_questions.values())} questions au total).")

        responses = {}
        options = ["Oui (100%)", "En partie (50%)", "Non (0%)"]

        # Affichage structuré par Dimension
        dim_scores = {}
        
        for dim_name, q_list in current_questions.items():
            with st.expander(f"📌 {dim_name} ({len(q_list)} questions)", expanded=True):
                dim_numeric_scores = []
                for idx, q_text in enumerate(q_list):
                    q_key = f"{profil}_{dim_name}_{idx}"
                    ans = st.radio(f"**{idx+1}.** {q_text}", options, index=0, horizontal=True, key=q_key)
                    
                    val = 100 if ans == "Oui (100%)" else (50 if ans == "En partie (50%)" else 0)
                    dim_numeric_scores.append(val)
                
                dim_scores[dim_name] = sum(dim_numeric_scores) / len(dim_numeric_scores)

        st.markdown("---")
        commentaires = st.text_area("Observations & Remarques Terrain", placeholder="Ex: Besoins de révisions des affichages d'hygiène au poste 3...")
        
        submitted = st.form_submit_button("💾 Enregistrer l'Audit dans la Base de Données")

        if submitted:
            if not evaluateur:
                st.error("⚠️ Veuillez indiquer le nom ou le matricule de l'évaluateur.")
            else:
                # Calcul des sous-scores
                global_score = sum(dim_scores.values()) / len(dim_scores)

                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Evaluateur": evaluateur,
                    "Profil": profil,
                    "Atelier": atelier,
                    "Score_Global_%": round(global_score, 1),
                    "Vision_Mission_%": round(dim_scores.get("1. Vision et Mission", 0), 1),
                    "Personnel_%": round(dim_scores.get("2. Personnel", 0), 1),
                    "Coherence_%": round(dim_scores.get("3. Cohérence", 0), 1),
                    "Adaptabilite_%": round(dim_scores.get("4. Adaptabilité", 0), 1),
                    "Conscience_Risques_%": round(dim_scores.get("5. Connaissance des Dangers et Risques", 0), 1),
                    "Commentaires": commentaires
                }

                # Sauvegarde Google Sheets ou Local
                saved_successfully = False
                if use_gsheets:
                    try:
                        df_existing = conn.read(ttl="0")
                        df_updated = pd.concat([df_existing, pd.DataFrame([entry])], ignore_index=True)
                        conn.update(data=df_updated)
                        saved_successfully = True
                    except Exception:
                        pass
                
                if not saved_successfully:
                    df_entry = pd.DataFrame([entry])
                    if not os.path.exists(LOCAL_FILE):
                        df_entry.to_csv(LOCAL_FILE, index=False)
                    else:
                        df_entry.to_csv(LOCAL_FILE, mode='a', header=False, index=False)

                st.success("✅ Audit enregistré avec succès dans la base de données !")
                st.balloons()

# -----------------------------------------------------------------------------
# ONGLET 2 : DASHBOARD INTERACTIF ET GRAPHISTIQUES
# -----------------------------------------------------------------------------
with tab_dash:
    st.subheader("📊 Tableau de Bord Synthetique - Culture Qualité FSSC 22000")

    # Chargement des données
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
        st.info("ℹ️ Aucune donnée disponible. Veuillez remplir au moins un questionnaire.")
    else:
        # Filtres
        c_f1, c_f2 = st.columns(2)
        with c_f1:
            filter_atelier = st.selectbox("Filtrer par Atelier", ["Tous les ateliers"] + list(df["Atelier"].unique()))
        with c_f2:
            filter_profil = st.selectbox("Filtrer par Profil", ["Tous les profils"] + list(df["Profil"].unique()))

        filtered_df = df.copy()
        if filter_atelier != "Tous les ateliers":
            filtered_df = filtered_df[filtered_df["Atelier"] == filter_atelier]
        if filter_profil != "Tous les profils":
            filtered_df = filtered_df[filtered_df["Profil"] == filter_profil]

        if filtered_df.empty:
            st.warning("Aucun résultat ne correspond à ces filtres.")
        else:
            avg_global = filtered_df["Score_Global_%"].mean()
            avg_vm = filtered_df["Vision_Mission_%"].mean()
            avg_pers = filtered_df["Personnel_%"].mean()
            avg_coh = filtered_df["Coherence_%"].mean()
            avg_adapt = filtered_df["Adaptabilite_%"].mean()
            avg_dangers = filtered_df["Conscience_Risques_%"].mean()

            # Métriques
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Audits Réalisés", len(filtered_df))
            m2.metric("Maturité Globale", f"{avg_global:.1f} %", delta=f"{avg_global-80:.1f}% vs Obj 80%")
            m3.metric("Dimension Fort", "Vision & Mission" if avg_vm >= max(avg_pers, avg_coh, avg_adapt, avg_dangers) else "Conscience Risques")
            m4.metric("Dernière Saisie", str(filtered_df["Date"].iloc[-1]))

            st.markdown("---")

            # Graphiques Plotly
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=avg_global,
                    title={'text': "Taux de Maturité Globale (%)", 'font': {'size': 18}},
                    gauge={
                        'axis': {'range': [0, 100]},
                        'bar': {'color': "#059669"},
                        'steps': [
                            {'range': [0, 50], 'color': "#FEE2E2"},
                            {'range': [50, 75], 'color': "#FEF3C7"},
                            {'range': [75, 100], 'color': "#D1FAE5"}
                        ],
                        'threshold': {'line': {'color': "red", 'width': 4}, 'value': 80}
                    }
                ))
                fig_gauge.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig_gauge, use_container_width=True)

            with col_g2:
                categories = ['Vision & Mission', 'Personnel', 'Cohérence', 'Adaptabilité', 'Risques & Dangers']
                scores = [avg_vm, avg_pers, avg_coh, avg_adapt, avg_dangers]

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=scores + [scores[0]],
                    theta=categories + [categories[0]],
                    fill='toself',
                    name='Culture Qualité',
                    line_color='#1E3A8A',
                    fillcolor='rgba(30, 58, 138, 0.25)'
                ))
                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
                    showlegend=False,
                    title="Profil Radar FSSC 22000 (5 Dimensions)",
                    height=350,
                    margin=dict(l=40, r=40, t=50, b=20)
                )
                st.plotly_chart(fig_radar, use_container_width=True)

            # Bar Chart comparatif par Atelier
            st.markdown("#### 🏭 Comparatif par Atelier")
            df_at = filtered_df.groupby("Atelier")["Score_Global_%"].mean().reset_index()
            fig_bar = px.bar(
                df_at, x="Atelier", y="Score_Global_%",
                color="Score_Global_%", color_continuous_scale="Viridis",
                text_auto='.1f', title="Maturité Moyenne par Atelier (%)"
            )
            fig_bar.update_layout(height=320, yaxis_range=[0, 100])
            st.plotly_chart(fig_bar, use_container_width=True)

            # Table des résultats
            st.markdown("---")
            st.markdown("#### 📜 Historique Complet des Enregistrements")
            st.dataframe(filtered_df, use_container_width=True)
