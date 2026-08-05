import streamlit as st
import requests

API_URL = "https://teacher-ai-platform-65ke.onrender.com/upload/"

st.set_page_config(page_title="AI Teaching Assistant", layout="wide")
st.title("AI Teaching Assistant")

uploaded_file = st.file_uploader("Upload a PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Process Document"):
        with st.spinner("Processing... this can take 1-2 minutes (multiple LLM calls per document)."):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                response = requests.post(API_URL, files=files, timeout=300)
                response.raise_for_status()
                data = response.json()
                st.session_state["result"] = data
                st.success("Done!")
            except Exception as e:
                st.error(f"Error: {e}")

if "result" in st.session_state:
    data = st.session_state["result"]

    # --- Classification ---
    st.header("Classification")
    c = data.get("classification", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Subject", c.get("subject", "N/A"))
    col2.metric("Grade", c.get("grade", "N/A"))
    col3.metric("Difficulty", c.get("difficulty", "N/A"))
    st.write(f"**Topic:** {c.get('topic', 'N/A')}")

    # --- Validation ---
    st.header("Validation Report")
    v = data.get("validation", {})
    if v.get("valid"):
        st.success("✅ Pipeline validation passed (0 issues)")
    else:
        st.warning(f"⚠️ {v.get('issue_count', 0)} validation issue(s) found")
        for issue in v.get("issues", []):
            st.write(f"- {issue}")

    # --- Knowledge Extraction ---
    st.header("Knowledge Extraction")
    knowledge = data.get("knowledge_extraction", {})
    if knowledge.get("error") == "parse_failed":
        st.error("Knowledge extraction failed to parse for this document.")
    else:
        with st.expander("Learning Objectives"):
            for obj in knowledge.get("learning_objectives", []):
                st.write(f"- {obj}")
        with st.expander("Definitions"):
            for d in knowledge.get("definitions", []):
                st.write(f"**{d.get('term')}:** {d.get('definition')}")
        with st.expander("Formulae"):
            for f in knowledge.get("formulae", []):
                st.write(f"**{f.get('name')}:** `{f.get('formula')}` — {f.get('description')}")
        with st.expander("Misconceptions"):
            for m in knowledge.get("misconceptions", []):
                st.write(f"- {m}")

    # --- Teaching Plan, Lessons, Activities, Assessments per period ---
    st.header("Teaching Plan & Materials")
    periods = data.get("teaching_plan", {}).get("periods", [])
    lessons_by_period = {l["period_number"]: l.get("lesson", {}) for l in data.get("lessons", {}).get("lessons", [])}
    activities_by_period = {a["period_number"]: a.get("activities", {}) for a in data.get("activities", {}).get("activity_sets", [])}
    assessments_by_period = {a["period_number"]: a.get("assessment", {}) for a in data.get("assessments", {}).get("assessments", [])}

    for p in periods:
        pnum = p.get("period_number")
        with st.expander(f"Period {pnum}: {', '.join(p.get('concepts', []))}"):
            st.write(f"**Objectives:** {', '.join(p.get('objectives', []))}")
            st.write(f"**Time allocation:** {p.get('time_allocation', '')}")

            tabs = st.tabs(["Lesson", "Activities", "Assessment"])

            with tabs[0]:
                lesson = lessons_by_period.get(pnum, {})
                if lesson.get("error") == "parse_failed":
                    st.error("Lesson generation failed for this period.")
                else:
                    st.write(f"**Entry Ticket:** {lesson.get('entry_ticket', '')}")
                    st.write(f"**Teacher Script:** {lesson.get('teacher_script', '')}")
                    st.write(f"**Blackboard Notes:**")
                    st.code(lesson.get("blackboard_notes", ""))
                    st.write("**Checkpoint Questions:**")
                    for q in lesson.get("checkpoint_questions", []):
                        st.write(f"- {q}")
                    st.write(f"**Exit Ticket:** {lesson.get('exit_ticket', '')}")
                    st.write(f"**Homework:** {lesson.get('homework', '')}")
                    st.info(lesson.get("mentor_moment", ""))

            with tabs[1]:
                acts = activities_by_period.get(pnum, {})
                if acts.get("error") == "parse_failed":
                    st.error("Activity generation failed for this period.")
                else:
                    for act_type in ["experiment", "role_play", "group_discussion", "demonstration"]:
                        act = acts.get(act_type, {})
                        if act:
                            st.subheader(act_type.replace("_", " ").title())
                            st.write(f"**{act.get('title', '')}** ({act.get('duration', '')})")
                            st.write("Materials: " + ", ".join(act.get("materials", [])))
                            for instr in act.get("instructions", []):
                                st.write(f"- {instr}")

            with tabs[2]:
                assess = assessments_by_period.get(pnum, {})
                if assess.get("error") == "parse_failed":
                    st.error("Assessment generation failed for this period.")
                else:
                    st.write("**MCQs**")
                    for i, mcq in enumerate(assess.get("mcqs", []), 1):
                        st.write(f"{i}. {mcq.get('question')}")
                        for opt in mcq.get("options", []):
                            marker = "✅" if opt == mcq.get("correct_option") else "▫️"
                            st.write(f"   {marker} {opt}")

                    st.write("**Short Answer**")
                    for q in assess.get("short_answer", []):
                        st.write(f"- {q.get('question')}")

                    st.write("**Numericals**")
                    for q in assess.get("numericals", []):
                        st.write(f"- {q.get('question')} → **{q.get('final_answer')}**")

    # --- Gap Analysis ---
    st.header("Learning Gap Analysis")
    gaps = data.get("gap_analysis", {}).get("gap_analysis", [])
    if not gaps:
        st.write("No misconceptions flagged for this document.")
    for g in gaps:
        severity_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(g.get("severity"), "⚪")
        st.write(f"{severity_color} **{g.get('misconception')}** ({g.get('severity')})")
        st.write(f"   Diagnostic: {g.get('diagnostic_question')}")
        st.write(f"   Remedy: {g.get('remedial_action')}")

    # --- Published Files ---
    st.header("Published Files")
    files = data.get("published_files", {})
    for key, path in files.items():
        st.write(f"**{key}:** `{path}`")
