"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json
from typing import List

import pandas as pd
import streamlit as st
from streamlit_annotation_tools import text_labeler


def render_manual_annotations(flattened_text: str) -> None:
    st.markdown("---")
    st.subheader("Annoter un texte")
    st.caption(
        "Définissez vos labels, puis surlignez le texte à la souris pour créer les annotations."
    )

    raw_text = st.text_area(
        "Texte à annoter",
        flattened_text,
        height=200,
        key="manual_annotation_text",
    )

    annotations_state = st.session_state.setdefault("manual_annotations", [])
    labels_state = st.session_state.setdefault("annotation_labels", [])

    st.markdown("#### Text Labeler")
    label_input = st.text_input("Nouveau label", key="annotation_label_input")
    add_label = st.button("Ajouter le label")
    if add_label:
        cleaned_label = label_input.strip()
        if not cleaned_label:
            st.error("Veuillez saisir un label non vide.")
        elif cleaned_label in labels_state:
            st.warning("Ce label existe déjà.")
        else:
            labels_state.append(cleaned_label)
            st.success("Label ajouté.")

    if labels_state:
        labels_to_remove = st.multiselect(
            "Labels existants (sélectionner pour supprimer)",
            options=labels_state,
            key="annotation_labels_remove",
        )
        if st.button("Supprimer les labels sélectionnés"):
            remaining_labels = [label for label in labels_state if label not in labels_to_remove]
            labels_state.clear()
            labels_state.extend(remaining_labels)
            st.info("Labels mis à jour.")
    else:
        st.info("Ajoutez au moins un label pour annoter le texte.")

    st.markdown("#### Annotation par surlignage")
    if labels_state:
        annotations_state[:] = text_labeler(
            raw_text,
            labels_state,
            key="manual_annotation_labeler",
        )
    else:
        st.info("Ajoutez au moins un label pour activer la sélection par surlignage.")

    if annotations_state:
        st.markdown("#### Aperçu des annotations")
        st.dataframe(pd.DataFrame(annotations_state), use_container_width=True)

    labels_payload = {"labels": labels_state}
    st.download_button(
        "Télécharger le JSON des labels",
        data=json.dumps(labels_payload, ensure_ascii=False, indent=2),
        file_name="labels.json",
        mime="application/json",
    )
