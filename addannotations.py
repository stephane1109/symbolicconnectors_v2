"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json

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
    st.info("Double-cliquez sur un mot pour l'annoter. Vous pouvez également surligner le texte. Le clic droit de la souris sur la zone annotée vous donne les informations.")

    with st.container(height=500, border=True):
        results = text_annotator(
            text=text,
            labels={},
            in_snake_case=False,
            colors=label_colors,
            key="annotator_main",
        )

    st.divider()
    st.subheader("Enregistrement des données au format json")

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
        st.success(f"{len(annotations_data)} annotation(s) détectée(s).")

        with st.expander("Voir le détail des labels"):
            st.json(annotations_data)

        json_string = json.dumps(annotations_data, indent=4, ensure_ascii=False)
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
