from pathlib import Path
import pytest
from unittest.mock import mock_open, patch

from jenv.util import read_version_file, write_version_file

# Tests for read_version_file
def test_read_version_file_exists_and_readable(mocker):
    mock_file_content = "openjdk-17.0.1"
    mocker.patch("pathlib.Path.is_file", return_value=True)
    # Mock read_text to directly return the content string
    mock_read_text_method = mocker.patch.object(Path, "read_text", return_value=mock_file_content)

    file_path = Path("/fake/path/.jenv-version")
    version = read_version_file(file_path)

    assert version == mock_file_content
    mock_read_text_method.assert_called_once_with() # read_text was called

def test_read_version_file_not_exists(mocker):
    mocker.patch("pathlib.Path.is_file", return_value=False)
    # Ensure read_text is not even called if is_file is false
    mock_read_text_method = mocker.patch.object(Path, "read_text")
    file_path = Path("/fake/path/.jenv-version")
    version = read_version_file(file_path)
    assert version is None
    mock_read_text_method.assert_not_called()

def test_read_version_file_empty(mocker):
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mock_read_text_method = mocker.patch.object(Path, "read_text", return_value="")
    file_path = Path("/fake/path/.jenv-version")
    version = read_version_file(file_path)
    assert version == "" # Or None, depending on desired behavior for empty. Current is ""
    mock_read_text_method.assert_called_once_with()

def test_read_version_file_io_error(mocker, caplog):
    mocker.patch("pathlib.Path.is_file", return_value=True)
    mocker.patch("pathlib.Path.read_text", side_effect=IOError("Test read error"))
    file_path = Path("/fake/path/.jenv-version")

    version = read_version_file(file_path)

    assert version is None
    assert "Error reading version from" in caplog.text
    assert "Test read error" in caplog.text

# Tests for write_version_file
def test_write_version_file_success(mocker):
    version_name = "temurin-11"
    file_path = Path("/fake/target/dir/.jenv-version")

    mock_mkdir = mocker.patch("pathlib.Path.mkdir")
    m_open = mock_open()
    mocker.patch("pathlib.Path.write_text", m_open)

    write_version_file(file_path, version_name)

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    m_open.assert_called_once_with(version_name)

@patch("pathlib.Path.mkdir") # Using @patch as an alternative to mocker.patch
@patch("pathlib.Path.write_text")
def test_write_version_file_strips_whitespace(mock_write_text, mock_mkdir):
    version_name_with_space = "  openjdk-21  \n"
    expected_written_version = "openjdk-21"
    file_path = Path("/fake/target/dir/.jenv-version")

    write_version_file(file_path, version_name_with_space)

    mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
    mock_write_text.assert_called_once_with(expected_written_version)

def test_write_version_file_io_error(mocker, caplog):
    version_name = "corretto-8"
    file_path = Path("/fake/target/dir/.jenv-version")

    mocker.patch("pathlib.Path.mkdir") # Assume mkdir works
    mocker.patch("pathlib.Path.write_text", side_effect=IOError("Test write error"))

    # No exception should be raised by write_version_file itself as it logs the error
    write_version_file(file_path, version_name)

    assert "Error writing version to" in caplog.text
    assert "Test write error" in caplog.text

# To run these tests, you would use `poetry run pytest` in the terminal.
# Ensure an __init__.py in tests/ and tests/unit/ if not already picked up.
# (pytest usually handles this well without __init__.py for simple cases)
