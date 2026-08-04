from pathlib import Path
from fastapi import APIRouter, UploadFile, File
from modules.parser import DocumentParser
from modules.classifier import EducationalClassifier
from modules.extractor import KnowledgeExtractor
from modules.planner import TeachingPlanner
from modules.generator import LessonGenerator
from modules.activity_generator import ActivityGenerator
from modules.assessment_generator import AssessmentGenerator
from modules.learning_gap_analyzer import LearningGapAnalyzer 
from modules.validator import PipelineValidator
from modules.publisher import Publisher

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = UPLOAD_DIR / file.filename

    with open(file_path, "wb") as f:
        f.write(await file.read())

    parser = DocumentParser()
    parsed = parser.parse(str(file_path))

    full_text = " ".join(p["text"] for p in parsed["pages"])
    classification = EducationalClassifier().classify(full_text)
    knowledge = KnowledgeExtractor().extract(full_text)
    teaching_plan = TeachingPlanner().plan(knowledge)
    lessons = LessonGenerator().generate(teaching_plan)
    activities = ActivityGenerator().generate(teaching_plan)
    assessments = AssessmentGenerator().generate(teaching_plan)
    gap_analysis = LearningGapAnalyzer().analyze(knowledge)  # NEW

    result =  {
        **parsed,
        "classification": classification,
        "knowledge_extraction": knowledge,
        "teaching_plan": teaching_plan,
        "lessons": lessons,
        "activities": activities,
        "assessments": assessments,
        "gap_analysis": gap_analysis
    }

    validation_report = PipelineValidator().validate(result)
    result["validation"] = validation_report

    base_name = Path(file.filename).stem
    published_files = Publisher().publish(result, base_filename=base_name)
    result["published_files"] = published_files
    return result