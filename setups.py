import streamlit as st
import pandas as pd
import altair as alt

@st.cache_data
def load_data():
    df = pd.read_csv('materiel.csv')
    return df

st.set_page_config(page_title="Simulateur Couchage Bikepacking", layout="wide")
st.title("🏕️ Simulateur de Système de Couchage")

try:
    df = load_data()
except FileNotFoundError:
    st.error("Le fichier materiel.csv est introuvable.")
    st.stop()

matelas_df = df[df['Categorie'] == 'Matelas']
sacs_df = df[df['Categorie'] == 'Sac']
accessoires_df_base = df[df['Categorie'] == 'Accessoire']

# --- NOUVEAU : MODE PINGRE ---
st.sidebar.header("🛠️ Options Générales")
mode_pingre = st.sidebar.checkbox("🤑 Mode Pingre (Ignorer les accessoires)", value=False, help="Désactive les accessoires pour voir les statistiques pures du Matelas + Sac.")
st.sidebar.divider()

# Logique du Mode Pingre : On réduit la liste à "Aucun"
if mode_pingre:
    accessoires_df = accessoires_df_base[accessoires_df_base['Nom'] == 'Aucun']
else:
    accessoires_df = accessoires_df_base

# --- FONCTION DE COMPATIBILITE ---
def est_compatible(acc_compat, sac_nom, sac_type):
    if acc_compat == 'Toutes':
        return True
    if acc_compat == 'Quilt' and sac_type == 'Quilt':
        return True
    if acc_compat != 'Toutes' and acc_compat != 'Quilt' and acc_compat in sac_nom:
        return True
    return False

@st.cache_data
def generate_all_combos(m_df, s_df, a_df):
    combo_data = []
    for _, m in m_df.iterrows():
        for _, s in s_df.iterrows():
            for _, a in a_df.iterrows():
                if not est_compatible(a['Compatibilite'], s['Nom'], s['Type']):
                    continue
                
                poids = m['Poids_g'] + s['Poids_g'] + a['Poids_g']
                prix = m['Prix_Eur'] + s['Prix_Eur'] + a['Prix_Eur']
                temp = s['Temp_C'] - a['Gain_Temp_C']
                confort_score = m['Confort'] + s['Confort'] + a['Confort']
                
                combo_data.append({
                    'Matelas': m['Nom'], 
                    'Sac / Quilt': s['Nom'], 
                    'Accessoire': a['Nom'],
                    'Poids Matelas': m['Poids_g'],
                    'Poids Sac': s['Poids_g'],
                    'Poids Accessoire': a['Poids_g'],
                    'Poids Total (g)': poids, 
                    'Prix Total (€)': prix,
                    'Temp Finale (°C)': temp, 
                    'R-Value': m['R_Value'],
                    'Confort Total (/12)': round(confort_score, 1)
                })
    return pd.DataFrame(combo_data)

df_combos = generate_all_combos(matelas_df, sacs_df, accessoires_df)

if 'm_sel' not in st.session_state:
    st.session_state.m_sel = matelas_df['Nom'].iloc[0]
    st.session_state.s_sel = sacs_df['Nom'].iloc[0]
    st.session_state.a_sel = 'Aucun'

def appliquer_preset(matelas, sac, accessoire):
    st.session_state.m_sel = matelas
    st.session_state.s_sel = sac
    st.session_state.a_sel = accessoire

st.sidebar.header("🎯 Configurations Rapides")

best_light = df_combos.loc[df_combos['Poids Total (g)'].idxmin()]
if st.sidebar.button("🪶 Le plus léger"):
    appliquer_preset(best_light['Matelas'], best_light['Sac / Quilt'], best_light['Accessoire'])

best_budget = df_combos.loc[df_combos['Prix Total (€)'].idxmin()]
if st.sidebar.button("💰 Le moins cher"):
    appliquer_preset(best_budget['Matelas'], best_budget['Sac / Quilt'], best_budget['Accessoire'])

best_froid = df_combos.sort_values(by=['Temp Finale (°C)', 'R-Value'], ascending=[True, False]).iloc[0]
if st.sidebar.button("🏔️ Résiste le plus au froid"):
    appliquer_preset(best_froid['Matelas'], best_froid['Sac / Quilt'], best_froid['Accessoire'])

