import {
  ActionIcon,
  Alert,
  Anchor,
  Divider,
  Drawer,
  Group,
  LoadingOverlay,
  type RenderTreeNodePayload,
  Space,
  Stack,
  Tooltip,
  Tree,
  type TreeNodeData,
  useTree
} from '@mantine/core';
import {
  IconChevronDown,
  IconChevronRight,
  IconEdit,
  IconExclamationCircle,
  IconPlus,
  IconSitemap
} from '@tabler/icons-react';
import { useQuery } from '@tanstack/react-query';
import { useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';

import { StylishText } from '@lib/components/StylishText';
import type { ApiEndpoints } from '@lib/enums/ApiEndpoints';
import type { ModelType } from '@lib/enums/ModelType';
import { apiUrl } from '@lib/functions/Api';
import {
  eventModified,
  getDetailUrl,
  navigateToLink
} from '@lib/functions/Navigation';
import { t } from '@lingui/core/macro';
import { useApi } from '../../contexts/ApiContext';
import { ApiIcon } from '../items/ApiIcon';

/*
 * A generic navigation tree component.
 */
export default function NavigationTree({
  title,
  opened,
  onClose,
  selectedId,
  modelType,
  endpoint,
  inline,
  onEdit,
  onAddChild
}: Readonly<{
  title: string;
  opened: boolean;
  onClose: () => void;
  selectedId?: number | null;
  modelType: ModelType;
  endpoint: ApiEndpoints;
  inline?: boolean;
  onEdit?: (pk: number) => void;
  onAddChild?: (parentPk: number | null) => void;
}>) {
  const api = useApi();
  const navigate = useNavigate();
  const treeState = useTree();

  // Data query to fetch the tree data from server
  const query = useQuery({
    enabled: opened || inline,
    queryKey: [modelType, 'nav_tree'],
    queryFn: async () =>
      api
        .get(apiUrl(endpoint), {
          data: {
            ordering: 'level'
          }
        })
        .then((response) => response.data ?? [])
  });

  const follow = useCallback(
    (node: TreeNodeData, event?: any) => {
      const url = getDetailUrl(modelType, node.value);
      if (eventModified(event)) {
        navigateToLink(url, navigate, event);
      } else {
        onClose();
        navigate(url);
      }
    },
    [modelType, navigate]
  );

  // Map returned query to a "tree" structure
  const data: TreeNodeData[] = useMemo(() => {
    /*
     * Reconstruct the navigation tree from the provided data.
     * It is required (and assumed) that the data is first sorted by level.
     */

    const nodes: Record<number, any> = {};
    const tree: TreeNodeData[] = [];

    if (!query || !query?.data?.length) {
      return [];
    }

    for (let ii = 0; ii < query.data.length; ii++) {
      const node = {
        ...query.data[ii],
        children: [],
        label: (
          <Group gap='xs'>
            <ApiIcon name={query.data[ii].icon} />
            {query.data[ii].name}
            {query.data[ii].part_count > 0 && (
              <span style={{ color: '#94a3b8', fontSize: 12, marginLeft: 4 }}>
                ({query.data[ii].part_count})
              </span>
            )}
          </Group>
        ),
        value: query.data[ii].pk.toString(),
        selected: query.data[ii].pk === selectedId
      };

      const pk: number = node.pk;
      const parent: number | null = node.parent;

      if (!parent) {
        // This is a top level node
        tree.push(node);
      } else {
        // This is *not* a top level node, so the parent *must* already exist
        nodes[parent]?.children.push(node);
      }

      // Finally, add this node
      nodes[pk] = node;

      if (pk === selectedId) {
        // Expand all parents
        let parent = nodes[node.parent];
        while (parent) {
          parent.expanded = true;
          parent = nodes[parent.parent];
        }
      }
    }

    return tree;
  }, [selectedId, query.data]);

  const renderNode = useCallback(
    (payload: RenderTreeNodePayload) => {
      const pk = parseInt(payload.node.value);
      const itemData: any = payload.node;
      return (
        <Group
          p={3}
          gap={4}
          justify='space-between'
          key={payload.node.value}
          wrap='nowrap'
          style={{ width: '100%' }}
          onClick={() => {
            if (payload.hasChildren) {
              treeState.toggleExpanded(payload.node.value);
            }
          }}
        >
          <Group gap={4} wrap='nowrap' style={{ minWidth: 0, flexShrink: 0 }}>
            <Space w={10 * (payload.level - 1)} />
            <ActionIcon
              size='sm'
              variant='transparent'
              aria-label={`nav-tree-toggle-${payload.node.value}}`}
            >
              {payload.hasChildren ? (
                payload.expanded ? (
                  <IconChevronDown />
                ) : (
                  <IconChevronRight />
                )
              ) : null}
            </ActionIcon>
            <Anchor
              onClick={(event: any) => follow(payload.node, event)}
              aria-label={`nav-tree-item-${payload.node.value}`}
              c='var(--mantine-color-text)'
              style={{ textDecoration: 'none' }}
            >
              {payload.node.label}
            </Anchor>
          </Group>
          {itemData.description && (
            <span
              style={{
                flex: 1,
                minWidth: 0,
                fontSize: 11,
                color: '#94a3b8',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
                textAlign: 'left' as const,
                paddingLeft: 8
              }}
            >
              {itemData.description}
            </span>
          )}
          <Group gap={2} wrap='nowrap'>
            {onEdit && (
              <Tooltip label='编辑分类'>
                <ActionIcon
                  size='sm'
                  variant='subtle'
                  color='gray'
                  onClick={(e: any) => {
                    e.stopPropagation();
                    onEdit(pk);
                  }}
                >
                  <IconEdit size={14} />
                </ActionIcon>
              </Tooltip>
            )}
            {onAddChild && (
              <Tooltip label='添加子分类'>
                <ActionIcon
                  size='sm'
                  variant='subtle'
                  color='blue'
                  onClick={(e: any) => {
                    e.stopPropagation();
                    onAddChild(pk);
                  }}
                >
                  <IconPlus size={14} />
                </ActionIcon>
              </Tooltip>
            )}
          </Group>
        </Group>
      );
    },
    [treeState, onEdit, onAddChild]
  );

  const treeContent = (
    <Stack gap='xs'>
      {onAddChild && (
        <Group justify='center' p='xs'>
          <Tooltip label='添加根分类'>
            <ActionIcon
              variant='light'
              color='blue'
              size='sm'
              onClick={() => onAddChild(null)}
            >
              <IconPlus size={16} />
            </ActionIcon>
          </Tooltip>
        </Group>
      )}
      <Divider />
      <LoadingOverlay visible={query.isFetching || query.isLoading} />
      {query.isError ? (
        <Alert color='red' title={t`Error`} icon={<IconExclamationCircle />}>
          {t`Error loading navigation tree.`}
        </Alert>
      ) : (
        <Tree data={data} tree={treeState} renderNode={renderNode} />
      )}
    </Stack>
  );

  if (inline) {
    return treeContent;
  }

  return (
    <Drawer
      opened={opened}
      size='md'
      position='left'
      onClose={onClose}
      withCloseButton={true}
      styles={{
        header: {
          width: '100%'
        },
        title: {
          width: '100%'
        }
      }}
      title={
        <Group justify='left' p='ms' gap='md' wrap='nowrap'>
          <IconSitemap />
          <StylishText size='lg'>{title}</StylishText>
        </Group>
      }
    >
      {treeContent}
    </Drawer>
  );
}
