from app.routes import pipeline
from app.utils.config import CONFIG_ROOT, PROJECT_ROOT


def test_local_project_root_prefers_repository_root():
    assert (PROJECT_ROOT / "backend").is_dir()
    assert (CONFIG_ROOT / "semantic_job_templates.json").is_file()
    assert pipeline.DATA_DIR == PROJECT_ROOT / "data"
