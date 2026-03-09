"""Tests for manifest comparison utilities."""

from agent_discover.tools.util_manifest import compute_changes


class TestComputeChanges:
    def test_all_new_when_no_prior(self):
        current = [
            {"gcs_path": "staging/files/a.csv", "hash": "abc123", "filename": "a.csv"},
            {"gcs_path": "staging/files/b.csv", "hash": "def456", "filename": "b.csv"},
        ]
        result = compute_changes(current, [])
        assert len(result["new"]) == 2
        assert len(result["modified"]) == 0
        assert len(result["unchanged"]) == 0
        assert len(result["removed"]) == 0

    def test_unchanged_when_same_hash(self):
        current = [{"gcs_path": "staging/files/a.csv", "hash": "abc123"}]
        prior = [{"file_path": "staging/files/a.csv", "file_hash": "abc123"}]
        result = compute_changes(current, prior)
        assert len(result["unchanged"]) == 1
        assert len(result["new"]) == 0
        assert len(result["modified"]) == 0

    def test_modified_when_different_hash(self):
        current = [{"gcs_path": "staging/files/a.csv", "hash": "new_hash"}]
        prior = [{"file_path": "staging/files/a.csv", "file_hash": "old_hash"}]
        result = compute_changes(current, prior)
        assert len(result["modified"]) == 1

    def test_removed_when_in_prior_not_current(self):
        current = []
        prior = [{"file_path": "staging/files/old.csv", "file_hash": "hash"}]
        result = compute_changes(current, prior)
        assert len(result["removed"]) == 1
        assert "staging/files/old.csv" in result["removed"]

    def test_mixed_changes(self):
        current = [
            {"gcs_path": "staging/files/same.csv", "hash": "same_hash"},
            {"gcs_path": "staging/files/changed.csv", "hash": "new_hash"},
            {"gcs_path": "staging/files/brand_new.csv", "hash": "fresh"},
        ]
        prior = [
            {"file_path": "staging/files/same.csv", "file_hash": "same_hash"},
            {"file_path": "staging/files/changed.csv", "file_hash": "old_hash"},
            {"file_path": "staging/files/deleted.csv", "file_hash": "gone"},
        ]
        result = compute_changes(current, prior)
        assert len(result["unchanged"]) == 1
        assert len(result["modified"]) == 1
        assert len(result["new"]) == 1
        assert len(result["removed"]) == 1
