import streamlit as st
import pandas as pd
import os
from datetime import datetime

FICHIER_DONNEES = "donnees_culture_qualite.csv"

st.set_page_config(page_title="Évaluation FSSC 22000", layout="wide")

st.title("🎯 Évaluation de la Culture Sécurité des Aliments")
st.markdown("---")

# --- 1. SÉLECTION DU PÉRIMÈTRE (Cascading menus) ---
col1, col2 = st.columns(2)

with col1:
    type_quest = st.radio("Cible du questionnaire :", ["Personnel", "Responsable"])
    societe = st.selectbox("Sélectionnez la société :", ["", "el dick", "el mazraa", "essanwbar"])

with col2:
    activite = ""
    # Logique d'affichage selon la société
    if societe == "el dick":
        activite = st.selectbox("Activité :", ["abattoir poulet"])
    elif societe == "el mazraa":
        activite = st.selectbox("Activité :", ["", "abattoir dinde", "charcuterie", "surgelé", "pet food", "usine de co-produit", "croquette"])
    elif societe == "essanwbar":
        activite = st.selectbox("Activité :", ["plat prepare"])
        
    sous_categorie = ""
    if activite == "charcuterie":
        sous_categorie = st.selectbox("Étape du process (Charcuterie) :", ["", "préparation", "cuisson", "conditionnement"])

