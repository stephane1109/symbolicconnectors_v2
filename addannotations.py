"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json
import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Callable, List, Optional

import pandas as pd
import streamlit as st
from streamlit.components.v1 import declare_component

TextLabeler = Callable[[str, List[str], str], List[dict]]

_LOCAL_COMPONENT_PATH = Path(__file__).resolve().parent / "components" / "text_annotator"
_local_text_annotator = declare_component(
    "local_text_annotator",
    path=str(_LOCAL_COMPONENT_PATH),
)


def _wrap_text_labeler(text_labeler: Callable[..., List[dict]]) -> TextLabeler:
    signature = inspect.signature(text_labeler)
    accepts_key = "key" in signature.parameters or any(
        parameter.kind == inspect.Parameter.VAR_KEYWORD
        for parameter in signature.parameters.values()
    )

    def _labeler(text: str, labels: List[str], key: str) -> List[dict]:
        kwargs = {"key": key} if accepts_key else {}
        return text_labeler(text, labels, **kwargs)

    return _labeler


def _load_text_labeler() -> Optional[TextLabeler]:
    candidates = (
        ("st_annotator", ("st_annotate",)),
        ("streamlit_annotator", ("text_annotator", "st_annotate", "annotate")),
    )

    for module_name, attributes in candidates:
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            continue

        module = importlib.import_module(module_name)
        for attribute in attributes:
            text_labeler = getattr(module, attribute, None)
            if callable(text_labeler):
                return _wrap_text_labeler(text_labeler)

    return None


def render_manual_annotations(flattened_text: str) -> None:
    st.markdown("---")
    st.subheader("Annoter un texte")
    st.caption(
        "Définissez vos labels, puis surlignez le texte à la souris pour créer les annotations."
    )

    raw_text = flattened_text
    st.text_area(
        "Texte importé",
        flattened_text,
        height=200,
        key="manual_annotation_text",
        disabled=True,
    )

    annotations_state = st.session_state.setdefault("manual_annotations", [])
    labels_state = st.session_state.setdefault("annotation_labels", [])

    st.markdown("#### Annotation")
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
    text_labeler = _load_text_labeler()
    if text_labeler is None:
        if labels_state:
            component_value = _local_text_annotator(
                text=raw_text,
                labels=labels_state,
                annotations=annotations_state,
                key="manual_annotation_component",
            )
            if component_value is not None:
                annotations_state[:] = component_value
        else:
            st.info("Ajoutez au moins un label pour activer la sélection par surlignage.")
    elif labels_state:
        annotations_state[:] = text_labeler(
            raw_text,
            labels_state,
            "manual_annotation_labeler",
        )
    else:
        st.info("Ajoutez au moins un label pour activer la sélection par surlignage.")

    if annotations_state:
        st.markdown("#### Aperçu des annotations")
        st.dataframe(pd.DataFrame(annotations_state), use_container_width=True)

    annotations_payload = {item.get("text", ""): item.get("label", "") for item in annotations_state}
    st.download_button(
        "Télécharger le JSON des annotations",
        data=json.dumps(annotations_payload, ensure_ascii=False, indent=2),
        file_name="annotations.json",
        mime="application/json",
    )
