import { IconUsers } from '@tabler/icons-react';
import { useCallback, useEffect, useMemo, useState } from 'react';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import type { ApiFormFieldSet } from '@lib/types/Forms';
import { t } from '@lingui/core/macro';
import type {
  StatusCodeInterface,
  StatusCodeListInterface
} from '../components/render/StatusRenderer';
import { useApi } from '../contexts/ApiContext';
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
    price_currency: {},
    project_code: {
      description: t`Select project code for this line item`
    },
    notes: {},
    link: {}
  };
}

export function useParameterTemplateFields(): ApiFormFieldSet {
  return useMemo(() => {
    return {
      name: {},
      description: {},
      units: {},
      model_type: {},
      choices: {},
      checkbox: {},
      selectionlist: {
        filters: {
          active: true
        }
      },
      enabled: {}
    };
  }, []);
}

export function useParameterFields({
  modelType,
  modelId,
  initialData
}: {
  modelType: ModelType;
  modelId: number;
  initialData?: any;
}): ApiFormFieldSet {
  const api = useApi();
  const [templatePk, setTemplatePk] = useState<number | null>(
    initialData?.template ?? null
  );
  const [templateName, setTemplateName] = useState<string>(
    initialData?.template_detail?.name ?? ''
  );
  const [templateUnits, setTemplateUnits] = useState<string>(
    initialData?.template_detail?.units ?? ''
  );
  const [paramType, setParamType] = useState<string>(
    initialData?.template_detail?.checkbox ? 'boolean'
    : (initialData?.template_detail?.choices ? 'choice' : 'text')
  );
  const [templateChoices, setTemplateChoices] = useState<string>(
    initialData?.template_detail?.choices ?? ''
  );

  // Build checkbox and choices from paramType
  const isCheckbox = paramType === 'boolean';
  const isChoice = paramType === 'choice';
  const needsChoices = isChoice;
  const needsUnits = paramType === 'number';

  // Debounced template creation/update
  useEffect(() => {
    if (!templateName.trim()) {
      setTemplatePk(null);
      return;
    }

    const timer = setTimeout(async () => {
      const name = templateName.trim();
      // Build template data
      const tplData: any = { name };
      if (needsUnits && templateUnits.trim()) tplData.units = templateUnits.trim();
      if (isCheckbox) tplData.checkbox = true;
      if (isChoice && templateChoices.trim()) tplData.choices = templateChoices.trim();

      try {
        const createRes = await api.post(
          apiUrl(ApiEndpoints.parameter_template_list),
          tplData
        );
        setTemplatePk(createRes.data.pk);
      } catch {
        try {
          const searchRes = await api.get(
            apiUrl(ApiEndpoints.parameter_template_list),
            { params: { search: name, limit: 5 } }
          );
          if (searchRes.data?.results?.length > 0) {
            const match = searchRes.data.results.find(
              (t: any) => t.name === name
            );
            setTemplatePk(match ? match.pk : null);
          } else {
            setTemplatePk(null);
          }
        } catch {
          setTemplatePk(null);
        }
      }
    }, 500);
    return () => clearTimeout(timer);
  }, [templateName, templateUnits, paramType, templateChoices, api]);

  // Data field type derived from paramType
  const dataFieldType: 'string' | 'boolean' | 'choice' = isCheckbox ? 'boolean' : (isChoice ? 'choice' : 'string');
  const choiceOptions: any[] = isChoice && templateChoices.trim()
    ? templateChoices.split(',').map(s => ({
        display_name: s.trim(),
        value: s.trim()
      }))
    : [];

  const typeChoices = [
    { value: 'text', display_name: '文本型' },
    { value: 'number', display_name: '数值型' },
    { value: 'boolean', display_name: '布尔型' },
    { value: 'choice', display_name: '选项型' }
  ];

  return {
    model_type: {
      hidden: true,
      value: modelType
    },
    model_id: {
      hidden: true,
      value: modelId
    },
    template: {
      hidden: true,
      required: false,
      value: templatePk,
      filters: {
        for_model: modelType,
        enabled: true
      }
    },
    name: {
      label: '参数名称',
      required: true,
      field_type: 'string',
      value: templateName || undefined,
      onValueChange: (value: any) => {
        // value is undefined during initial data load (field not in API response)
        if (value === undefined) return;
        setTemplateName(value?.toString() || '');
      }
    },
    param_type: {
      label: '数据类型',
      required: true,
      field_type: 'choice',
      choices: typeChoices,
      value: paramType,
      onValueChange: (value: any) => {
        setParamType(value?.toString() || 'text');
        if (value !== 'choice') setTemplateChoices('');
        if (value !== 'number') setTemplateUnits('');
      }
    },
    units: {
      label: '单位',
      required: false,
      field_type: 'string',
      hidden: !needsUnits,
      onValueChange: (value: any) => {
        setTemplateUnits(value?.toString() || '');
      }
    },
    choices: {
      label: '选项值（逗号分隔）',
      required: false,
      field_type: 'string',
      hidden: !needsChoices,
      onValueChange: (value: any) => {
        setTemplateChoices(value?.toString() || '');
      }
    },
    data: {
      label: '数值',
      required: true,
      field_type: dataFieldType,
      choices: dataFieldType === 'choice' ? choiceOptions : undefined,
      default: dataFieldType === 'boolean' ? false : undefined
    },
    note: {}
  };
}
