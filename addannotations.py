"""Helpers for manual annotation UI in Streamlit."""
from __future__ import annotations

import json
from typing import Any, Dict, List

import pandas as pd
import streamlit as st
from st_annotator import text_annotator


def _build_annotation_rows(annotations: List[Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for entry in annotations:
        if not isinstance(entry, dict):
            continue
        text_value = entry.get("text") or entry.get("token") or entry.get("value")
        label_value = entry.get("label") or entry.get("tag") or entry.get("category")
        if text_value is None or label_value is None:
            continue
        rows.append({"Texte": str(text_value), "Label": str(label_value)})
    return rows


def _build_markdown_table(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return ""
    lines = ["| Texte | Label |", "| --- | --- |"]
    for row in rows:
        text_value = row.get("Texte", "").replace("|", "\\|")
        label_value = row.get("Label", "").replace("|", "\\|")
        lines.append(f"| {text_value} | {label_value} |")
    return "\n".join(lines)


def render_manual_annotations() -> None:
    st.title("Annotation d'un texte")

    label_colors = {
        "label_input": "#ff9500",
    }

    uploaded_file = st.file_uploader("Upload a .txt file to annotate", type=["txt"])

    if uploaded_file is not None:
        text = uploaded_file.getvalue().decode("utf-8")

        st.subheader("Annotation du texte")
        st.info("Double-cliquez sur un mot pour l'annoter. Vous pouvez surligner un passage entier. clic droit de la souris pour visualiser l'information")

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

        annotations_data: List[Any] = []
        if results:
            if isinstance(results, str):
                try:
                    annotations_data = json.loads(results)
                except json.JSONDecodeError:
                    st.error("Format de données invalide reçu du composant.")
            else:
                annotations_data = results

        if annotations_data:
            annotation_rows = _build_annotation_rows(annotations_data)
            st.success(f"{len(annotation_rows)} annotation(s) détectée(s).")

            if annotation_rows:
                annotation_df = pd.DataFrame(annotation_rows)
                with st.expander("Voir le détail des labels"):
                    st.dataframe(annotation_df, use_container_width=True)

                json_mapping = {row["Texte"]: row["Label"] for row in annotation_rows}
                json_string = json.dumps(json_mapping, indent=4, ensure_ascii=False)
                st.download_button(
                    label="Enregistrer le fichier JSON",
                    data=json_string,
                    file_name="annotations.json",
                    mime="application/json",
                    use_container_width=True,
                )

                markdown_content = _build_markdown_table(annotation_rows)
                st.download_button(
                    label="Exporter les labels (Markdown)",
                    data=markdown_content,
                    file_name="annotations.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                st.warning(
                    "Les annotations reçues ne contiennent pas de labels exploitables."
                )
        else:
            st.warning(
                "Aucune annotation n'a été faite pour le moment. Double-cliquez sur un mot dans la zone ci-dessus."
            )

    else:
        st.info("Veuillez charger un fichier .txt pour commencer.")
