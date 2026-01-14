import { useEffect, useState } from 'react';
import useReportStore from '../store/reportStore';
import useToast from '../hooks/useToast';
import { getApiBase, setApiBase } from '../services/api';
import api from '../services/api';

const DEFAULT_TERMS = ['Mid Year', 'Annual Year'];

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
  const [termsInput, setTermsInput] = useState('');
  const [marksInput, setMarksInput] = useState('');
  const [newSubjectName, setNewSubjectName] = useState('');
  const [newSubjectType, setNewSubjectType] = useState('Core');
  const [editingSubject, setEditingSubject] = useState(null);
  const [academicExpanded, setAcademicExpanded] = useState(false);
  const [presetsExpanded, setPresetsExpanded] = useState(false);
  const [subjectsExpanded, setSubjectsExpanded] = useState(false);
  const [developerExpanded, setDeveloperExpanded] = useState(false);
  const [filterName, setFilterName] = useState('');
  const [filterSearch, setFilterSearch] = useState('');
  const [filterSelection, setFilterSelection] = useState([]);
  const [editingFilter, setEditingFilter] = useState(null);
  const [apiBaseInput, setApiBaseInput] = useState(getApiBase());
  const [dbConfig, setDbConfig] = useState({
    host: '127.0.0.1',
    port: 5432,
    dbname: 'report_system',
    user: 'postgres',
    password: 'rayyanshah04',
    output_dir: '',
  });
  const [users, setUsers] = useState([]);
  const [usersLoading, setUsersLoading] = useState(false);
  const [userEdits, setUserEdits] = useState({});
  const [accountExpanded, setAccountExpanded] = useState(false);
  const [accountForm, setAccountForm] = useState({
    full_name: '',
    username: '',
    password: '',
    role: 'teacher',
  });
  const [showAccountPassword, setShowAccountPassword] = useState(false);
  const [showUserPasswords, setShowUserPasswords] = useState(false);
  const [showDbPassword, setShowDbPassword] = useState(false);
  const [openUsers, setOpenUsers] = useState({});

  useEffect(() => {
    if (!config && !loading) {
      fetchInitial();
    }
  }, [config, loading, fetchInitial]);

  useEffect(() => {
    api.get('/db/config')
      .then((response) => {
        setDbConfig(response.data);
      })
      .catch(() => {
        // Ignore if backend not reachable yet.
      });
  }, []);

  const loadUsers = async () => {
    setUsersLoading(true);
    try {
      const response = await api.get('/admin/user-accounts');
      const nextUsers = response.data.users || [];
      setUsers(nextUsers);
      const nextEdits = {};
      nextUsers.forEach((user) => {
        nextEdits[user.user_id] = {
          username: user.username || '',
          password: user.password || '',
          role: (user.role || 'teacher').toLowerCase(),
          full_name: user.full_name || '',
        };
      });
      setUserEdits(nextEdits);
    } catch (error) {
      toast({
        type: 'error',
        title: 'User load failed',
        message: error.response?.data?.detail || 'Unable to load users.',
      });
    } finally {
      setUsersLoading(false);
    }
  };

  useEffect(() => {
    if (config) {
      setDraft(config);
      setSessionsInput(toLines(config.sessions || []));
      const terms = config.terms?.length ? config.terms : DEFAULT_TERMS;
      setTermsInput(toLines(terms));
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
      terms: fromLines(termsInput),
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

  const handleToggleFilterSubject = (subjectName) => {
    setFilterSelection((prev) =>
      prev.includes(subjectName) ? prev.filter((name) => name !== subjectName) : [...prev, subjectName],
    );
  };

  const handleEditFilter = (name) => {
    setEditingFilter(name);
    setFilterName(name);
    setFilterSelection(filters?.[name] || []);
  };

  const handleSaveFilter = async () => {
    if (!filterName.trim()) {
      toast({ type: 'warning', title: 'Missing name', message: 'Enter a filter name first.' });
      return;
    }
    const nextFilters = { ...filters };
    if (editingFilter && editingFilter !== filterName.trim()) {
      delete nextFilters[editingFilter];
    }
    nextFilters[filterName.trim()] = filterSelection;
    await saveFilters(nextFilters);
    toast({ type: 'success', title: 'Filter saved', message: `Filter "${filterName.trim()}" stored.` });
    setEditingFilter(null);
    setFilterName('');
    setFilterSelection([]);
  };

  const handleClearFilter = () => {
    setEditingFilter(null);
    setFilterName('');
    setFilterSelection([]);
  };

  const filteredSubjects = subjects.filter((subject) => {
    if (!filterSearch.trim()) return true;
    const query = filterSearch.toLowerCase();
    return (
      subject.subject_name.toLowerCase().includes(query) ||
      (subject.type || '').toLowerCase().includes(query)
    );
  });

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

  const handleSaveApiBase = () => {
    const value = setApiBase(apiBaseInput);
    setApiBaseInput(value);
    toast({ type: 'success', title: 'Server saved', message: `API base set to ${value}.` });
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

  const handleSaveDbConfig = async () => {
    try {
      await api.put('/db/config', dbConfig);
      toast({ type: 'success', title: 'DB Saved', message: 'Database settings updated.' });
    } catch (error) {
      toast({
        type: 'error',
        title: 'DB Save failed',
        message: error.response?.data?.detail || 'Unable to update DB settings.',
      });
    }
  };



  const handleSaveAccount = async () => {
    if (!accountForm.full_name.trim() || !accountForm.username.trim() || !accountForm.password.trim()) {
      toast({ type: 'warning', title: 'Missing info', message: 'Name, username, and password are required.' });
      return;
    }
    try {
      const user = users.find(
        (item) => (item.username || '').toLowerCase() === accountForm.username.trim().toLowerCase(),
      );
      if (user) {
        await api.put(`/admin/user-accounts/${user.user_id}`, {
          username: accountForm.username.trim(),
          password: accountForm.password.trim(),
          role: accountForm.role,
          full_name: accountForm.full_name.trim(),
        });
      } else {
        await api.post('/admin/user-accounts', {
          username: accountForm.username.trim(),
          password: accountForm.password.trim(),
          role: accountForm.role,
          full_name: accountForm.full_name.trim(),
        });
      }
      toast({ type: 'success', title: 'Account saved', message: 'Teacher login updated.' });
      setAccountForm({ full_name: '', username: '', password: '', role: 'teacher' });
      loadUsers();
    } catch (error) {
      toast({
        type: 'error',
        title: 'Save failed',
        message: error.response?.data?.detail || 'Unable to save account.',
      });
    }
  };

  const handleUpdateUser = async (userId) => {
    const edit = userEdits[userId];
    if (!edit || !edit.username.trim() || !edit.password.trim() || !edit.full_name.trim()) {
      toast({ type: 'warning', title: 'Missing info', message: 'Name, username, and password are required.' });
      return;
    }
    try {
      await api.put(`/admin/user-accounts/${userId}`, {
        username: edit.username.trim(),
        password: edit.password.trim(),
        role: edit.role,
        full_name: edit.full_name.trim(),
      });
      toast({ type: 'success', title: 'User updated', message: 'Account updated successfully.' });
      loadUsers();
    } catch (error) {
      toast({
        type: 'error',
        title: 'Update failed',
        message: error.response?.data?.detail || 'Unable to update account.',
      });
    }
  };

  return (
    <div className="settings-page">
      <section className="panel glass-surface">
        <header
          className="panel-header"
          onClick={() => setAcademicExpanded(!academicExpanded)}
          style={{ cursor: 'pointer' }}
        >
          <div>
            <p className="eyebrow">Global</p>
            <h3>Academic settings</h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={(event) => {
              event.stopPropagation();
              setAcademicExpanded(!academicExpanded);
            }}
          >
            {academicExpanded ? 'Collapse' : 'Expand'}
          </button>
        </header>
        {academicExpanded && (
          <>
            <div className="settings-grid">
              <label>
                <span>Sessions (one per line)</span>
                <textarea className="input dark" rows={4} value={sessionsInput} onChange={(event) => setSessionsInput(event.target.value)} />
              </label>
              <label>
                <span>Terms (one per line)</span>
                <textarea className="input dark" rows={4} value={termsInput} onChange={(event) => setTermsInput(event.target.value)} />
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
              <button className="btn btn-primary" onClick={handleSaveConfig}>
                Save Config
              </button>
            </div>
          </>
        )}
      </section>

      <section className="panel glass-surface">
        <header
          className="panel-header"
          onClick={() => setPresetsExpanded(!presetsExpanded)}
          style={{ cursor: 'pointer' }}
        >
          <div>
            <p className="eyebrow">Presets</p>
            <h3>Remarks & Filters</h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={(event) => {
              event.stopPropagation();
              setPresetsExpanded(!presetsExpanded);
            }}
          >
            {presetsExpanded ? 'Collapse' : 'Expand'}
          </button>
        </header>
        {presetsExpanded && (
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
                    <div className="filter-card-actions">
                      <button className="btn btn-text" onClick={() => handleEditFilter(name)}>
                        Edit
                      </button>
                      <button className="btn btn-text" onClick={() => handleRemoveFilter(name)}>
                        Delete
                      </button>
                    </div>
                  </div>
                ))}
                {!Object.keys(filters || {}).length && <p className="muted">No filters saved.</p>}
              </div>
              <div className="filter-editor">
                <div className="filter-editor-header">
                  <h5>{editingFilter ? 'Edit Filter' : 'New Filter'}</h5>
                  <div className="filter-editor-actions">
                    <button className="btn btn-secondary" onClick={handleSaveFilter}>
                      Save Filter
                    </button>
                    <button className="btn btn-ghost" onClick={handleClearFilter}>
                      Clear
                    </button>
                  </div>
                </div>
                <div className="filter-editor-fields">
                  <label>
                    <span>Filter Name</span>
                    <input
                      className="input dark"
                      value={filterName}
                      onChange={(event) => setFilterName(event.target.value)}
                      placeholder="e.g., 1-4"
                    />
                  </label>
                  <label>
                    <span>Search subjects</span>
                    <input
                      className="input dark"
                      value={filterSearch}
                      onChange={(event) => setFilterSearch(event.target.value)}
                      placeholder="Type to filter subjects"
                    />
                  </label>
                </div>
                <div className="filter-editor-summary">
                  <span className="muted">{filterSelection.length} selected</span>
                  <div className="filter-editor-actions">
                    <button
                      className="btn btn-text"
                      onClick={() => setFilterSelection(subjects.map((subject) => subject.subject_name))}
                    >
                      Select All
                    </button>
                    <button className="btn btn-text" onClick={() => setFilterSelection([])}>
                      Clear All
                    </button>
                  </div>
                </div>
                <div className="subject-grid scroll-area">
                  {filteredSubjects.map((subject) => {
                    const isSelected = filterSelection.includes(subject.subject_name);
                    return (
                      <button
                        key={subject.subject_name}
                        className={`subject-chip ${isSelected ? 'is-selected' : ''}`}
                        onClick={() => handleToggleFilterSubject(subject.subject_name)}
                      >
                        <span>{subject.subject_name}</span>
                        <small>{subject.type || 'Core'}</small>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          </div>
        )}
      </section>

      <section className="panel glass-surface">
        <header
          className="panel-header"
          onClick={() => {
            if (!accountExpanded) {
              loadUsers();
            }
            setAccountExpanded(!accountExpanded);
          }}
          style={{ cursor: 'pointer' }}
        >
          <div>
            <p className="eyebrow">Accounts</p>
            <h3>Assign logins to teachers</h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={(event) => {
              event.stopPropagation();
              if (!accountExpanded) {
                loadUsers();
              }
              setAccountExpanded(!accountExpanded);
            }}
          >
            {accountExpanded ? 'Collapse' : 'Expand'}
          </button>
        </header>
        {accountExpanded && (
          <div className="users-panel">
            {usersLoading ? (
              <p className="muted">Loading accounts...</p>
            ) : (
              <>
                <div className="user-card glass-surface">
                  <h4>Assign account</h4>
                  <div className="settings-grid">
                    <label>
                      <span>Teacher Name</span>
                      <input
                        className="input dark"
                        value={accountForm.full_name}
                        onChange={(event) => setAccountForm((prev) => ({ ...prev, full_name: event.target.value }))}
                        placeholder="Full name"
                      />
                    </label>
                    <label>
                      <span>Username</span>
                      <input
                        className="input dark"
                        value={accountForm.username}
                        onChange={(event) => setAccountForm((prev) => ({ ...prev, username: event.target.value }))}
                      />
                    </label>
                  <label>
                    <span>Password</span>
                    <div className="password-field">
                      <input
                        className="input dark"
                        type={showAccountPassword ? 'text' : 'password'}
                        value={accountForm.password}
                        onChange={(event) => setAccountForm((prev) => ({ ...prev, password: event.target.value }))}
                      />
                      <button
                        type="button"
                        className="btn btn-text password-toggle"
                        onClick={() => setShowAccountPassword((prev) => !prev)}
                      >
                        {showAccountPassword ? 'Hide' : 'Show'}
                      </button>
                    </div>
                  </label>
                    <label>
                      <span>Role</span>
                      <select
                        className="input dark"
                        value={accountForm.role}
                        onChange={(event) => setAccountForm((prev) => ({ ...prev, role: event.target.value }))}
                      >
                        <option value="teacher">Teacher</option>
                        <option value="admin">Admin</option>
                      </select>
                    </label>
                  </div>
                  <button className="btn btn-primary" onClick={handleSaveAccount}>
                    Save Account
                  </button>
                </div>
                <div className="user-card glass-surface">
                  <div className="panel-header">
                    <div>
                      <p className="eyebrow">Accounts</p>
                      <h4>Current users</h4>
                    </div>
                    <button className="btn btn-secondary" onClick={loadUsers}>
                      Refresh
                    </button>
                  </div>
                  {!users.length ? (
                    <p className="muted">No users found.</p>
                  ) : (
                    <div className="users-list">
                      {users.map((user) => {
                        const edit = userEdits[user.user_id] || {
                          username: user.username || '',
                          password: user.password || '',
                          role: (user.role || 'teacher').toLowerCase(),
                          full_name: user.full_name || '',
                        };
                        const teacherName = edit.full_name || user.full_name || 'Unassigned';
                        const isOpen = !!openUsers[user.user_id];
                        return (
                          <div key={user.user_id} className={`user-row ${isOpen ? 'is-open' : ''}`}>
                            <div className="user-row-header">
                              <div>
                                <strong>{teacherName}</strong>
                                <div className="user-row-meta">
                                  <span className="muted">Username: {edit.username || '—'}</span>
                                  <span className="muted">Role: {edit.role}</span>
                                  <span className="muted">ID {user.user_id}</span>
                                </div>
                              </div>
                              <button
                                type="button"
                                className="btn btn-secondary"
                                onClick={() =>
                                  setOpenUsers((prev) => ({ ...prev, [user.user_id]: !isOpen }))
                                }
                              >
                                {isOpen ? 'Collapse' : 'Edit'}
                              </button>
                            </div>
                            {isOpen && (
                              <>
                                <div className="user-row-grid">
                                  <label>
                                    <span>Name</span>
                                    <input
                                      className="input dark"
                                      value={edit.full_name}
                                      onChange={(event) =>
                                        setUserEdits((prev) => ({
                                          ...prev,
                                          [user.user_id]: { ...edit, full_name: event.target.value },
                                        }))
                                      }
                                    />
                                  </label>
                                  <label>
                                    <span>Username</span>
                                    <input
                                      className="input dark"
                                      value={edit.username}
                                      onChange={(event) =>
                                        setUserEdits((prev) => ({
                                          ...prev,
                                          [user.user_id]: { ...edit, username: event.target.value },
                                        }))
                                      }
                                    />
                                  </label>
                                  <label>
                                    <span>Password</span>
                                    <div className="password-field">
                                      <input
                                        className="input dark"
                                        type={showUserPasswords ? 'text' : 'password'}
                                        value={edit.password}
                                        onChange={(event) =>
                                          setUserEdits((prev) => ({
                                            ...prev,
                                            [user.user_id]: { ...edit, password: event.target.value },
                                          }))
                                        }
                                      />
                                      <button
                                        type="button"
                                        className="btn btn-text password-toggle"
                                        onClick={() => setShowUserPasswords((prev) => !prev)}
                                      >
                                        {showUserPasswords ? 'Hide' : 'Show'}
                                      </button>
                                    </div>
                                  </label>
                                  <label>
                                    <span>Role</span>
                                    <select
                                      className="input dark"
                                      value={edit.role}
                                      onChange={(event) =>
                                        setUserEdits((prev) => ({
                                          ...prev,
                                          [user.user_id]: { ...edit, role: event.target.value },
                                        }))
                                      }
                                    >
                                      <option value="teacher">Teacher</option>
                                      <option value="admin">Admin</option>
                                    </select>
                                  </label>
                                </div>
                                <div className="user-row-actions">
                                  <button className="btn btn-primary" onClick={() => handleUpdateUser(user.user_id)}>
                                    Update User
                                  </button>
                                </div>
                              </>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              </>
            )}
          </div>
        )}
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
        <header
          className="panel-header"
          onClick={() => setDeveloperExpanded(!developerExpanded)}
          style={{ cursor: 'pointer' }}
        >
          <div>
            <p className="eyebrow">Developer</p>
            <h3>Server + database controls</h3>
          </div>
          <button
            className="btn btn-secondary"
            onClick={(event) => {
              event.stopPropagation();
              setDeveloperExpanded(!developerExpanded);
            }}
          >
            {developerExpanded ? 'Collapse' : 'Expand'}
          </button>
        </header>
        {developerExpanded && (
          <div className="settings-flex">
            <div className="panel glass-surface">
              <header className="panel-header">
                <div>
                  <p className="eyebrow">Connection</p>
                  <h4>Server endpoint</h4>
                </div>
                <button className="btn btn-secondary" onClick={handleSaveApiBase}>
                  Save Server
                </button>
              </header>
              <div className="settings-grid">
                <label>
                  <span>API Base URL</span>
                  <input
                    className="input dark"
                    value={apiBaseInput}
                    onChange={(event) => setApiBaseInput(event.target.value)}
                    placeholder="http://127.0.0.1:8000"
                  />
                </label>
              </div>
            </div>
            <div className="panel glass-surface">
              <header className="panel-header">
                <div>
                  <p className="eyebrow">Database</p>
                  <h4>Postgres connection</h4>
                </div>
                <button className="btn btn-secondary" onClick={handleSaveDbConfig}>
                  Save DB
                </button>
              </header>
              <div className="settings-grid">
                <label>
                  <span>Host</span>
                  <input
                    className="input dark"
                    value={dbConfig.host}
                    onChange={(event) => setDbConfig((prev) => ({ ...prev, host: event.target.value }))}
                  />
                </label>
                <label>
                  <span>Port</span>
                  <input
                    className="input dark"
                    type="number"
                    value={dbConfig.port}
                    onChange={(event) => setDbConfig((prev) => ({ ...prev, port: Number(event.target.value) || 0 }))}
                  />
                </label>
                <label>
                  <span>Database</span>
                  <input
                    className="input dark"
                    value={dbConfig.dbname}
                    onChange={(event) => setDbConfig((prev) => ({ ...prev, dbname: event.target.value }))}
                  />
                </label>
                <label>
                  <span>User</span>
                  <input
                    className="input dark"
                    value={dbConfig.user}
                    onChange={(event) => setDbConfig((prev) => ({ ...prev, user: event.target.value }))}
                  />
                </label>
                <label>
                  <span>Password</span>
                  <div className="password-field">
                    <input
                      className="input dark"
                      type={showDbPassword ? 'text' : 'password'}
                      value={dbConfig.password}
                      onChange={(event) => setDbConfig((prev) => ({ ...prev, password: event.target.value }))}
                    />
                    <button
                      type="button"
                      className="btn btn-text password-toggle"
                      onClick={() => setShowDbPassword((prev) => !prev)}
                    >
                      {showDbPassword ? 'Hide' : 'Show'}
                    </button>
                  </div>
                </label>
                <label>
                  <span>Output Folder</span>
                  <input
                    className="input dark"
                    value={dbConfig.output_dir || ''}
                    onChange={(event) => setDbConfig((prev) => ({ ...prev, output_dir: event.target.value }))}
                    placeholder="C:\\Reports\\Output"
                  />
                </label>
              </div>
            </div>
            <div className="panel glass-surface">
              <header className="panel-header">
                <div>
                  <p className="eyebrow">Danger Zone</p>
                  <h4>Clear results table</h4>
                </div>
                <button className="btn btn-danger" onClick={handleClearResults}>
                  Delete All Results
                </button>
              </header>
              <p className="muted">Testing only. This deletes all saved report results in the database.</p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
}

