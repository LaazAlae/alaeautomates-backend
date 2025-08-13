###############################################################################
# EXCEL MACROS API MODULE
# RESTful endpoints for Excel VBA macro generation
###############################################################################

from flask import Blueprint, jsonify

excel_macros_api = Blueprint('excel_macros_api', __name__)

@excel_macros_api.route('/cleanup')
def get_cleanup_macro():
    """Get Excel cleanup and format macro code"""
    cleanup_macro = """Sub CleanupAndFormat()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim lastCol As Long
    Dim i As Long
    Dim j As Long
    
    Set ws = ActiveSheet
    
    ' Find the last row and column with data
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    Application.ScreenUpdating = False
    
    ' Remove empty rows
    For i = lastRow To 1 Step -1
        If Application.WorksheetFunction.CountA(ws.Rows(i)) = 0 Then
            ws.Rows(i).Delete
        End If
    Next i
    
    ' Remove empty columns
    For j = lastCol To 1 Step -1
        If Application.WorksheetFunction.CountA(ws.Columns(j)) = 0 Then
            ws.Columns(j).Delete
        End If
    Next j
    
    ' Recalculate ranges after deletion
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    ' Trim whitespace from all cells
    For i = 1 To lastRow
        For j = 1 To lastCol
            If Not IsEmpty(ws.Cells(i, j)) Then
                ws.Cells(i, j).Value = Trim(ws.Cells(i, j).Value)
            End If
        Next j
    Next i
    
    ' Auto-fit all columns
    ws.Columns.AutoFit
    
    ' Apply basic formatting
    With ws.Range(ws.Cells(1, 1), ws.Cells(lastRow, lastCol))
        .Font.Name = "Arial"
        .Font.Size = 10
        .Borders.LineStyle = xlContinuous
        .Borders.Weight = xlThin
    End With
    
    ' Format header row if it exists
    If lastRow > 0 Then
        With ws.Range(ws.Cells(1, 1), ws.Cells(1, lastCol))
            .Font.Bold = True
            .Interior.Color = RGB(220, 220, 220)
        End With
    End If
    
    Application.ScreenUpdating = True
    
    MsgBox "Cleanup and formatting completed!", vbInformation
End Sub"""

    instructions = [
        "Open your Excel file",
        "Press Alt + F11 to open the VBA Editor",
        "Go to Insert → Module to create a new module",
        "Copy and paste the macro code into the module",
        "Close the VBA Editor (Alt + Q)",
        "Press Alt + F8 to open the Macro dialog",
        "Select CleanupAndFormat and click Run"
    ]
    
    features = [
        "Removes all empty rows and columns",
        "Trims whitespace from all cells",
        "Auto-fits column widths to content",
        "Applies consistent Arial 10pt font",
        "Adds borders to all data cells",
        "Formats the first row as a header with bold text and gray background"
    ]
    
    return jsonify({
        'macro_name': 'CleanupAndFormat',
        'macro_code': cleanup_macro,
        'instructions': instructions,
        'features': features,
        'usage': 'Cleans and formats Excel spreadsheets automatically'
    })

@excel_macros_api.route('/sort')
def get_sort_macro():
    """Get Excel sort and sum macro code"""
    sort_macro = """Sub SortAndSum()
    Dim ws As Worksheet
    Dim lastRow As Long
    Dim lastCol As Long
    Dim dataRange As Range
    Dim response As Integer
    Dim sortCol As Integer
    
    Set ws = ActiveSheet
    
    ' Find the last row and column with data
    lastRow = ws.Cells(ws.Rows.Count, 1).End(xlUp).Row
    lastCol = ws.Cells(1, ws.Columns.Count).End(xlToLeft).Column
    
    If lastRow <= 1 Then
        MsgBox "No data to sort!", vbExclamation
        Exit Sub
    End If
    
    ' Ask user which column to sort by
    sortCol = InputBox("Enter column number to sort by (1 for A, 2 for B, etc.):", "Sort Column", 1)
    
    If sortCol < 1 Or sortCol > lastCol Then
        MsgBox "Invalid column number!", vbExclamation
        Exit Sub
    End If
    
    Set dataRange = ws.Range(ws.Cells(2, 1), ws.Cells(lastRow, lastCol))
    
    Application.ScreenUpdating = False
    
    ' Sort the data (excluding header row)
    dataRange.Sort Key1:=ws.Cells(2, sortCol), Order1:=xlAscending, Header:=xlNo
    
    ' Ask if user wants to add sum row
    response = MsgBox("Add sum row for numeric columns?", vbYesNo + vbQuestion, "Add Totals")
    
    If response = vbYes Then
        Dim i As Integer
        Dim sumRow As Long
        sumRow = lastRow + 2
        
        ' Add "Total:" label
        ws.Cells(sumRow, 1).Value = "Total:"
        ws.Cells(sumRow, 1).Font.Bold = True
        
        ' Add sums for numeric columns
        For i = 2 To lastCol
            If IsNumeric(ws.Cells(2, i).Value) Then
                ws.Cells(sumRow, i).Formula = "=SUM(" & ws.Range(ws.Cells(2, i), ws.Cells(lastRow, i)).Address & ")"
                ws.Cells(sumRow, i).Font.Bold = True
            End If
        Next i
        
        ' Format sum row
        With ws.Range(ws.Cells(sumRow, 1), ws.Cells(sumRow, lastCol))
            .Borders(xlEdgeTop).LineStyle = xlContinuous
            .Borders(xlEdgeTop).Weight = xlMedium
        End With
    End If
    
    ' Auto-fit columns
    ws.Columns.AutoFit
    
    Application.ScreenUpdating = True
    
    MsgBox "Sort and sum completed!", vbInformation
End Sub"""

    instructions = [
        "Open your Excel file with data (including headers in row 1)",
        "Press Alt + F11 to open the VBA Editor",
        "Go to Insert → Module to create a new module",
        "Copy and paste the macro code into the module",
        "Close the VBA Editor (Alt + Q)",
        "Press Alt + F8 to open the Macro dialog",
        "Select SortAndSum and click Run",
        "Enter the column number to sort by when prompted",
        "Choose Yes or No when asked to add sum totals"
    ]
    
    features = [
        "Sorts your data by the specified column (ascending order)",
        "Preserves the header row during sorting",
        "Optionally adds sum totals for all numeric columns",
        "Formats the total row with bold text and top border",
        "Auto-fits all column widths",
        "Handles data validation to prevent errors"
    ]
    
    tips = [
        "Make sure your data has headers in the first row",
        "Column A = 1, Column B = 2, Column C = 3, etc.",
        "Only numeric columns will show sum totals"
    ]
    
    return jsonify({
        'macro_name': 'SortAndSum',
        'macro_code': sort_macro,
        'instructions': instructions,
        'features': features,
        'tips': tips,
        'usage': 'Sorts Excel data and optionally adds sum totals'
    })