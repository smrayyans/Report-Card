import { useEffect, useMemo, useState } from 'react';
import useToast from '../hooks/useToast';
import api, { API_BASE } from '../services/api';
import RemarksModal from '../components/RemarksModal';
import useDiagnosticsStore from '../store/diagnosticsStore';
import useReportStore from '../store/reportStore';

const ratingOptions = ['Excellent', 'Very Good', 'Good', 'Fair'];
const rankOptions = ['N/A', ...Array.from({ length: 10 }, (_, idx) => `${idx + 1}`)];
const diagnosticsSections = [
  {
    title: 'GENERAL PROGRESS',
    items: [
      'Punctuality',
      'Conduct',
      'Tidiness',
      'Works Independently & Neatly',
      'Shows Interest & Efforts',
      'Follows Instructions',
      'Confidence',
    ],
  },
  {
    title: 'MATHS',
    items: [
      'Oral Counting',
      'Recognition of Numbers',
      'Tracing/Writing of Numbers',
      'Recognition of Shapes',
      'Understanding of Concept',
    ],
  },
  {
    title: 'ENGLISH',
    items: [
      'Recognition of Sound/Letter',
      'Tracing',
      'Writing of Letter',
      'Listening/Speaking',
      'Recitation of Rhymes',
      'Reading',
    ],
  },
  {
    title: 'URDU',
    items: ['Recognition of Sound/Letter', 'Tracing/Writing of Letter', 'Recitation of Rhymes', 'Reading'],
  },
  {
    title: 'OTHER SUBJECTS',
    items: ['General Knowledge - Oral', 'Art/Drawing'],
  },
  {
    title: 'ISLAMIAT',
    items: ['Islamiat - Oral'],
  },
];

const buildRatingState = () =>
  diagnosticsSections.reduce((acc, section) => {
    section.items.forEach((item) => {
      acc[item] = ratingOptions[0];
    });
    return acc;
  }, {});

