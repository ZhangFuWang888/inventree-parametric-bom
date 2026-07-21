import { IconUsers } from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';

import { ModelType } from '@lib/enums/ModelType';
import type { ApiFormFieldSet, ApiFormFieldType } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import type {
  StatusCodeInterface,
  StatusCodeListInterface
} from '../components/render/StatusRenderer';
import { useGlobalStatusState } from '../states/GlobalStatusState';
import { useUserState } from '../states/UserState';

export function projectCodeFields(): ApiFormFieldSet {
  return {
    code: {},
    description: {},
    responsible: {
      icon: <IconUsers />
    }
  };
}

export function useCustomStateFields(): ApiFormFieldSet {
  // Status codes
  const statusCodes = useGlobalStatusState();

  // Selected base status class
  const [statusClass, setStatusClass] = useState<string>('');

  // Construct a list of status options based on the selected status class
  const statusOptions: any[] = useMemo(() => {
    const options: any[] = [];

    const valuesList = Object.values(statusCodes.status ?? {}).find(
      (value: StatusCodeListInterface) => value.status_class === statusClass
    );

    Object.values(valuesList?.values ?? {}).forEach(
      (value: StatusCodeInterface) => {
        options.push({
          value: value.key,
          display_name: value.label
        });
      }
    );

    return options;
  }, [statusCodes, statusClass]);

  return useMemo(() => {
    return {
      reference_status: {
        onValueChange(value) {
          setStatusClass(value);
        }
      },
      logical_key: {
        field_type: 'choice',
        choices: statusOptions
      },
      key: {},
      name: {},
      label: {},
      color: {},
      model: {}
    };
  }, [statusOptions]);
}

export function customUnitsFields(): ApiFormFieldSet {
  return {
    name: {},
    definition: {},
    symbol: {}
  };
}

export function extraLineItemFields(): ApiFormFieldSet {
  return {
    order: {
      hidden: true
    },
    line: {},
    reference: {},
    description: {},
    quantity: {},
    price: {},
    price_currency: {
      description: t`Select project code for this line item`
    },
    project_code: {},
    notes: {},
    link: {}
  };
}

export function useParameterTemplateFields(): ApiFormFieldSet {
  const [paramType, setParamType] = useState<string>('text');

  return useMemo(() => {
    const isNumber = paramType === 'number';
    const isBoolean = paramType === 'boolean';
    const isChoice = paramType === 'choice';
    const isText = paramType === 'text';

    return {
      param_type: {
        label: '参数类型',
        required: true,
        field_type: 'choice',
        choices: [
          { value: 'text', display_name: '文本型' },
          { value: 'number', display_name: '数值型' },
          { value: 'boolean', display_name: '布尔型（开关）' },
          { value: 'choice', display_name: '选项型（下拉）' }
        ],
        value: paramType,
        onValueChange: (value: any) => {
          if (value === undefined) return;
          setParamType(value?.toString() || 'text');
        }
      },
      name: {
        label: '参数名称',
        required: true,
        description:
          isText ? '例如：备注、说明'
          : isNumber ? '例如：密度、长度、温度'
          : isBoolean ? '例如：是否启用、有无附件'
          : '例如：表面处理方式、材料等级'
      },
      units: {
        label: '单位',
        required: false,
        hidden: !isNumber,
        description: '输入物理单位（必填有效单位，如 g/cm³, mm, kg, °C）。❌ 不要填数值！'
      },
      checkbox: {
        label: '布尔值',
        hidden: !isBoolean,
        value: isBoolean ? true : undefined
      },
      choices: {
        label: '选项值',
        required: false,
        hidden: !isChoice,
        description: '多个选项用逗号分隔，例如：喷塑,电镀,阳极氧化,拉丝'
      },
      model_type: { hidden: true },
      selectionlist: { hidden: true },
      description: { hidden: true },
      enabled: { hidden: true }
    };
  }, [paramType]);
}

export function useParameterFields({
  modelType,
  modelId
}: {
  modelType: ModelType;
  modelId: number;
}): ApiFormFieldSet {
  // Track selected template to dynamically adjust the data field type
  const [templateData, setTemplateData] = useState<any>(null);
  const templateCreateFields = useParameterTemplateFields();

  // Build data field definition based on selected template type
  const dataField: ApiFormFieldType = useMemo(() => {
    if (templateData?.checkbox) {
      return { field_type: 'boolean' as const };
    }

    const choicesStr: string | undefined = templateData?.choices;
    if (choicesStr && choicesStr.trim()) {
      const choices: { value: string; display_name: string }[] = choicesStr
        .split(',')
        .map((c: string) => c.trim())
        .filter((c: string) => c.length > 0)
        .map((c: string) => ({ value: c, display_name: c }));

      if (choices.length > 0) {
        return { field_type: 'choice' as const, choices };
      }
    }

    // Default: text field
    return {};
  }, [templateData]);

  // Extract template info from various callback shapes
  const handleTemplateChange = useCallback((_pk: number, instance: any) => {
    // instance may be the full API response (with template_detail)
    // or the template object directly
    const tpl = instance?.template_detail ?? instance;
    if (tpl && typeof tpl === 'object') {
      setTemplateData(tpl);
    }
  }, []);

  return useMemo(() => ({
    model_type: {
      hidden: true,
      value: modelType
    },
    model_id: {
      hidden: true,
      value: modelId
    },
    template: {
      filters: {
        for_model: modelType,
        enabled: true
      },
      addCreateFields: templateCreateFields,
      onValueChange: handleTemplateChange
    },
    data: dataField,
    note: {}
  }), [modelType, modelId, dataField, templateCreateFields, handleTemplateChange]);
}
