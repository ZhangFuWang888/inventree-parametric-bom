
# ═══════════════════════════════════════════
# 参数导入/导出 (Excel)
# ═══════════════════════════════════════════

from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from django.http import HttpResponse
from parametric_bom.models import PartParameterConfig
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def export_params_excel(request):
    """Export parameter configs for a part as Excel file.

    GET /api/parametric-bom/export-params/?part=<part_id>
    """
    from part.models import Part
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    import io

    part_id = request.GET.get('part')
    if not part_id:
        return Response({'success': False, 'error': 'Provide part parameter'}, status=400)

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({'success': False, 'error': 'Part not found'}, status=404)

    configs = PartParameterConfig.objects.filter(part=part).order_by('display_order', 'id')

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = '参数配置'

    # Column widths
    widths = {'A': 25, 'B': 12, 'C': 15, 'D': 12, 'E': 12, 'F': 12, 'G': 35, 'H': 30, 'I': 12}
    for col, w in widths.items():
        ws.column_dimensions[col].width = w

    # Styles
    header_font = Font(name='微软雅黑', bold=True, size=11, color='FFFFFF')
    header_fill = PatternFill(start_color='2563EB', end_color='2563EB', fill_type='solid')
    header_align = Alignment(horizontal='center', vertical='center')
    thin_border = Border(
        left=Side(style='thin', color='D1D5DB'),
        right=Side(style='thin', color='D1D5DB'),
        top=Side(style='thin', color='D1D5DB'),
        bottom=Side(style='thin', color='D1D5DB'),
    )
    instruction_font = Font(name='微软雅黑', size=9, color='6B7280', italic=True)
    data_font = Font(name='微软雅黑', size=10)

    # Row 1: Instruction
    ws.merge_cells('A1:I1')
    ws['A1'] = f'📋 参数配置导出 — {part.name}。修改后可通过「导入参数」重新导入。类型：number(数值)/boolean(布尔)/text(文本)/option(选项)'
    ws['A1'].font = instruction_font
    ws['A1'].alignment = Alignment(horizontal='left', vertical='center')
    ws.row_dimensions[1].height = 22

    # Row 2: Headers
    headers = ['参数名称*', '类型', '默认值', '最小值', '最大值', '步长', '选项', '描述', '驱动参数']
    for col_idx, h in enumerate(headers, 1):
        cell = ws.cell(row=2, column=col_idx, value=h)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = header_align
        cell.border = thin_border
    ws.row_dimensions[2].height = 28

    # Data rows
    for row_idx, cfg in enumerate(configs, 3):
        ptype = cfg.parameter_type or 'number'
        opts = ''
        if cfg.options:
            if isinstance(cfg.options, list):
                opts = ', '.join(cfg.options)
            else:
                opts = str(cfg.options)

        row_data = [
            cfg.name or '',
            ptype,
            str(cfg.default_value) if cfg.default_value is not None else '',
            str(cfg.min_value) if cfg.min_value is not None else '',
            str(cfg.max_value) if cfg.max_value is not None else '',
            str(cfg.step_value) if cfg.step_value is not None else '',
            opts,
            cfg.description or '',
            '是' if cfg.is_driving else '否',
        ]
        for col_idx, val in enumerate(row_data, 1):
            cell = ws.cell(row=row_idx, column=col_idx, value=val)
            cell.font = data_font
            cell.border = thin_border
            cell.alignment = Alignment(vertical='center')
        ws.row_dimensions[row_idx].height = 22

    # Freeze header
    ws.freeze_panes = 'A3'

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f'参数配置_{part.name}.xlsx'
    from urllib.parse import quote
    response = HttpResponse(
        output.read(),
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename*=UTF-8\'\'{quote(filename)}'
    return response


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def import_params_excel(request):
    """Import parameter configs from uploaded Excel file.

    POST /api/parametric-bom/import-params/
    Form data: file (.xlsx), part_id, create_if_missing (bool)

    Columns: 参数名称, 类型, 默认值, 最小值, 最大值, 步长, 选项, 描述, 驱动参数
    """
    from part.models import Part
    import openpyxl
    import io
    from decimal import Decimal

    part_id = request.data.get('part_id')
    create_if_missing = request.data.get('create_if_missing', 'true').lower() in ('true', '1', 'yes')
    uploaded_file = request.FILES.get('file')

    if not part_id:
        return Response({'success': False, 'error': 'Provide part_id'}, status=400)
    if not uploaded_file:
        return Response({'success': False, 'error': 'Provide file (.xlsx)'}, status=400)

    try:
        part = Part.objects.get(pk=part_id)
    except Part.DoesNotExist:
        return Response({'success': False, 'error': 'Part not found'}, status=404)

    # Read Excel
    try:
        wb = openpyxl.load_workbook(io.BytesIO(uploaded_file.read()), read_only=True)
        ws = wb.active
        rows = list(ws.iter_rows(min_row=1, values_only=True))
    except Exception as e:
        return Response({'success': False, 'error': f'读取Excel失败: {str(e)}'}, status=400)

    if len(rows) < 2:
        return Response({'success': False, 'error': 'Excel至少需要表头+1行数据'}, status=400)

    # Find header row
    header_row_idx = None
    for i, row in enumerate(rows):
        if row and row[0]:
            first = str(row[0]).strip()
            if first in ('参数名称', '参数名称*') or first.startswith('参数名称'):
                header_row_idx = i
                break

    if header_row_idx is None:
        return Response({'success': False, 'error': '未找到"参数名称"列'}, status=400)

    header = [str(c or '').strip() for c in (rows[header_row_idx] or [])]
    col_map = {}
    for i, h in enumerate(header):
        h_clean = h.replace(' ', '').replace('*', '')
        if '参数名称' in h_clean:
            col_map['name'] = i
        elif '类型' in h_clean:
            col_map['type'] = i
        elif '默认值' in h_clean:
            col_map['default'] = i
        elif '最小值' in h_clean:
            col_map['min'] = i
        elif '最大值' in h_clean:
            col_map['max'] = i
        elif '步长' in h_clean:
            col_map['step'] = i
        elif '选项' in h_clean:
            col_map['options'] = i
        elif '描述' in h_clean:
            col_map['desc'] = i
        elif '驱动' in h_clean:
            col_map['driving'] = i

    if 'name' not in col_map:
        return Response({'success': False, 'error': '缺少"参数名称"列'}, status=400)

    # Parse data rows
    items = []
    for row_idx in range(header_row_idx + 1, len(rows)):
        row = rows[row_idx]
        if not row or all(c is None or str(c).strip() == '' for c in row):
            continue
        name = str(row[col_map['name']]).strip() if col_map['name'] < len(row) and row[col_map['name']] else ''
        if not name or name == 'None':
            continue

        def _col(key, default=''):
            if key not in col_map or col_map[key] >= len(row) or row[col_map[key]] is None:
                return default
            val = str(row[col_map[key]]).strip()
            return default if val == 'None' or val == '' else val

        items.append({
            'name': name,
            'type': _col('type', 'number'),
            'default': _col('default'),
            'min': _col('min'),
            'max': _col('max'),
            'step': _col('step', '1'),
            'options': _col('options'),
            'desc': _col('desc'),
            'driving': _col('driving', '是'),
        })

    if not items:
        return Response({'success': False, 'error': 'Excel中没有有效数据行'}, status=400)

    # Process items
    created = []
    updated = []
    skipped = []
    failed = []

    for idx, item in enumerate(items):
        name = item['name']
        ptype = item['type']
        if ptype not in ('number', 'boolean', 'text', 'option', 'multiselect', 'longtext'):
            ptype = 'number'

        # Parse values
        try:
            default_val = item['default'] if item['default'] else ''
            min_val = item['min'] if item['min'] else None
            max_val = item['max'] if item['max'] else None
            step_val = Decimal(item['step']) if item['step'] else Decimal('1')
            options_raw = item['options']
            options = [o.strip() for o in options_raw.split(',') if o.strip()] if options_raw else []
            is_driving = item['driving'] not in ('否', 'false', 'False', '0', 'no')
        except Exception as e:
            failed.append({'index': idx, 'name': name, 'error': f'数据解析失败: {str(e)}'})
            continue

        # Find existing config by name
        existing = PartParameterConfig.objects.filter(part=part, name=name).first()

        if existing:
            if not create_if_missing:
                skipped.append({'index': idx, 'name': name, 'reason': '参数已存在（未勾选覆盖）'})
                continue
            # Update
            try:
                existing.parameter_type = ptype
                existing.default_value = default_val
                existing.min_value = min_val
                existing.max_value = max_val
                existing.step_value = step_val
                existing.options = options
                existing.description = item['desc']
                existing.is_driving = is_driving
                existing.save()
                updated.append({'index': idx, 'name': name, 'status': '已更新'})
            except Exception as e:
                failed.append({'index': idx, 'name': name, 'error': f'更新失败: {str(e)}'})
        else:
            # Create new
            try:
                PartParameterConfig.objects.create(
                    part=part,
                    name=name,
                    parameter_type=ptype,
                    default_value=default_val,
                    min_value=min_val,
                    max_value=max_val,
                    step_value=step_val,
                    options=options,
                    description=item['desc'],
                    is_driving=is_driving,
                )
                created.append({'index': idx, 'name': name, 'status': '新建'})
            except Exception as e:
                failed.append({'index': idx, 'name': name, 'error': f'创建失败: {str(e)}'})

    return Response({
        'success': True,
        'created': created,
        'updated': updated,
        'skipped': skipped,
        'failed': failed,
        'total': len(items),
    })