best_confort = df_combos.sort_values(by='Confort Total (/12)', ascending=False).iloc[0]
if st.sidebar.button("⭐ Le plus confortable"):
    appliquer_preset(best_confort['Matelas'], best_confort['Sac / Quilt'], best_confort['Accessoire'])

try:
    compromis_df = df_combos[(df_combos['Temp Finale (°C)'] <= -5) & (df_combos['R-Value'] >= 4.0)].copy()
    compromis_df['Score'] = compromis_df['Poids Total (g)'] * compromis_df['Prix Total (€)']
    best_compromis = compromis_df.loc[compromis_df['Score'].idxmin()]
    if st.sidebar.button("⚖️ Compromis Ultime (Froid + Léger)"):
        appliquer_preset(best_compromis['Matelas'], best_compromis['Sac / Quilt'], best_compromis['Accessoire'])
except:
    pass

st.sidebar.divider()

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("1. Matelas")
    matelas_choisi = st.selectbox("Choisis ton matelas :", matelas_df['Nom'], key='m_sel')
    matelas_data = matelas_df[matelas_df['Nom'] == matelas_choisi].iloc[0]
    st.caption(f"⚖️ **{matelas_data['Poids_g']}g** | 💰 **{matelas_data['Prix_Eur']}€** | 🌡️ R-Value: {matelas_data['R_Value']} | ⭐ **{matelas_data['Confort']}/5**")

with col2:
    st.subheader("2. Sac / Quilt")
    sac_choisi = st.selectbox("Choisis ton sac de couchage :", sacs_df['Nom'], key='s_sel')
    sac_data = sacs_df[sacs_df['Nom'] == sac_choisi].iloc[0]
    st.caption(f"⚖️ **{sac_data['Poids_g']}g** | 💰 **{sac_data['Prix_Eur']}€** | 🌡️ Temp: {sac_data['Temp_C']}°C | ⭐ **{sac_data['Confort']}/5**")

with col3:
    st.subheader("3. Accessoire")
    mask = accessoires_df.apply(lambda row: est_compatible(row['Compatibilite'], sac_data['Nom'], sac_data['Type']), axis=1)
    acc_dispos = accessoires_df[mask]
        
    if st.session_state.a_sel not in acc_dispos['Nom'].values:
        st.session_state.a_sel = 'Aucun'
        
    # Le sélecteur est visuellement désactivé si le mode pingre est ON
    acc_choisi = st.selectbox("Choisis ton drap/liner :", acc_dispos['Nom'], key='a_sel', disabled=mode_pingre)
    acc_data = accessoires_df[accessoires_df['Nom'] == acc_choisi].iloc[0]
    
    if mode_pingre:
        st.caption("🛑 *Désactivé par le Mode Pingre*")
    else:
        gain_txt = f"+{acc_data['Gain_Temp_C']}°C" if acc_data['Gain_Temp_C'] > 0 else "0"
        gain_conf = f"+{acc_data['Confort']}" if acc_data['Confort'] > 0 else "0"
        st.caption(f"⚖️ **{acc_data['Poids_g']}g** | 💰 **{acc_data['Prix_Eur']}€** | 🌡️ Gain: {gain_txt} | ⭐ Bonus: **{gain_conf}**")

poids_total = matelas_data['Poids_g'] + sac_data['Poids_g'] + acc_data['Poids_g']
prix_total = matelas_data['Prix_Eur'] + sac_data['Prix_Eur'] + acc_data['Prix_Eur']
r_value = matelas_data['R_Value']
temp_finale = sac_data['Temp_C'] - acc_data['Gain_Temp_C'] 
confort_total = matelas_data['Confort'] + sac_data['Confort'] + acc_data['Confort']

st.divider()

st.header("📊 Résultat de la sélection")
res_col1, res_col2, res_col3, res_col4 = st.columns(4)

res_col1.metric("Poids Total", f"{poids_total:.0f} g")
res_col2.metric("Prix Total", f"{prix_total:.0f} €")
res_col3.metric("Température Modulée", f"{temp_finale:.0f} °C", f"R-Value: {r_value:.1f}")
res_col4.metric("Score de Confort", f"{confort_total:.1f} / 12", "Max 12.0")

