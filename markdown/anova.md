# Test d’ANOVA : déroulement dans le script

Ce document décrit comment le test d’ANOVA à un facteur et les comparaisons post‑hoc sont réalisés dans le code.

## 1) Préparation des données

Le flux commence dans l’onglet ANOVA de l’application Streamlit :

- L’utilisateur choisit une variable de regroupement (par ex. modèle/LLM) via un menu déroulant.
- La densité de connecteurs est calculée **par réponse individuelle** (normalisée par 1 000 mots par défaut).
- Seules les réponses avec un nombre de mots strictement supérieur à 0 sont conservées.

Ces étapes sont gérées dans `onglets/onglet_anova.py`.

## 2) Calcul de la densité par réponse

La fonction `compute_density_per_response` construit le texte de chaque ligne (en concaténant `entete` et `texte` si nécessaire), puis calcule :

- le nombre de mots,
- le nombre de connecteurs,
- la densité des connecteurs (pour 1 000 mots par défaut).

Elle renvoie un DataFrame enrichi avec ces indicateurs.

## 3) Constitution des groupes

Une fois les densités calculées, les réponses sont groupées par modalité de la variable choisie (ex. `grok`, `gpt`, etc.).
Pour chaque modalité, on récupère la liste des densités associées.

Cette structure est un dictionnaire de type :

```python
{
  "modalite_1": [densite_1, densite_2, ...],
  "modalite_2": [densite_1, densite_2, ...],
  ...
}
```

## 4) ANOVA à un facteur

Le test ANOVA est appliqué via `scipy.stats.f_oneway` dans la fonction `effectuer_test_anova` :

- Les valeurs `None` ou `NaN` sont retirées.
- Si moins de **deux** modalités ont des données valides, le test est abandonné.
- Le résultat renvoie : statistique F, p‑value, degrés de liberté inter/intra, effectif total, nombre de groupes.

Ces informations sont ensuite affichées dans l’interface Streamlit.

## 5) Comparaisons post‑hoc (t‑tests)

Après l’ANOVA, des comparaisons par paires sont effectuées entre toutes les modalités via `tests_post_hoc_ttest` :

- Chaque paire est comparée avec `scipy.stats.ttest_ind`.
- Par défaut, **Welch** est utilisé (`equal_var=False`), mais l’utilisateur peut cocher l’option “variances égales”.
- Une correction de p‑values peut être appliquée (`Bonferroni` ou `Holm`) via `statsmodels.stats.multitest.multipletests`.
- Les résultats sont triés par p‑value ajustée et affichés sous forme de tableau.

### Pourquoi corriger les p‑values ?

Lorsque tu compares beaucoup de paires en parallèle, le risque de faux positifs augmente fortement. Par exemple, avec 7 modalités, il y a 21 comparaisons. Si tu testes chacune au seuil de 5 % sans correction, la probabilité d’obtenir au moins une p < 0,05 par hasard vaut :

```
1 − 0,95^21 ≈ 0,66 (66 %)
```

Autrement dit, même si toutes les hypothèses nulles étaient vraies, tu as environ 2 chances sur 3 de déclarer au moins une différence “significative” par erreur.

### Quelle correction choisir ?

Le choix dépend de ton objectif :

- **Objectif confirmatoire (contrôle strict de l’erreur)**  
  Utilise une correction qui contrôle l’erreur de famille (FWER).  
  - **Holm (Holm–Bonferroni)** est souvent recommandé : il contrôle l’erreur globale comme Bonferroni, mais avec plus de puissance.  
  - **Bonferroni** est le plus simple et le plus conservateur (seuil ≈ 0,05/21 = 0,00238).  
  Avec tes p‑values, cela peut changer l’interprétation des résultats.

- **Objectif exploratoire (repérer des tendances)**  
  Une correction de type **Benjamini–Hochberg (FDR)** est plus adaptée : elle contrôle le taux de fausses découvertes au lieu d’éliminer tout faux positif.

### Alternative plus standard en post‑hoc

Quand l’ANOVA est suivie de comparaisons par paires, l’approche la plus classique consiste à utiliser un post‑hoc qui intègre directement la multiplicité :

- **Tukey HSD** si les variances sont comparables.  
- **Games–Howell** si les variances sont inégales ou pour plus de robustesse.

Ces méthodes répondent directement à la question “quelles paires diffèrent” en contrôlant correctement les comparaisons multiples.

> **Remarque importante :** si le tableau montre `p ajustée = p brute`, cela signifie qu’aucune correction n’a été appliquée. Pour une interprétation défendable, il faut soit recalculer des p‑values ajustées (Holm/BH), soit utiliser un post‑hoc adapté (Tukey/Games–Howell).

## 6) Résultat affiché

L’interface affiche :

- La ligne de synthèse de l’ANOVA (F, p‑value, ddl, effectif, nombre de groupes).
- Un tableau des t‑tests post‑hoc (modalités comparées, t, p brute, p ajustée, tailles d’échantillon).

---

## Résumé du flux

1. Choix de la variable de comparaison.
2. Calcul des densités de connecteurs par réponse.
3. Regroupement des densités par modalité.
4. ANOVA à un facteur (test global).
5. Comparaisons post‑hoc par t‑tests (avec correction optionnelle).
6. Affichage des résultats dans l’interface.

---

## Fichiers impliqués

- `anova.py` (calculs ANOVA + post‑hoc)
- `onglets/onglet_anova.py` (interface et orchestration)
- `densite.py` (calculs de densité et comptages)
