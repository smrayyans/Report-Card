import { useEffect, useMemo, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';

export default function SubjectSelectorModal({
  open,
  subjects,
  selectedSubjects,
  filters,
  onApply,
  onClose,
  onSaveFilter,
  onDeleteFilter,
}) {
  const [search, setSearch] = useState('');
  const [draftSelection, setDraftSelection] = useState([]);
  const [activeFilter, setActiveFilter] = useState('--');
  const [filterName, setFilterName] = useState('');

  useEffect(() => {
    if (open) {
      // Check if '1-4' filter exists and apply it by default
      if (filters && filters['1-4']) {
        setActiveFilter('1-4');
        setDraftSelection(filters['1-4']);
      } else {
        setDraftSelection(selectedSubjects.map((subject) => subject.name));
      }
      // Prevent body scrolling when modal is open
      document.body.style.overflow = 'hidden';
    } else {
      // Restore body scrolling when modal is closed
      document.body.style.overflow = '';
    }

    // Cleanup function to restore scrolling if component unmounts
    return () => {
      document.body.style.overflow = '';
    };
  }, [selectedSubjects, open, filters]);

  const filteredSubjects = useMemo(() => {
    const query = search.toLowerCase();
    return subjects.filter(
      (subject) =>
        subject.subject_name.toLowerCase().includes(query) ||
        (subject.type || '').toLowerCase().includes(query),
    );
  }, [subjects, search]);

  const toggleSubject = (subjectName) => {
    setDraftSelection((prev) =>
      prev.includes(subjectName) ? prev.filter((name) => name !== subjectName) : [...prev, subjectName],
    );
  };

  const handleApplyFilter = (filterKey) => {
    setActiveFilter(filterKey);
    if (filterKey === '--') {
      setDraftSelection(selectedSubjects.map((subject) => subject.name));
    } else if (filters[filterKey]) {
      setDraftSelection(filters[filterKey]);
    }
  };

  const handleSaveFilter = () => {
    if (!filterName.trim()) return;
    onSaveFilter(filterName.trim(), draftSelection);
    setFilterName('');
  };

  const handleDeleteFilter = () => {
    if (activeFilter !== '--') {
      onDeleteFilter(activeFilter);
      setActiveFilter('--');
    }
  };

  const handleApply = () => {
    const selected = subjects.filter((subject) => draftSelection.includes(subject.subject_name));
    onApply(selected);
    onClose();
  };

  return (
    <AnimatePresence>
      {open && (
        <div style={{ position: 'fixed', inset: 0, display: 'grid', placeItems: 'center', overflow: 'hidden', zIndex: 20 }}>
          <motion.div
            className="modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />
          <motion.div
            className="modal-panel glass-surface"
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.92, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            <header>
              <div>
                <p className="eyebrow">Subject Matrix</p>
                <h3>Choose active subjects</h3>
              </div>
              <button className="btn btn-text" onClick={onClose}>
                Close
              </button>
            </header>
            <div className="modal-controls">
              <input
                className="input dark"
                placeholder="Search subject or category…"
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
              <select className="input dark" value={activeFilter} onChange={(event) => handleApplyFilter(event.target.value)}>
                <option value="--">-- Filters --</option>
                {Object.keys(filters).map((filterKey) => (
                  <option key={filterKey} value={filterKey}>
                    {filterKey}
                  </option>
                ))}
              </select>
              <div className="filter-actions">
                <input
                  className="input dark"
                  placeholder="Name new filter…"
                  value={filterName}
                  onChange={(event) => setFilterName(event.target.value)}
                />
                <button className="btn btn-secondary" onClick={handleSaveFilter}>
                  Save
                </button>
                <button className="btn btn-ghost" onClick={handleDeleteFilter} disabled={activeFilter === '--'}>
                  Delete
                </button>
              </div>
            </div>
            <div className="subject-grid scroll-area">
              {filteredSubjects.map((subject) => {
                const isSelected = draftSelection.includes(subject.subject_name);
                return (
                  <button
                    key={subject.subject_name}
                    className={`subject-chip ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => toggleSubject(subject.subject_name)}
                  >
                    <span>{subject.subject_name}</span>
                    <small>{subject.type || 'Core'}</small>
                  </button>
                );
              })}
            </div>
            <footer className="modal-footer">
              <span className="muted">{draftSelection.length} subjects selected</span>
              <div>
                <button className="btn btn-ghost" onClick={onClose}>
                  Cancel
                </button>
                <button className="btn btn-primary" onClick={handleApply}>
                  Apply Selection
                </button>
              </div>
            </footer>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