# --- 2. AFFICHAGE DU QUESTIONNAIRE ---
# On affiche le formulaire uniquement si la zone charcuterie est bien définie (pour le test)
if activite == "charcuterie" and sous_categorie != "":
    st.markdown(f"### 📋 Questionnaire {type_quest} - El Mazraa (Charcuterie / {sous_categorie})")
    
    with st.form("form_fssc", clear_on_submit=True):
        
        # --- QUESTIONNAIRE RESPONSABLE ---
        if type_quest == "Responsable":
            st.subheader("1. Vision et mission")
            r_q1 = st.radio("Q1 : La direction démontre-t-elle son engagement (politique, objectifs, ressources, culture) ?", ["Oui", "En partie", "Non"])
            r_q2 = st.radio("Q2 : La communication est-elle claire, quotidienne, adaptée et évaluée ?", ["Oui", "En partie", "Non"])
            r_q3 = st.radio("Q3 : La vision/mission est-elle affichée, comprise et intégrée dès l'intégration ?", ["Oui", "En partie", "Non"])
            
            st.subheader("2. Cohérence")
            r_q4 = st.radio("Q4 : Les employés participent-ils à l'amélioration des procédures et leurs suggestions sont-elles valorisées ?", ["Oui", "En partie", "Non"])
            r_q5 = st.radio("Q5 : La documentation est-elle claire, visuelle et aide-t-elle à prendre les bonnes décisions ?", ["Oui", "En partie", "Non"])
            r_q6 = st.radio("Q6 : Les employés sont-ils impliqués dans la conception et l'amélioration des protocoles ?", ["Oui", "En partie", "Non"])
            
            st.subheader("3. Personnel")
            r_q7 = st.radio("Q7 : Existe-t-il un canal formel et sûr pour signaler les préoccupations, suivi d'actions correctives ?", ["Oui", "En partie", "Non"])
            r_q8 = st.radio("Q8 : Chaque responsable est-il conscient de son impact et applique-t-il les bonnes pratiques ?", ["Oui", "En partie", "Non"])
            r_q9 = st.radio("Q9 : La performance est-elle mesurée (indicateurs, non-conformités, audits) et communiquée ?", ["Oui", "En partie", "Non"])
            
            st.subheader("4. Adaptabilité")
            r_q10 = st.radio("Q10 : L'organisation anticipe-t-elle les changements (veille, gestion du changement, retours d'expérience) ?", ["Oui", "En partie", "Non"])
            r_q11 = st.radio("Q11 : Les décisions opérationnelles intègrent-elles systématiquement les exigences Food Safety ?", ["Oui", "En partie", "Non"])
            r_q12 = st.radio("Q12 : Une stratégie d'urgence est-elle documentée, testée par des simulations et maîtrisée ?", ["Oui", "En partie", "Non"])
            
            st.subheader("5. Conscience des dangers et des risques")
            r_q13 = st.radio("Q13 : Les quasi-accidents sont-ils signalés, analysés et suivis d'actions préventives ?", ["Oui", "En partie", "Non"])
            r_q14 = st.radio("Q14 : L'engagement du personnel est-elle évaluée et les initiatives positives valorisées ?", ["Oui", "En partie", "Non"])

        # --- QUESTIONNAIRE PERSONNEL ---
        else:
            st.subheader("1. Vision et mission")
            p_q1 = st.radio("Connaissez-vous la politique de votre entreprise en matière de sécurité des aliments ?", ["Oui", "Non"])
            p_q2 = st.radio("Avez-vous reçu des connaissances sur la vision et la mission de l'entreprise (et pouvez-vous l'expliquer) ?", ["Oui", "Non"])
            p_q3 = st.radio("Savez-vous que l'entreprise dispose de certifications qualité ?", ["Oui", "Non"])
            p_q4 = st.radio("Vos responsables vous communiquent-ils les attentes en matière de sécurité des aliments ?", ["Oui", "Non"])

            st.subheader("2. Personnel")
            p_q5 = st.radio("Avez-vous suivi une sensibilisation en matière de sécurité des aliments lors des 2 derniers mois ?", ["Oui", "Non"])
            p_q6 = st.radio("Êtes-vous favorisé(e) à la mise en place d'outils (ex: boîte à suggestions) ?", ["Oui", "Non"])
            p_q7 = st.radio("Respectez-vous rigoureusement les règles d'hygiène (gants, lavage des mains, masque) ?", ["Oui", "Non"])
            p_q8 = st.radio("Respectez-vous l'interdiction de manger, fumer, cracher, et le non-port de bijoux/vernis ?", ["Oui", "Non"])

            st.subheader("3. Cohérence")
            p_q9 = st.radio("Connaissez-vous vos responsabilités exactes en matière de sécurité des aliments ?", ["Oui", "Non"])
            p_q10 = st.radio("Vous sentez-vous valorisé après avoir présenté vos observations ?", ["Oui", "Non"])
            p_q11 = st.radio("Les affiches/mémentos sont-ils compréhensibles et visibles dans votre atelier ?", ["Oui", "Non"])
            p_q12 = st.radio("Êtes-vous consulté lors de l'élaboration des protocoles ou participez-vous aux réunions ?", ["Oui", "Non"])

            st.subheader("4. Adaptabilité")
            p_q13 = st.radio("Êtes-vous convoqué à des réunions en cas de changements (matériel, nouvelles instructions) ?", ["Oui", "Non"])
            p_q14 = st.radio("Vous sentez-vous à l'aise d'arrêter la ligne si vous constatez un risque pour la sécurité des aliments ?", ["Oui", "Non"])
            p_q15 = st.radio("Avez-vous été informé des procédures d'urgence à suivre en cas d'incident ?", ["Oui", "Non"])

            st.subheader("5. Connaissance des dangers et des risques")
            p_q16 = st.radio("Avez-vous reçu une formation sur la contamination croisée et les agents (physiques, chimiques, bio, allergènes) ?", ["Oui", "Non"])
            p_q17 = st.radio("Êtes-vous en mesure d'identifier les risques dans votre environnement de travail ?", ["Oui", "Non"])
            p_q18 = st.radio("Signalez-vous immédiatement tout incident ou toute contamination potentielle ?", ["Oui", "Non"])

        # Bouton de validation
        submit = st.form_submit_button("💾 Enregistrer l'évaluation")

        # Logique de sauvegarde basique pour le moment
        if submit:
            st.success("Données enregistrées avec succès ! (La liaison avec la base de données est prête pour la prochaine étape)")
            
elif societe != "" and activite != "" and activite != "charcuterie":
    st.info("⚠️ Application en phase de test : Seule l'activité 'Charcuterie' est disponible pour le moment.")
