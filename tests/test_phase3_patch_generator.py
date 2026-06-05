from autofix.patch_generator import PatchGenerator, PatchOperation


def test_create_rollback_data_works_for_external_importer(tmp_path):
    target = tmp_path / "target.py"
    target.write_text("VALUE = 1\n", encoding="utf-8")

    operation = PatchOperation(
        operation_type="replace",
        file_path=str(target),
        old_content="VALUE = 1",
        new_content="VALUE = 2",
        line_start=1,
        line_end=1,
    )

    generator = PatchGenerator.__new__(PatchGenerator)
    rollback = generator._create_rollback_data([operation])

    assert rollback["timestamp"]
    assert rollback["file_backups"][str(target)] == "VALUE = 1\n"
    assert rollback["operation_order"] == [
        {
            "operation_type": "replace",
            "file_path": str(target),
            "line_start": 1,
            "line_end": 1,
        }
    ]
