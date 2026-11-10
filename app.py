"""Application Dash Atlas Commerce. Compléter les ZONES dans l'ordre du TP."""
from dash import Dash, dcc, html, Input, Output, ctx
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from donnees import df, filtrer, calculer_kpis, mad

app = Dash(__name__, external_stylesheets=[dbc.themes.FLATLY])
app.title = "Atlas Commerce Dashboard decisionnel"

DATE_MIN = df["Date"].min().date().isoformat()
DATE_MAX = df["Date"].max().date().isoformat()

# ZONE FONCTIONS
def carte_kpi(titre, identifiant, classe_kpi, icone_symbole, classe_icone, variation_texte=""):
    """Construit une carte KPI stylisée avec icône pastel."""
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Div(icone_symbole, className=f"kpi-icon {classe_icone}"),
                html.Div([
                    html.Div(titre, className="kpi-label"),
                    html.Div("--", id=identifiant, className="kpi-valeur"),
                    html.Div(f"↑ {variation_texte} vs période précédente", className="kpi-variation")
                ], className="ms-3")
            ], className="d-flex align-items-center")
        ]), 
        className=f"kpi-card {classe_kpi}"
    )

def carte_graphique(identifiant):
    """Construit une carte contenant un graphique Dash."""
    return dbc.Card(dbc.CardBody(
        dcc.Loading(dcc.Graph(id=identifiant))
), className="graph-card")

def figure_vide(titre):
    """Affiche un message pour les filtres sans ventes."""
    fig = go.Figure()
    fig.add_annotation(
        text="Aucune vente pour ces filtres",
        x=0.5, y=0.5, xref="paper", yref="paper",
        showarrow=False
        )
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(title=titre, template="plotly_white", height=350)
    return fig

def harmoniser(fig):
    """Applique une hauteur et un fond communs aux figures."""
    fig.update_layout(
        template="plotly_white", height=360,
        margin=dict(l=25, r=20, t=60, b=35)
        )
    return fig

