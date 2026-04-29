from __future__ import annotations

import json
import os
from datetime import date, timedelta
from io import BytesIO
from typing import Any, Dict

import pandas as pd
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError


def resolve_api_base_url() -> str:
    try:
        secret_value = st.secrets.get("STREAMLIT_API_BASE_URL")
        if secret_value:
            return str(secret_value)
    except StreamlitSecretNotFoundError:
        pass

    return os.environ.get(
        "STREAMLIT_API_BASE_URL",
        "http://127.0.0.1:8000/api/v1",
    )


API_BASE_URL = resolve_api_base_url()

st.set_page_config(page_title="ScholarTrend AI", page_icon="📚", layout="wide")


def fetch_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    response = requests.post(f"{API_BASE_URL}/research/report", json=payload, timeout=180)
    if not response.ok:
        try:
            detail = response.json()
        except Exception:
            detail = response.text
        raise RuntimeError(f"API request failed with status {response.status_code}: {detail}")
    return response.json()


def main() -> None:
    st.title("ScholarTrend AI")
    st.caption("Multi-agent research assistant for discovering recent scholarly trends.")

    with st.sidebar:
        st.header("Research Settings")
        topic = st.text_area(
            "Research topic",
            value="Agentic AI in financial services",
            height=120,
        )
        time_range = st.selectbox("Time range", ["6m", "1y", "3y", "custom"], index=1)
        paper_limit = st.slider("Number of papers", min_value=5, max_value=30, value=12)
        sources = st.multiselect(
            "Sources",
            options=["arxiv", "semantic_scholar", "crossref", "openalex", "pubmed"],
            default=["arxiv", "semantic_scholar", "crossref", "openalex"],
        )
        custom_start_date = None
        custom_end_date = None
        if time_range == "custom":
            custom_start_date = st.date_input("Start date", value=date.today() - timedelta(days=365))
            custom_end_date = st.date_input("End date", value=date.today())
        provider = st.selectbox("LLM provider", ["mock", "openai", "anthropic", "ollama"], index=0)
        require_human_review = st.checkbox("Require human review", value=False)
        run_button = st.button("Generate Research Brief", type="primary", use_container_width=True)

    if not run_button:
        st.info("Configure the topic and click **Generate Research Brief**.")
        return

    topic = topic.strip()
    if len(topic) < 5:
        st.error("Please enter a research topic with at least 5 characters.")
        return
    if not sources:
        st.error("Please select at least one academic source.")
        return
    if time_range == "custom" and custom_start_date and custom_end_date and custom_start_date > custom_end_date:
        st.error("Custom start date must be earlier than or equal to the end date.")
        return

    payload = {
        "topic": topic,
        "time_range": time_range,
        "paper_limit": paper_limit,
        "sources": sources,
        "llm_provider": provider,
        "require_human_review": require_human_review,
    }
    if time_range == "custom":
        payload["custom_start_date"] = custom_start_date.isoformat() if custom_start_date else None
        payload["custom_end_date"] = custom_end_date.isoformat() if custom_end_date else None

    try:
        with st.spinner("Running ScholarTrend AI workflow..."):
            result = fetch_report(payload)
    except Exception as exc:
        st.error(str(exc))
        st.code(json.dumps(payload, indent=2), language="json")
        return

    st.subheader("Executive Summary")
    st.write(result["executive_summary"])

    col1, col2 = st.columns([1.4, 1.0])
    with col1:
        st.subheader("Top Emerging Themes")
        for theme in result["key_research_themes"]:
            with st.container(border=True):
                st.markdown(f"**{theme['label']}**")
                st.write(theme["description"])
                st.write(f"Trend signal: `{theme['trend_signal']}`")
                if theme["repeated_methods"]:
                    st.write("Methods:", ", ".join(theme["repeated_methods"]))

        st.subheader("Methods and Techniques")
        for item in result["methods_and_techniques"]:
            st.markdown(f"- {item}")

        st.subheader("Research Gaps")
        for item in result["research_gaps"]:
            st.markdown(f"- {item}")

        st.subheader("Business / Product Implications")
        for item in result["business_implications"]:
            st.markdown(f"- {item}")

    with col2:
        st.subheader("Evaluation")
        evaluation = result["evaluation"]
        st.metric("Overall score", f"{evaluation['overall_score']:.2f}")
        st.metric("Source diversity", f"{evaluation['source_diversity']:.2f}")
        st.metric("Grounding score", f"{evaluation['grounding_score']:.2f}")
        st.metric("Citation completeness", f"{evaluation['citation_completeness']:.2f}")

        st.subheader("Validation Issues")
        if result["validation_issues"]:
            for issue in result["validation_issues"]:
                st.warning(f"{issue['severity'].upper()}: {issue['message']}")
        else:
            st.success("No validation issues were flagged.")

        st.subheader("Workflow Trace")
        for step in result["agent_steps"]:
            with st.expander(step["agent_name"], expanded=False):
                for detail in step["details"]:
                    st.markdown(f"- {detail}")

    st.subheader("Top Papers")
    paper_rows = []
    summary_lookup = {summary["paper_id"]: summary for summary in result["paper_summaries"]}
    for item in result["top_papers"]:
        paper = item["paper"]
        summary = summary_lookup.get(paper["paper_id"], {})
        paper_rows.append(
            {
                "Title": paper["title"],
                "Year": paper["publication_date"][:4] if paper.get("publication_date") else "n/a",
                "Source": paper["source"],
                "Relevance": item["relevance_score"],
                "Summary": summary.get("short_summary", ""),
                "Link": paper.get("url"),
            }
        )
    st.dataframe(pd.DataFrame(paper_rows), use_container_width=True)

    st.subheader("Download Report")
    markdown_text = result["report_markdown"]
    st.download_button(
        "Download Markdown",
        markdown_text,
        file_name=f"{result['run_id']}.md",
        mime="text/markdown",
        use_container_width=True,
    )

    pdf_response = requests.get(f"{API_BASE_URL}/reports/{result['run_id']}/pdf", timeout=180)
    pdf_response.raise_for_status()
    st.download_button(
        "Download PDF",
        BytesIO(pdf_response.content),
        file_name=f"{result['run_id']}.pdf",
        mime="application/pdf",
        use_container_width=True,
    )

    st.subheader("Raw API Response")
    st.code(json.dumps(result, indent=2), language="json")


if __name__ == "__main__":
    main()
