import { t } from '@lingui/core/macro';
import { ActionIcon, Group, LoadingOverlay, Skeleton, Stack, Tooltip } from '@mantine/core';
import {
  IconCategory,
  IconEdit,
  IconHierarchy2,
  IconInfoCircle,
  IconLayoutList,
  IconListCheck,
  IconPackages,
  IconPlus,
  IconSitemap
} from '@tabler/icons-react';
import { useCallback, useMemo, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import { ModelType } from '@lib/enums/ModelType';
import { UserRoles } from '@lib/enums/Roles';
import { getDetailUrl } from '@lib/functions/Navigation';
import type { PanelType } from '@lib/types/Panel';
import AdminButton from '../../components/buttons/AdminButton';
import StarredToggleButton from '../../components/buttons/StarredToggleButton';
import {
  type DetailsField,
  DetailsTable
} from '../../components/details/Details';
import { ItemDetailsGrid } from '../../components/details/ItemDetails';
import {
  DeleteItemAction,
  EditItemAction,
  OptionsActionDropdown
} from '../../components/items/ActionDropdown';
import { ApiIcon } from '../../components/items/ApiIcon';
import InstanceDetail from '../../components/nav/InstanceDetail';
import NavigationTree from '../../components/nav/NavigationTree';
import { PageDetail } from '../../components/nav/PageDetail';
import { PanelGroup } from '../../components/panels/PanelGroup';
import { partCategoryFields } from '../../forms/PartForms';
import {
  useCreateApiFormModal,
  useDeleteApiFormModal,
  useEditApiFormModal
} from '../../hooks/UseForm';
import { useInstance } from '../../hooks/UseInstance';
import { useUserSettingsState } from '../../states/SettingsStates';
import { useUserState } from '../../states/UserState';
import { PartCategoryTable } from '../../tables/part/PartCategoryTable';
import PartCategoryTemplateTable from '../../tables/part/PartCategoryTemplateTable';
import { PartListTable } from '../../tables/part/PartTable';
import { StockItemTable } from '../../tables/stock/StockItemTable';

/**
 * Detail view for a single PartCategory instance.
 *
 * Note: If no category ID is supplied, this acts as the top-level part category page
 */
export default function CategoryDetail() {
  const { id: _id } = useParams();
  const id = useMemo(
    () => (!Number.isNaN(Number.parseInt(_id || '')) ? _id : undefined),
    [_id]
  );

  const navigate = useNavigate();
  const user = useUserState();
  const settings = useUserSettingsState();

  const [treeOpen, setTreeOpen] = useState(false);
  const [viewMode, setViewMode] = useState<'list' | 'tree'>('list');

  const {
    instance: category,
    refreshInstance,
    instanceQuery
  } = useInstance({
    endpoint: ApiEndpoints.category_list,
    hasPrimaryKey: true,
    pk: id,
    params: {
      path_detail: true
    }
  });

  const detailsPanel = useMemo(() => {
    if (id && instanceQuery.isFetching) {
      return <Skeleton />;
    }

    const left: DetailsField[] = [
      {
        type: 'text',
        name: 'name',
        label: t`Name`,
        copy: true,
        value_formatter: () => (
          <Group gap='xs'>
            {category.icon && <ApiIcon name={category.icon} />}
            {category.name}
          </Group>
        )
      },
      {
        type: 'text',
        name: 'pathstring',
        label: t`Path`,
        icon: 'sitemap',
        copy: true,
        hidden: !id
      },
      {
        type: 'text',
        name: 'description',
        label: t`Description`,
        copy: true
      },
      {
        type: 'link',
        name: 'parent',
        model_field: 'name',
        icon: 'location',
        label: t`Parent Category`,
        model: ModelType.partcategory,
        hidden: !category?.parent
      },
      {
        type: 'boolean',
        name: 'starred',
        icon: 'notification',
        label: t`Subscribed`
      }
    ];

    const right: DetailsField[] = [
      {
        type: 'text',
        name: 'part_count',
        label: t`Parts`,
        icon: 'part',
        value_formatter: () => category?.part_count || '0'
      },
      {
        type: 'text',
        name: 'subcategories',
        label: t`Subcategories`,
        icon: 'sitemap',
        hidden: !category?.subcategories
      },
      {
        type: 'boolean',
        name: 'structural',
        label: t`Structural`,
        icon: 'sitemap'
      },
      {
        type: 'link',
        name: 'parent_default_location',
        label: t`Parent default location`,
        model: ModelType.stocklocation,
        hidden: !category.parent_default_location || category.default_location
      },
      {
        type: 'link',
        name: 'default_location',
        label: t`Default location`,
        model: ModelType.stocklocation,
        hidden: !category.default_location
      }
    ];

    return (
      <ItemDetailsGrid>
        {id && category?.pk && <DetailsTable item={category} fields={left} />}
        {id && category?.pk && <DetailsTable item={category} fields={right} />}
      </ItemDetailsGrid>
    );
  }, [category, instanceQuery]);

  const editCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: id,
    title: '编辑物料类别',
    fields: partCategoryFields({}),
    onFormSuccess: refreshInstance
  });

  const deleteOptions = useMemo(() => {
    return [
      {
        value: 'false',
        display_name: t`Move items to parent category`
      },
      {
        value: 'true',
        display_name: t`Delete items`
      }
    ];
  }, []);

  const deleteCategory = useDeleteApiFormModal({
    url: ApiEndpoints.category_list,
    pk: id,
    title: '删除物料类别',
    fields: {
      delete_parts: {
        label: t`Parts Action`,
        description: t`Action for parts in this category`,
        choices: deleteOptions,
        required: true,
        field_type: 'choice'
      },
      delete_child_categories: {
        label: t`Child Categories Action`,
        description: t`Action for child categories in this category`,
        choices: deleteOptions,
        required: true,
        field_type: 'choice'
      }
    },
    onFormSuccess: () => {
      if (category.parent) {
        navigate(getDetailUrl(ModelType.partcategory, category.parent));
      } else {
        navigate('/part/');
      }
    }
  });

  // Tree view: edit category state
  const [treeEditPk, setTreeEditPk] = useState<number | undefined>(undefined);
  const [treeAddParent, setTreeAddParent] = useState<number | null | undefined>(undefined);

  const treeCreateCategory = useCreateApiFormModal({
    url: ApiEndpoints.category_list,
    title: '新建物料类别',
    fields: partCategoryFields({ create: true }),
    focus: 'name',
    initialData: {
      parent: treeAddParent ?? undefined
    },
    follow: true,
    modelType: ModelType.partcategory,
    keepOpenOption: true
  });

  const treeEditCategory = useEditApiFormModal({
    url: ApiEndpoints.category_list,
    pk: treeEditPk,
    title: '编辑物料类别',
    fields: partCategoryFields({}),
    onFormSuccess: (record: any) => {
      refreshInstance();
    }
  });

  const handleTreeEdit = useCallback(
    (pk: number) => {
      setTreeEditPk(pk);
      treeEditCategory.open();
    },
    [treeEditCategory]
  );

  const handleTreeAddChild = useCallback(
    (parentPk: number | null) => {
      setTreeAddParent(parentPk);
      treeCreateCategory.open();
    },
    [treeCreateCategory]
  );

  const categoryActions = useMemo(() => {
    return [
      <AdminButton
        key='admin'
        model={ModelType.partcategory}
        id={category.pk}
      />,
      <StarredToggleButton
        key='starred_change'
        instance={category}
        model={ModelType.partcategory}
        successFunction={() => {
          refreshInstance();
        }}
      />,
      <OptionsActionDropdown
        key='category-actions'
        tooltip={t`Category Actions`}
        actions={[
          EditItemAction({
            hidden: !id || !user.hasChangeRole(UserRoles.part_category),
            tooltip: t`Edit Part Category`,
            onClick: () => editCategory.open()
          }),
          DeleteItemAction({
            hidden: !id || !user.hasDeleteRole(UserRoles.part_category),
            tooltip: t`Delete Part Category`,
            onClick: () => deleteCategory.open()
          })
        ]}
      />
    ];
  }, [id, user, category.pk, category.starred]);

  const panels: PanelType[] = useMemo(
    () => [
      {
        name: 'details',
        label: '类别详情',
        icon: <IconInfoCircle />,
        content: detailsPanel,
        hidden: !id || !category?.pk
      },
      {
        name: 'subcategories',
        label: id ? '子类别' : '物料类别',
        icon: <IconSitemap />,
        controls: (
          <Tooltip label={viewMode === 'list' ? '切换树形视图' : '切换列表视图'}>
            <ActionIcon
              variant='light'
              size='sm'
              onClick={() => setViewMode(viewMode === 'list' ? 'tree' : 'list')}
            >
              {viewMode === 'list' ? <IconHierarchy2 size={16} /> : <IconLayoutList size={16} />}
            </ActionIcon>
          </Tooltip>
        ),
        content: viewMode === 'list' ? (
          <PartCategoryTable parentId={id} />
        ) : (
          <NavigationTree
            title='物料类别'
            modelType={ModelType.partcategory}
            endpoint={ApiEndpoints.category_tree}
            opened={true}
            onClose={() => {}}
            selectedId={category?.pk}
            inline
            onEdit={handleTreeEdit}
            onAddChild={handleTreeAddChild}
          />
        )
      },
      {
        name: 'products',
        label: '产品',
        icon: <IconCategory />,
        content: <PartListTable createButtonLabel='添加产品' props={{ params: { category: id, assembly: true, is_template: true } }} />
      },
      {
        name: 'subassemblies',
        label: '部装',
        icon: <IconCategory />,
        content: <PartListTable createButtonLabel='添加工件' props={{ params: { category: id, assembly: true, is_template: false } }} />
      },
      {
        name: 'parts',
        label: '零件',
        icon: <IconCategory />,
        content: <PartListTable createButtonLabel='添加物料' props={{ params: { category: id, assembly: false } }} />
      },
      {
        name: 'stockitem',
        label: '库存物料',
        icon: <IconPackages />,
        hidden: !id,
        content: (
          <StockItemTable
            params={{
              category: id
            }}
            allowAdd={false}
            tableName='category-stockitems'
          />
        )
      },
      {
        name: 'category_parameters',
        label: '类别参数',
        icon: <IconListCheck />,
        hidden: !id || !category.pk,
        content: <PartCategoryTemplateTable categoryId={category?.pk} />
      }
    ],
    [category, id, viewMode]
  );

  const breadcrumbs = useMemo(
    () => [
      { name: '物料', url: '/part' },
      ...(category.path ?? []).map((c: any) => ({
        name: c.name,
        url: getDetailUrl(ModelType.partcategory, c.pk),
        icon: c.icon ? <ApiIcon name={c.icon} /> : undefined
      }))
    ],
    [category]
  );

  const defaultPanel = useMemo(() => {
    if (
      settings.isSet('DISPLAY_ITEMS_FINAL_LEVEL', true) &&
      category.pk &&
      category.subcategories === 0
    ) {
      return 'parts';
    }
    return undefined;
  }, [settings, category]);

  return (
    <>
      {editCategory.modal}
      {deleteCategory.modal}
      {treeCreateCategory.modal}
      {treeEditCategory.modal}
      <InstanceDetail
        query={instanceQuery}
        requiredRole={UserRoles.part_category}
      >
        <Stack gap='xs'>
          <LoadingOverlay visible={instanceQuery.isFetching} />
          <NavigationTree
            modelType={ModelType.partcategory}
            title='物料类别'
            endpoint={ApiEndpoints.category_tree}
            opened={treeOpen}
            onClose={() => {
              setTreeOpen(false);
            }}
            selectedId={category?.pk}
          />
          <PageDetail
            title={(category?.name ?? id) ? '物料类别' : '物料'}
            subtitle={category?.description}
            icon={category?.icon && <ApiIcon name={category?.icon} />}
            breadcrumbs={breadcrumbs}
            breadcrumbAction={() => {
              setTreeOpen(true);
            }}
            actions={categoryActions}
            editAction={editCategory.open}
            editEnabled={
              !!category?.pk && user.hasChangePermission(ModelType.partcategory)
            }
          />
          <PanelGroup
            pageKey='partcategory'
            panels={panels}
            model={ModelType.partcategory}
            instance={category}
            reloadInstance={refreshInstance}
            id={category.pk ?? null}
            defaultPanel={defaultPanel}
          />
        </Stack>
      </InstanceDetail>
    </>
  );
}