if r_value < 4.0:
    st.warning("⚠️ **Avertissement :** R-Value trop faible pour le Pamir ou les Alpes.")
if poids_total > 2000:
    st.warning(f"⚖️ **Poids élevé :** Ton système dépasse les 2 kg.")

st.divider()

st.header("📈 Comparateur Global des Combinaisons")

tab1, tab2, tab3 = st.tabs(["📋 Top (Tableau)", "📊 Composition du Poids", "🌌 Graphique Nuage"])

sort_col, order_col = st.columns(2)
with sort_col:
    critere = st.selectbox("Trier l'analyse par :", ["Confort Total (/12)", "Poids Total (g)", "Prix Total (€)", "Temp Finale (°C)"])
with order_col:
    ordre = st.radio("Ordre de tri :", ["Décroissant (Du meilleur au pire)", "Croissant (Du pire au meilleur)"])
    est_croissant = True if "Croissant" in ordre else False

nb_combos = 20
top10_df = df_combos.sort_values(by=critere, ascending=est_croissant).head(nb_combos).copy()
top10_df['Nom_Combo'] = top10_df['Matelas'].str.split().str[-1] + " + " + top10_df['Sac / Quilt'].str.split().str[0]
if not mode_pingre:
    top10_df['Nom_Combo'] += " + " + top10_df['Accessoire'].str.split().str[0]

with tab1:
    st.dataframe(top10_df[['Matelas', 'Sac / Quilt', 'Accessoire', 'Confort Total (/12)', 'Poids Total (g)', 'Prix Total (€)', 'Temp Finale (°C)', 'R-Value']], use_container_width=True, hide_index=True)

with tab2:
    st.write(f"Ce graphique décompose d'où vient le poids pour les **{nb_combos} meilleures combinaisons** selon le critère : {critere}.")
    top10_df['Rang'] = range(1, len(top10_df) + 1)
    top10_df['Label_Graphique'] = top10_df['Rang'].astype(str) + ". " + top10_df['Matelas'] + " + " + top10_df['Sac / Quilt']
    
    colonnes_id = ['Label_Graphique', 'Poids Total (g)']
    if critere not in colonnes_id:
        colonnes_id.append(critere)
    
    df_melt = top10_df.melt(id_vars=colonnes_id, 
                            value_vars=['Poids Matelas', 'Poids Sac', 'Poids Accessoire'],
                            var_name='Composant', value_name='Poids (g)')
    
    bar_chart = alt.Chart(df_melt).mark_bar().encode(
        y=alt.Y('Label_Graphique:N', 
                sort=alt.EncodingSortField(field=critere, order='ascending' if est_croissant else 'descending'), 
                title="",
                axis=alt.Axis(labelLimit=400)),
        x=alt.X('Poids (g):Q', title="Poids Cumulé (grammes)"),
        color=alt.Color('Composant:N', scale=alt.Scale(scheme='pastel1'), title="Élément"),
        tooltip=['Label_Graphique', 'Composant', 'Poids (g)', 'Poids Total (g)']
    ).interactive().properties(height=600)
    
    st.altair_chart(bar_chart, use_container_width=True)

with tab3:
    st.write("Le graphique global : Poids vs Prix. La taille des bulles représente le Confort !")
    graph = alt.Chart(df_combos).mark_circle(opacity=0.8).encode(
        x=alt.X('Poids Total (g)', scale=alt.Scale(zero=False)),
        y=alt.Y('Prix Total (€)', scale=alt.Scale(zero=False)),
        color=alt.Color('Temp Finale (°C)', scale=alt.Scale(scheme='redblue', reverse=True)),
        size=alt.Size('Confort Total (/12)', scale=alt.Scale(range=[10, 400]), title="Confort"),
        tooltip=['Matelas', 'Sac / Quilt', 'Accessoire', 'Confort Total (/12)', 'Poids Total (g)', 'Prix Total (€)', 'Temp Finale (°C)']
    ).interactive().properties(height=500)
    st.altair_chart(graph, use_container_width=True)