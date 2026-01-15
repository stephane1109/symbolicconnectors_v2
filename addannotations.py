"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json
from typing import Dict, List

import pandas as pd
import streamlit as st


def render_manual_annotations(flattened_text: str) -> None:
    st.markdown("---")
    st.subheader("Créer un JSON d'annotations manuelles")
    st.caption(
        "Pour l'instant, Streamlit ne permet pas de surligner directement le texte. "
        "Copiez/collez un passage ou indiquez des indices de début/fin pour créer "
        "vos annotations, puis téléchargez le JSON généré."
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

    col_label, col_text = st.columns([1, 2])
    with col_label:
        if labels_state:
            annotation_label = st.selectbox(
                "Label",
                options=labels_state,
                key="manual_annotation_label_select",
            )
        else:
            annotation_label = st.text_input(
                "Label (temporaire)",
                key="manual_annotation_label_temp",
            )
        start_index = st.number_input(
            "Indice début (optionnel)",
            min_value=0,
            step=1,
            value=0,
            key="manual_annotation_start",
        )
        end_index = st.number_input(
            "Indice fin (optionnel)",
            min_value=0,
            step=1,
            value=0,
            key="manual_annotation_end",
        )
    with col_text:
        selected_text = st.text_area(
            "Passage à annoter (copier/coller)",
            height=120,
            key="manual_annotation_selection",
        )

    add_annotation = st.button("Ajouter l'annotation")
    reset_annotations = st.button("Réinitialiser les annotations")

    if reset_annotations:
        annotations_state.clear()
        st.info("Annotations réinitialisées.")

    if add_annotation:
        _handle_add_annotation(
            annotations_state,
            annotation_label,
            raw_text,
            start_index,
            end_index,
            selected_text,
        )

    if annotations_state:
        st.markdown("#### Aperçu des annotations")
        st.dataframe(pd.DataFrame(annotations_state), use_container_width=True)

    annotations_payload = {
        "text": raw_text,
        "annotations": annotations_state,
    }
    st.download_button(
        "Télécharger le JSON d'annotations",
        data=json.dumps(annotations_payload, ensure_ascii=False, indent=2),
        file_name="annotations.json",
        mime="application/json",
    )

    labels_payload = {"labels": labels_state}
    st.download_button(
        "Télécharger le JSON des labels",
        data=json.dumps(labels_payload, ensure_ascii=False, indent=2),
        file_name="labels.json",
        mime="application/json",
    )


def _handle_add_annotation(
    annotations_state: List[Dict[str, str | int]],
    annotation_label: str,
    raw_text: str,
    start_index: int,
    end_index: int,
    selected_text: str,
) -> None:
    if not annotation_label.strip():
        st.error("Veuillez renseigner un label pour l'annotation.")
        return

    if not raw_text.strip():
        st.error("Veuillez fournir un texte à annoter.")
        return

    computed_start = None
    computed_end = None
    resolved_text = selected_text

    if end_index > start_index:
        if end_index <= len(raw_text):
            computed_start = int(start_index)
            computed_end = int(end_index)
            resolved_text = raw_text[computed_start:computed_end]
        else:
            st.error("L'indice de fin dépasse la longueur du texte.")
    elif selected_text.strip():
        occurrences = [
            idx
            for idx in range(len(raw_text))
            if raw_text.startswith(selected_text, idx)
        ]
        if not occurrences:
            st.error("Le passage fourni n'a pas été trouvé dans le texte.")
        else:
            if len(occurrences) > 1:
                st.warning(
                    "Plusieurs occurrences trouvées : la première a été utilisée. "
                    "Précisez des indices pour cibler une occurrence exacte."
                )
            computed_start = occurrences[0]
            computed_end = computed_start + len(selected_text)
    else:
        st.error("Indiquez un passage à annoter ou des indices de début/fin valides.")

    if computed_start is not None and computed_end is not None:
        annotations_state.append(
            {
                "start": computed_start,
                "end": computed_end,
                "label": annotation_label.strip(),
                "text": resolved_text,
            }
        )
        st.success("Annotation ajoutée.")
