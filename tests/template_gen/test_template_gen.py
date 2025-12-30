import os
import shutil
import project_template_gen as gen
import helpers
import pytest

BASE_DIR = os.path.dirname(__file__)
TEST_FILE_DIR = os.path.join(BASE_DIR, "__pycache__", "test")
gen.TARGET_REPO_DIR = os.path.join(TEST_FILE_DIR, "repositories")
gen.PERSISTENCE_DIR = os.path.join(TEST_FILE_DIR, "gen-projects")

def _cleanup():
    if os.path.exists(TEST_FILE_DIR):
        shutil.rmtree(TEST_FILE_DIR)
    if os.path.exists(os.path.join(gen.GIT_REPO_DIR, "ofgo")):
        shutil.rmtree(os.path.join(gen.GIT_REPO_DIR, "ofgo"))

def test_generate_from_templates():
    _cleanup()
    assert not os.path.exists(os.path.join(gen.GIT_REPO_DIR, "ofgo"))
    assert not os.path.exists(os.path.join(gen.PERSISTENCE_DIR, "ofgo"))

    with pytest.raises(SystemExit):
        gen.generate_from_templates(repo_url = "https://github.com/knotmyrealname/ofgo", 
                                    email = "ddong2@ncsu.edu",
                                    language = "python",
                                    model = "None")
    assert os.path.exists(os.path.join(gen.PERSISTENCE_DIR, "ofgo"))

    for root, dirs, files in os.walk(os.path.join(gen.TEMPLATE_DIR, "python")):
        for name in files:
            assert os.path.exists(os.path.join(gen.PERSISTENCE_DIR, "ofgo", name))
            assert os.path.getsize(os.path.join(gen.PERSISTENCE_DIR, "ofgo", name)) != 0
    _cleanup()


