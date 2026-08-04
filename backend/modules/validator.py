class ValidationError(Exception):
    pass


class PipelineValidator:
    def __init__(self):
        self.issues = []

    def _fail(self, message: str):
        self.issues.append(message)

    def validate_required_fields(self, data: dict):
        required_top_level = [
            "classification", "knowledge_extraction", "teaching_plan",
            "lessons", "activities", "assessments"
        ]
        for field in required_top_level:
            if field not in data:
                self._fail(f"Missing required top-level field: {field}")

    def validate_no_parse_errors(self, data: dict):
        def scan(obj, path="root"):
            if isinstance(obj, dict):
                if obj.get("error") == "parse_failed":
                    self._fail(f"Unparsed LLM output found at: {path}")
                for key, value in obj.items():
                    scan(value, f"{path}.{key}")
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    scan(item, f"{path}[{i}]")

        scan(data)

    def validate_no_empty_concepts(self, teaching_plan: dict):
        periods = teaching_plan.get("periods", [])
        if not periods:
            self._fail("Teaching plan has no periods")
            return

        for period in periods:
            period_num = period.get("period_number", "unknown")
            if not period.get("concepts"):
                self._fail(f"Period {period_num} has empty concepts list")
            if not period.get("objectives"):
                self._fail(f"Period {period_num} has empty objectives list")

    def validate_objectives_in_lessons(self, teaching_plan: dict, lessons: dict):
        lessons_by_period = {
            item.get("period_number"): item.get("lesson", {})
            for item in lessons.get("lessons", [])
        }

        for period in teaching_plan.get("periods", []):
            period_num = period.get("period_number")
            objectives = period.get("objectives", [])
            lesson = lessons_by_period.get(period_num)

            if lesson is None:
                self._fail(f"Period {period_num} has no matching lesson")
                continue

            if lesson.get("error") == "parse_failed":
                continue

            lesson_text = " ".join([
                lesson.get("teacher_script", ""),
                lesson.get("entry_ticket", ""),
                lesson.get("blackboard_notes", "")
            ]).lower()

            for objective in objectives:
                keywords = [w for w in objective.lower().split() if len(w) > 4]
                if keywords and not any(kw in lesson_text for kw in keywords):
                    self._fail(
                        f"Period {period_num} objective not reflected in lesson: '{objective}'"
                    )

    def validate(self, data: dict) -> dict:
        self.issues = []

        self.validate_required_fields(data)
        self.validate_no_parse_errors(data)

        if "teaching_plan" in data:
            self.validate_no_empty_concepts(data["teaching_plan"])

        if "teaching_plan" in data and "lessons" in data:
            self.validate_objectives_in_lessons(data["teaching_plan"], data["lessons"])

        return {
            "valid": len(self.issues) == 0,
            "issue_count": len(self.issues),
            "issues": self.issues
        }