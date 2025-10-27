/**
 * ScheduledExams Component
 * Displays upcoming exams for a patient with sorting and filtering
 */

import { useState, useMemo } from 'react';
import {
  Container,
  Header,
  Table,
  Badge,
  Box,
  TextFilter,
  Pagination,
  CollectionPreferences
} from '@cloudscape-design/components';
import type { Reservation } from '../../types/api';
import { es } from '../../i18n/es';

interface ScheduledExamsProps {
  exams: Reservation[];
  loading?: boolean;
}

export const ScheduledExams: React.FC<ScheduledExamsProps> = ({
  exams,
  loading = false
}) => {
  const [filteringText, setFilteringText] = useState('');
  const [currentPageIndex, setCurrentPageIndex] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Status badge color mapping
  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { color: 'blue' | 'green' | 'grey' | 'red'; label: string }> = {
      'scheduled': { color: 'blue', label: es.exam.scheduled },
      'in-progress': { color: 'blue', label: es.exam.inProgress },
      'completed': { color: 'green', label: es.exam.completed },
      'cancelled': { color: 'grey', label: es.exam.cancelled }
    };

    const statusInfo = statusMap[status] || { color: 'grey' as const, label: status };
    return <Badge color={statusInfo.color}>{statusInfo.label}</Badge>;
  };

  // Format date and time
  const formatDateTime = (dateString: string) => {
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString('es-MX', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      }),
      time: date.toLocaleTimeString('es-MX', {
        hour: '2-digit',
        minute: '2-digit'
      })
    };
  };

  // Filter exams based on search text
  const filteredExams = useMemo(() => {
    if (!filteringText) return exams;

    const searchLower = filteringText.toLowerCase();
    return exams.filter(exam =>
      exam.exam_name?.toLowerCase().includes(searchLower) ||
      exam.reservation_id.toLowerCase().includes(searchLower) ||
      exam.status.toLowerCase().includes(searchLower) ||
      exam.medic_name?.toLowerCase().includes(searchLower)
    );
  }, [exams, filteringText]);

  // Paginate exams
  const paginatedExams = useMemo(() => {
    const startIndex = (currentPageIndex - 1) * pageSize;
    return filteredExams.slice(startIndex, startIndex + pageSize);
  }, [filteredExams, currentPageIndex, pageSize]);

  // Sort exams by date (upcoming first)
  const sortedExams = useMemo(() => {
    return [...paginatedExams].sort((a, b) => {
      return new Date(a.appointment_date).getTime() - new Date(b.appointment_date).getTime();
    });
  }, [paginatedExams]);

  return (
    <Container
      header={
        <Header
          variant="h2"
          counter={`(${filteredExams.length})`}
        >
          {es.patient.scheduledExams}
        </Header>
      }
    >
      <Table
        columnDefinitions={[
          {
            id: 'exam_name',
            header: es.exam.type,
            cell: (exam: Reservation) => exam.exam_name || '-',
            sortingField: 'exam_name'
          },
          {
            id: 'appointment_date',
            header: es.exam.date,
            cell: (exam: Reservation) => {
              const { date, time } = formatDateTime(exam.appointment_date);
              return (
                <Box>
                  <div>{date}</div>
                  <Box variant="small" color="text-body-secondary">
                    {time}
                  </Box>
                </Box>
              );
            },
            sortingField: 'appointment_date'
          },
          {
            id: 'medic',
            header: es.exam.medic,
            cell: (exam: Reservation) => exam.medic_name || '-'
          },
          {
            id: 'status',
            header: es.exam.status,
            cell: (exam: Reservation) => getStatusBadge(exam.status)
          },
          {
            id: 'notes',
            header: es.exam.results,
            cell: (exam: Reservation) => exam.notes ? (
              <Badge color="green">Disponible</Badge>
            ) : (
              <Box color="text-body-secondary">Pendiente</Box>
            )
          }
        ]}
        items={sortedExams}
        loading={loading}
        loadingText="Cargando exámenes..."
        empty={
          <Box textAlign="center" color="inherit">
            <Box padding={{ bottom: 's' }} variant="p" color="inherit">
              <b>No hay exámenes programados</b>
            </Box>
            <Box variant="p" color="inherit">
              No se encontraron exámenes para este paciente.
            </Box>
          </Box>
        }
        filter={
          <TextFilter
            filteringText={filteringText}
            filteringPlaceholder="Buscar exámenes..."
            filteringAriaLabel="Filtrar exámenes"
            onChange={({ detail }) => {
              setFilteringText(detail.filteringText);
              setCurrentPageIndex(1);
            }}
          />
        }
        pagination={
          <Pagination
            currentPageIndex={currentPageIndex}
            pagesCount={Math.ceil(filteredExams.length / pageSize)}
            onChange={({ detail }) => setCurrentPageIndex(detail.currentPageIndex)}
            ariaLabels={{
              nextPageLabel: 'Página siguiente',
              previousPageLabel: 'Página anterior',
              pageLabel: (pageNumber) => `Página ${pageNumber}`
            }}
          />
        }
        preferences={
          <CollectionPreferences
            title="Preferencias"
            confirmLabel="Confirmar"
            cancelLabel="Cancelar"
            preferences={{
              pageSize: pageSize
            }}
            pageSizePreference={{
              title: 'Elementos por página',
              options: [
                { value: 5, label: '5 exámenes' },
                { value: 10, label: '10 exámenes' },
                { value: 20, label: '20 exámenes' }
              ]
            }}
            onConfirm={({ detail }) => {
              setPageSize(detail.pageSize || 10);
              setCurrentPageIndex(1);
            }}
          />
        }
      />
    </Container>
  );
};
