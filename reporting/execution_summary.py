"""
Module: execution_summary.py

Purpose:
Builds and formats execution summaries for DataAnonFramework.

Main responsibilities:
- Combine execution statistics with source, target, rule, and exclusion settings.
- Calculate a readable execution duration.
- Produce a structured summary dictionary.
- Convert the summary into readable text for display in the GUI.
- Keep reporting logic separate from GUI and database-processing logic.

This module does not access Oracle, perform anonymization, or create GUI widgets.
"""


def build_execution_summary(source_config, rules, target_config, execution_stats):
    # ------------------------------------------------------------------
    # SECTION 1: BUILD EXECUTION SUMMARY
    # ------------------------------------------------------------------
    # Combine source, target, anonymization, and worker execution
    # statistics into one structured dictionary.
    return {
        "status": execution_stats["status"],
        "source": f'{source_config["source_schema"]}.{source_config["source_table"]}',
        "target": f'{target_config["target_schema"]}.{target_config["target_table"]}',
        "rows_processed": execution_stats["rows_processed"],
        "batches_processed": execution_stats["batches_processed"],
        "batch_size": execution_stats["batch_size"],
        "rules": rules.copy(),
        "excluded_columns": target_config["excluded_columns"].copy(),
        "started_at": execution_stats["started_at"],
        "completed_at": execution_stats["completed_at"],
        "duration_seconds": execution_stats["duration_seconds"],
        "error": execution_stats.get("error")
    }


def format_duration(duration_seconds):
    # ------------------------------------------------------------------
    # SECTION 2: FORMAT EXECUTION DURATION
    # ------------------------------------------------------------------
    # Convert total seconds into HH:MM:SS for easier reading.
    total_seconds = int(duration_seconds)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60

    return f"{hours:02}:{minutes:02}:{seconds:02}"


def format_execution_summary(summary):
    # ------------------------------------------------------------------
    # SECTION 3: FORMAT EXECUTION INFORMATION
    # ------------------------------------------------------------------
    # Convert datetime values into human-readable timestamps.
    started_at = summary["started_at"].strftime("%d-%b-%Y %H:%M:%S")
    completed_at = summary["completed_at"].strftime("%d-%b-%Y %H:%M:%S")
    duration = format_duration(summary["duration_seconds"])

    lines = [
        "ANONYMIZATION EXECUTION SUMMARY",
        "",
        f'Status:              {summary["status"]}',
        f'Source:              {summary["source"]}',
        f'Target:              {summary["target"]}',
        f'Rows Processed:      {summary["rows_processed"]:,}',
        f'Batches Processed:   {summary["batches_processed"]:,}',
        f'Batch Size:          {summary["batch_size"]:,}',
        f'Started:             {started_at}',
        f'Completed:           {completed_at}',
        f'Duration:            {duration}',
        "",
        "ANONYMIZATION RULES"
    ]

    # ------------------------------------------------------------------
    # SECTION 4: FORMAT ANONYMIZATION RULES
    # ------------------------------------------------------------------
    # Display every configured column -> strategy relationship.
    if summary["rules"]:
        for column_name, strategy in summary["rules"].items():
            lines.append(f"{column_name} -> {strategy}")
    else:
        lines.append("None")

    # ------------------------------------------------------------------
    # SECTION 5: FORMAT EXCLUDED COLUMNS
    # ------------------------------------------------------------------
    # Display columns that were intentionally omitted from the target.
    lines.append("")
    lines.append("EXCLUDED COLUMNS")

    if summary["excluded_columns"]:
        for column_name in summary["excluded_columns"]:
            lines.append(column_name)
    else:
        lines.append("None")

    # ------------------------------------------------------------------
    # SECTION 6: FORMAT EXECUTION ERROR
    # ------------------------------------------------------------------
    # Failed executions include the error message for troubleshooting.
    if summary["error"]:
        lines.append("")
        lines.append("ERROR")
        lines.append(summary["error"])

    return "\n".join(lines)