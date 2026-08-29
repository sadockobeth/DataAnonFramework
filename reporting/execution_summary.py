"""
Module: execution_summary.py

Purpose:
Builds and formats execution summaries for anonymization runs.

Main responsibilities:
- Build a consistent summary for SUCCESS, FAILED, and CANCELLED executions.
- Record source and target table information.
- Record processed rows, batches, batch size, rules, and exclusions.
- Record execution start time, completion time, and duration.
- Record execution errors when applicable.
- Format execution duration for human-readable display.
- Format execution summaries for the GUI.

This module does not execute anonymization, access Oracle, write logs,
persist execution history, or display GUI components.
"""


# ------------------------------------------------------------------
# SECTION 1: FORMAT EXECUTION DURATION
# ------------------------------------------------------------------
def format_duration(seconds):
    if seconds is None:
        return "N/A"

    try:
        total_seconds = float(seconds)
    except (TypeError, ValueError):
        return str(seconds)

    if total_seconds < 60:
        return f"{total_seconds:.2f} seconds"

    minutes = int(total_seconds // 60)
    remaining_seconds = total_seconds % 60

    if minutes < 60:
        return f"{minutes} min {remaining_seconds:.2f} sec"

    hours = minutes // 60
    remaining_minutes = minutes % 60

    return f"{hours} hr {remaining_minutes} min {remaining_seconds:.2f} sec"


# ------------------------------------------------------------------
# SECTION 2: BUILD EXECUTION SUMMARY
# ------------------------------------------------------------------
def build_execution_summary(source_config, rules, target_config, execution_stats):
    source_schema = source_config.get("source_schema", "")
    source_table = source_config.get("source_table", "")

    target_schema = target_config.get("target_schema", "")
    target_table = target_config.get("target_table", "")

    return {
        "status": execution_stats.get("status", "UNKNOWN"),
        "source": f"{source_schema}.{source_table}",
        "target": f"{target_schema}.{target_table}",
        "rows_processed": execution_stats.get("rows_processed", 0),
        "batches_processed": execution_stats.get("batches_processed", 0),
        "batch_size": execution_stats.get("batch_size", 0),
        "rules": rules.copy(),
        "excluded_columns": target_config.get("excluded_columns", []).copy(),
        "started_at": execution_stats.get("started_at"),
        "completed_at": execution_stats.get("completed_at"),
        "duration_seconds": execution_stats.get("duration_seconds"),
        "error": execution_stats.get("error")
    }


# ------------------------------------------------------------------
# SECTION 3: FORMAT EXECUTION SUMMARY
# ------------------------------------------------------------------
def format_execution_summary(summary):
    status = summary.get("status", "UNKNOWN")
    source = summary.get("source", "")
    target = summary.get("target", "")

    rows_processed = summary.get("rows_processed", 0)
    batches_processed = summary.get("batches_processed", 0)
    batch_size = summary.get("batch_size", 0)

    started_at = summary.get("started_at") or "N/A"
    completed_at = summary.get("completed_at") or "N/A"

    duration = format_duration(
        summary.get("duration_seconds")
    )

    rules = summary.get("rules", {})
    excluded_columns = summary.get("excluded_columns", [])
    error = summary.get("error")

    lines = []

    # ------------------------------------------------------------------
    # SECTION 4: GENERAL EXECUTION INFORMATION
    # ------------------------------------------------------------------
    lines.append("EXECUTION RESULT")
    lines.append("-" * 70)

    lines.append(f"Status               : {status}")
    lines.append(f"Source               : {source}")
    lines.append(f"Target               : {target}")
    lines.append(f"Started              : {started_at}")
    lines.append(f"Completed            : {completed_at}")
    lines.append(f"Duration             : {duration}")

    lines.append("")

    # ------------------------------------------------------------------
    # SECTION 5: PROCESSING INFORMATION
    # ------------------------------------------------------------------
    lines.append("PROCESSING")
    lines.append("-" * 70)

    if status == "CANCELLED":
        lines.append(
            f"Rows before rollback : {rows_processed:,}"
        )
    else:
        lines.append(
            f"Rows processed       : {rows_processed:,}"
        )

    lines.append(
        f"Batches processed    : {batches_processed:,}"
    )

    lines.append(
        f"Batch size           : {batch_size:,}"
    )

    lines.append("")

    # ------------------------------------------------------------------
    # SECTION 6: ANONYMIZATION RULES
    # ------------------------------------------------------------------
    lines.append("ANONYMIZATION RULES")
    lines.append("-" * 70)

    if rules:
        for column_name, strategy in rules.items():
            lines.append(
                f"{column_name:<30} {strategy}"
            )
    else:
        lines.append(
            "No anonymization rules recorded."
        )

    lines.append("")

    # ------------------------------------------------------------------
    # SECTION 7: EXCLUDED COLUMNS
    # ------------------------------------------------------------------
    lines.append("EXCLUDED COLUMNS")
    lines.append("-" * 70)

    if excluded_columns:
        for column_name in excluded_columns:
            lines.append(
                column_name
            )
    else:
        lines.append(
            "None"
        )

    # ------------------------------------------------------------------
    # SECTION 8: FAILURE INFORMATION
    # ------------------------------------------------------------------
    if error:
        lines.append("")
        lines.append("ERROR")
        lines.append("-" * 70)
        lines.append(str(error))

    # ------------------------------------------------------------------
    # SECTION 9: TRANSACTION RESULT
    # ------------------------------------------------------------------
    lines.append("")
    lines.append("TRANSACTION")
    lines.append("-" * 70)

    if status == "SUCCESS":
        lines.append(
            "Anonymized data committed successfully."
        )

    elif status == "CANCELLED":
        lines.append(
            "Execution cancelled. Uncommitted anonymized rows were rolled back."
        )

    elif status == "FAILED":
        lines.append(
            "Execution failed. Uncommitted anonymized rows were rolled back."
        )

    else:
        lines.append(
            "Transaction outcome unavailable."
        )

    return "\n".join(lines)