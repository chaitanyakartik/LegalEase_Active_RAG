import os
import tempfile
import streamlit as st

from db.init_db import init_db
from db.models import (
    create_case, get_cases, get_case, update_case_description,
    get_documents, save_message, get_chat_history,
    add_timeline_event, get_timeline, update_event_status, delete_timeline_event,
    get_drafts, delete_draft
)
from ingestion.ingest import ingest_file
from features.analysis import analyze_case
from features.summarizer import summarize_document
from features.precedent_search import search_precedents
from features.drafter import generate_draft
from features.timeline import suggest_timeline_events, add_suggested_event
from rag.graph import run_rag
from config import LAW_CATEGORIES, DRAFT_TYPES, EVENT_TYPES

# Initialize DB on startup
init_db()

st.set_page_config(page_title="LegalEase", page_icon="⚖️", layout="wide")
st.title("⚖️ LegalEase — AI Legal Assistant")


# ─── Sidebar ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("Case Management")

    cases = get_cases()
    case_options = {c["title"]: c["id"] for c in cases}

    col1, col2 = st.columns([3, 1])
    with col1:
        selected_case_title = st.selectbox(
            "Select Case",
            options=["— New Case —"] + list(case_options.keys()),
            key="case_selector"
        )
    with col2:
        st.write("")
        st.write("")

    if selected_case_title == "— New Case —":
        with st.form("new_case_form"):
            new_title = st.text_input("Case Title")
            new_category = st.selectbox("Law Category", LAW_CATEGORIES)
            new_description = st.text_area("Case Description", height=100)
            if st.form_submit_button("Create Case"):
                if new_title:
                    new_id = create_case(new_title, new_category, new_description)
                    st.success(f"Case created!")
                    st.rerun()
        st.stop()

    case_id = case_options[selected_case_title]
    case = get_case(case_id)
    law_category = case["category"]

    st.markdown(f"**Category:** {law_category}")
    st.divider()

    # File uploader
    st.subheader("Upload Documents")
    uploaded_file = st.file_uploader("Upload PDF or DOCX", type=["pdf", "docx"])
    if uploaded_file:
        if st.button("Process Document"):
            with st.spinner("Extracting, chunking, and indexing..."):
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as tmp:
                    tmp.write(uploaded_file.read())
                    tmp_path = tmp.name
                try:
                    ingest_file(tmp_path, case_id, uploaded_file.name)
                    st.success(f"'{uploaded_file.name}' indexed successfully!")
                except Exception as e:
                    st.error(f"Error processing file: {e}")
                finally:
                    os.unlink(tmp_path)

    st.divider()
    st.subheader("Navigate")
    page = st.radio(
        "Feature",
        ["Analysis", "Precedents", "Summarize", "Draft", "Timeline", "Search"],
        label_visibility="collapsed"
    )


# ─── Main Content ─────────────────────────────────────────────────────────────

if page == "Analysis":
    st.header("AI Legal Analysis")
    st.caption(f"Case: {case['title']} · {law_category}")

    # Show/edit case description
    with st.expander("Case Description", expanded=not case.get("description")):
        desc = st.text_area("Describe the case facts", value=case.get("description", ""), height=150)
        if st.button("Save Description"):
            update_case_description(case_id, desc)
            st.success("Saved.")
            st.rerun()

    st.divider()

    # Chat interface
    history = get_chat_history(case_id)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    question = st.chat_input("Ask a legal question about this case...")
    if question:
        with st.chat_message("user"):
            st.write(question)
        save_message("user", question, case_id)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing..."):
                answer = analyze_case(case_id, question, law_category)
            st.write(answer)
        save_message("assistant", answer, case_id)


elif page == "Precedents":
    st.header("Case & Precedent Search")
    st.caption(f"Case: {case['title']} · {law_category}")

    history = get_chat_history(case_id)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Describe the situation to find relevant precedents...")
    if query:
        with st.chat_message("user"):
            st.write(query)
        save_message("user", query, case_id)

        with st.chat_message("assistant"):
            with st.spinner("Searching for precedents..."):
                result = search_precedents(query, law_category, case_id)
            st.write(result)
        save_message("assistant", result, case_id)


