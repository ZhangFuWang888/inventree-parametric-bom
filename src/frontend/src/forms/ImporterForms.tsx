import { t } from '@lingui/core/macro';
import type { ModelType } from '@lib/enums/ModelType';
import type { ApiFormFieldSet } from '@lib/types/Forms';

export function dataImporterSessionFields({
  modelType,
  allowUpdate = false
}: {
  modelType?: ModelType | string;
  allowUpdate?: boolean;
}): ApiFormFieldSet {
  const templateUrl = modelType
    ? `/api/importer/template/?model=${modelType}`
    : null;

  return {
    data_file: {
      description: templateUrl
        ? `支持 CSV / XLSX / TSV 格式。也可以先 <a href="${templateUrl}" target="_blank" style="color:#228be6;text-decoration:underline">📥 下载导入模板</a> 填写后再上传。`
        : t`支持 CSV、XLSX、TSV 格式。`
    },
    model_type: {
      value: modelType,
      hidden: modelType != undefined
    },
    update_records: {
      hidden: allowUpdate !== true,
      value: allowUpdate ? undefined : false
    },
    field_defaults: {
      hidden: true,
      value: {}
    },
    field_overrides: {
      hidden: true,
      value: {}
    },
    field_filters: {
      hidden: true,
      value: {}
    }
  };
}
