from __future__ import annotations

from pathlib import Path


def test_keep_current_merge_policy_is_checked_in():
    attributes = Path('.gitattributes').read_text(encoding='utf-8')
    assert 'services/** merge=keep-current' in attributes
    assert 'shared/** merge=keep-current' in attributes
    assert 'training/** merge=keep-current' in attributes
    assert 'tests/** merge=keep-current' in attributes


def test_merge_setup_script_exists_and_configures_driver_name():
    script = Path('scripts/setup_keep_current_merge.sh')
    text = script.read_text(encoding='utf-8')
    assert script.exists()
    assert 'merge.keep-current.driver true' in text
    assert 'merge.keep-current.recursive binary' in text
