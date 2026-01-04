"""Tests non paramétriques (Mann–Whitney, Kruskal) sur indicateurs par réponse."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy.stats import kruskal, mannwhitneyu
from statsmodels.stats.multitest import multipletests


@dataclass
class ResultatMannWhitney:
    """Résultat structuré pour un test de Mann–Whitney."""

    statistique: float
    p_value: float
    n_a: int
    n_b: int


@dataclass
class ResultatKruskal:
    """Résultat structuré pour un test de Kruskal–Wallis."""

    statistique: float
    p_value: float
    effectif_total: int


def effectuer_test_mann_whitney(valeurs_a: List[float], valeurs_b: List[float]) -> Optional[ResultatMannWhitney]:
    """Appliquer le test de Mann–Whitney à deux échantillons.

    Les listes doivent contenir au moins une valeur non nulle pour que le test soit
    calculé. Les valeurs NaN sont ignorées.
    """

    propres_a = [v for v in valeurs_a if v is not None and not np.isnan(v)]
    propres_b = [v for v in valeurs_b if v is not None and not np.isnan(v)]

    if len(propres_a) == 0 or len(propres_b) == 0:
        return None

    resultat = mannwhitneyu(propres_a, propres_b, alternative="two-sided")

    return ResultatMannWhitney(
        statistique=float(resultat.statistic),
        p_value=float(resultat.pvalue),
        n_a=len(propres_a),
        n_b=len(propres_b),
    )


def effectuer_test_kruskal(donnees_par_modalite: Dict[str, List[float]]) -> Optional[ResultatKruskal]:
    """Appliquer un test de Kruskal–Wallis sur plusieurs modalités."""

    modalites = sorted(donnees_par_modalite)
    valeurs = []

    for modalite in modalites:
        echantillon = [v for v in donnees_par_modalite[modalite] if v is not None and not np.isnan(v)]
        if echantillon:
            valeurs.append(echantillon)

    if len(valeurs) < 2:
        return None

    resultat = kruskal(*valeurs)

    effectif_total = sum(len(donnees_par_modalite[m]) for m in modalites)

    return ResultatKruskal(
        statistique=float(resultat.statistic),
        p_value=float(resultat.pvalue),
        effectif_total=effectif_total,
    )


def comparaisons_post_hoc(
    donnees_par_modalite: Dict[str, List[float]],
    methode_correction: Optional[str] = None,
) -> pd.DataFrame:
    """Comparer toutes les modalités deux à deux (Mann–Whitney) avec correction."""

    modalites = sorted(donnees_par_modalite)

    if len(modalites) < 2:
        return pd.DataFrame(
            columns=["modalite_a", "modalite_b", "statistique", "p_brute", "p_ajustee", "n_a", "n_b", "rejette"]
        )

    lignes = []
    p_values = []

    for modalite_a, modalite_b in combinations(modalites, 2):
        valeurs_a = donnees_par_modalite.get(modalite_a, [])
        valeurs_b = donnees_par_modalite.get(modalite_b, [])
        resultat = effectuer_test_mann_whitney(valeurs_a, valeurs_b)

        if resultat is None:
            continue

        lignes.append(
            {
                "modalite_a": modalite_a,
                "modalite_b": modalite_b,
                "statistique": resultat.statistique,
                "p_brute": resultat.p_value,
                "n_a": resultat.n_a,
                "n_b": resultat.n_b,
            }
        )
        p_values.append(resultat.p_value)

    if not lignes:
        return pd.DataFrame(
            columns=["modalite_a", "modalite_b", "statistique", "p_brute", "p_ajustee", "n_a", "n_b", "rejette"]
        )

    p_ajustees = p_values
    rejets = [False] * len(p_values)

    if methode_correction:
        _, p_ajustees, _, rejets = multipletests(p_values, method=methode_correction)

    for idx, ligne in enumerate(lignes):
        ligne["p_ajustee"] = float(p_ajustees[idx])
        ligne["rejette"] = bool(rejets[idx])

    return pd.DataFrame(lignes)
