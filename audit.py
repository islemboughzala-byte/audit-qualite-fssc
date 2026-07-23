import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. CONFIGURATION & DESIGN CSS SUR MESURE (LOOK MODERN APP)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Audit Culture Qualité - FSSC 22000",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injection CSS avancée pour masquer le look "brut" de Streamlit
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');
    
    /* Police globale et fond */
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #F8FAFC;
        color: #1E293B;
    }
    
    /* Masquer le menu Streamlit et le footer par défaut */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Bannière de secours si pas d'image Canva */
    .fallback-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E3A8A 50%, #059669 100%);
        padding: 40px 20px;
        border-radius: 16px;
        color: white;
        text-align: center;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
    }
    .fallback-banner h1 {
        color: #FFFFFF !important;
        font-weight: 700;
        font-size: 2.2rem;
        margin-bottom: 8px;
        letter-spacing: -0.5px;
    }
    .fallback-banner p {
        color: #E2E8F0;
        font-size: 1.1rem;
        margin: 0;
    }

    /* Style des cartes pour les sections */
    .css-card {
        background-color: #FFFFFF;
        border-radius: 14px;
        padding: 24px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }

    /* Titres de sections */
    .section-header {
        color: #1E3A8A;
        font-weight: 700;
        font-size: 1.25rem;
        padding-left: 10px;
        border-left: 4px solid #059669;
        margin-top: 15px;
        margin-bottom: 15px;
    }

    /* Bouton d'enregistrement principal */
    .stButton>button {
        background: linear-gradient(135deg, #059669 0%, #047857 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        font-size: 1.1rem !important;
        border-radius: 10px !important;
        padding: 14px 28px !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(5, 150, 105, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100%;
        margin-top: 20px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 18px rgba(5, 150, 105, 0.4) !important;
    }

    /* Personnalisation des onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
        background-color: #E2E8F0;
        padding: 6px;
        border-radius: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #475569;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: #1E3A8A !important;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_allow_html=True)

# Connexion Google Sheets / CSV
try:
    from streamlit_gsheets import GSheetsConnection
    conn = st.connection("gsheets", type=GSheetsConnection)
    use_gsheets = True
except Exception:
    use_gsheets = False

LOCAL_FILE = "resultats_audit_qualite.csv"

# -----------------------------------------------------------------------------
# 2. DONNÉES : SOCIÉTÉS, DÉPARTEMENTS & QUESTIONS
# -----------------------------------------------------------------------------

DEPARTEMENTS_PAR_SOCIETE = {
    "El Mazraa": [
        "Charcuterie",
        "Surgelés",
        "Abattage & Découpe",
        "Produits Élaborés",
        "Stockage & Logistique",
        "Laboratoire / Qualité",
        "Maintenance & Technique"
    ],
    "Société 2": [
        "Production / Transformation",
        "Conditionnement",
        "Stockage & Froid",
        "Qualité & Hygiène",
        "Logistique"
    ],
    "Société 3": [
        "Unité de Production",
        "Emballage & Expédition",
        "Contrôle Qualité",
        "Maintenance"
    ]
}

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
        "Êtes-vous favorisé(e) à la mise en place d'outils (interne, comme une boîte à suggestions, pour signaler les problèmes et exprimer des idées d'amélioration au sein de l'entreprise) ?",
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
        "Vous sentez-vous à l'aise d'arrêter la ligne chaque fois que vous constatez quelque chose qui pourrait nuire à la qualité et à la sécurité des aliments ?",
        "Avez-vous suivi une formation à la suite des nouvelles évolutions (matériel, nouvelles instructions) ?",
        "Avez-vous été informé des procédures d'urgence à suivre en cas d'incident ?"
    ],
    "5. Connaissance des dangers et des risques": [
        "Avez-vous reçu une formation sur la gestion des risques et des dangers ?",
        "Savez-vous ce qu'est la contamination croisée ?",
        "Comprenez-vous comment les aliments peuvent être contaminés par des agents physiques, chimiques, microbiologiques ou allergènes ?",
        "Êtes-vous en mesure d'identifier les risques liés à la sécurité des aliments dans votre environnement de travail ?",
        "Signalez-vous immédiatement tout incident ou toute contamination potentielle des aliments ?",
        "Respectez-vous les instructions de travail visant à limiter la contamination croisée ?"
    ]
}

QUESTIONS_RESPONSABLES = {
    "1. Vision et mission": [
        "Q1.1 : La direction démontre-t-elle son engagement envers la sécurité des aliments en définissant une politique, des objectifs clairs et les suit régulièrement en mettant à disposition les ressources nécessaires ?",
        "Q1.2 : L'importance de la politique et les objectifs de sécurité des aliments sont-ils communiqués, compris et appliqués par l'ensemble du personnel ?",
        "Q1.3 : La direction encourage-t-elle activement l'amélioration continue de la culture de la sécurité des aliments par la participation à des formations ou des événements liés à la sécurité des aliments ?",
        "Q2.1 : Les attentes relatives à la sécurité des aliments sont-elles communiquées de manière claire quotidiennement, adaptée et comprise par tous les employés ?",
        "Q2.2 : Des formations sont-elles organisées régulièrement pour s'assurer que les employés comprennent les attentes en matière de sécurité des aliments ?",
        "Q2.3 : Les communications sur la sécurité des aliments (réunions, affichage, documents, formations...) sont-elles régulières et adaptées aux différents niveaux de l'entreprise ?",
        "Q2.4 : La communication de la sécurité des aliments est-elle suivie d'une évaluation pour mesurer son efficacité (par exemple, via des sondages auprès des employés ou des évaluations de compréhension) ?",
        "Q3.1 : La vision et la mission de l'entreprise sont-elles affichées, communiquées, accessibles et intégrées dans les documents et les activités de l'entreprise ?",
        "Q3.2 : Les employés reçoivent-ils une présentation de la vision et de la mission lors de leur intégration ou formation initiale ?",
        "Q3.3 : Des rappels ou des explications de la vision/mission sont-ils régulièrement partagés lors de réunions ou de briefings ?",
        "Q3.4 : L’entreprise a-t-elle évalué récemment la compréhension ou l’adhésion des employés à la mission et à la vision ?"
    ],
    "2. Cohérence": [
        "Q4.1 : Les employés participent-ils à la création, à la mise à jour et à l'amélioration des procédures de sécurité des aliments ?",
        "Q4.2 : Les suggestions des employés sont-elles valorisées, prises en compte et intégrées dans les processus ?",
        "Q4.3 : Les instructions de travail sont-elles testées en conditions réelles avec les opérateurs avant validation finale ?",
        "Q5.1 : Les documents relatifs à la sécurité des aliments sont-ils clairs, régulièrement à jour, communiqués aux personnes concernées et facilement accessibles par les personnels ?",
        "Q5.2 : La documentation aide-t-elle les employés à prendre les bonnes décisions en cas de doute ou de situation imprévue ?",
        "Q5.3 : Existe-t-il des supports visuels ou simplifiés pour soutenir la compréhension de la documentation ?",
        "Q5.4 : Les documents sont-ils conçus pour faciliter la conformité plutôt que pour complexifier les tâches ?",
        "Q6.1 : Les employés participent-ils à l'amélioration des procédures et les modifications sont-elles communiquées efficacement ?",
        "Q6.2 : Y a-t-il un mécanisme formel encourageant les employés de proposer des améliorations aux instructions en place ?",
        "Q6.3 : Y a-t-il une formation spécifique permettant aux employés de comprendre comment contribuer à l’amélioration des protocoles ?",
        "Q6.4 : Les retours d’audit ou de production sont-ils analysés avec les opérateurs pour ajuster les instructions ?",
        "Q6.5 : L’implication des employés dans l’amélioration est-elle suivie et mesurée ?"
    ],
    "3. Personnel": [
        "Q7.1 : Existe-t-il un canal formel pour signaler les préoccupations (registre, application, boîte dédiée) dont la procédure est connue et maîtrisée par tous les employés ?",
        "Q7.2 : Votre environnement de travail encourage-t-il l'expression libre des inquiétudes, et les employés se sentent-ils valorisés lorsqu'ils signalent une anomalie ou un risque ?",
        "Q7.3 : Les alertes signalées au cours des 6 derniers mois ont-elles été suivies d'actions correctives concrètes, et évaluez-vous l'efficacité de ce système pour l'améliorer ?",
        "Q7.4 : Chaque collaborateur est-il pleinement conscient de l'impact direct de sa performance individuelle et de ses signalements sur la sécurité des aliments ?",
        "Q8.1 : Avez-vous une mission clairement définie en sécurité des aliments et êtes-vous pleinement conscient de l’impact de vos actions quotidiennes sur la qualité du produit ?",
        "Q8.2 : Appliquez-vous systématiquement les bonnes pratiques, et participez-vous activement aux réunions qualité ainsi qu’aux actions d’amélioration continue ?",
        "Q8.3 : Avez-vous été formé(e) au cours des 12 derniers mois, et avez-vous déjà signalé des non-conformités ou contribué à sensibiliser vos collègues aux règles d’hygiène ?",
        "Q9.1 : Existe-t-il des indicateurs de performance dédiés à la sécurité des aliments, suivis à une fréquence régulière et communiqués aux équipes concernées ?",
        "Q9.2 : Votre suivi de performance intègre-t-il systématiquement la mesure des non-conformités, des alertes et l'analyse des réclamations clients ?",
        "Q9.3 : Les audits (internes/externes) évaluent-ils ces performances, et les écarts constatés sont-ils analysés pour ajuster vos indicateurs et vos objectifs ?"
    ],
    "4. Adaptabilité": [
        "Q10.1 : Votre organisation met-elle en place une veille pour anticiper les évolutions réglementaires ou sectorielles en sécurité des aliments ?",
        "Q10.2 : Existe-t-il une procédure de gestion du changement intégrée permettant d'évaluer systématiquement les risques et d'accompagner ces transitions par les formations et sensibilisations nécessaires ?",
        "Q10.3 : Utilisez-vous les retours d'expérience (leçons apprises des changements passés, efficacité des actions correctives) pour améliorer durablement vos pratiques et maintenir un plan de gestion de crise opérationnel ?",
        "Q10.4 : Des formations, sensibilisations ou réunions sont-elles organisées lors de l'introduction ou de la mise à jour de nouveaux procédés, produits ou exigences, ainsi qu'en cas de nouvelles exigences ou évolutions ?",
        "Q10.5 : Avez-vous un plan de continuité ou de gestion de crise lié à la sécurité des aliments ?",
        "Q11.1 : Les décisions opérationnelles intègrent-elles systématiquement les exigences de sécurité des aliments (nouveaux produits, changements de procédé, etc.) ?",
        "Q11.2 : Les responsables sont-ils formés et sensibilisés à prendre des décisions conformes aux exigences de sécurité des aliments ?",
        "Q11.3 : Les décisions prises et les attentes en matière de sécurité des aliments sont-elles régulièrement revues et communiquées en cas de changement ?",
        "Q12.1 : L’entreprise dispose-t-elle d’une stratégie documentée pour gérer les situations d’urgence ou les changements critiques liés à la sécurité des aliments ?",
        "Q12.2 : Les rôles et responsabilités sont-ils clairement définis, et les collaborateurs concernés sont-ils formés à appliquer cette stratégie ?",
        "Q12.3 : Les retours d’expérience sont-ils utilisés pour améliorer la stratégie et maintenir la conformité aux exigences FSSC 22000 ?",
        "Q12.4 : Des exercices ou des simulations sont-ils réalisés, et l’entreprise est-elle capable de réagir efficacement en cas d’incident ou d’alerte ?"
    ],
    "5. Connaissance des dangers et des risques": [
        "Q13.1 : L’entreprise dispose-t-elle d’une procédure documentée pour signaler, enregistrer et analyser les quasi-accidents, les non-conformités ou les risques liés à la sécurité des aliments ?",
        "Q13.2 : Les collaborateurs sont-ils formés et encouragés à identifier et signaler les risques liés à la sécurité des aliments ?",
        "Q13.3 : Les analyses des quasi-accidents et des non-conformités permettent-elles de mettre en œuvre des actions correctives et préventives efficaces ?",
        "Q13.4 : Les actions mises en place sont-elles suivies et évaluées afin de prévenir la récurrence des incidents et d’améliorer le système de sécurité des aliments ?",
        "Q14.1 : L’entreprise dispose-t-elle d’un système permettant de promouvoir, suivre et évaluer l’engagement du personnel en matière de sécurité des aliments ?",
        "Q14.2 : Les responsables montrent-ils l’exemple, et les employés sont-ils encouragés et soutenus pour signaler les risques, poser des questions et proposer des améliorations ?",
        "Q14.3 : Les comportements non conformes sont-ils rapidement corrigés, les initiatives positives valorisées et l’engagement maintenu de manière homogène dans tous les services ?"
    ]
}

# -----------------------------------------------------------------------------
# 3. AFFICHAGE DE LA BANNIÈRE (CANVA OU SECOURS)
# -----------------------------------------------------------------------------
if os.path.exists("banner.png"):
    st.image("banner.png", use_container_width=True)
elif os.path.exists("banner.jpg"):
    st.image("banner.jpg", use_container_width=True)
else:
    st.markdown("""
    <div class="fallback-banner">
        <h1>Évaluation de la Culture Sécurité des Aliments</h1>
        <p>Référentiel FSSC 22000 — Diagnostic Multi-Sociétés & Multi-Départements</p>
    </div>
    """, unsafe_allow_html=True)

tab_form, tab_dash = st.tabs(["📋 Formulaire d'Audit", "📊 Dashboard & Statistiques"])

# -----------------------------------------------------------------------------
# 4. ONGLET 1 : FORMULAIRE D'AUDIT
# -----------------------------------------------------------------------------
with tab_form:
    st.markdown("<div class='section-header'>1. Informations Générales</div>", unsafe_allow_html=True)
    
    with st.form("audit_form_main", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            evaluateur = st.text_input("Nom / Matricule Évaluateur", placeholder="Ex: Ben Ali")
            
        with c2:
            societe = st.selectbox("Société", list(DEPARTEMENTS_PAR_SOCIETE.keys()))
            
        with c3:
            departement_options = DEPARTEMENTS_PAR_SOCIETE[societe]
            departement = st.selectbox("Département / Secteur", departement_options)
            
        with c4:
            profil = st.selectbox("Profil Évalué", ["Personnel / Opérateur", "Responsable / Cadre"])

        current_questions = QUESTIONS_PERSONNEL if profil == "Personnel / Opérateur" else QUESTIONS_RESPONSABLES
        total_q = sum(len(q) for q in current_questions.values())
        
        st.info(f"💡 **Questionnaire chargé :** {societe} — Sector : **{departement}** | Profil : **{profil}** ({total_q} questions)")

        options = ["Oui (100%)", "En partie (50%)", "Non (0%)"]
        dim_scores = {}

        st.markdown("<div class='section-header'>2. Évaluation des Dimensions</div>", unsafe_allow_html=True)

        for dim_name, q_list in current_questions.items():
            st.markdown(f"#### 📌 {dim_name}")
            numeric_scores = []
            
            for idx, q_text in enumerate(q_list):
                key_id = f"{societe}_{departement}_{profil}_{dim_name}_{idx}"
                ans = st.radio(f"**{idx+1}.** {q_text}", options, index=0, horizontal=True, key=key_id)
                
                val = 100 if ans == "Oui (100%)" else (50 if ans == "En partie (50%)" else 0)
                numeric_scores.append(val)
                
            dim_scores[dim_name] = sum(numeric_scores) / len(numeric_scores)
            st.markdown("---")

        # Zone de remarques conservée
        st.markdown("<div class='section-header'>3. Remarques & Observations Terrain</div>", unsafe_allow_html=True)
        commentaires = st.text_area(
            "Observations, points forts ou opportunités d'amélioration constatés pendant l'entretien :",
            placeholder="Ex : Très bonne maîtrise des procédures d'hygiène, matériel bien entretenu..."
        )

        submitted = st.form_submit_button("💾 Enregistrer l'Audit")

        if submitted:
            if not evaluateur:
                st.error("⚠️ Veuillez renseigner le nom ou le matricule de l'évaluateur avant de valider.")
            else:
                score_global = sum(dim_scores.values()) / len(dim_scores)

                entry = {
                    "Date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Evaluateur": evaluateur,
                    "Societe": societe,
                    "Departement": departement,
                    "Profil": profil,
                    "Score_Global_%": round(score_global, 1),
                    "Vision_Mission_%": round(dim_scores.get("1. Vision et mission", 0), 1),
                    "Personnel_%": round(dim_scores.get("2. Personnel", 0) if profil == "Personnel / Opérateur" else dim_scores.get("3. Personnel", 0), 1),
                    "Coherence_%": round(dim_scores.get("3. Cohérence", 0) if profil == "Personnel / Opérateur" else dim_scores.get("2. Cohérence", 0), 1),
                    "Adaptabilite_%": round(dim_scores.get("4. Adaptabilité", 0), 1),
                    "Conscience_Risques_%": round(dim_scores.get("5. Connaissance des dangers et des risques", 0), 1),
                    "Remarques_Observations": commentaires
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

                st.success(f"✅ Audit enregistré avec succès pour {societe} ({departement}) !")
                st.balloons()

# -----------------------------------------------------------------------------
# 5. ONGLET 2 : DASHBOARD & STATISTIQUES
# -----------------------------------------------------------------------------
with tab_dash:
    st.markdown("<div class='section-header'>Tableau de Bord Synthetique</div>", unsafe_allow_html=True)

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
        st.info("ℹ️ Aucun audit n'a encore été enregistré. Complétez le formulaire pour alimenter les statistiques.")
    else:
        # Filtres
        f1, f2, f3 = st.columns(3)
        with f1:
            sel_soc = st.selectbox("Société", ["Toutes"] + list(df["Societe"].unique()))
        with f2:
            sel_dep = st.selectbox("Département", ["Tous"] + list(df["Departement"].unique()))
        with f3:
            sel_prof = st.selectbox("Profil", ["Tous"] + list(df["Profil"].unique()))

        filtered = df.copy()
        if sel_soc != "Toutes":
            filtered = filtered[filtered["Societe"] == sel_soc]
        if sel_dep != "Tous":
            filtered = filtered[filtered["Departement"] == sel_dep]
        if sel_prof != "Tous":
            filtered = filtered[filtered["Profil"] == sel_prof]

        if filtered.empty:
            st.warning("Aucune donnée ne correspond aux filtres sélectionnés.")
        else:
            avg_g = filtered["Score_Global_%"].mean()
            
            m1, m2, m3 = st.columns(3)
            m1.metric("Audits Réalisés", len(filtered))
            m2.metric("Score Moyen Global", f"{avg_g:.1f} %")
            m3.metric("Seuil FSSC 22000", "80.0 %", delta=f"{avg_g-80:.1f}%")

            st.markdown("---")

            g1, g2 = st.columns(2)

            with g1:
                cats = ['Vision & Mission', 'Personnel', 'Cohérence', 'Adaptabilité', 'Risques']
                scs = [
                    filtered["Vision_Mission_%"].mean(),
                    filtered["Personnel_%"].mean(),
                    filtered["Coherence_%"].mean(),
                    filtered["Adaptabilite_%"].mean(),
                    filtered["Conscience_Risques_%"].mean()
                ]
                
                fig_r = go.Figure()
                fig_r.add_trace(go.Scatterpolar(
                    r=scs + [scs[0]],
                    theta=cats + [cats[0]],
                    fill='toself',
                    fillcolor='rgba(5, 150, 105, 0.2)',
                    line_color='#059669'
                ))
                fig_r.update_layout(
                    polar=dict(radialaxis=dict(range=[0, 100])),
                    title="<b>Niveau de Maturité par Axe (%)</b>",
                    showlegend=False
                )
                st.plotly_chart(fig_r, use_container_width=True)

            with g2:
                df_dep = filtered.groupby("Departement")["Score_Global_%"].mean().reset_index()
                fig_b = px.bar(
                    df_dep, x="Departement", y="Score_Global_%",
                    color="Score_Global_%", text_auto='.1f',
                    title="<b>Score Moyen par Département (%)</b>",
                    color_continuous_scale="Blues"
                )
                fig_b.update_layout(yaxis_range=[0, 100], showlegend=False)
                st.plotly_chart(fig_b, use_container_width=True)

            st.markdown("---")
            st.markdown("#### 📜 Historique complet des saisies & remarques")
            st.dataframe(filtered, use_container_width=True)
