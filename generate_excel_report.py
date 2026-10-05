"""
generate_excel_report.py
--------------------------
Reads reports/results.json (the same source the HTML dashboard uses) and
writes reports/dashboard.xlsx — a formatted Excel workbook with two sheets:

  Summary  — one row per control per repo, with framework mappings and a
             live formula-based count of pass/fail/evidence-only totals
  Findings — every individual finding (per PR, per collaborator, etc.)
             flattened into one filterable table

This gives GRC reviewers who prefer Excel (pivot tables, filtering, sharing
with auditors who expect a spreadsheet) the same evidence the live
dashboard shows, in a format they're used to working with.
"""

import json
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.table import Table, TableStyleInfo

FONT_NAME = "Arial"

STATUS_FILLS = {
    "PASS": PatternFill("solid", fgColor="C6EFCE"),
    "FAIL": PatternFill("solid", fgColor="FFC7CE"),
    "NO_DATA": PatternFill("solid", fgColor="FFEB9C"),
    "EVIDENCE_CAPTURED": PatternFill("solid", fgColor="BDD7EE"),
    "EVIDENCE": PatternFill("solid", fgColor="BDD7EE"),
}

STATUS_FONTS = {
    "PASS": Font(name=FONT_NAME, color="006100"),
    "FAIL": Font(name=FONT_NAME, color="9C0006"),
    "NO_DATA": Font(name=FONT_NAME, color="9C6500"),
    "EVIDENCE_CAPTURED": Font(name=FONT_NAME, color="1F4E78"),
    "EVIDENCE": Font(name=FONT_NAME, color="1F4E78"),
}

HEADER_FILL = PatternFill("solid", fgColor="2F5496")
HEADER_FONT = Font(name=FONT_NAME, bold=True, color="FFFFFF")


def style_header_row(ws, row_num, num_cols):
    for col in range(1, num_cols + 1):
        cell = ws.cell(row=row_num, column=col)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)


def autosize_columns(ws, min_width=10, max_width=60):
    for col_cells in ws.columns:
        length = max((len(str(c.value)) for c in col_cells if c.value is not None), default=0)
        col_letter = get_column_letter(col_cells[0].column)
        ws.column_dimensions[col_letter].width = max(min_width, min(length + 2, max_width))


def build_summary_sheet(wb, results):
    ws = wb.active
    ws.title = "Summary"

    ws["A1"] = "SDLC Controls — Summary"
    ws["A1"].font = Font(name=FONT_NAME, bold=True, size=14)
    ws["A2"] = f"Generated at {results['generated_at']} UTC"
    ws["A2"].font = Font(name=FONT_NAME, italic=True, color="595959")

    headers = ["Control ID", "Control Name", "SOC2", "ISO27001", "PCI-DSS", "NIST 800-53", "Repo", "Overall Status"]
    header_row = 4
    for col, header in enumerate(headers, start=1):
        ws.cell(row=header_row, column=col, value=header)
    style_header_row(ws, header_row, len(headers))

    row = header_row + 1
    first_data_row = row
    for control in results["controls"]:
        mapping = control["framework_mapping"]
        for repo_name, repo_result in control["per_repo"].items():
            ws.cell(row=row, column=1, value=control["id"]).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=2, value=control["name"]).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=3, value=mapping.get("soc2", "")).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=4, value=mapping.get("iso27001", "")).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=5, value=mapping.get("pci_dss", "")).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=6, value=mapping.get("nist_800_53", "")).font = Font(name=FONT_NAME)
            ws.cell(row=row, column=7, value=repo_name).font = Font(name=FONT_NAME)

            status = repo_result["overall"]
            status_cell = ws.cell(row=row, column=8, value=status)
            status_cell.font = STATUS_FONTS.get(status, Font(name=FONT_NAME))
            status_cell.fill = STATUS_FILLS.get(status, PatternFill())
            status_cell.alignment = Alignment(horizontal="center")
            row += 1
    last_data_row = row - 1

    # Live counts via formulas (not hardcoded) — these recalculate if rows are
    # added or edited later, per the workbook's own data.
    status_range = f"H{first_data_row}:H{last_data_row}"
    ws["J4"] = "Status"
    ws["K4"] = "Count"
    style_header_row(ws, 4, 0)  # no-op width guard; explicit styling below
    for cell_ref in ["J4", "K4"]:
        ws[cell_ref].fill = HEADER_FILL
        ws[cell_ref].font = HEADER_FONT

    summary_rows = [
        ("PASS", 5),
        ("FAIL", 6),
        ("NO_DATA", 7),
        ("EVIDENCE_CAPTURED", 8),
    ]
    for status_label, r in summary_rows:
        ws.cell(row=r, column=10, value=status_label).font = Font(name=FONT_NAME)
        ws.cell(row=r, column=11, value=f'=COUNTIF({status_range},"{status_label}")').font = Font(name=FONT_NAME)

    ws.freeze_panes = f"A{header_row + 1}"

    table_ref = f"A{header_row}:H{last_data_row}"
    table = Table(displayName="ControlsSummary", ref=table_ref)
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False
    )
    ws.add_table(table)

    autosize_columns(ws)
    return ws


def build_findings_sheet(wb, results):
    ws = wb.create_sheet("Findings")

    headers = ["Control ID", "Control Name", "Repo", "Item", "Status", "Detail"]
    header_row = 1
    for col, header in enumerate(headers, start=1):
        ws.cell(row=header_row, column=col, value=header)
    style_header_row(ws, header_row, len(headers))

    row = 2
    for control in results["controls"]:
        for repo_name, repo_result in control["per_repo"].items():
            for finding in repo_result["findings"]:
                item = finding.get("title") or finding.get("login") or ""
                pr_number = finding.get("pr_number")
                item_label = f"PR #{pr_number} — {item}" if pr_number else item

                ws.cell(row=row, column=1, value=control["id"]).font = Font(name=FONT_NAME)
                ws.cell(row=row, column=2, value=control["name"]).font = Font(name=FONT_NAME)
                ws.cell(row=row, column=3, value=repo_name).font = Font(name=FONT_NAME)
                ws.cell(row=row, column=4, value=item_label).font = Font(name=FONT_NAME)

                status = finding.get("status", "")
                status_cell = ws.cell(row=row, column=5, value=status)
                status_cell.font = STATUS_FONTS.get(status, Font(name=FONT_NAME))
                status_cell.fill = STATUS_FILLS.get(status, PatternFill())
                status_cell.alignment = Alignment(horizontal="center")

                detail_cell = ws.cell(row=row, column=6, value=finding.get("detail", ""))
                detail_cell.font = Font(name=FONT_NAME)
                detail_cell.alignment = Alignment(wrap_text=True, vertical="top")
                row += 1
    last_data_row = max(row - 1, header_row + 1)

    ws.freeze_panes = "A2"
    table = Table(displayName="Findings", ref=f"A{header_row}:F{last_data_row}")
    table.tableStyleInfo = TableStyleInfo(
        name="TableStyleMedium2", showRowStripes=True, showFirstColumn=False
    )
    ws.add_table(table)

    autosize_columns(ws, max_width=70)
    ws.column_dimensions["F"].width = 70  # Detail column stays wide and wraps
    return ws


def main():
    with open("reports/results.json") as f:
        results = json.load(f)

    wb = Workbook()
    build_summary_sheet(wb, results)
    build_findings_sheet(wb, results)

    wb.save("reports/dashboard.xlsx")
    print("Wrote reports/dashboard.xlsx")


if __name__ == "__main__":
    main()
