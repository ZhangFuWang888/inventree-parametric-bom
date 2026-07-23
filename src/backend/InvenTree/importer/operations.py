"""Data import operational functions."""

from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

import tablib
import tablib.core

import InvenTree.helpers


def load_data_file(data_file, file_format=None, skip_hint_row=True):
    """Load data file into a tablib dataset.

    Arguments:
        data_file: django file object containing data to import (should be already opened!)
        file_format: Format specifier for the data file
        skip_hint_row: If True, skip the first row (hint/instruction row) and use row 2 as headers
    """
    # Introspect the file format based on the provided file
    if not file_format:
        file_format = data_file.name.split('.')[-1]

    if file_format and file_format.startswith('.'):
        file_format = file_format[1:]

    file_format = file_format.strip().lower()

    if file_format not in InvenTree.helpers.GetExportFormats():
        raise ValidationError(_('Unsupported data file format'))

    file_object = data_file.file

    if hasattr(file_object, 'open'):
        file_object.open('r')

    file_object.seek(0)

    try:
        raw_data = file_object.read()
    except OSError:
        raise ValidationError(_('Failed to open data file'))

    # For Excel formats, handle hint row via openpyxl
    if skip_hint_row and file_format in ['xls', 'xlsx']:
        import io
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw_data), data_only=True)
        ws = wb.active

        # Row 2 = headers, Row 3+ = data
        headers = [str(cell.value).strip() if cell.value is not None else f'Column {idx + 1}'
                   for idx, cell in enumerate(ws[2])]
        data_rows = []
        for row in ws.iter_rows(min_row=3, values_only=True):
            # Stop at first fully empty row
            if all(cell is None for cell in row):
                break
            data_rows.append(list(row))

        data = tablib.Dataset(*data_rows, headers=headers)
        return data

    # Non-Excel formats: decode and skip first line
    raw_data = raw_data.decode()

    if skip_hint_row:
        # Skip the first line (hint row)
        lines = raw_data.splitlines()
        if len(lines) > 1:
            raw_data = '\n'.join(lines[1:])

    try:
        data = tablib.Dataset().load(raw_data, headers=True, format=file_format)
    except tablib.core.UnsupportedFormat:
        raise ValidationError(_('Unsupported data file format'))
    except tablib.core.InvalidDimensions:
        raise ValidationError(_('Invalid data file dimensions'))

    return data


def extract_column_names(data_file) -> list:
    """Extract column names from a data file.

    Uses the tablib library to extract column names from a data file.

    Args:
        data_file: File object containing data to import

    Returns:
        List of column names extracted from the file

    Raises:
        ValidationError: If the data file is not in a valid format
    """
    data = load_data_file(data_file)

    headers = []

    for idx, header in enumerate(data.headers):
        if header:
            header = str(header).strip()
            headers.append(header)
        else:
            # If the header is empty, generate a default header
            headers.append(f'Column {idx + 1}')

    return headers


def get_field_label(field) -> Optional[str]:
    """Return the label for a field in a serializer class.

    Check for labels in the following order of descending priority:

    - The serializer class has a 'label' specified for the field
    - The underlying model has a 'verbose_name' specified
    - The field name is used as the label

    Arguments:
        field: Field instance from a serializer class

    Returns:
        str: Field label
    """
    if field and (label := getattr(field, 'label', None)):
        return label

    # TODO: Check if the field is a model field

    return None
