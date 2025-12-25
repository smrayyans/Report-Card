import { useEffect, useState } from 'react';
import useReportStore from '../store/reportStore';
import useToast from '../hooks/useToast';

const toLines = (items = []) => items.join('\n');
const fromLines = (value) =>
  value
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean);

export default function SettingsPage() {
  const toast = useToast();
  const config = useReportStore((state) => state.config);
  const filters = useReportStore((state) => state.filters);
  const remarks = useReportStore((state) => state.remarks);
  const subjects = useReportStore((state) => state.subjects);
  const loading = useReportStore((state) => state.loading);
  const fetchInitial = useReportStore((state) => state.fetchInitial);
  const saveConfig = useReportStore((state) => state.saveConfig);
  const saveRemarks = useReportStore((state) => state.saveRemarks);
  const saveFilters = useReportStore((state) => state.saveFilters);
  const createSubject = useReportStore((state) => state.createSubject);
  const updateSubject = useReportStore((state) => state.updateSubject);
  const deleteSubject = useReportStore((state) => state.deleteSubject);
  const clearResults = useReportStore((state) => state.clearResults);
  const [draft, setDraft] = useState(config);
  const [sessionsInput, setSessionsInput] = useState('');
  const [marksInput, setMarksInput] = useState('');
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectType, setNewSubjectType] = useState('Core');
  const [editingSubject, setEditingSubject] = useState(null);
  const [subjectsExpanded, setSubjectsExpanded] = useState(false);

  useEffect(() => {
    if (!config && !loading) {
      fetchInitial();
    }
  }, [config, loading, fetchInitial]);

  useEffect(() => {
    if (config) {
      setDraft(config);
      setSessionsInput(toLines(config.sessions || []));
      setMarksInput(toLines((config.max_marks_options || []).map(String)));
    }
  }, [config]);

  if (!draft) {
    return (
      <div className="panel glass-surface">
        <p className="muted">Loading configuration…</p>
      </div>
    );
  }

  const updateDraft = (updates) => setDraft((prev) => ({ ...prev, ...updates }));

  const handleSaveConfig = async () => {
    const nextConfig = {
      ...draft,
      sessions: fromLines(sessionsInput),
      max_marks_options: fromLines(marksInput).map((entry) => Number(entry) || 0).filter((value) => value > 0),
    };
    await saveConfig(nextConfig);
    toast({ type: 'success', title: 'Config saved', message: 'Settings updated successfully.' });
  };

  const handleAddClass = () => {
    const className = prompt('Enter class name (e.g., III):');
    if (!className) return;
    const days = Number(prompt('Default school days for this class?', '220')) || 0;
    updateDraft({
      class_defaults: {
        ...(draft.class_defaults || {}),
        [className.toUpperCase()]: days,
      },
    });
  };

  const handleRemoveFilter = async (filterName) => {
    const next = { ...filters };
    delete next[filterName];
    await saveFilters(next);
    toast({ type: 'success', title: 'Filter removed', message: `${filterName} deleted.` });
  };

  const handleAddSubject = async () => {
    if (!newSubjectName.trim()) {
      toast({ type: 'warning', title: 'Missing name', message: 'Please enter a subject name.' });
      return;
    }
    try {
      await createSubject(newSubjectName.trim(), newSubjectType);
      toast({ type: 'success', title: 'Subject added', message: `${newSubjectName} created successfully.` });
      setNewSubjectName('');
      setNewSubjectType('Core');
    } catch (error) {
      toast({ type: 'error', title: 'Failed to add', message: error.response?.data?.detail || 'Could not create subject.' });
    }
  };

  const handleUpdateSubject = async () => {
    if (!editingSubject || !editingSubject.newName.trim()) {
      toast({ type: 'warning', title: 'Missing name', message: 'Please enter a subject name.' });
      return;
    }
    try {
      await updateSubject(editingSubject.oldName, editingSubject.newName.trim(), editingSubject.type);
      toast({ type: 'success', title: 'Subject updated', message: `Subject renamed successfully.` });
      setEditingSubject(null);
    } catch (error) {
      toast({ type: 'error', title: 'Failed to update', message: error.response?.data?.detail || 'Could not update subject.' });
    }
  };

  const handleDeleteSubject = async (subjectName) => {
    if (!confirm(`Are you sure you want to delete "${subjectName}"?`)) return;
    try {
      await deleteSubject(subjectName);
      toast({ type: 'success', title: 'Subject deleted', message: `${subjectName} removed successfully.` });
    } catch (error) {
      toast({ type: 'error', title: 'Failed to delete', message: error.response?.data?.detail || 'Could not delete subject.' });
    }
  };

  const handleClearResults = async () => {
    const confirmClear = window.confirm(
      'This will permanently delete all saved report results. Continue?',
    );
    if (!confirmClear) return;
    try {
      await clearResults();
      toast({ type: 'success', title: 'Cleared', message: 'All report results have been deleted.' });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Clear failed',
        message: error.response?.data?.detail || 'Could not clear the results table.',
      });
    }
  };

  return (
    <div className="settings-page">
      <section className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Global</p>
            <h3>Academic settings</h3>
          </div>
          <button className="btn btn-primary" onClick={handleSaveConfig}>
            Save Config
          </button>
        </header>
        <div className="settings-grid">
          <label>
            <span>Sessions (one per line)</span>
            <textarea className="input dark" rows={4} value={sessionsInput} onChange={(event) => setSessionsInput(event.target.value)} />
          </label>
          <label>
            <span>Default Session</span>
            <select
              className="input dark"
              value={draft.default_session}
              onChange={(event) => updateDraft({ default_session: event.target.value })}
            >
              {fromLines(sessionsInput).map((session) => (
                <option key={session} value={session}>
                  {session}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Max Marks Options</span>
            <textarea className="input dark" rows={3} value={marksInput} onChange={(event) => setMarksInput(event.target.value)} />
          </label>
          <label>
            <span>Default Max Marks</span>
            <select
              className="input dark"
              value={draft.default_max_marks}
              onChange={(event) => updateDraft({ default_max_marks: Number(event.target.value) })}
            >
              {fromLines(marksInput).map((option) => (
                <option key={option} value={option}>
                  {option}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="class-defaults">
          <header>
            <h4>Class Defaults</h4>
            <button className="btn btn-secondary" onClick={handleAddClass}>
              Add Class
            </button>
          </header>
          <div className="class-grid">
            {Object.entries(draft.class_defaults || {}).map(([className, days]) => (
              <label key={className}>
                <span>{className}</span>
                <input
                  className="input dark"
                  type="number"
                  min="0"
                  value={days}
                  onChange={(event) =>
                    updateDraft({
                      class_defaults: {
                        ...draft.class_defaults,
                        [className]: Number(event.target.value),
                      },
                    })
                  }
                />
              </label>
            ))}
          </div>
        </div>
      </section>

      <section className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Presets</p>
            <h3>Remarks & Filters</h3>
          </div>
        </header>
        <div className="settings-flex">
          <div className="remarks-manager">
            <h4>Preset Remarks</h4>
            <div className="remarks-list scroll-area">
              {remarks?.length ? (
                remarks.map((remark, index) => (
                  <div key={remark + index} className="remark-chip">
                    <span>{remark}</span>
                    <button
                      className="btn btn-text"
                      onClick={() => {
                        const next = remarks.filter((_, i) => i !== index);
                        saveRemarks(next);
                      }}
                    >
                      Remove
                    </button>
                  </div>
                ))
              ) : (
                <p className="muted">No remarks saved yet.</p>
              )}
            </div>
            <button
              className="btn btn-secondary"
              onClick={() => {
                const text = prompt('New preset remark:');
                if (text) {
                  saveRemarks([...(remarks || []), text]);
                }
              }}
            >
              Add Remark
            </button>
          </div>
          <div className="filters-manager">
            <h4>Subject Filters</h4>
            <div className="filters-grid">
              {Object.entries(filters || {}).map(([name, entries]) => (
                <div key={name} className="filter-card glass-surface">
                  <strong>{name}</strong>
                  <p className="muted">{entries.length} subjects</p>
                  <button className="btn btn-text" onClick={() => handleRemoveFilter(name)}>
                    Delete
                  </button>
                </div>
              ))}
              {!Object.keys(filters || {}).length && <p className="muted">No filters saved.</p>}
            </div>
          </div>
        </div>
      </section>

      <section className="panel glass-surface">
        <header
          className="panel-header"
          onClick={() => setSubjectsExpanded(!subjectsExpanded)}
          style={{ cursor: 'pointer' }}
        >
          <div>
            <p className="eyebrow">Database</p>
            <h3>Subjects Management</h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={(e) => {
              e.stopPropagation();
              setSubjectsExpanded(!subjectsExpanded);
            }}
          >
            {subjectsExpanded ? 'Collapse' : 'Expand'}
          </button>
        </header>
        {subjectsExpanded && (
          <div className="settings-flex">
            <div className="subjects-manager">
              <h4>All Subjects</h4>
              <div className="subjects-list">
                {subjects?.length ? (
                  subjects.map((subject) => (
                    <div key={subject.subject_name} className="subject-item">
                      {editingSubject?.oldName === subject.subject_name ? (
                        <div className="subject-edit-form">
                          <input
                            className="input dark"
                            value={editingSubject.newName}
                            onChange={(e) => setEditingSubject({ ...editingSubject, newName: e.target.value })}
                            placeholder="Subject name"
                          />
                          <select
                            className="input dark"
                            value={editingSubject.type}
                            onChange={(e) => setEditingSubject({ ...editingSubject, type: e.target.value })}
                          >
                            <option value="Core">Core</option>
                            <option value="Non-Core">Non-Core</option>
                          </select>
                          <button className="btn btn-primary" onClick={handleUpdateSubject}>
                            Save
                          </button>
                          <button className="btn btn-ghost" onClick={() => setEditingSubject(null)}>
                            Cancel
                          </button>
                        </div>
                      ) : (
                        <>
                          <div className="subject-info">
                            <strong>{subject.subject_name}</strong>
                            <span className="subject-type">{subject.type}</span>
                          </div>
                          <div className="subject-actions">
                            <button
                              className="btn btn-text"
                              onClick={() =>
                                setEditingSubject({
                                  oldName: subject.subject_name,
                                  newName: subject.subject_name,
                                  type: subject.type,
                                })
                              }
                            >
                              Edit
                            </button>
                            <button className="btn btn-text" onClick={() => handleDeleteSubject(subject.subject_name)}>
                              Delete
                            </button>
                          </div>
                        </>
                      )}
                    </div>
                  ))
                ) : (
                  <p className="muted">No subjects found.</p>
                )}
              </div>
              <div className="subject-add-form">
                <input
                  className="input dark"
                  placeholder="New subject name"
                  value={newSubjectName}
                  onChange={(e) => setNewSubjectName(e.target.value)}
                />
                <select className="input dark" value={newSubjectType} onChange={(e) => setNewSubjectType(e.target.value)}>
                  <option value="Core">Core</option>
                  <option value="Non-Core">Non-Core</option>
                </select>
                <button className="btn btn-primary" onClick={handleAddSubject}>
                  Add Subject
                </button>
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Danger Zone</p>
            <h3>Clear Results Table</h3>
          </div>
          <button className="btn btn-danger" onClick={handleClearResults}>
            Delete All Results
          </button>
        </header>
        <p className="muted">Testing only. This deletes all saved report results in the database.</p>
      </section>
    </div>
  );
}