elif page == "Summarize":
    st.header("Document Summarization")
    st.caption(f"Case: {case['title']} · {law_category}")

    docs = get_documents(case_id)
    if not docs:
        st.info("No documents uploaded yet. Use the sidebar to upload a PDF or DOCX.")
    else:
        doc_options = {d["filename"]: d["id"] for d in docs}
        selected_doc_name = st.selectbox("Select a document to summarize", list(doc_options.keys()))
        selected_doc_id = doc_options[selected_doc_name]

        if st.button("Generate Summary"):
            with st.spinner("Generating structured summary..."):
                summary = summarize_document(case_id, selected_doc_id)
            st.markdown(summary)


elif page == "Draft":
    st.header("Drafting Assistant")
    st.caption(f"Case: {case['title']} · {law_category}")

    tab1, tab2 = st.tabs(["Generate New Draft", "Saved Drafts"])

    with tab1:
        draft_type = st.selectbox("Document Type", DRAFT_TYPES)
        instructions = st.text_area(
            "Additional instructions (optional)",
            placeholder="e.g., Address to XYZ company, include specific clauses about...",
            height=100
        )
        if st.button("Generate Draft"):
            with st.spinner(f"Drafting {draft_type}..."):
                content, draft_id = generate_draft(case_id, draft_type, law_category, instructions)
            st.success("Draft generated and saved!")
            st.markdown(content)

    with tab2:
        drafts = get_drafts(case_id)
        if not drafts:
            st.info("No drafts saved yet.")
        else:
            for draft in drafts:
                with st.expander(f"{draft['draft_type']} — {draft['created_at'][:10]}"):
                    st.markdown(draft["content"])
                    if st.button("Delete", key=f"del_draft_{draft['id']}"):
                        delete_draft(draft["id"])
                        st.rerun()


elif page == "Timeline":
    st.header("Case Timeline & Tracker")
    st.caption(f"Case: {case['title']} · {law_category}")

    tab1, tab2, tab3 = st.tabs(["Timeline", "Add Event", "AI Suggestions"])

    with tab1:
        events = get_timeline(case_id)
        if not events:
            st.info("No events yet. Add events manually or use AI suggestions.")
        else:
            for event in events:
                col1, col2, col3 = st.columns([6, 2, 1])
                status_icon = "✅" if event["status"] == "completed" else "⏳"
                with col1:
                    st.markdown(f"{status_icon} **{event['title']}** _{event.get('event_type', '')}_ — {event.get('event_date', 'No date')}")
                    if event.get("description"):
                        st.caption(event["description"])
                with col2:
                    new_status = "pending" if event["status"] == "completed" else "completed"
                    if st.button("Toggle", key=f"toggle_{event['id']}"):
                        update_event_status(event["id"], new_status)
                        st.rerun()
                with col3:
                    if st.button("🗑", key=f"del_{event['id']}"):
                        delete_timeline_event(event["id"])
                        st.rerun()

    with tab2:
        with st.form("add_event_form"):
            ev_title = st.text_input("Event Title")
            ev_type = st.selectbox("Event Type", EVENT_TYPES)
            ev_date = st.date_input("Date (optional)", value=None)
            ev_desc = st.text_area("Description (optional)", height=80)
            if st.form_submit_button("Add Event"):
                if ev_title:
                    add_timeline_event(
                        case_id, ev_title, ev_type, ev_desc,
                        str(ev_date) if ev_date else None
                    )
                    st.success("Event added!")
                    st.rerun()

    with tab3:
        if st.button("Get AI Suggestions"):
            with st.spinner("Generating timeline suggestions..."):
                suggestions = suggest_timeline_events(case_id, law_category)
            if suggestions:
                st.write("**Suggested events:**")
                for i, s in enumerate(suggestions):
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.markdown(f"**{s['title']}** ({s['event_type']})  \n{s['description']}  \n_{s.get('timeframe', '')}_")
                    with col2:
                        if st.button("Add", key=f"add_sug_{i}"):
                            add_suggested_event(case_id, s)
                            st.success("Added!")
                            st.rerun()
            else:
                st.info("No suggestions generated. Add a case description first.")


elif page == "Search":
    st.header("Search Across All Case Files")
    st.caption("Ask questions that span all uploaded documents across all cases.")

    history = get_chat_history(case_id=None)
    for msg in history:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    query = st.chat_input("Ask a question across all your case documents...")
    if query:
        with st.chat_message("user"):
            st.write(query)
        save_message("user", query, case_id=None)

        with st.chat_message("assistant"):
            with st.spinner("Searching across all case files..."):
                result = run_rag(query, law_category, case_id=None)
            st.write(result)
        save_message("assistant", result, case_id=None)
