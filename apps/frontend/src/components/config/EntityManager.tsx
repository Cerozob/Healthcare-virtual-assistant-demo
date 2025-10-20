/**
 * EntityManager Component
 * Generic CRUD interface for managing entities using Cloudscape components
 */

import { useState } from 'react';
import {
  Table,
  Box,
  Button,
  SpaceBetween,
  Header,
  Pagination,
  Modal,
  Alert,
  TextFilter,
} from '@cloudscape-design/components';
import { useLanguage } from '../../contexts/LanguageContext';

export interface EntityColumn<T> {
  id: string;
  header: string;
  cell: (item: T) => React.ReactNode;
  sortingField?: string;
  width?: number;
}

export interface EntityManagerProps<T> {
  title: string;
  columns: EntityColumn<T>[];
  items: T[];
  loading: boolean;
  error?: string;
  selectedItems: T[];
  onSelectionChange: (items: T[]) => void;
  onRefresh: () => void;
  onCreate: () => void;
  onEdit: (item: T) => void;
  onDelete: (items: T[]) => void;
  getItemId: (item: T) => string;
  filteringPlaceholder?: string;
  emptyMessage?: string;
  totalItems?: number;
  currentPage?: number;
  pageSize?: number;
  onPageChange?: (page: number) => void;
}

export function EntityManager<T>({
  title,
  columns,
  items,
  loading,
  error,
  selectedItems,
  onSelectionChange,
  onRefresh,
  onCreate,
  onEdit,
  onDelete,
  getItemId: _getItemId,
  filteringPlaceholder,
  emptyMessage,
  totalItems,
  currentPage = 1,
  pageSize = 10,
  onPageChange,
}: EntityManagerProps<T>) {
  const { t } = useLanguage();
  const [filteringText, setFilteringText] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);

  const filteredItems = items.filter((item) => {
    if (!filteringText) return true;
    const searchText = filteringText.toLowerCase();
    return columns.some((column) => {
      const cellValue = column.cell(item);
      return String(cellValue).toLowerCase().includes(searchText);
    });
  });

  const handleDelete = () => {
    onDelete(selectedItems);
    setShowDeleteModal(false);
  };

  const totalPages = totalItems ? Math.ceil(totalItems / pageSize) : Math.ceil(filteredItems.length / pageSize);

  return (
    <SpaceBetween size="l">
      {error && (
        <Alert type="error" dismissible onDismiss={() => {}}>
          {error}
        </Alert>
      )}

      <Table
        columnDefinitions={columns}
        items={filteredItems}
        loading={loading}
        loadingText={t.common.loading}
        selectionType="multi"
        selectedItems={selectedItems}
        onSelectionChange={({ detail }) => onSelectionChange(detail.selectedItems)}
        empty={
          <Box textAlign="center" color="inherit">
            <b>{emptyMessage || 'No hay elementos'}</b>
          </Box>
        }
        filter={
          <TextFilter
            filteringText={filteringText}
            filteringPlaceholder={filteringPlaceholder || t.common.search}
            onChange={({ detail }) => setFilteringText(detail.filteringText)}
          />
        }
        header={
          <Header
            variant="h2"
            counter={`(${filteredItems.length})`}
            actions={
              <SpaceBetween direction="horizontal" size="xs">
                <Button iconName="refresh" onClick={onRefresh} disabled={loading}>
                  Actualizar
                </Button>
                <Button onClick={onCreate}>{t.config.addNew}</Button>
                <Button
                  onClick={() => onEdit(selectedItems[0])}
                  disabled={selectedItems.length !== 1}
                >
                  {t.common.edit}
                </Button>
                <Button
                  onClick={() => setShowDeleteModal(true)}
                  disabled={selectedItems.length === 0}
                >
                  {t.common.delete}
                </Button>
              </SpaceBetween>
            }
          >
            {title}
          </Header>
        }
        pagination={
          onPageChange && totalPages > 1 ? (
            <Pagination
              currentPageIndex={currentPage}
              pagesCount={totalPages}
              onChange={({ detail }) => onPageChange(detail.currentPageIndex)}
            />
          ) : undefined
        }
      />

      <Modal
        visible={showDeleteModal}
        onDismiss={() => setShowDeleteModal(false)}
        header="Confirmar eliminación"
        footer={
          <Box float="right">
            <SpaceBetween direction="horizontal" size="xs">
              <Button variant="link" onClick={() => setShowDeleteModal(false)}>
                {t.common.cancel}
              </Button>
              <Button variant="primary" onClick={handleDelete}>
                {t.common.delete}
              </Button>
            </SpaceBetween>
          </Box>
        }
      >
        {t.config.confirmDelete}
        <br />
        <br />
        <Box variant="p">
          Elementos seleccionados: <strong>{selectedItems.length}</strong>
        </Box>
      </Modal>
    </SpaceBetween>
  );
}
