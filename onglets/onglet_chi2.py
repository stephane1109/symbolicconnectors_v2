"""# Onglet Test du chi2

Interface Streamlit pour construire un tableau de contingence à partir des
variables/modalités du corpus et des connecteurs sélectionnés, puis exécuter un
test du chi2 avec options complémentaires (simulation Monte Carlo, résidus,
export CSV)."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List

import altair as alt
import pandas as pd
import streamlit as st

from chi2 import (
    ResultatChiDeux,
    calculer_statistiques_chi2,
    construire_table_contingence_categories,
    construire_table_contingence_connecteurs,
    fusionner_tables_export,
    p_value_monte_carlo,
)
from connecteurs import get_selected_labels
from fcts_utils import render_connectors_reminder


def _afficher_residus_heatmap(residus: pd.DataFrame) -> None:
    """Afficher une heatmap Altair des résidus standardisés."""

    if residus.empty:
        st.info("Aucun résidu à afficher.")
        return

    data = residus.reset_index().rename(columns={residus.index.name or "index": "Modalité"})
    data_long = data.melt(id_vars=["Modalité"], var_name="Colonne", value_name="Résidu")

    chart = (
        alt.Chart(data_long)
        .mark_rect()
        .encode(
            x=alt.X("Colonne:N", title="Colonnes"),
            y=alt.Y("Modalité:N", title="Modalités"),
            color=alt.Color(
                "Résidu:Q",
                scale=alt.Scale(scheme="redblue", domainMid=0),
                title="Résidus standardisés",
            ),
            tooltip=["Modalité", "Colonne", alt.Tooltip("Résidu:Q", format=".2f")],
        )
    )

    st.altair_chart(chart, use_container_width=True)


def _afficher_resultats(affichage: ResultatChiDeux) -> None:
    """Afficher les résultats du test du chi2 dans l'interface."""

    st.markdown("---")
    st.subheader("Résultats du test")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chi2", f"{affichage.chi2:.3f}")
    col2.metric("Degrés de liberté", affichage.ddl)
    col3.metric("p-value", f"{affichage.p_value:.4f}")
    col4.metric("V de Cramér", f"{affichage.cramers_v:.3f}")

    st.caption("Le V de Cramér mesure l'intensité de l'association entre les lignes et les colonnes du tableau.")

    st.subheader("Tableau attendu")
    st.dataframe(affichage.tableau_attendu, use_container_width=True)

    st.subheader("Résidus standardisés")
    st.dataframe(affichage.residus_standardises, use_container_width=True)
    _afficher_residus_heatmap(affichage.residus_standardises)

    st.subheader("Contributions au chi2")
    st.caption(
        "Chaque cellule contribue à la statistique via (observé - attendu)^2 / attendu. Les lignes suivantes synthétisent ces apports."
    )
    st.dataframe(affichage.contributions, use_container_width=True)

    st.subheader("Contribution par modalité")
    st.caption(
        "Somme des contributions de chaque modalité (ligne) et part relative dans la statistique totale du chi2."
    )
    st.dataframe(affichage.contributions_modalites, use_container_width=True)


def _afficher_conclusion(resultats: ResultatChiDeux) -> None:
    """Proposer une phrase de conclusion en fonction de la p-value."""

    if resultats.p_value < 0.001:
        interpretation = "Association très significative entre lignes et colonnes."
    elif resultats.p_value < 0.01:
        interpretation = "Association significative entre lignes et colonnes."
    elif resultats.p_value < 0.05:
        interpretation = "Association modérément significative entre lignes et colonnes."
    else:
        interpretation = "Aucune association statistiquement significative détectée."

    st.info(
        f"Statistique chi2 = {resultats.chi2:.3f} avec {resultats.ddl} ddl, p-value = {resultats.p_value:.4f}. {interpretation}"
    )


def _proposer_simulation(attendus: pd.DataFrame) -> bool:
    """Indiquer la présence d'attendus faibles et proposer la simulation."""

    if attendus.empty:
        return False

    if (attendus < 5).any().any():
        st.warning(
            "Certaines cases du tableau attendu sont inférieures à 5. Les résultats du chi2 peuvent être fragiles."
        )
        return True

    return False


