import json
import os
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.models.schemas import CaseCreateRequest
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.orchestration.controller import controller
from app.storage.case_store import case_store

BASE_DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "sample_cases"


def seed_case(case_id: str, case_name: str, description: str):
    case_folder = BASE_DATA_DIR / case_id
    if not case_folder.exists():
        print(f"Folder not found: {case_folder}")
        return

    # Delete if exists to allow fresh re-seed
    case_store.delete_case(case_id)

    case = case_store.create_case(
        name=case_name,
        description=description,
        is_demo=True,
        custom_id=case_id
    )

    uploads_dir = case_store.uploads_dir / case_id
    uploads_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing documents for {case_name} ({case_id})...")
    for file_path in sorted(case_folder.glob("*.txt")):
        dest = uploads_dir / file_path.name
        with open(file_path, "r", encoding="utf-8") as fin:
            content = fin.read()
        with open(dest, "w", encoding="utf-8") as fout:
            fout.write(content)

        doc_meta = process_uploaded_file(
            case_id=case_id,
            file_path=dest,
            original_filename=file_path.name,
        )
        case_store.add_document(case_id, doc_meta)
        print(f"  + Ingested {file_path.name} ({len(doc_meta.chunks)} chunks)")

    # Load ground-truth candidate hypotheses (1 correct + 2 decoys) to evaluate
    gt_file = Path(__file__).resolve().parent.parent / "data" / "ground_truth" / f"{case_id}_ground_truth.json"
    custom_hyps = []
    if gt_file.exists():
        with open(gt_file, "r", encoding="utf-8") as fgt:
            gt_data = json.load(fgt)
            if "correct_hypothesis" in gt_data:
                from app.models.schemas import HypothesisInput
                custom_hyps.append(
                    HypothesisInput(
                        title=gt_data["correct_hypothesis"]["title"],
                        description=gt_data["correct_hypothesis"]["description"]
                    )
                )
            for dec in gt_data.get("decoy_hypotheses", []):
                from app.models.schemas import HypothesisInput
                custom_hyps.append(
                    HypothesisInput(
                        title=dec["title"],
                        description=dec["description"]
                    )
                )

    print(f"Running full investigation pipeline for {case_name} with {len(custom_hyps)} candidate hypotheses...")
    report = controller.run_investigation(case_id=case_id, custom_hypotheses=custom_hyps if custom_hyps else None)
    print(f"  => Analysis complete. Proposed Explanation: {report.proposed_explanation.title if report.proposed_explanation else 'None'}")
    print(f"  => Contradictions: {len(report.contradictions)}, Timeline Events: {len(report.chronological_timeline)}")


def main():
    print("=== SEEDING DEMO CASES ===")
    seed_case(
        case_id="case_01_meridian",
        case_name="The Meridian Tech Data Leak",
        description="Investigation into unauthorized customer database extraction from Server Room B on October 12, 2024."
    )
    seed_case(
        case_id="case_02_blackwood",
        case_name="The Blackwood Manor Art Heist",
        description="Theft of the 14.5 million GBP Vermeer canvas 'The Silent Witness' from the basement vault of Blackwood Manor."
    )
    seed_case(
        case_id="case_03_helios",
        case_name="The Helios Pharma Clinical Trial Discrepancy",
        description="Audit of cryogenic cold chain excursion in Trial HL-902 and adverse event reporting discrepancies."
    )
    seed_case(
        case_id="case_04_apex_robotics",
        case_name="The Apex Robotics Drone Sabotage",
        description="Investigation into unauthorized motor-kill firmware flashing and catastrophic failure of SkyHarrier-9 prototype."
    )
    print("\nAll demo cases successfully seeded and analyzed!")


if __name__ == "__main__":
    main()
