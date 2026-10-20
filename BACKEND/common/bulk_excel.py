import hashlib
import json
import re
import zipfile
import zlib
from io import BytesIO
from xml.etree import ElementTree

from django.core import signing
from django.db import DatabaseError
from django.http import HttpResponse
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils.exceptions import InvalidFileException
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


MAX_UPLOAD_SIZE = 2 * 1024 * 1024
MAX_WORKBOOK_SIZE = 20 * 1024 * 1024
MAX_IMPORT_ROWS = 2000
MAX_WORKSHEETS = 10
IMPORT_TOKEN_MAX_AGE = 30 * 60


class ImportFileError(Exception):
    pass


def _normalize_header(value):
    if not isinstance(value, str):
        return ''
    return re.sub(r'[^a-z0-9]', '', value.strip().lower())


def build_import_template(title, columns, instructions):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = title[:31]
    sheet.append([header for header, _, _ in columns])
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = f'A1:{_excel_column(len(columns))}1'
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill(fill_type='solid', fgColor='1F4E78')
    for index, (header, field_name, _) in enumerate(columns, start=1):
        sheet.column_dimensions[_excel_column(index)].width = max(16, min(len(header) + 4, 40))
        if field_name in {'order', 'capacity'}:
            for row_number in range(2, MAX_IMPORT_ROWS + 2):
                sheet.cell(row=row_number, column=index).number_format = '0'
        elif field_name in {'username', 'email', 'employee_id', 'phone_number', 'code', 'grade_level_codes', 'strand_code'}:
            for row_number in range(2, MAX_IMPORT_ROWS + 2):
                sheet.cell(row=row_number, column=index).number_format = '@'

    guide = workbook.create_sheet('Instructions')
    guide.append([f'{title} bulk import template'])
    guide.append(['Required fields are identified in the column headings.'])
    for instruction in instructions:
        guide.append([instruction])
    guide.column_dimensions['A'].width = 115
    for row in guide.iter_rows():
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')

    return workbook


def _excel_column(index):
    name = ''
    while index:
        index, remainder = divmod(index - 1, 26)
        name = chr(65 + remainder) + name
    return name