def rendu_chi2(tab, dataframe: pd.DataFrame, filtered_connectors: Dict[str, str]) -> None:
    """Afficher l'onglet de test du chi2."""

    st.subheader("Test du chi2")
    render_connectors_reminder(filtered_connectors)

    if dataframe.empty:
        st.info("Aucun texte filtré disponible. Sélectionnez des données dans l'onglet « Données brutes ».")
        return

    variables_disponibles: List[str] = [
        colonne for colonne in dataframe.columns if colonne not in ("texte", "entete")
    ]

    if not variables_disponibles:
        st.info("Aucune variable IRaMuTeQ n'est disponible pour construire un tableau de contingence.")
        return

    variable = st.selectbox("Variable pour les lignes", variables_disponibles)

    if not variable:
        st.info("Choisissez une variable pour lancer le test du chi2.")
        return

    modalities_options = sorted(dataframe[variable].dropna().unique().tolist())
    selected_modalities = st.multiselect(
        "Modalités à inclure", modalities_options, default=modalities_options
    )

    mode = st.radio(
        "Type de colonnes",
        options=["Catégories de connecteurs", "Connecteurs vs non-connecteurs"],
        help="Choisissez entre l'analyse par catégories ou un regroupement global connecteurs/non-connecteurs.",
    )

    table_observee: pd.DataFrame
    categories_selectionnees: List[str] = []
    connecteurs_selectionnes: List[str] = []

    if mode == "Catégories de connecteurs":
        categories_disponibles = get_selected_labels(filtered_connectors.values())
        if not categories_disponibles:
            st.info("Aucune catégorie disponible : sélectionnez des connecteurs dans l'onglet dédié.")
            return

        categories_selectionnees = st.multiselect(
            "Catégories à inclure",
            categories_disponibles,
            default=categories_disponibles,
            help="Les colonnes du tableau correspondent aux catégories choisies.",
        )
    else:
        connecteurs_options = [
            f"{connector} ({label})" for connector, label in filtered_connectors.items()
        ]
        option_map = {f"{connector} ({label})": connector for connector, label in filtered_connectors.items()}

        connecteurs_selectionnes_affiche = st.multiselect(
            "Connecteurs inclus",
            connecteurs_options,
            default=[],
            help="Sélectionnez les connecteurs comptabilisés dans la colonne « Connecteurs ».",
        )
        connecteurs_selectionnes = [option_map[label] for label in connecteurs_selectionnes_affiche]

    lancer_calcul = st.button("Calculer le test du chi2")

    if not lancer_calcul:
        st.info("Configurez les options puis lancez le calcul.")
        return

    try:
        if mode == "Catégories de connecteurs":
            table_observee = construire_table_contingence_categories(
                dataframe,
                variable,
                selected_modalities,
                filtered_connectors,
                categories_selectionnees,
            )
        else:
            if not connecteurs_selectionnes:
                st.error("Sélectionnez au moins un connecteur à inclure.")
                return
            table_observee = construire_table_contingence_connecteurs(
                dataframe,
                variable,
                selected_modalities,
                filtered_connectors,
                connecteurs_selectionnes,
            )
    except ValueError as err:
        st.error(str(err))
        return

    if table_observee.empty:
        st.info("Le tableau de contingence est vide après application des filtres.")
        return

    st.subheader("Tableau observé")
    st.dataframe(table_observee, use_container_width=True)

    try:
        resultats = calculer_statistiques_chi2(table_observee)
    except ValueError as err:
        st.error(str(err))
        return

    _afficher_resultats(resultats)
    _afficher_conclusion(resultats)

    simulation_possible = _proposer_simulation(resultats.tableau_attendu)

    if simulation_possible:
        with st.expander("P-value par simulation Monte Carlo"):
            nb_simulations = st.slider(
                "Nombre de simulations", min_value=500, max_value=20000, step=500, value=5000
            )
            utiliser_simulation = st.checkbox(
                "Activer la simulation (permutation sous H0)",
                value=True,
                help="La p-value simulée complète la p-value classique du chi2.",
            )
            if utiliser_simulation:
                try:
                    p_value_simulee = p_value_monte_carlo(table_observee, simulations=nb_simulations)
                except ValueError as err:
                    st.error(str(err))
                else:
                    st.info(f"p-value simulée : {p_value_simulee:.4f}")

    st.markdown("---")
    st.caption(
        "Interprétation : des résidus standardisés positifs indiquent une sur-représentation relative, "
        "des résidus négatifs une sous-représentation. Le V de Cramér mesure la force de l'association "
        "(0 = aucune association, 1 = association parfaite)."
    )

    export_df = fusionner_tables_export(
        table_observee,
        resultats.tableau_attendu,
        resultats.residus_standardises,
        resultats.contributions,
        resultats.contributions_modalites,
        (resultats.chi2, resultats.ddl, resultats.p_value, resultats.cramers_v),
    )

    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    nom_fichier = f"chi2_{variable}_{horodatage}.csv"

    st.download_button(
        label="Exporter les résultats (CSV)",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=nom_fichier,
        mime="text/csv",
    )

