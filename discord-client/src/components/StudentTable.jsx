import { memo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

const columns = [
  { key: 'gr_no', label: 'G.R No' },
  { key: 'student_name', label: 'Student' },
  { key: 'father_name', label: 'Father' },
  { key: 'current_class_sec', label: 'Class' },
  { key: 'current_session', label: 'Session' },
  { key: 'status', label: 'Status' },
  { key: 'contact', label: 'Primary Contact' },
  { key: 'address', label: 'Address' },
];

const rowVariants = {
  initial: { opacity: 0, y: 8 },
  animate: { opacity: 1, y: 0 },
  exit: { opacity: 0, y: -8 },
};

function StudentRow({ student, onSelect, isSelected, onCopyGrNo }) {
  return (
    <motion.div
      variants={rowVariants}
      initial="initial"
      animate="animate"
      exit="exit"
      className={`student-row ${isSelected ? 'is-selected' : ''}`}
      onClick={() => onSelect(student)}
    >
      <div>
        <button
          type="button"
          className="gr-copy"
          onClick={(event) => {
            event.stopPropagation();
            onCopyGrNo?.(student.gr_no);
          }}
        >
          {student.gr_no}
        </button>
      </div>
      <div>
        <strong>{student.student_name}</strong>
      </div>
      <div>{student.father_name}</div>
      <div>{student.current_class_sec}</div>
      <div>{student.current_session}</div>
      <div>
        <span className={`status-pill status-${student.status?.toLowerCase() || 'active'}`}>{student.status}</span>
      </div>
      <div>{student.contact || '—'}</div>
      <div className="truncate">{student.address || '—'}</div>
    </motion.div>
  );
}

const StudentTable = memo(function StudentTable({ students, loading, onSelect, selected, onCopyGrNo }) {
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const sortedStudents = [...students].sort((a, b) => {
    if (!sortConfig.key) return 0;

    const aValue = a[sortConfig.key] || '';
    const bValue = b[sortConfig.key] || '';

    const aStr = String(aValue).toLowerCase();
    const bStr = String(bValue).toLowerCase();

    if (aStr < bStr) return sortConfig.direction === 'asc' ? -1 : 1;
    if (aStr > bStr) return sortConfig.direction === 'asc' ? 1 : -1;
    return 0;
  });

  return (
    <div className="student-table glass-surface">
      <div className="student-table__header">
        {columns.map((column) => (
          <div
            key={column.key}
            className={`sortable-header ${sortConfig.key === column.key ? 'is-sorted' : ''}`}
            onClick={() => handleSort(column.key)}
          >
            {column.label}
            {sortConfig.key === column.key && (
              <span className="sort-indicator">{sortConfig.direction === 'asc' ? '↑' : '↓'}</span>
            )}
          </div>
        ))}
      </div>
      <div className="student-table__body">
        {loading ? (
          <div className="table-empty">Fetching students…</div>
        ) : sortedStudents.length === 0 ? (
          <div className="table-empty">No students found for the applied filters.</div>
        ) : (
          <AnimatePresence initial={false}>
            {sortedStudents.map((student) => (
              <StudentRow
                key={student.gr_no}
                student={student}
                onSelect={onSelect}
                isSelected={selected?.gr_no === student.gr_no}
                onCopyGrNo={onCopyGrNo}
              />
            ))}
          </AnimatePresence>
        )}
      </div>
    </div>
  );
});

export default StudentTable;
