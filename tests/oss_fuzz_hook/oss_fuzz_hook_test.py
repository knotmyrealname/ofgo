from oss_fuzz_hook import run_project


def test_run_project_unknown_harness_type(mocker):
    """Test error handling for unknown harness type"""
    mocker.patch('oss_fuzz_hook.subprocess.run')
    mock_log = mocker.patch('oss_fuzz_hook.log')
    
    result = run_project(project="jupyter_server", harness_type="invalid_type")
    
    mock_log.assert_called_with("Error: Unknown harness_type 'invalid_type'. Use 'existing' or 'generated'.")
    assert result is False


def test_run_project_no_fuzzers_directory(mocker):
    """Test error handling when fuzzers directory doesn't exist"""
    mock_subprocess_run = mocker.patch('oss_fuzz_hook.subprocess.run')
    mock_exists = mocker.patch('oss_fuzz_hook.os.path.exists')
    mock_log = mocker.patch('oss_fuzz_hook.log')
    
    mock_subprocess_run.return_value = mocker.Mock(returncode=0)
    mock_exists.return_value = False
    
    result = run_project(project="jupyter_server", harness_type="existing")
    
    assert result is False
    error_log_found = any("Fuzzers directory not found" in str(call) for call in mock_log.call_args_list)
    assert error_log_found


def test_run_project_no_fuzzers_found(mocker):
    """Test error handling when no fuzzers are found"""
    mock_subprocess_run = mocker.patch('oss_fuzz_hook.subprocess.run')
    mock_exists = mocker.patch('oss_fuzz_hook.os.path.exists')
    mock_listdir = mocker.patch('oss_fuzz_hook.os.listdir')
    mock_log = mocker.patch('oss_fuzz_hook.log')
    
    mock_subprocess_run.return_value = mocker.Mock(returncode=0)
    mock_exists.return_value = True
    mock_listdir.return_value = []
    
    result = run_project(project="jupyter_server", harness_type="existing")
    
    assert result is False
    mock_log.assert_any_call("Error: No existing fuzzers found with pattern 'fuzz_*'.")


def test_run_project_fuzzer_execution_fails(mocker):
    """Test error handling when fuzzer execution fails"""
    mock_subprocess_run = mocker.patch('oss_fuzz_hook.subprocess.run')
    mock_exists = mocker.patch('oss_fuzz_hook.os.path.exists')
    mock_listdir = mocker.patch('oss_fuzz_hook.os.listdir')
    mock_log = mocker.patch('oss_fuzz_hook.log')
    
    mock_subprocess_run.side_effect = [
        mocker.Mock(returncode=0),  # pull_images
        mocker.Mock(returncode=0),  # build_image
        mocker.Mock(returncode=0),  # build_fuzzers
        mocker.Mock(returncode=1)   # run_fuzzer fails
    ]
    mock_exists.return_value = True
    mock_listdir.return_value = ["fuzz_serialization"]
    
    result = run_project(project="jupyter_server", harness_type="existing")
    
    assert result is True
    mock_log.assert_any_call("fuzz_serialization failed")