def parse_import_workbook(upload, columns, required_fields, header_aliases, row_label, numeric_fields):
    if upload.size > MAX_UPLOAD_SIZE:
        raise ImportFileError('The selected file exceeds the 2 MB upload limit. Split the workbook into smaller files and try again.')
    if not (upload.name or '').lower().endswith('.xlsx'):
        raise ImportFileError('Select an Excel .xlsx file.')

    upload.seek(0)
    try:
        with zipfile.ZipFile(upload) as archive:
            entries = archive.infolist()
            if len(entries) > 1000:
                raise ImportFileError('The workbook contains too many internal files.')
            if sum(entry.file_size for entry in entries) > MAX_WORKBOOK_SIZE:
                raise ImportFileError('The uncompressed workbook is too large to process.')
            if any(entry.flag_bits & 0x1 for entry in entries):
                raise ImportFileError('Encrypted workbooks are not supported.')
            if any(
                entry.file_size > 10 * 1024 * 1024
                or (entry.compress_size and entry.file_size / entry.compress_size > 100)
                for entry in entries
            ):
                raise ImportFileError('The workbook contains an oversized or highly compressed file.')
            for entry in entries:
                if entry.filename.endswith(('.xml', '.rels')):
                    xml_content = archive.read(entry)
                    if b'<!doctype' in xml_content.lower() or b'<!entity' in xml_content.lower():
                        raise ImportFileError('The workbook contains unsupported XML declarations.')
            names = set(archive.namelist())
            if '[Content_Types].xml' not in names or 'xl/workbook.xml' not in names:
                raise ImportFileError('The uploaded file is not a valid Excel workbook.')
    except ImportFileError:
        raise
    except (zipfile.BadZipFile, OSError, ValueError, RuntimeError, EOFError, zlib.error) as exc:
        raise ImportFileError('The uploaded file is not a valid .xlsx workbook.') from exc
    finally:
        upload.seek(0)

    try:
        workbook = load_workbook(upload, read_only=True, data_only=False)
    except (InvalidFileException, OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, EOFError, zlib.error, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ImportFileError('The uploaded file could not be read as an Excel workbook.') from exc

    try:
        if not workbook.worksheets or len(workbook.worksheets) > MAX_WORKSHEETS:
            raise ImportFileError('The workbook must contain between 1 and 10 worksheets.')
        sheet = next((item for item in workbook.worksheets if item.sheet_state == 'visible'), None)
        if sheet is None:
            raise ImportFileError(f'The workbook must contain a visible {row_label.lower()} worksheet.')
        if sheet.max_row is None or sheet.max_row < 1:
            raise ImportFileError(f'The {row_label.lower()} worksheet is empty.')
        if sheet.max_row > MAX_IMPORT_ROWS + 1:
            raise ImportFileError(f'The workbook may contain at most {MAX_IMPORT_ROWS} {row_label.lower()} rows.')
        if sheet.max_column is None or sheet.max_column > len(columns):
            raise ImportFileError(f'The {row_label.lower()} worksheet contains too many columns.')

        aliases = dict(header_aliases)
        for header, field_name, _ in columns:
            aliases.setdefault(_normalize_header(header), field_name)
            aliases.setdefault(_normalize_header(field_name), field_name)

        header_cells = next(sheet.iter_rows(min_row=1, max_row=1, max_col=sheet.max_column))
        headers = []
        for cell in header_cells:
            if cell.data_type == 'f':
                raise ImportFileError('Spreadsheet headers cannot contain formulas.')
            headers.append(aliases.get(_normalize_header(cell.value), ''))
        if any(not header for header in headers):
            raise ImportFileError('The header row contains a blank or unsupported column name.')
        if len(set(headers)) != len(headers):
            raise ImportFileError('The header row contains duplicate columns.')
        missing_headers = required_fields - set(headers)
        if missing_headers:
            labels = ', '.join(
                header for header, field_name, _ in columns if field_name in missing_headers
            )
            raise ImportFileError(f'Missing required column(s): {labels}.')

        rows = []
        for row_number, cells in enumerate(
            sheet.iter_rows(min_row=2, max_row=sheet.max_row, max_col=sheet.max_column),
            start=2,
        ):
            if all(cell.value is None for cell in cells):
                continue
            values = {}
            errors = []
            for field_name, cell in zip(headers, cells):
                if cell.data_type == 'f':
                    errors.append(f'{field_name.replace("_", " ").title()} cannot contain a formula.')
                elif cell.value is None:
                    values[field_name] = ''
                elif field_name in numeric_fields and isinstance(cell.value, (int, float)) and not isinstance(cell.value, bool):
                    if float(cell.value).is_integer():
                        values[field_name] = str(int(cell.value))
                    else:
                        errors.append(f'{field_name.replace("_", " ").title()} must be a whole number.')
                elif not isinstance(cell.value, str):
                    errors.append(f'{field_name.replace("_", " ").title()} must be entered as text.')
                else:
                    values[field_name] = cell.value.strip()
            for field_name in required_fields:
                if field_name in values and not values[field_name]:
                    errors.append(f'{field_name.replace("_", " ").title()} is required.')
            for _, field_name, _ in columns:
                values.setdefault(field_name, '')
            rows.append({'row': row_number, 'values': values, 'errors': errors})
        if not rows:
            raise ImportFileError(f'The worksheet does not contain any {row_label.lower()} rows.')
        return rows
    except ImportFileError:
        raise
    except (InvalidFileException, OSError, ValueError, KeyError, TypeError, IndexError, RuntimeError, EOFError, zlib.error, zipfile.BadZipFile, ElementTree.ParseError) as exc:
        raise ImportFileError(f'The {row_label.lower()} worksheet is malformed or could not be read.') from exc
    finally:
        workbook.close()


def preview_digest(parsed_rows):
    encoded = json.dumps(
        parsed_rows,
        sort_keys=True,
        separators=(',', ':'),
        ensure_ascii=True,
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


class BulkImportBase(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    columns = ()
    required_fields = frozenset()
    header_aliases = {}
    numeric_fields = frozenset()
    import_title = 'Import'
    row_label = 'Record'
    token_salt = 'academic.bulk-import'
    filename = 'edu-assist-import-template.xlsx'

    def get(self, request):
        workbook = build_import_template(
            self.import_title,
            self.columns,
            self.template_instructions(),
        )
        output = BytesIO()
        workbook.save(output)
        response = HttpResponse(
            output.getvalue(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = f'attachment; filename="{self.filename}"'
        response['Cache-Control'] = 'no-store'
        return response

    def template_instructions(self):
        return []

    def parse(self, upload):
        return parse_import_workbook(
            upload,
            self.columns,
            self.required_fields,
            self.header_aliases,
            self.row_label,
            self.numeric_fields,
        )

    def review_rows(self, parsed_rows):
        raise NotImplementedError

    def persist_records(self, records, request):
        raise NotImplementedError

    def post(self, request):
        upload = request.FILES.get('file')
        if upload is None:
            return Response({'detail': 'Select an .xlsx file to preview.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            parsed_rows = self.parse(upload)
        except ImportFileError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        rows, valid_records = self.review_rows(parsed_rows)
        token = None
        if valid_records:
            token = signing.dumps(
                {'user_id': request.user.pk, 'digest': preview_digest(parsed_rows)},
                salt=self.token_salt,
                compress=True,
            )
        return Response({
            'rows': rows,
            'valid_count': len(valid_records),
            'rejected_count': len(rows) - len(valid_records),
            'import_token': token,
            'expires_in_seconds': IMPORT_TOKEN_MAX_AGE if token else 0,
        })


class BulkImportPreviewBase(BulkImportBase):
    http_method_names = ['post', 'options']


class BulkImportConfirmBase(BulkImportBase):
    http_method_names = ['post', 'options']
    importer_class = None

    def post(self, request):
        import_token = request.data.get('import_token')
        upload = request.FILES.get('file')
        if not isinstance(import_token, str) or upload is None:
            return Response({'detail': 'A valid preview and the same .xlsx workbook are required to confirm.'}, status=status.HTTP_400_BAD_REQUEST)
        importer = self.importer_class()
        try:
            parsed_rows = importer.parse(upload)
        except ImportFileError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        try:
            signed_preview = signing.loads(
                import_token,
                salt=importer.token_salt,
                max_age=IMPORT_TOKEN_MAX_AGE,
            )
        except signing.SignatureExpired:
            return Response({'detail': 'The preview has expired. Upload the workbook again.'}, status=status.HTTP_400_BAD_REQUEST)
        except signing.BadSignature:
            return Response({'detail': 'The preview could not be verified. Upload the workbook again.'}, status=status.HTTP_400_BAD_REQUEST)

        if (
            signed_preview.get('user_id') != request.user.pk
            or signed_preview.get('digest') != preview_digest(parsed_rows)
        ):
            return Response({'detail': 'The preview does not match this user or submitted data. Upload the workbook again.'}, status=status.HTTP_400_BAD_REQUEST)

        rows, valid_records = importer.review_rows(parsed_rows)
        try:
            imported_rows = importer.persist_records(valid_records, request)
        except DatabaseError:
            return Response({
                'detail': 'The import was rolled back because a record changed or conflicted while saving. Preview the workbook again before retrying.',
            }, status=status.HTTP_409_CONFLICT)
        return Response({
            'imported_count': len(imported_rows),
            'imported_rows': imported_rows,
            'rejected_count': len(rows) - len(valid_records),
            'rejected_rows': [
                {'row': row['row'], 'errors': row['errors']}
                for row in rows if row['status'] != 'valid'
            ],
        })
