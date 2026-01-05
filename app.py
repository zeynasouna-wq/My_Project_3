import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns

# ==================================================
# CONFIG
# ==================================================
st.set_page_config(page_title="CoinAfrique Data App", layout="wide")

st.markdown("""
<style>
h1, h2, h3 { color: #7b61ff; }
</style>
""", unsafe_allow_html=True)


# ==================================================
# CONSTANTES
# ==================================================
MAX_PAGES_BY_CATEGORY = {
    "chiens": 11,
    "moutons": 16,
    "volailles": 10,
    "autres-animaux": 6
}

# ==================================================
# KPI CARD
# ==================================================
def kpi(title, value, color="#00d4ff"):
    st.markdown(
        f"""
        <div style="
            background-color:#0e1117;
            padding:20px;
            border-radius:14px;
            border:1px solid #262730;
            text-align:center;
            min-height:110px;
        ">
            <div style="color:{color}; font-size:14px; margin-bottom:8px;">
                {title}
            </div>
            <div style="color:white; font-size:26px; font-weight:600;">
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )



# ==================================================
# FONCTIONS
# ==================================================
def clean_webscraper_data(df):
    df = df.copy()
    if "Prix" in df.columns:
        df["Prix"] = df["Prix"].astype(str)
        df["Prix"] = df["Prix"].str.replace(r"(FCFA|F\s?CFA)", "", regex=True)
        df["Prix"] = df["Prix"].str.replace(" ", "", regex=False)
        df["Prix_Numeric"] = df["Prix"].str.replace(r"[^0-9]", "", regex=True)
        df["Prix_Numeric"] = pd.to_numeric(df["Prix_Numeric"], errors="coerce")
        df = df[df["Prix_Numeric"].notna()]
    return df

def remove_outliers(df, col="Prix_Numeric"):
    q_low = df[col].quantile(0.05)
    q_high = df[col].quantile(0.95)
    return df[(df[col] >= q_low) & (df[col] <= q_high)]

@st.cache_data
def load_data(methode, categorie):
    prefix = "bs" if methode == "beautifulsoup" else "ws"
    path = f"data/{methode}/{prefix}_coinafrique_{categorie}.csv"
    if os.path.exists(path):
        df = pd.read_csv(path, sep=None, engine="python")
        df.columns = df.columns.str.replace("\ufeff", "").str.strip()
        return df
    return None

def filter_by_pages_real(df, nb_pages, max_pages):
    rows_per_page = max(1, len(df) // max_pages)
    max_rows = nb_pages * rows_per_page
    return df.iloc[:min(len(df), max_rows)]

def show_df_info(df, label=""):
    st.info(f"📐 **{df.shape[0]} lignes × {df.shape[1]} colonnes** {label}")

# ==================================================
# SIDEBAR
# ==================================================
st.sidebar.title("🧭 Navigation")

page = st.sidebar.radio(
    "Aller vers :",
    [
        "🏠 Accueil",
        "📄 Consultation des données",
        "⬇️ Téléchargement (WebScraper brut)",
        "📊 Dashboard (WebScraper nettoyé)",
        "📝 Évaluer l'app"
    ]
)

st.sidebar.divider()

methode = st.sidebar.selectbox(
    "Méthode de scraping",
    ["beautifulsoup", "webscraper"]
)

categorie = st.sidebar.selectbox(
    "Catégorie",
    list(MAX_PAGES_BY_CATEGORY.keys())
)

max_pages = MAX_PAGES_BY_CATEGORY[categorie]

nb_pages = st.sidebar.slider(
    "Nombre de pages",
    1,
    max_pages,
    min(5, max_pages)
)

# ==================================================
# ACCUEIL
# ==================================================
if page == "🏠 Accueil":
    st.title("🐾 CoinAfrique – Application de Data Scraping")
    st.markdown("""
    Cette application permet :
    - consulter les données scrapées via BeautifulSoup et WebScraper
    - télécharger les données brutes issues de WebScraper
    - analyser les données nettoyées via un dashboard interactif
    """)

# ==================================================
# CONSULTATION
# ==================================================
elif page == "📄 Consultation des données":
    st.title("📄 Consultation des données")

    df = load_data(methode, categorie)
    if df is not None:
        df_view = filter_by_pages_real(df, nb_pages, max_pages)
        show_df_info(df_view, f"(simulation {nb_pages} page(s))")
        st.dataframe(df_view, use_container_width=True)
    else:
        st.error("❌ Données introuvables")

# ==================================================
# TELECHARGEMENT
# ==================================================
elif page == "⬇️ Téléchargement (WebScraper brut)":
    st.title("⬇️ Téléchargement des données brutes")

    if methode != "webscraper":
        st.warning("Disponible uniquement pour WebScraper")
    else:
        df = load_data("webscraper", categorie)
        if df is not None:
            df_dl = filter_by_pages_real(df, nb_pages, max_pages)
            show_df_info(df_dl)
            st.dataframe(df_dl, use_container_width=True)

            csv = df_dl.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Télécharger le CSV brut",
                csv,
                f"coinafrique_{categorie}_webscraper_brut.csv",
                "text/csv"
            )

# ==================================================
# DASHBOARD
# ==================================================
elif page == "📊 Dashboard (WebScraper nettoyé)":
    st.title("📊 Dashboard – WebScraper nettoyé")

    if methode != "webscraper":
        st.warning("⚠️ Disponible uniquement pour WebScraper.")
    else:
        df = load_data("webscraper", categorie)

        if df is not None:
            df_clean = clean_webscraper_data(df)
            df_clean = remove_outliers(df_clean)
            df_dash = filter_by_pages_real(df_clean, nb_pages, max_pages)

            show_df_info(df_dash, f"(simulation {nb_pages} page(s))")

            # =====================================
            # 1. DISTRIBUTION DES PRIX
            # =====================================
            st.subheader("📈 Distribution des prix")

            prix = df_dash["Prix_Numeric"].dropna()

            if prix.empty or prix.nunique() < 2:
                st.warning("⚠️ Pas assez de données pour afficher la distribution des prix.")
            else:
                fig, ax = plt.subplots(figsize=(7, 4))

                sns.histplot(
                    prix,
                    bins=30,
                    kde=True,
                    ax=ax
                )

                ax.set_title("Distribution des prix des annonces")
                ax.set_xlabel("Prix (FCFA)")
                ax.set_ylabel("Nombre d'annonces")

                st.pyplot(fig)

            st.divider()


            # =====================================
            # 2. TRANCHES DE PRIX
            # =====================================
            st.subheader("📊 Répartition par tranches de prix")

            prix = df_dash["Prix_Numeric"].dropna()
            if prix.nunique() >= 3:
                df_dash["Tranche_Prix"] = pd.qcut(
                    prix,
                    q=min(5, prix.nunique()),
                    duplicates="drop"
                )

                tranche_df = (
                    df_dash
                    .groupby("Tranche_Prix", observed=True)
                    .size()
                    .reset_index(name="Nombre d'annonces")
                )

                fig, ax = plt.subplots()
                ax.bar(
                    tranche_df["Tranche_Prix"].astype(str),
                    tranche_df["Nombre d'annonces"]
                )
                ax.set_xlabel("Tranche de prix (FCFA)")
                ax.set_ylabel("Nombre d'annonces")
                plt.xticks(rotation=45)
                st.pyplot(fig)
            else:
                st.warning("Pas assez de variation de prix pour afficher les tranches.")

            st.divider()

            # =====================================
            # 3. RÉPARTITION GÉOGRAPHIQUE
            # =====================================
            if "Adresse" in df_dash.columns:
                st.subheader("📍 Répartition géographique (Top 10)")

                loc = df_dash["Adresse"].value_counts().head(10)
                st.bar_chart(loc)

                st.divider()

            # =====================================
            # 4. TOP 10 ANNONCES
            # =====================================
            st.subheader("🏆 Top 10 annonces les plus chères")
            top10 = df_dash.sort_values("Prix_Numeric", ascending=False).head(10)
            show_df_info(top10)
            st.dataframe(top10, use_container_width=True)

            st.divider()

        
            # =====================================
            # 5. KPI (SYNTHÈSE FINALE)
            # =====================================
            c1, c2, c3, c4 = st.columns(4)

            with c1:
                kpi("📦 Annonces", len(df_dash))

            with c2:
                kpi(
                    "💰 Prix moyen",
                    f"{int(df_dash['Prix_Numeric'].mean()):,} FCFA".replace(",", " ")
                )

            with c3:
                kpi(
                    "📊 Prix médian",
                    f"{int(df_dash['Prix_Numeric'].median()):,} FCFA".replace(",", " ")
                )

            with c4:
                kpi(
                    "⬆️ Prix max",
                    f"{int(df_dash['Prix_Numeric'].max()):,} FCFA".replace(",", " ")
            )

            # =====================================
            # 6. DONNÉES UTILISÉES
            # =====================================
            with st.expander("📄 Voir les données nettoyées utilisées pour le dashboard"):
                show_df_info(df_dash)
                st.dataframe(df_dash, use_container_width=True)


           

# ==================================================
# ÉVALUATION
# ==================================================
elif page == "📝 Évaluer l'app":
    st.title("📝 Évaluer l'application")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("[👉 Formulaire Kobo](https://ee.kobotoolbox.org/x/irBDbBex)")
    with c2:
        st.markdown("[👉 Google Forms](https://docs.google.com/forms/d/e/1FAIpQLScbB-zm6Wo8P3rmQO3PC4jjCFPd_Gt4-tBQ7_n-Nl1XAEiJbw/viewform?usp=header)")