export default function DiagnosticsPage() {
  const toast = useToast();
  const queueCount = useDiagnosticsStore((state) => state.queueCount);
  const queueItems = useDiagnosticsStore((state) => state.queueItems);
  const refreshQueueCount = useDiagnosticsStore((state) => state.refreshQueueCount);
  const refreshQueueItems = useDiagnosticsStore((state) => state.refreshQueueItems);
  const saveDiagnostics = useDiagnosticsStore((state) => state.saveDiagnostics);
  const updateQueuedDiagnostics = useDiagnosticsStore((state) => state.updateQueuedDiagnostics);
  const clearQueue = useDiagnosticsStore((state) => state.clearQueue);
  const exportDiagnostics = useDiagnosticsStore((state) => state.exportDiagnostics);
  const remarks = useReportStore((state) => state.remarks);
  const saveRemarks = useReportStore((state) => state.saveRemarks);
  const fetchInitial = useReportStore((state) => state.fetchInitial);
  const [editingQueueId, setEditingQueueId] = useState(null);
  const [remarksModal, setRemarksModal] = useState(false);
  const [form, setForm] = useState({
    term: 'Diagnostics',
    grNo: '',
    studentName: '',
    fatherName: '',
    classSec: '',
    rank: rankOptions[0],
    totalDays: '',
    daysAttended: '',
    attendanceDates: '',
    overallRemark: '',
    comment: '',
  });
  const [ratings, setRatings] = useState(() => buildRatingState());
  const [pdfInfo, setPdfInfo] = useState(null);
  const [lastFetchedGrNo, setLastFetchedGrNo] = useState('');

  const canAutoFill = useMemo(() => Boolean(form.grNo.trim()) && form.grNo.trim() !== lastFetchedGrNo, [form.grNo, lastFetchedGrNo]);
  const daysAbsent = Math.max(Number(form.totalDays || 0) - Number(form.daysAttended || 0), 0);

  useEffect(() => {
    refreshQueueCount().catch(() => {
      console.warn('Unable to fetch diagnostics queue count.');
    });
    refreshQueueItems().catch(() => {
      console.warn('Unable to fetch diagnostics queue.');
    });
  }, [refreshQueueCount, refreshQueueItems]);

  useEffect(() => {
    fetchInitial().catch(() =>
      toast({
        type: 'error',
        title: 'Backend unreachable',
        message: 'Start the FastAPI server before building diagnostics.',
      }),
    );
  }, [fetchInitial, toast]);

  const fetchStudentProfile = async () => {
    if (!canAutoFill) return;
    const grNo = form.grNo.trim();
    try {
      const response = await api.get(`/students/${grNo}`);
      const student = response.data;
      setForm((prev) => ({
        ...prev,
        studentName: student.student_name,
        fatherName: student.father_name,
        classSec: student.current_class_sec,
      }));
      setLastFetchedGrNo(grNo);
      toast({ type: 'success', title: 'Data synced', message: 'Student details auto-filled.' });
    } catch (error) {
      toast({ type: 'error', title: 'Not found', message: error.response?.data?.detail || 'Student not found' });
    }
  };

  const updateRating = (item, value) => {
    setRatings((prev) => ({ ...prev, [item]: value }));
  };

  const buildDiagnosticsPayload = () => ({
    student_name: form.studentName.trim(),
    father_name: form.fatherName.trim(),
    class_sec: form.classSec.trim(),
    gr_no: form.grNo.trim(),
    rank: form.rank,
    total_days: form.totalDays ? String(form.totalDays).trim() : '',
    days_attended: form.daysAttended ? String(form.daysAttended).trim() : '',
    days_absent: String(daysAbsent),
    attendance_dates: form.attendanceDates.trim(),
    overall_remark: form.overallRemark.trim(),
    term: form.term,
    comment: form.comment.trim(),
    diagnostics_sections: diagnosticsSections.map((section) => ({
      title: section.title,
      rows: section.items.map((item) => ({
        label: item,
        value: ratings[item] || ratingOptions[0],
      })),
    })),
  });

  const handleInsertRemark = (text) => {
    setForm((prev) => ({
      ...prev,
      comment: prev.comment ? `${prev.comment}\n${text}` : text,
    }));
  };

  const loadQueuedDiagnostics = (item) => {
    const payload = item.payload || {};
    setEditingQueueId(item.id);
    setForm({
      term: payload.term || 'Diagnostics',
      grNo: payload.gr_no || '',
      studentName: payload.student_name || '',
      fatherName: payload.father_name || '',
      classSec: payload.class_sec || '',
      rank: payload.rank || rankOptions[0],
      totalDays: payload.total_days || '',
      daysAttended: payload.days_attended || '',
      attendanceDates: payload.attendance_dates || '',
      overallRemark: payload.overall_remark || '',
      comment: payload.comment || '',
    });

    const nextRatings = buildRatingState();
    (payload.diagnostics_sections || []).forEach((section) => {
      (section.rows || []).forEach((row) => {
        if (row.label) {
          nextRatings[row.label] = row.value || ratingOptions[0];
        }
      });
    });
    setRatings(nextRatings);
    setPdfInfo(null);
  };

  const resetForm = () => {
    setEditingQueueId(null);
    setForm({
      term: 'Diagnostics',
      grNo: '',
      studentName: '',
      fatherName: '',
      classSec: '',
      rank: rankOptions[0],
      totalDays: '',
      daysAttended: '',
      attendanceDates: '',
      overallRemark: '',
      comment: '',
    });
    setRatings(buildRatingState());
    setPdfInfo(null);
    setLastFetchedGrNo('');
  };

  const handleSave = async () => {
    if (!form.studentName.trim() || !form.classSec.trim()) {
      toast({ type: 'warning', title: 'Missing data', message: 'Enter student name and class before saving.' });
      return;
    }
    try {
      const payload = buildDiagnosticsPayload();
      const response = editingQueueId
        ? await updateQueuedDiagnostics(editingQueueId, payload)
        : await saveDiagnostics(payload);
      setEditingQueueId(null);
      resetForm();
      refreshQueueItems().catch(() => {
        console.warn('Unable to refresh diagnostics queue.');
      });
      toast({
        type: 'success',
        title: editingQueueId ? 'Updated' : 'Saved',
        message: `Diagnostics form queued. ${response.count ?? 0} record(s) ready for export.`,
      });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Save failed',
        message: error.response?.data?.detail || 'Unable to store diagnostics.',
      });
    }
  };

  const handleExport = async () => {
    if (queueCount === 0) {
      toast({ type: 'warning', title: 'Nothing to export', message: 'Save at least one diagnostics form before exporting.' });
      return;
    }
    try {
      const response = await exportDiagnostics();
      setPdfInfo(response);
      refreshQueueItems().catch(() => {
        console.warn('Unable to refresh diagnostics queue.');
      });
      toast({ type: 'success', title: 'Batch exported', message: 'Diagnostics PDF generated successfully.' });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Export failed',
        message: error.response?.data?.detail || 'Unable to export diagnostics.',
      });
    }
  };

  const handleClearQueue = async () => {
    try {
      await clearQueue();
      setEditingQueueId(null);
      resetForm();
      toast({ type: 'success', title: 'Queue cleared', message: 'All queued diagnostics removed.' });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Clear failed',
        message: error.response?.data?.detail || 'Unable to clear diagnostics queue.',
      });
    }
  };

  return (
    <div className="reports-page">
      <div className="panel glass-surface">
        <div className="form-grid">
          <label>
            <span>Term</span>
            <select className="input dark" value={form.term} onChange={(event) => setForm((prev) => ({ ...prev, term: event.target.value }))}>
              <option value="Diagnostics">Diagnostics</option>
            </select>
          </label>
          <label>
            <span>G.R No.</span>
            <div className="input-with-button">
              <input
                className="input dark"
                value={form.grNo}
                onChange={(event) => setForm((prev) => ({ ...prev, grNo: event.target.value }))}
                onBlur={fetchStudentProfile}
              />
              <button className="btn btn-secondary" type="button" onClick={fetchStudentProfile}>
                Auto Fill
              </button>
            </div>
          </label>
          <label>
            <span>Name</span>
            <input
              className="input dark"
              value={form.studentName}
              onChange={(event) => setForm((prev) => ({ ...prev, studentName: event.target.value }))}
            />
          </label>
          <label>
            <span>Father's Name</span>
            <input
              className="input dark"
              value={form.fatherName}
              onChange={(event) => setForm((prev) => ({ ...prev, fatherName: event.target.value }))}
            />
          </label>
          <label>
            <span>Class/Sec</span>
            <input
              className="input dark"
              value={form.classSec}
              onChange={(event) => setForm((prev) => ({ ...prev, classSec: event.target.value }))}
            />
          </label>
          <label>
            <span>Rank in Class</span>
            <select className="input dark" value={form.rank} onChange={(event) => setForm((prev) => ({ ...prev, rank: event.target.value }))}>
              {rankOptions.map((rank) => (
                <option key={rank} value={rank}>
                  {rank}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Total Days</span>
            <input
              className="input dark"
              type="number"
              min="0"
              value={form.totalDays}
              onChange={(event) => setForm((prev) => ({ ...prev, totalDays: event.target.value }))}
            />
          </label>
          <label>
            <span>Days Attended</span>
            <input
              className="input dark"
              type="number"
              min="0"
              value={form.daysAttended}
              onChange={(event) => setForm((prev) => ({ ...prev, daysAttended: event.target.value }))}
            />
          </label>
          <label>
            <span>Days Absent</span>
            <input className="input dark" value={daysAbsent} readOnly />
          </label>
          <label>
            <span>Dates Attendance</span>
            <input
              className="input dark"
              value={form.attendanceDates}
              onChange={(event) => setForm((prev) => ({ ...prev, attendanceDates: event.target.value }))}
              placeholder="e.g., 01 Feb - 28 Feb"
            />
          </label>
          <label>
            <span>Overall Remark</span>
            <input
              className="input dark"
              value={form.overallRemark}
              onChange={(event) => setForm((prev) => ({ ...prev, overallRemark: event.target.value }))}
            />
          </label>
        </div>
        <div className="remarks-row">
          <textarea
            className="input dark"
            rows={4}
            placeholder="Comment"
            value={form.comment}
            onChange={(event) => setForm((prev) => ({ ...prev, comment: event.target.value }))}
          />
          <button className="btn btn-secondary" type="button" onClick={() => setRemarksModal(true)}>
            Presets
          </button>
        </div>
      </div>

      <div className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Diagnostics</p>
            <h3>Performance checklist</h3>
          </div>
        </header>
        <div className="diagnostics-sections">
          {diagnosticsSections.map((section) => (
            <section key={section.title} className="diagnostics-section">
              <h4>{section.title}</h4>
              <div className="diagnostics-grid">
                {section.items.map((item) => (
                  <label key={item} className="diagnostics-row">
                    <span>{item}</span>
                    <select className="input dark" value={ratings[item]} onChange={(event) => updateRating(item, event.target.value)}>
                      {ratingOptions.map((option) => (
                        <option key={option} value={option}>
                          {option}
                        </option>
                      ))}
                    </select>
                  </label>
                ))}
              </div>
            </section>
          ))}
        </div>
        <div className="panel-footer">
          <div className="pdf-meta">
            {pdfInfo ? (
              <a className="link" href={`${API_BASE}${pdfInfo.download_url}`} target="_blank" rel="noreferrer">
                Download latest PDF
              </a>
            ) : (
              <p className="muted">PDF link will appear after generation.</p>
            )}
          </div>
          <div className="panel-actions">
            <button className="btn btn-ghost" onClick={resetForm}>
              Reset
            </button>
            <button className="btn btn-secondary" type="button" onClick={handleSave}>
              {editingQueueId ? 'Update' : 'Save'}
            </button>
            <button className="btn btn-danger" type="button" onClick={handleClearQueue} disabled={queueItems.length === 0}>
              Clear Queue
            </button>
            <button className="btn btn-primary" type="button" onClick={handleExport} disabled={queueCount === 0}>
              {queueCount ? `Export(${queueCount})` : 'Export'}
            </button>
          </div>
        </div>
        <div className="queue-panel">
          <div className="queue-header">
            <span className="eyebrow">Queue</span>
            <span className="muted">{queueItems.length} saved</span>
          </div>
          {queueItems.length ? (
            <div className="queue-list">
              {queueItems.map((item) => (
                <button
                  key={item.id}
                  className={`queue-item${editingQueueId === item.id ? ' is-active' : ''}`}
                  type="button"
                  onClick={() => loadQueuedDiagnostics(item)}
                >
                  <span>{item.payload?.student_name || 'Unnamed Student'}</span>
                  <span className="muted">{item.payload?.class_sec || ''}</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="muted">No saved diagnostics yet.</p>
          )}
        </div>
      </div>
      <RemarksModal open={remarksModal} remarks={remarks} onInsert={handleInsertRemark} onSave={saveRemarks} onClose={() => setRemarksModal(false)} />
    </div>
  );
}
