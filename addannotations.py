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
        "Pour retirer un mot d'un label, utilisez le bouton de suppression dans la liste des annotations. "
        "Pour supprimer un label, utilisez la section de gestion des labels ci-dessous."
    )

    if "annotation_labels" not in st.session_state:
        st.session_state.annotation_labels = []

    st.markdown("**Gestion des labels**")
    new_label = st.text_input("Ajouter un label", key="annotation_new_label")
    add_label_clicked = st.button("Ajouter le label", disabled=not new_label.strip())
    if add_label_clicked:
        label_value = new_label.strip()
        if label_value not in st.session_state.annotation_labels:
            st.session_state.annotation_labels.append(label_value)
        st.session_state.annotation_new_label = ""

    with st.container(height=500, border=True):
        results = text_annotator(
            text=text,
            labels=st.session_state.annotation_labels,
            in_snake_case=False,
            colors=label_colors,
            key="annotator_main",
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

    word_label_rows = []
    label_summary = {}
    annotations_mapping: dict[str, str | list[str]] = {}
    if annotations_data:
        for annotation in annotations_data:
            label = annotation.get("label", "")
            text_value = annotation.get("text", "").strip()
            if not label or not text_value:
                continue
            word_label_rows.append({"Mot": text_value, "Label": label})
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

    if word_label_rows:
        st.markdown("**Tableau récapitulatif des mots annotés**")
        st.dataframe(pd.DataFrame(word_label_rows), use_container_width=True)
    else:
        st.info("Aucun mot annoté pour le moment.")

    st.divider()
    st.subheader("Enregistrement des données au format json")
    st.caption(
        "Le fichier exporté associe chaque mot ou segment annoté à son label "
        "(exemple : `{ \"sinon\": \"NOM DU LABEL\" }`). Si un mot est associé à plusieurs labels, "
        "la valeur devient une liste."
    )

    if annotations_data:
        st.success(f"{len(annotations_data)} annotation(s) détectée(s).")

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
