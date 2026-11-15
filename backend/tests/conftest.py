import json
import logging
import os
import shutil
from pathlib import Path
import pytest

from app.config import settings
from app.models.schemas import DocumentMetadata
from app.services.ingestion.preprocessor import process_uploaded_file
from app.services.orchestration.controller import controller
from app.services.retrieval.retriever import retriever
from app.storage.case_store import case_store


@pytest.fixture(scope="session", autouse=True)
def setup_isolated_test_storage(tmp_path_factory):
    """
    Session-scoped fixture that redirects case_store and retriever storage
    to an isolated temporary directory for the duration of the test run,
    preventing contamination of user runtime storage.
    """
    test_storage = tmp_path_factory.mktemp("isolated_text_detective_storage")

    original_base_storage = case_store.base_storage
    original_uploads_dir = case_store.uploads_dir
    original_cases_dir = case_store.cases_dir
    original_chroma_dir = case_store.chroma_dir
    original_retriever_storage = retriever.storage_dir

    # Re-point storage to isolated temporary directory
    case_store.base_storage = test_storage
    case_store.uploads_dir = test_storage / "uploads"
    case_store.cases_dir = test_storage / "cases"
    case_store.chroma_dir = test_storage / "chroma"
    case_store.uploads_dir.mkdir(parents=True, exist_ok=True)
    case_store.cases_dir.mkdir(parents=True, exist_ok=True)
    case_store.chroma_dir.mkdir(parents=True, exist_ok=True)

    retriever.storage_dir = test_storage / "chroma"
    retriever.storage_dir.mkdir(parents=True, exist_ok=True)

    # Seed isolated case_01_meridian from sample cases without any ground truth
    base_data = Path(__file__).resolve().parent.parent.parent / "data" / "sample_cases"
    meridian_folder = base_data / "case_01_meridian"

    case_store.create_case(
        name="The Meridian Tech Data Leak",
        description="Investigation into customer database extraction from Server Room B.",
        is_demo=True,
        custom_id="case_01_meridian",
    )
    uploads_dir = case_store.uploads_dir / "case_01_meridian"
    uploads_dir.mkdir(parents=True, exist_ok=True)

    if meridian_folder.exists():
        for file_path in sorted(meridian_folder.iterdir()):
            if file_path.is_file() and file_path.suffix.lower() in {".txt", ".log", ".csv"}:
                dest = uploads_dir / file_path.name
                shutil.copyfile(file_path, dest)
                doc_meta = process_uploaded_file(
                    case_id="case_01_meridian",
                    file_path=dest,
                    original_filename=file_path.name,
                )
                case_store.add_document("case_01_meridian", doc_meta)

        controller.run_investigation(case_id="case_01_meridian")

    # Seed stub demo cases expected by CasesPage / Directory tests
    for cid, cname in [
        ("case_02_blackwood", "The Blackwood Manor Art Heist"),
        ("case_03_helios", "The Helios Pharma Clinical Trial Discrepancy"),
        ("case_04_apex_robotics", "The Apex Robotics Drone Sabotage"),
    ]:
        case_store.create_case(
            name=cname,
            description=f"Automated benchmark case {cid}",
            is_demo=True,
            custom_id=cid,
        )

    yield test_storage

    # Cleanup and restore
    case_store.base_storage = original_base_storage
    case_store.uploads_dir = original_uploads_dir
    case_store.cases_dir = original_cases_dir
    case_store.chroma_dir = original_chroma_dir
    retriever.storage_dir = original_retriever_storage
