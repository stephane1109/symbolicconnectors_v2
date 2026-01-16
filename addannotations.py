"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st
from st_annotator import text_annotator


def render_manual_annotations() -> None:
    st.markdown("---")
    st.subheader("Annoter un texte")

    label_colors = {
        "label_input": "#ff9500",
    }

    uploaded_file = st.file_uploader("Telechargement d'un fichier texte .txt", type=["txt"])
    if uploaded_file is None:
        st.info("Veuillez charger un fichier .txt pour commencer.")
        return

    try:
        text = uploaded_file.getvalue().decode("utf-8")
    except UnicodeDecodeError:
        st.error("Impossible de décoder le fichier téléversé en UTF-8.")
        return

    st.subheader("Annotation")
    st.info(
        "Double-cliquez sur un mot pour l'annoter. Vous pouvez également surligner le texte. "
        "Le clic droit de la souris sur la zone annotée vous donne les informations."
    )
    st.caption(
        "Pour retirer un mot d'un label, utilisez le bouton de suppression dans la liste des annotations."
    )

    if "annotation_labels" not in st.session_state:
        st.session_state.annotation_labels = ["label_input"]

    with st.container(height=500, border=True):
        results = text_annotator(
            text=text,
            labels=st.session_state.annotation_labels,
            in_snake_case=False,
            colors=label_colors,
            key="annotator_main",
        )

    st.divider()
    st.subheader("Enregistrement des données au format json")
    st.caption(
        "Le fichier exporté associe chaque mot ou segment annoté à son label "
        "(exemple : `{ \"sinon\": \"NOM DU LABEL\" }`). Si un mot est associé à plusieurs labels, "
        "la valeur devient une liste."
    )

    annotations_data = []
    if results:
        if isinstance(results, str):
            try:
                annotations_data = json.loads(results)
            except json.JSONDecodeError:
                st.error("Format de données invalide reçu du composant.")
        else:
            annotations_data = results

    if annotations_data:
        if isinstance(annotations_data, dict):
            annotations_iterable = [
                {"text": text_value, "label": label_value}
                for text_value, label_value in annotations_data.items()
            ]
        elif isinstance(annotations_data, list):
            annotations_iterable = annotations_data
        else:
            annotations_iterable = []

        st.success(f"{len(annotations_iterable)} annotation(s) détectée(s).")

        label_summary: dict[str, list[str]] = {}
        annotations_mapping: dict[str, str | list[str]] = {}
        for annotation in annotations_iterable:
            if not isinstance(annotation, dict):
                continue
            label_value = annotation.get("label", "")
            labels = label_value if isinstance(label_value, list) else [label_value]
            text_value = str(annotation.get("text", "")).strip()
            if not text_value:
                continue

            for label in labels:
                if not label:
                    continue
                label_summary.setdefault(label, []).append(text_value)
                if text_value in annotations_mapping:
                    existing = annotations_mapping[text_value]
                    if isinstance(existing, list):
                        if label not in existing:
                            existing.append(label)
                    elif existing != label:
                        annotations_mapping[text_value] = [existing, label]
                else:
                    annotations_mapping[text_value] = label

        if label_summary:
            label_rows = [
                {
                    "Label": label,
                    "Occurrences": len(words),
                    "Mots annotés": ", ".join(sorted(set(words))),
                }
                for label, words in sorted(label_summary.items())
            ]
            st.markdown("**Tableau des labels**")
            st.dataframe(pd.DataFrame(label_rows), use_container_width=True)

        json_string = json.dumps(annotations_mapping, indent=4, ensure_ascii=False)
        st.download_button(
            label="Enregistrer le fichier json",
            data=json_string,
            file_name="mes_annotations.json",
            mime="application/json",
            use_container_width=True,
        )
    else:
        st.warning(
            "Aucune annotation n'a été faite pour le moment. Double-cliquez sur un mot dans la zone ci-dessus."
        )
