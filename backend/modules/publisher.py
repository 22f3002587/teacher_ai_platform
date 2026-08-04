import json
import os
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

styles = getSampleStyleSheet()


def _safe(text) -> str:
    # ReportLab's Paragraph treats text as mini-HTML, so raw < > & from
    # LLM output can break rendering. Escape it before use.
    if not isinstance(text, str):
        text = str(text)
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Publisher:
    def publish(self, result: dict, base_filename: str = "output") -> dict:
        json_path = self._write_json_package(result, base_filename)
        lesson_pdf_path = self._write_lesson_plan_pdf(result, base_filename)
        assessment_pdf_path = self._write_assessment_pdf(result, base_filename)
        guide_pdf_path = self._write_teacher_guide_pdf(result, base_filename)

        return {
            "teacher_knowledge_package_json": str(json_path),
            "lesson_plan_pdf": str(lesson_pdf_path),
            "assessment_pdf": str(assessment_pdf_path),
            "teacher_guide_pdf": str(guide_pdf_path)
        }

    def _write_json_package(self, result: dict, base_filename: str) -> Path:
        path = OUTPUT_DIR / f"{base_filename}_TeacherKnowledgePackage.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        return path

    def _write_lesson_plan_pdf(self, result: dict, base_filename: str) -> Path:
        path = OUTPUT_DIR / f"{base_filename}_lesson_plan.pdf"
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        story = [Paragraph("Lesson Plan", styles["Title"]), Spacer(1, 12)]

        lessons = result.get("lessons", {}).get("lessons", [])
        for entry in lessons:
            period_num = entry.get("period_number")
            lesson = entry.get("lesson", {})

            if lesson.get("error") == "parse_failed":
                story.append(Paragraph(f"Period {period_num}: content unavailable (generation error)", styles["Heading2"]))
                story.append(Spacer(1, 12))
                continue

            story.append(Paragraph(f"Period {period_num}", styles["Heading1"]))
            story.append(Paragraph("Entry Ticket", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("entry_ticket", "")), styles["Normal"]))
            story.append(Paragraph("Teacher Script", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("teacher_script", "")), styles["Normal"]))
            story.append(Paragraph("Blackboard Notes", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("blackboard_notes", "")).replace("\n", "<br/>"), styles["Normal"]))
            story.append(Paragraph("Checkpoint Questions", styles["Heading3"]))
            for q in lesson.get("checkpoint_questions", []):
                story.append(Paragraph(f"• {_safe(q)}", styles["Normal"]))
            story.append(Paragraph("Exit Ticket", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("exit_ticket", "")), styles["Normal"]))
            story.append(Paragraph("Homework", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("homework", "")), styles["Normal"]))
            story.append(Paragraph("Mentor Moment", styles["Heading3"]))
            story.append(Paragraph(_safe(lesson.get("mentor_moment", "")), styles["Normal"]))
            story.append(PageBreak())

        doc.build(story)
        return path

    def _write_assessment_pdf(self, result: dict, base_filename: str) -> Path:
        path = OUTPUT_DIR / f"{base_filename}_assessment.pdf"
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        story = [Paragraph("Assessment", styles["Title"]), Spacer(1, 12)]

        assessments = result.get("assessments", {}).get("assessments", [])
        for entry in assessments:
            period_num = entry.get("period_number")
            assessment = entry.get("assessment", {})

            if assessment.get("error") == "parse_failed":
                story.append(Paragraph(f"Period {period_num}: content unavailable (generation error)", styles["Heading2"]))
                story.append(Spacer(1, 12))
                continue

            story.append(Paragraph(f"Period {period_num}", styles["Heading1"]))

            story.append(Paragraph("MCQs", styles["Heading3"]))
            for i, mcq in enumerate(assessment.get("mcqs", []), 1):
                story.append(Paragraph(f"{i}. {_safe(mcq.get('question', ''))}", styles["Normal"]))
                for opt in mcq.get("options", []):
                    story.append(Paragraph(f"   - {_safe(opt)}", styles["Normal"]))

            story.append(Paragraph("Short Answer", styles["Heading3"]))
            for q in assessment.get("short_answer", []):
                story.append(Paragraph(f"• {_safe(q.get('question', ''))}", styles["Normal"]))

            story.append(Paragraph("Long Answer", styles["Heading3"]))
            for q in assessment.get("long_answer", []):
                story.append(Paragraph(f"• {_safe(q.get('question', ''))}", styles["Normal"]))

            story.append(Paragraph("Numericals", styles["Heading3"]))
            for q in assessment.get("numericals", []):
                story.append(Paragraph(f"• {_safe(q.get('question', ''))}", styles["Normal"]))

            story.append(Paragraph("Rubrics", styles["Heading3"]))
            for r in assessment.get("rubrics", []):
                story.append(Paragraph(
                    f"{_safe(r.get('criterion', ''))} — {_safe(r.get('description', ''))} "
                    f"(Max marks: {_safe(r.get('max_marks', ''))})",
                    styles["Normal"]
                ))

            story.append(PageBreak())

        doc.build(story)
        return path

    def _write_teacher_guide_pdf(self, result: dict, base_filename: str) -> Path:
        path = OUTPUT_DIR / f"{base_filename}_teacher_guide.pdf"
        doc = SimpleDocTemplate(str(path), pagesize=letter)
        story = [Paragraph("Teacher Guide", styles["Title"]), Spacer(1, 12)]

        classification = result.get("classification", {})
        story.append(Paragraph("Document Overview", styles["Heading1"]))
        for key in ["subject", "grade", "difficulty", "topic", "chapter", "language"]:
            story.append(Paragraph(f"<b>{_safe(key.capitalize())}:</b> {_safe(classification.get(key, 'N/A'))}", styles["Normal"]))
        story.append(Spacer(1, 12))

        knowledge = result.get("knowledge_extraction", {})
        if knowledge.get("error") != "parse_failed":
            story.append(Paragraph("Key Definitions", styles["Heading1"]))
            for d in knowledge.get("definitions", []):
                story.append(Paragraph(f"<b>{_safe(d.get('term', ''))}:</b> {_safe(d.get('definition', ''))}", styles["Normal"]))
            story.append(PageBreak())

        activities = result.get("activities", {}).get("activity_sets", [])
        story.append(Paragraph("Activity Summary", styles["Heading1"]))
        for entry in activities:
            period_num = entry.get("period_number")
            acts = entry.get("activities", {})
            if acts.get("error") == "parse_failed":
                continue
            story.append(Paragraph(f"Period {period_num}", styles["Heading2"]))
            for act_type in ["experiment", "role_play", "group_discussion", "demonstration"]:
                act = acts.get(act_type, {})
                if act:
                    story.append(Paragraph(f"<b>{act_type.replace('_', ' ').title()}:</b> {_safe(act.get('title', ''))} ({_safe(act.get('duration', ''))})", styles["Normal"]))
        story.append(PageBreak())

        gap = result.get("gap_analysis", {}).get("gap_analysis", [])
        story.append(Paragraph("Learning Gap Analysis", styles["Heading1"]))
        if not gap:
            story.append(Paragraph("No misconceptions flagged for this document.", styles["Normal"]))
        for g in gap:
            story.append(Paragraph(f"<b>Misconception:</b> {_safe(g.get('misconception', ''))}", styles["Normal"]))
            story.append(Paragraph(f"<b>Severity:</b> {_safe(g.get('severity', ''))}", styles["Normal"]))
            story.append(Paragraph(f"<b>Diagnostic Question:</b> {_safe(g.get('diagnostic_question', ''))}", styles["Normal"]))
            story.append(Paragraph(f"<b>Remedial Action:</b> {_safe(g.get('remedial_action', ''))}", styles["Normal"]))
            story.append(Spacer(1, 8))

        validation = result.get("validation", {})
        story.append(Paragraph("Pipeline Validation Report", styles["Heading1"]))
        story.append(Paragraph(f"<b>Valid:</b> {validation.get('valid', 'N/A')}", styles["Normal"]))
        for issue in validation.get("issues", []):
            story.append(Paragraph(f"• {_safe(issue)}", styles["Normal"]))

        doc.build(story)
        return path