app.layout = dbc.Container([
    # ZONE ENTETE
    html.Div([
            html.H1("ATLAS COMMERCE"),
            html.P("Pilotage des ventes - jeu de donnees fictif")
        ], className="bandeau"),
    # ZONE FILTRES
        dbc.Card(
            dbc.CardBody(
                dbc.Row([
                    dbc.Col([
                        html.Label("Periode", className="etiquette"),
                        dcc.DatePickerRange(
                            id="dates",
                            start_date=DATE_MIN,
                            end_date=DATE_MAX,
                            min_date_allowed=DATE_MIN,
                            max_date_allowed=DATE_MAX,
                            display_format="DD/MM/YYYY"
                        )
                    ], xs=12, lg=5),
                    dbc.Col([
                        html.Label("Categorie", className="etiquette"),
                        dcc.Dropdown(
                            id="categorie",
                            value="Toutes",
                            options=["Toutes"] + sorted(df["Categorie"].unique()),
                            clearable=False
                        )
                    ], xs=12, lg=4),
                    dbc.Col([
                        html.Label("Regroupement temporel", className="etiquette"),
                        dcc.RadioItems(
                            id="freq",
                            value="M",
                            inline=True,
                            options=[
                                {"label": "Jour", "value": "J"},
                                {"label": "Mois", "value": "M"}
                            ]
                        )
                    ], xs=12, lg=3)
                ], className="g-3")
            ), className="filter-card mb-3"
        ),
    
# ZONE KPIS
        dbc.Row([
            dbc.Col(carte_kpi("Chiffre d'affaires", "ca", "kpi-ca", "📊", "icon-ca", "+8.4%"), xs=12, sm=6, lg=3),
            dbc.Col(carte_kpi("Commandes distinctes", "commandes", "kpi-commandes", "📦", "icon-commandes", "+4.6%"), xs=12, sm=6, lg=3),
            dbc.Col(carte_kpi("Panier moyen", "panier", "kpi-panier", "💳", "icon-panier", "+1.9%"), xs=12, sm=6, lg=3),
            dbc.Col(carte_kpi("Marge commerciale", "marge", "kpi-marge", "🤝", "icon-marge", "+10.3%"), xs=12, sm=6, lg=3),
        ], className="g-3 mb-4"),
        html.P(id="etat", className="text-muted"),
    # ZONE EVOLUTION UI
    dbc.Row([
        dbc.Col(carte_graphique("evolution"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE CATEGORIES UI
    dbc.Row([
        dbc.Col(carte_graphique("categories"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE REGIONS UI
    dbc.Row([
        dbc.Col(carte_graphique("regions"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE MARGES UI
    dbc.Row([
        dbc.Col(carte_graphique("marges"), xs=12)
    ], className="g-3 mb-4"),
    # ZONE TOP UI
    dbc.Row([
        dbc.Col([
            html.H5(id="titre-top"),
            carte_graphique("top-produits")
        ], xs=12)
    ], className="g-3 mb-4"),
    dcc.Store(id="region-active", data=None),
    # ZONE RESET UI
    dbc.Row([
        dbc.Col(dbc.Button(
            "Effacer le filtre region", id="reset-region",
            color="outline-secondary", className="mb-3"
        ), xs=12)
    ]),
    # ZONE MESSAGE UI
    dbc.Alert(id="lecture-metier", color="info"),
], fluid=True, className="px-3 px-xl-5 py-4")

# ZONE KPI CALLBACK
@app.callback(
        Output("ca", "children"),
        Output("commandes", "children"),
        Output("panier", "children"),
        Output("marge", "children"),
        Output("etat", "children"),
        Input("dates", "start_date"),
        Input("dates", "end_date"),
        Input("categorie", "value")
)
def actualiser_kpis(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    k = calculer_kpis(ventes)
    message = f"{len(ventes)} lignes | {k['commandes']} commandes"
    return (
        mad(k["ca"]), str(k["commandes"]),
        mad(k["panier"]), mad(k["marge"]), message
    )


# ZONE EVOLUTION CB
@app.callback(
       Output("evolution", "figure"),
       Input("dates", "start_date"),
       Input("dates", "end_date"),
       Input("categorie", "value"),
       Input("freq", "value")
   )
def tracer_evolution(debut, fin, categorie, freq):
       ventes = filtrer(debut, fin, categorie)
       if ventes.empty:
           return figure_vide("Évolution du chiffre d'affaires")
       
       ventes["Periode"] = (
           ventes["Date"].dt.to_period("M").dt.to_timestamp()
           if freq == "M" else ventes["Date"]
       )
       evolution = (
           ventes.groupby("Periode", as_index=False)["Chiffre_Affaires"]
           .sum().sort_values("Periode")
       )
       fig = px.line(
           evolution, x="Periode", y="Chiffre_Affaires",
           markers=True, title="Évolution du chiffre d'affaires",
           labels={"Chiffre_Affaires": "CA (MAD)"}
       )
       fig.update_traces(
           line=dict(color="#6366f1", width=3, shape="spline"),
           marker=dict(size=8, color="#4f46e5"),
           fill="tozeroy",
           fillcolor="rgba(99, 102, 241, 0.12)"
       )
       return harmoniser(fig)

# ZONE CATEGORIES CB
@app.callback(
        Output("categories", "figure"),
        Input("dates", "start_date"),
        Input("dates", "end_date"),
        Input("categorie", "value")
)
def tracer_categories(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("CA par categorie")
    resume = (ventes.groupby("Categorie", as_index=False)
              ["Chiffre_Affaires"].sum()
              .sort_values("Chiffre_Affaires", ascending=False))
    fig = px.bar(
    resume, x="Categorie", y="Chiffre_Affaires",
    color="Categorie", title="CA par categorie"
    )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)



# ZONE REGIONS CB
@app.callback(
    Output("regions", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_regions(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Part de chaque région")
    
    resume = (
        ventes.groupby("Region", as_index=False)["Chiffre_Affaires"].sum()
        .sort_values("Chiffre_Affaires", ascending=False)
    )
    
    # 1. Formatage du libellé de légende : Nom + Montant sur la ligne du dessous
    resume["Legende_Libelle"] = resume.apply(
        lambda r: f"{r['Region']}<br><b>{r['Chiffre_Affaires']:,.0f} MAD</b>".replace(",", " "), 
        axis=1
    )
    
    # 2. Calcul du total pour le centre exact du donut
    total_ca = resume["Chiffre_Affaires"].sum()
    total_texte = f"<b>{total_ca/1e6:.2f}M</b><br><span style='font-size:11px;color:#64748b;'>MAD</span>"
    
    # Palette pastel
    couleurs = ["#6366f1", "#0084ff", "#10b981", "#f97316", "#8b5cf6", "#94a3b8"]

    fig = px.pie(
        resume, 
        names="Legende_Libelle", 
        values="Chiffre_Affaires",
        title="Part de chaque région dans le CA",
        hole=0.55,
        color_discrete_sequence=couleurs
    )

    # 3. Placement et style des tranches
    fig.update_traces(
        textinfo="percent",
        textposition="inside",
        insidetextfont=dict(color="white", size=12, weight="bold"),
        marker=dict(line=dict(color="#ffffff", width=2)),
        domain=dict(x=[0.0, 0.45], y=[0.0, 1.0])  # Décale le donut à gauche pour laisser place à la légende
    )

    # 4. Positionnement du texte central et de la légende à droite
    fig.update_layout(
        annotations=[
            dict(
                text=total_texte,
                x=0.225, y=0.5, # Centré exactement au milieu du donut réaligné
                font_size=18,
                showarrow=False,
                align="center"
            )
        ],
        legend=dict(
            orientation="v",
            y=0.5,
            x=0.52,
            xanchor="left",
            yanchor="middle",
            font=dict(size=11, color="#1e293b"),
            tracegroupgap=8
        ),
        margin=dict(l=10, r=10, t=40, b=10)
    )

    return harmoniser(fig)
# ZONE MARGES CB
@app.callback(
    Output("marges", "figure"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value")
)
def tracer_marges(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return figure_vide("Marge par categorie")
    resume = (ventes.groupby("Categorie", as_index=False)
              ["Marge"].sum().sort_values("Marge", ascending=False))
    fig = px.bar(
        resume, x="Categorie", y="Marge", color="Categorie",
        title="Marge commerciale par categorie"
        )
    fig.update_layout(showlegend=False)
    return harmoniser(fig)
# ZONE TOP CB
@app.callback(
        Output("top-produits", "figure"),
        Output("titre-top", "children"),
        Input("dates", "start_date"),
        Input("dates", "end_date"),
        Input("categorie", "value"),
        Input("region-active", "data")
)
def tracer_top(debut, fin, categorie, region):
    ventes = filtrer(debut, fin, categorie)
    if region:
        ventes = ventes[ventes["Region"] == region].copy()
    titre = "Top produits" + (f" | {region}" if region else " | Toutes regions")
    if ventes.empty:
        return figure_vide(titre), titre
    resume = (ventes.groupby("Produit", as_index=False)
              ["Chiffre_Affaires"].sum()
              .nlargest(10, "Chiffre_Affaires")
              .sort_values("Chiffre_Affaires"))
    fig = px.bar(
        resume, x="Chiffre_Affaires", y="Produit",
        orientation="h", color="Chiffre_Affaires",
        color_continuous_scale="Blues"
    )
    fig.update_layout(coloraxis_showscale=False)
    return harmoniser(fig), titre
# ZONE RESET CB
@app.callback(
    Output("region-active", "data"),
    Input("regions", "clickData"),
    Input("reset-region", "n_clicks"),
    Input("dates", "start_date"),
    Input("dates", "end_date"),
    Input("categorie", "value"),
    prevent_initial_call=True
)
def selectionner_region(clic, reset, debut, fin, categorie):
    """Mémorise le clic régional ou efface le filtre au clic sur le bouton."""
    # 1. Si l'action vient du clic sur un secteur du donut
    if ctx.triggered_id == "regions" and clic and clic.get("points"):
        return clic["points"][0].get("label")
    
    # 2. Si l'action vient du bouton Reset, des dates ou de la catégorie
    return None
# ZONE MESSAGE CB
@app.callback(
        Output("lecture-metier", "children"),
        Input("dates", "start_date"),
        Input("dates", "end_date"),
        Input("categorie", "value")
)
def recommandation_metier(debut, fin, categorie):
    ventes = filtrer(debut, fin, categorie)
    if ventes.empty:
        return "Aucune vente : elargissez la plage ou changez la categorie."
    par_region = ventes.groupby("Region")["Chiffre_Affaires"].sum()
    par_categorie = ventes.groupby("Categorie")["Marge"].sum()
    region = par_region.idxmax()
    cat = par_categorie.idxmax()
    return (f"Region au CA le plus eleve : {region}. "
            f"Categorie a la marge totale la plus forte : {cat}. "
            "Analyse sur les filtres courants, pas en temps reel.")

if __name__ == "__main__":
    app.run(debug=True)