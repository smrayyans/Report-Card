import { useEffect, useState } from 'react';
import StatCard from '../components/StatCard';
import StudentTable from '../components/StudentTable';
import StudentDetailDrawer from '../components/StudentDetailDrawer';
import StudentEditModal from '../components/StudentEditModal';
import FileUploadButton from '../components/FileUploadButton';
import useStudentStore from '../store/studentStore';
import useToast from '../hooks/useToast';
import api from '../services/api';

const statusOptions = ['All', 'Active', 'Left', 'Inactive'];

export default function StudentsPage() {
  const toast = useToast();
  const [filters, setFilters] = useState({ search: '', selectedClasses: [], status: 'All' });
  const [selected, setSelected] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [classFilterOpen, setClassFilterOpen] = useState(false);

  const students = useStudentStore((state) => state.students);
  const stats = useStudentStore((state) => state.stats);
  const classes = useStudentStore((state) => state.classes);
  const loading = useStudentStore((state) => state.loading);
  const detail = useStudentStore((state) => state.detail);
  const detailLoading = useStudentStore((state) => state.detailLoading);
  const history = useStudentStore((state) => state.history);
  const historyLoading = useStudentStore((state) => state.historyLoading);
  const fetchStudents = useStudentStore((state) => state.fetchStudents);
  const fetchStats = useStudentStore((state) => state.fetchStats);
  const fetchClasses = useStudentStore((state) => state.fetchClasses);
  const fetchStudentDetail = useStudentStore((state) => state.fetchStudentDetail);
  const fetchReportHistory = useStudentStore((state) => state.fetchReportHistory);
  const downloadReportHistoryPdf = useStudentStore((state) => state.downloadReportHistoryPdf);
  const importStudents = useStudentStore((state) => state.importStudents);
  const importLoading = useStudentStore((state) => state.importLoading);
  const clearDetail = useStudentStore((state) => state.clearDetail);
  const updateStudent = useStudentStore((state) => state.updateStudent);
  const deleteStudent = useStudentStore((state) => state.deleteStudent);
  const loadMoreStudents = useStudentStore((state) => state.loadMoreStudents);
  const hasMore = useStudentStore((state) => state.hasMore);
  const loadingMore = useStudentStore((state) => state.loadingMore);
  const totalStudents = useStudentStore((state) => state.totalStudents);

  const [saveLoading, setSaveLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);

  useEffect(() => {
    fetchStats();
    fetchClasses();
  }, [fetchStats, fetchClasses]);

  useEffect(() => {
    const timeout = setTimeout(() => {
      // If specific classes are selected, filter client-side
      const apiFilters = {
        search: filters.search,
        class_sec: filters.selectedClasses.length === 0 ? undefined : filters.selectedClasses.join(','),
        status: filters.status === 'All' ? undefined : filters.status,
      };

      fetchStudents(apiFilters).catch(() =>
        toast({ type: 'error', title: 'Unable to load students', message: 'Check if the Python backend is running.' }),
      );
    }, 250);
    return () => clearTimeout(timeout);
  }, [filters, fetchStudents, toast]);

  const handleSelect = async (student) => {
    setSelected(student);
    try {
      await fetchStudentDetail(student.gr_no);
      await fetchReportHistory(student.gr_no);
      setDrawerOpen(true);
    } catch (error) {
      toast({ type: 'error', title: 'Student lookup failed', message: error.response?.data?.detail || 'Unknown error' });
    }
  };

  const handleImport = async (file) => {
    try {
      const result = await importStudents(file);
      toast({
        type: 'success',
        title: 'Import complete',
        message: `Imported ${result.imported} students${result.errors.length ? `, ${result.errors.length} failed` : ''}.`,
      });
      if (result.errors.length) {
        console.warn('Import errors', result.errors);
      }
      fetchStudents(filters);
      fetchStats();
    } catch (error) {
      toast({ type: 'error', title: 'Import failed', message: error.response?.data?.detail || 'Could not import file' });
    }
  };

  const downloadSample = () => {
    api
      .get('/students/sample')
      .then((response) => {
        const file = response?.data?.file;
        toast({
          type: 'success',
          title: 'Sample saved',
          message: file ? `${file} saved to output folder.` : 'Sample Excel saved to output folder.',
          openOutput: true,
        });
      })
      .catch((error) => {
        toast({
          type: 'error',
          title: 'Sample failed',
          message: error.response?.data?.detail || 'Unable to save sample Excel.',
        });
      });
  };

  const downloadAllStudents = async () => {
    try {
      const response = await api.get('/students/export');
      const file = response?.data?.file;
      toast({
        type: 'success',
        title: 'Exported',
        message: file ? `${file} saved to output folder.` : 'Student export saved to output folder.',
        openOutput: true,
      });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Export failed',
        message: error.response?.data?.detail || 'Unable to export students.',
      });
    }
  };

  const resetFilters = () => {
    setFilters({ search: '', selectedClasses: [], status: 'All' });
  };

  const toggleClass = (className) => {
    setFilters((prev) => ({
      ...prev,
      selectedClasses: prev.selectedClasses.includes(className)
        ? prev.selectedClasses.filter((c) => c !== className)
        : [...prev.selectedClasses, className],
    }));
  };

  const selectAllClasses = () => {
    setFilters((prev) => ({ ...prev, selectedClasses: [...classes] }));
  };

  const clearAllClasses = () => {
    setFilters((prev) => ({ ...prev, selectedClasses: [] }));
  };

  const openDetailModal = () => {
    setDetailModalOpen(true);
  };

  const closeDrawer = () => {
    setDrawerOpen(false);
    clearDetail();
  };

  const handleDownloadHistory = async (resultId) => {
    try {
      const response = await downloadReportHistoryPdf(resultId);
      if (response?.file) {
        toast({
          type: 'success',
          title: 'Saved',
          message: `${response.file} saved to output folder.`,
          openOutput: true,
        });
      }
    } catch (error) {
      toast({
        type: 'error',
        title: 'Download failed',
        message: error.response?.data?.detail || 'Unable to generate PDF.',
      });
    }
  };

  const handleSaveStudent = async (updates) => {
    if (!detail?.gr_no) return;

    setSaveLoading(true);
    try {
      await updateStudent(detail.gr_no, updates);
      toast({
        type: 'success',
        title: 'Student updated',
        message: `${detail.student_name}'s details have been saved successfully.`,
      });
      // Refresh the student list and stats
      await fetchStudents(filters);
      await fetchStats();
      setDetailModalOpen(false);
    } catch (error) {
      toast({
        type: 'error',
        title: 'Update failed',
        message: error.response?.data?.detail || 'Could not save student details.',
      });
    } finally {
      setSaveLoading(false);
    }
  };

  const handleDeleteStudent = async () => {
    if (!detail?.gr_no) return;
    const confirmDelete = window.confirm(
      `Are you sure you want to permanently delete ${detail.student_name}? This cannot be undone.`,
    );
    if (!confirmDelete) return;

    setDeleteLoading(true);
    try {
      await deleteStudent(detail.gr_no);
      toast({
        type: 'success',
        title: 'Student deleted',
        message: `${detail.student_name} has been removed from the roster.`,
      });
      setDetailModalOpen(false);
      setDrawerOpen(false);
      setSelected(null);
      clearDetail();
      await fetchStudents(filters);
      await fetchStats();
    } catch (error) {
      toast({
        type: 'error',
        title: 'Delete failed',
        message: error.response?.data?.detail || 'Could not delete the student.',
      });
    } finally {
      setDeleteLoading(false);
    }
  };

  const handleLoadMore = async () => {
    try {
      await loadMoreStudents(filters);
    } catch (error) {
      toast({
        type: 'error',
        title: 'Failed to load more',
        message: 'Could not fetch additional students.',
      });
    }
  };

  const handleCopyGrNo = async (grNo) => {
    if (!grNo) return;
    try {
      await navigator.clipboard.writeText(grNo);
      toast({ type: 'success', title: 'Copied', message: `G.R No ${grNo} copied.` });
    } catch (error) {
      toast({ type: 'error', title: 'Copy failed', message: 'Could not copy G.R No.' });
    }
  };

  return (
    <div className="students-page page-grid">
      <section className="panel glass-surface">
        <div className="panel-header">
          <div>
            <p className="eyebrow">Roster Overview</p>
            <h2>Live student metrics</h2>
          </div>
          <div className="panel-actions">
            <button className="btn btn-ghost" onClick={resetFilters}>
              View All
            </button>
            <button className="btn btn-secondary" onClick={() => fetchStudents(filters)}>
              Refresh
            </button>
          </div>
        </div>
        <div className="stat-grid">
          <StatCard label="Total Students" value={stats.total} accent="iris" />
          <StatCard label="Active" value={stats.active} accent="emerald" />
          <StatCard label="Inactive" value={stats.inactive} accent="rose" />
        </div>
      </section>

      <section className="panel glass-surface">
        <div className="filter-bar">
          <input
            className="input dark"
            placeholder="Search name, G.R, or class…"
            value={filters.search}
            onChange={(event) => setFilters((prev) => ({ ...prev, search: event.target.value }))}
          />
          <div className="class-filter-container">
            <button
              className="btn btn-secondary class-filter-toggle"
              onClick={() => setClassFilterOpen(!classFilterOpen)}
            >
              Classes ({filters.selectedClasses.length || 'All'})
            </button>
            {classFilterOpen && (
              <div className="class-filter-dropdown">
                <div className="class-filter-header">
                  <button className="btn btn-text" onClick={selectAllClasses}>
                    Select All
                  </button>
                  <button className="btn btn-text" onClick={clearAllClasses}>
                    Clear All
                  </button>
                </div>
                <div className="class-filter-list">
                  {classes.map((cls) => (
                    <label key={cls} className="class-filter-item">
                      <input
                        type="checkbox"
                        checked={filters.selectedClasses.includes(cls)}
                        onChange={() => toggleClass(cls)}
                      />
                      <span>{cls}</span>
                    </label>
                  ))}
                </div>
              </div>
            )}
          </div>
          <select
            className="input dark"
            value={filters.status}
            onChange={(event) => setFilters((prev) => ({ ...prev, status: event.target.value }))}
          >
            {statusOptions.map((status) => (
              <option key={status} value={status}>
                {status}
              </option>
            ))}
          </select>
          <button className="btn btn-secondary" onClick={() => setFilters((prev) => ({ ...prev, search: '' }))}>
            Clear Search
          </button>
        </div>
        <div className="action-row">
          <button className="btn btn-ghost" onClick={downloadAllStudents}>
            Export Students
          </button>
          <button className="btn btn-ghost" onClick={downloadSample}>
            Sample Excel
          </button>
          <FileUploadButton label="Import Excel" onSelect={handleImport} loading={importLoading} />
        </div>
        <StudentTable
          students={students}
          loading={loading}
          onSelect={handleSelect}
          selected={selected}
          onCopyGrNo={handleCopyGrNo}
        />

        {hasMore && (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '20px 0' }}>
            <button
              className="btn btn-secondary"
              onClick={handleLoadMore}
              disabled={loadingMore}
            >
              {loadingMore ? 'Loading...' : `Show More (${students.length} of ${totalStudents})`}
            </button>
          </div>
        )}
      </section >

      <StudentDetailDrawer
        open={drawerOpen}
        detail={detail}
        loading={detailLoading}
        history={history}
        historyLoading={historyLoading}
        onDownloadHistory={handleDownloadHistory}
        onClose={closeDrawer}
        onDetailedView={openDetailModal}
      />

      <StudentEditModal
        open={detailModalOpen}
        student={detail}
        onClose={() => setDetailModalOpen(false)}
        onSave={handleSaveStudent}
        onDelete={handleDeleteStudent}
        deleteLoading={deleteLoading}
        loading={saveLoading}
      />
    </div >
  );
}
