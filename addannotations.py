"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json

import streamlit as st
from st_annotator import text_annotator


def render_manual_annotations() -> None:
    st.title("Text Annotator Tool")

    label_colors = {
        "label_input": "#ff9500",
    }

    uploaded_file = st.file_uploader("Upload a .txt file to annotate", type=["txt"])

    if uploaded_file is not None:
        text = uploaded_file.getvalue().decode("utf-8")

        st.subheader("Annotation du texte")
        st.info("Double-cliquez sur un mot pour l'annoter. clic droit de la souris pour visualiser l'information")

        with st.container(height=500, border=True):
            results = text_annotator(
                text=text,
                labels={},
                in_snake_case=False,
                colors=label_colors,
                key="annotator_main",
            )

        st.divider()
        st.subheader("Enregistrement des annotations")

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
                label="Enregistrer le fichier JSON",
                data=json_string,
                file_name="mes_annotations.json",
                mime="application/json",
                use_container_width=True,
            )
        else:
            st.warning(
                "Aucune annotation n'a été faite pour le moment. Double-cliquez sur un mot dans la zone ci-dessus."
            )

    else:
        st.info("Veuillez charger un fichier .txt pour commencer.")
