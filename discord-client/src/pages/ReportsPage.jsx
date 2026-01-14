import { useEffect, useMemo, useState } from 'react';
import dayjs from 'dayjs';
import SubjectSelectorModal from '../components/SubjectSelectorModal';
import RemarksModal from '../components/RemarksModal';
import DuplicateResultModal from '../components/DuplicateResultModal';
import useReportStore from '../store/reportStore';
import useToast from '../hooks/useToast';
import api, { getApiBase } from '../services/api';
import { gradeFromPercentage } from '../utils/formatters';

const DEFAULT_TERM_OPTIONS = ['Mid Year', 'Annual Year'];
const rankOptions = ['N/A', ...Array.from({ length: 10 }, (_, idx) => `${idx + 1}`)];
const conductOptions = ['Excellent', 'Good', 'Fair', 'Needs Work'];
const performanceOptions = ['Excellent', 'Good', 'Average', 'Needs Support'];
const progressOptions = ['Satisfactory', 'Unsatisfactory'];
const statusOptions = ['Passed', 'Promoted with Support', 'Needs Improvement'];

const createSubjectRow = (subject, type, defaultMax) => ({
  name: subject,
  type: type || 'Core',
  coursework: '',
  termExam: '',
  cwAbsent: false,
  teAbsent: false,
  maxMarks: (defaultMax || 100).toString(),
});

const computeRow = (row) => {
  if (row.cwAbsent && row.teAbsent) {
    return { ...row, obtained: 'Absent', percent: 'Absent', grade: 'Absent' };
  }
  const cw = row.cwAbsent ? 0 : Number(row.coursework || 0);
  const te = row.teAbsent ? 0 : Number(row.termExam || 0);
  const max = Number(row.maxMarks || 0);
  const obtained = cw + te;
  const percent = max > 0 ? (obtained / max) * 100 : 0;
  return {
    ...row,
    obtained: obtained.toFixed(1),
    percent: percent.toFixed(1),
    grade: gradeFromPercentage(percent),
  };
};

export default function ReportsPage() {
  const toast = useToast();
  const [form, setForm] = useState({
    term: DEFAULT_TERM_OPTIONS[0],
    session: '',
    grNo: '',
    studentName: '',
    fatherName: '',
    classSec: '',
    rank: 'N/A',
    totalDays: 0,
    daysAttended: 0,
    conduct: conductOptions[0],
    performance: performanceOptions[0],
    progress: progressOptions[0],
    status: statusOptions[0],
    remarks: '',
    date: dayjs().format('YYYY-MM-DD'),
  });
  const [selectedSubjects, setSelectedSubjects] = useState([]);
  const [subjectModal, setSubjectModal] = useState(false);
  const [remarksModal, setRemarksModal] = useState(false);
  const [pdfInfo, setPdfInfo] = useState(null);
  const [duplicatePrompt, setDuplicatePrompt] = useState({ open: false, message: '', detail: null, payload: null });

  const config = useReportStore((state) => state.config);
  const filters = useReportStore((state) => state.filters);
  const remarks = useReportStore((state) => state.remarks);
  const subjects = useReportStore((state) => state.subjects);
  const fetchInitial = useReportStore((state) => state.fetchInitial);
  const saveFilters = useReportStore((state) => state.saveFilters);
  const saveRemarks = useReportStore((state) => state.saveRemarks);
  const queueCount = useReportStore((state) => state.queueCount);
  const queueItems = useReportStore((state) => state.queueItems);
  const refreshQueueCount = useReportStore((state) => state.refreshQueueCount);
  const refreshQueueItems = useReportStore((state) => state.refreshQueueItems);
  const saveReport = useReportStore((state) => state.saveReport);
  const updateQueuedReport = useReportStore((state) => state.updateQueuedReport);
  const clearQueue = useReportStore((state) => state.clearQueue);
  const exportReports = useReportStore((state) => state.exportReports);
  const [editingQueueId, setEditingQueueId] = useState(null);

  const baseTermOptions = useMemo(() => {
    const configTerms = Array.isArray(config?.terms) ? config.terms.filter(Boolean) : [];
    return configTerms.length ? configTerms : DEFAULT_TERM_OPTIONS;
  }, [config?.terms]);

  const termOptions = useMemo(() => {
    if (form.term && !baseTermOptions.includes(form.term)) {
      return [form.term, ...baseTermOptions];
    }
    return baseTermOptions;
  }, [baseTermOptions, form.term]);

  const defaultTerm = baseTermOptions[0] || DEFAULT_TERM_OPTIONS[0];

  useEffect(() => {
    fetchInitial().catch(() =>
      toast({
        type: 'error',
        title: 'Backend unreachable',
        message: 'Start the FastAPI server before building reports.',
      }),
    );
  }, [fetchInitial, toast]);

  useEffect(() => {
    refreshQueueCount().catch(() => {
      console.warn('Unable to fetch report queue count.');
    });
    refreshQueueItems().catch(() => {
      console.warn('Unable to fetch report queue.');
    });
  }, [refreshQueueCount, refreshQueueItems]);

  useEffect(() => {
    if (config && !form.session) {
      setForm((prev) => ({
        ...prev,
        session: config.default_session || config.sessions?.[0] || '',
      }));
    }
  }, [config, form.session]);


  const buildDefaultSubjects = () => {
    if (!subjects.length || !filters) return [];
    const baseList = filters['1-4']
      ? subjects.filter((subject) => filters['1-4'].includes(subject.subject_name))
      : subjects;
    return baseList.map((subject) =>
      createSubjectRow(subject.subject_name, subject.type, config?.default_max_marks),
    );
  };

  useEffect(() => {
    if (subjects.length && !selectedSubjects.length && filters) {
      setSelectedSubjects(buildDefaultSubjects());
    }
  }, [subjects, selectedSubjects.length, config, filters]);

  const computedRows = useMemo(() => selectedSubjects.map((row) => computeRow(row)), [selectedSubjects]);

  const daysAbsent = Math.max(Number(form.totalDays || 0) - Number(form.daysAttended || 0), 0);

  const grandTotals = useMemo(() => {
    let totalCw = 0;
    let totalTe = 0;
    let totalMax = 0;
    computedRows.forEach((row) => {
      if (row.cwAbsent && row.teAbsent) return;
      totalCw += Number(row.coursework || 0);
      totalTe += Number(row.termExam || 0);
      totalMax += Number(row.maxMarks || 0);
    });
    const totalObt = totalCw + totalTe;
    const pct = totalMax > 0 ? (totalObt / totalMax) * 100 : 0;
    return {
      cw: totalCw.toString(),
      te: totalTe.toString(),
      max: totalMax.toString(),
      obt: totalObt.toString(),
      pct: pct.toFixed(1),
      grade: gradeFromPercentage(pct),
    };
  }, [computedRows]);

  const updateSubject = (name, key, value) => {
    setSelectedSubjects((prev) =>
      prev.map((row) => (row.name === name ? { ...row, [key]: value } : row)),
    );
  };

  const handleApplySubjects = (subjectList) => {
    setSelectedSubjects((prev) =>
      subjectList.map((subject) => {
        const existing = prev.find((entry) => entry.name === subject.subject_name);
        return existing || createSubjectRow(subject.subject_name, subject.type, config?.default_max_marks);
      }),
    );
  };

  const handleSaveFilter = async (name, entries) => {
    if (!name) return;
    const nextFilters = { ...filters, [name]: entries };
    await saveFilters(nextFilters);
    toast({ type: 'success', title: 'Filter saved', message: `Filter "${name}" stored.` });
  };

  const handleDeleteFilter = async (name) => {
    const nextFilters = { ...filters };
    delete nextFilters[name];
    await saveFilters(nextFilters);
    toast({ type: 'success', title: 'Filter removed', message: `Filter "${name}" deleted.` });
  };

  const handleInsertRemark = (text) => {
    setForm((prev) => ({
      ...prev,
      remarks: prev.remarks ? `${prev.remarks}\n${text}` : text,
    }));
  };

  const fetchStudentProfile = async () => {
    if (!form.grNo.trim()) return;
    try {
      const response = await api.get(`/students/${form.grNo.trim()}`);
      const student = response.data;
      setForm((prev) => ({
        ...prev,
        studentName: student.student_name,
        fatherName: student.father_name,
        classSec: student.current_class_sec,
        session: student.current_session || prev.session,
      }));
      toast({ type: 'success', title: 'Data synced', message: 'Student details auto-filled.' });
    } catch (error) {
      toast({ type: 'error', title: 'Not found', message: error.response?.data?.detail || 'Student not found' });
    }
  };

  const buildReportPayload = () => {
    const payload = {
      student_name: form.studentName.trim(),
      father_name: form.fatherName.trim(),
      class_sec: form.classSec.trim(),
      session: form.session,
      gr_no: form.grNo.trim(),
      rank: form.rank,
      total_days: String(form.totalDays),
      days_attended: String(form.daysAttended),
      days_absent: String(daysAbsent),
      term: form.term,
      conduct: form.conduct,
      performance: form.performance,
      progress: form.progress,
      remarks: form.remarks,
      status: form.status,
      date: dayjs(form.date).format('DD MMMM YYYY'),
      grand_totals: {
        ...grandTotals,
        pct: `${grandTotals.pct}%`,
      },
      marks_data: {},
    };

    computedRows.forEach((row) => {
      if (row.cwAbsent && row.teAbsent) {
        payload.marks_data[row.name] = {
          coursework: 'Absent',
          termexam: 'Absent',
          maxmarks: 'Absent',
          obt: 'Absent',
          pct: 'Absent',
          grade: 'Absent',
          is_absent: true,
        };
      } else {
        payload.marks_data[row.name] = {
          coursework: row.cwAbsent ? 'Absent' : (row.coursework || '0'),
          termexam: row.teAbsent ? 'Absent' : (row.termExam || '0'),
          maxmarks: row.maxMarks,
          obt: row.obtained,
          pct: row.percent === 'Absent' ? 'Absent' : `${row.percent}%`,
          grade: row.grade,
          is_absent: false,
        };
      }
    });

    return payload;
  };

  const buildSubjectsFromPayload = (payload) => {
    const marksData = payload?.marks_data || {};
    const knownTypes = subjects.reduce((acc, subject) => {
      acc[subject.subject_name] = subject.type;
      return acc;
    }, {});

    return Object.entries(marksData).map(([name, details]) => {
      const cwAbsent = String(details.coursework).toLowerCase() === 'absent';
      const teAbsent = String(details.termexam).toLowerCase() === 'absent';
      return {
        name,
        type: knownTypes[name] || 'Core',
        coursework: cwAbsent ? '' : (details.coursework || ''),
        termExam: teAbsent ? '' : (details.termexam || ''),
        cwAbsent,
        teAbsent,
        maxMarks: (details.maxmarks || config?.default_max_marks || 100).toString(),
      };
    });
  };

  const loadQueuedReport = (item) => {
    const payload = item.payload || {};
    setEditingQueueId(item.id);
    setForm({
      term: payload.term || defaultTerm,
      session: payload.session || config?.default_session || '',
      grNo: payload.gr_no || '',
      studentName: payload.student_name || '',
      fatherName: payload.father_name || '',
      classSec: payload.class_sec || '',
      rank: payload.rank || 'N/A',
      totalDays: Number(payload.total_days || 0),
      daysAttended: Number(payload.days_attended || 0),
      conduct: payload.conduct || conductOptions[0],
      performance: payload.performance || performanceOptions[0],
      progress: payload.progress || progressOptions[0],
      status: payload.status || statusOptions[0],
      remarks: payload.remarks || '',
      date: payload.date ? dayjs(payload.date, 'DD MMMM YYYY').format('YYYY-MM-DD') : dayjs().format('YYYY-MM-DD'),
    });
    setSelectedSubjects(buildSubjectsFromPayload(payload));
    setPdfInfo(null);
  };

  const handleSaveReport = async () => {
    if (!form.studentName.trim() || !form.classSec.trim()) {
      toast({ type: 'warning', title: 'Missing data', message: 'Enter student name and class before saving.' });
      return;
    }
    try {
      const payload = buildReportPayload();
      const response = editingQueueId
        ? await updateQueuedReport(editingQueueId, payload)
        : await saveReport(payload);
      setEditingQueueId(null);
      resetForm();
      refreshQueueItems().catch(() => {
        console.warn('Unable to refresh report queue.');
      });
      toast({
        type: 'success',
        title: editingQueueId ? 'Updated' : 'Saved',
        message: `Record stored. ${response.count ?? 0} report(s) ready for export.`,
      });
    } catch (error) {
      const detail = error.response?.data?.detail;
      if (error.response?.status === 409 && detail?.type) {
        setDuplicatePrompt({
          open: true,
          message: detail.message || 'This result already exists for the selected term and session.',
          detail,
          payload: buildReportPayload(),
        });
        return;
      }
      toast({
        type: 'error',
        title: 'Save failed',
        message: error.response?.data?.detail || 'Unable to store the report.',
      });
    }
  };

  const handleDuplicateOverwrite = async () => {
    if (!duplicatePrompt.payload) return;
    try {
      const response = await saveReport(duplicatePrompt.payload, true);
      setDuplicatePrompt({ open: false, message: '', detail: null, payload: null });
      setEditingQueueId(null);
      resetForm();
      refreshQueueItems().catch(() => {
        console.warn('Unable to refresh report queue.');
      });
      toast({
        type: 'success',
        title: 'Overwritten',
        message: `Record updated. ${response.count ?? 0} report(s) ready for export.`,
      });
    } catch (overwriteError) {
      toast({
        type: 'error',
        title: 'Overwrite failed',
        message: overwriteError.response?.data?.detail || 'Unable to overwrite the report.',
      });
    }
  };

  const handleDuplicateView = async () => {
    const detail = duplicatePrompt.detail;
    if (!detail) return;
    try {
      if (detail.type === 'queue' && detail.queue_id) {
        const response = await api.get(`/reports/queue/${detail.queue_id}/pdf`);
        if (response.data?.file) {
          toast({
            type: 'success',
            title: 'Saved',
            message: `${response.data.file} saved to output folder.`,
            openOutput: true,
          });
        }
      } else if (detail.type === 'history' && detail.result_id) {
        const response = await api.get(`/reports/history/${detail.result_id}/pdf`);
        if (response.data?.file) {
          toast({
            type: 'success',
            title: 'Saved',
            message: `${response.data.file} saved to output folder.`,
            openOutput: true,
          });
        }
      } else {
        return;
      }
      setDuplicatePrompt({ open: false, message: '', detail: null, payload: null });
    } catch (downloadError) {
      toast({
        type: 'error',
        title: 'View failed',
        message: downloadError.response?.data?.detail || 'Unable to generate the PDF.',
      });
    }
  };

  const handleExportBatch = async () => {
    if (queueCount === 0) {
      toast({
        type: 'warning',
        title: 'Nothing to export',
        message: 'Save at least one report before exporting.',
      });
      return;
    }
    try {
      const response = await exportReports();
      setPdfInfo(response);
      refreshQueueItems().catch(() => {
        console.warn('Unable to refresh report queue.');
      });
      toast({
        type: 'success',
        title: 'Batch exported',
        message: 'All saved reports were compiled into a single PDF.',
        openOutput: true,
      });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Export failed',
        message: error.response?.data?.detail || 'Unable to export saved reports.',
      });
    }
  };

  const handleClearQueue = async () => {
    try {
      await clearQueue();
      setEditingQueueId(null);
      resetForm();
      toast({ type: 'success', title: 'Queue cleared', message: 'All queued reports removed.' });
    } catch (error) {
      toast({
        type: 'error',
        title: 'Clear failed',
        message: error.response?.data?.detail || 'Unable to clear report queue.',
      });
    }
  };

  const resetForm = () => {
    setEditingQueueId(null);
    setForm({
      term: defaultTerm,
      session: config?.default_session || config?.sessions?.[0] || '',
      grNo: '',
      studentName: '',
      fatherName: '',
      classSec: '',
      rank: 'N/A',
      totalDays: 0,
      daysAttended: 0,
      conduct: conductOptions[0],
      performance: performanceOptions[0],
      progress: progressOptions[0],
      status: statusOptions[0],
      remarks: '',
      date: dayjs().format('YYYY-MM-DD'),
    });
    setSelectedSubjects(buildDefaultSubjects());
    setPdfInfo(null);
  };

  return (
    <div className="reports-page">
      <div className="panel glass-surface">
        <div className="form-grid">
          <label>
            <span>Term</span>
            <select className="input dark" value={form.term} onChange={(event) => setForm((prev) => ({ ...prev, term: event.target.value }))}>
              {termOptions.map((term) => (
                <option key={term} value={term}>
                  {term}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>Session</span>
            <select className="input dark" value={form.session} onChange={(event) => setForm((prev) => ({ ...prev, session: event.target.value }))}>
              {(config?.sessions || []).map((session) => (
                <option key={session} value={session}>
                  {session}
                </option>
              ))}
            </select>
          </label>
          <label>
            <span>G.R No.</span>
            <div className="input-with-button">
              <input
                className="input dark"
                value={form.grNo}
                onChange={(event) => setForm((prev) => ({ ...prev, grNo: event.target.value }))}
              />
              <button className="btn btn-secondary" type="button" onClick={fetchStudentProfile}>
                Auto Fill
              </button>
            </div>
          </label>
          <label>
            <span>Student Name</span>
            <input
              className="input dark"
              value={form.studentName}
              onChange={(event) => setForm((prev) => ({ ...prev, studentName: event.target.value }))}
            />
          </label>
          <label>
            <span>Father Name</span>
            <input
              className="input dark"
              value={form.fatherName}
              onChange={(event) => setForm((prev) => ({ ...prev, fatherName: event.target.value }))}
            />
          </label>
          <label>
            <span>Class / Sec</span>
            <input
              className="input dark"
              value={form.classSec}
              onChange={(event) => setForm((prev) => ({ ...prev, classSec: event.target.value }))}
            />
          </label>
          <label>
            <span>Rank</span>
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
              onChange={(event) => setForm((prev) => ({ ...prev, totalDays: Number(event.target.value) }))}
            />
          </label>
          <label>
            <span>Days Attended</span>
            <input
              className="input dark"
              type="number"
              min="0"
              value={form.daysAttended}
              onChange={(event) => setForm((prev) => ({ ...prev, daysAttended: Number(event.target.value) }))}
            />
          </label>
          <label>
            <span>Days Absent</span>
            <input className="input dark" value={daysAbsent} readOnly />
          </label>
          <label>
            <span>Date</span>
            <input
              className="input dark"
              type="date"
              value={form.date}
              onChange={(event) => setForm((prev) => ({ ...prev, date: event.target.value }))}
            />
          </label>
        </div>
        <div className="chip-row">
          {[['Conduct', 'conduct', conductOptions], ['Performance', 'performance', performanceOptions], ['Progress', 'progress', progressOptions]].map(([label, key, options]) => (
            <label key={key}>
              <span>{label}</span>
              <select className="input dark" value={form[key]} onChange={(event) => setForm((prev) => ({ ...prev, [key]: event.target.value }))}>
                {options.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </label>
          ))}
        </div>
        <div className="status-row">
          {statusOptions.map((option) => (
            <label key={option} className="status-option">
              <input
                type="radio"
                name="status"
                value={option}
                checked={form.status === option}
                onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value }))}
              />
              <span>{option}</span>
            </label>
          ))}
        </div>
        <div className="remarks-row">
          <textarea
            className="input dark"
            rows={4}
            placeholder="Teacher's remarks…"
            value={form.remarks}
            onChange={(event) => setForm((prev) => ({ ...prev, remarks: event.target.value }))}
          />
          <button className="btn btn-secondary" type="button" onClick={() => setRemarksModal(true)}>
            Presets
          </button>
        </div>
      </div>

      <div className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Subjects</p>
            <h3>Marks grid</h3>
          </div>
          <div className="panel-actions">
            <button className="btn btn-ghost" onClick={() => setSubjectModal(true)}>
              Select Subjects
            </button>
          </div>
        </header>
        <div className="marks-table">
          <div className="marks-header">
            {['Subject', 'Course Work', 'Term Exam', 'Max', 'Obtained', '%', 'Grade', 'CW Absent', 'TE Absent'].map((header) => (
              <span key={header}>{header}</span>
            ))}
          </div>
          <div className="marks-body">
            {computedRows.map((row, rowIndex) => (
              <div key={row.name} className="marks-row">
                <span>
                  <strong>{row.name}</strong>
                </span>
                <input
                  className="input dark"
                  value={row.cwAbsent ? 'Absent' : row.coursework}
                  disabled={row.cwAbsent}
                  onChange={(event) => updateSubject(row.name, 'coursework', event.target.value)}
                  placeholder={row.cwAbsent ? 'Absent' : '0'}
                  data-row={rowIndex}
                  data-col={0}
                  onKeyDown={(e) => {
                    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                      e.preventDefault();
                      const row = parseInt(e.target.dataset.row);
                      const col = parseInt(e.target.dataset.col);
                      let newRow = row;
                      let newCol = col;

                      if (e.key === 'ArrowUp') newRow = Math.max(0, row - 1);
                      if (e.key === 'ArrowDown') newRow = Math.min(computedRows.length - 1, row + 1);
                      if (e.key === 'ArrowLeft') newCol = Math.max(0, col - 1);
                      if (e.key === 'ArrowRight') newCol = Math.min(2, col + 1);

                      const nextInput = document.querySelector(`input[data-row="${newRow}"][data-col="${newCol}"]`);
                      if (nextInput && !nextInput.disabled) {
                        nextInput.focus();
                        nextInput.select();
                      }
                    }
                  }}
                />
                <input
                  className="input dark"
                  value={row.teAbsent ? 'Absent' : row.termExam}
                  disabled={row.teAbsent}
                  onChange={(event) => updateSubject(row.name, 'termExam', event.target.value)}
                  placeholder={row.teAbsent ? 'Absent' : '0'}
                  data-row={rowIndex}
                  data-col={1}
                  onKeyDown={(e) => {
                    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                      e.preventDefault();
                      const row = parseInt(e.target.dataset.row);
                      const col = parseInt(e.target.dataset.col);
                      let newRow = row;
                      let newCol = col;

                      if (e.key === 'ArrowUp') newRow = Math.max(0, row - 1);
                      if (e.key === 'ArrowDown') newRow = Math.min(computedRows.length - 1, row + 1);
                      if (e.key === 'ArrowLeft') newCol = Math.max(0, col - 1);
                      if (e.key === 'ArrowRight') newCol = Math.min(2, col + 1);

                      const nextInput = document.querySelector(`input[data-row="${newRow}"][data-col="${newCol}"]`);
                      if (nextInput && !nextInput.disabled) {
                        nextInput.focus();
                        nextInput.select();
                      }
                    }
                  }}
                />
                <select className="input dark" value={row.maxMarks} onChange={(event) => updateSubject(row.name, 'maxMarks', event.target.value)}>
                  {(config?.max_marks_options || [50, 75, 100]).map((option) => (
                    <option key={option} value={option}>
                      {option}
                    </option>
                  ))}
                </select>
                <span>{row.obtained}</span>
                <span>{row.percent === 'Absent' ? 'Absent' : `${row.percent}%`}</span>
                <span>{row.grade}</span>
                <label className="toggle-chip">
                  <input type="checkbox" checked={row.cwAbsent} onChange={(event) => updateSubject(row.name, 'cwAbsent', event.target.checked)} />
                  <span>Absent</span>
                </label>
                <label className="toggle-chip">
                  <input type="checkbox" checked={row.teAbsent} onChange={(event) => updateSubject(row.name, 'teAbsent', event.target.checked)} />
                  <span>Absent</span>
                </label>
              </div>
            ))}
          </div>
        </div>
        <div className="grand-row">
          <span>Grand Total</span>
          <span>{grandTotals.cw}</span>
          <span>{grandTotals.te}</span>
          <span>{grandTotals.max}</span>
          <span>{grandTotals.obt}</span>
          <span>{grandTotals.pct}%</span>
          <span>{grandTotals.grade}</span>
        </div>
        <div className="panel-footer">
          <div className="pdf-meta">
            {pdfInfo ? (
              <a className="link" href={`${getApiBase()}${pdfInfo.download_url}`} target="_blank" rel="noreferrer">
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
            <button className="btn btn-secondary" type="button" onClick={handleSaveReport}>
              {editingQueueId ? 'Update' : 'Save'}
            </button>
            <button className="btn btn-danger" type="button" onClick={handleClearQueue} disabled={queueItems.length === 0}>
              Clear Queue
            </button>
            <button
              className="btn btn-primary"
              type="button"
              onClick={handleExportBatch}
              disabled={queueCount === 0}
            >
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
                  onClick={() => loadQueuedReport(item)}
                >
                  <span>{item.payload?.student_name || 'Unnamed Student'}</span>
                  <span className="muted">{item.payload?.class_sec || ''}</span>
                </button>
              ))}
            </div>
          ) : (
            <p className="muted">No saved reports yet.</p>
          )}
        </div>
      </div>

      <SubjectSelectorModal
        open={subjectModal}
        subjects={subjects}
        selectedSubjects={selectedSubjects}
        filters={filters}
        onApply={handleApplySubjects}
        onClose={() => setSubjectModal(false)}
        onSaveFilter={handleSaveFilter}
        onDeleteFilter={handleDeleteFilter}
      />
      <RemarksModal open={remarksModal} remarks={remarks} onInsert={handleInsertRemark} onSave={saveRemarks} onClose={() => setRemarksModal(false)} />
      <DuplicateResultModal
        open={duplicatePrompt.open}
        message={duplicatePrompt.message}
        onOverwrite={handleDuplicateOverwrite}
        onView={handleDuplicateView}
        onClose={() => setDuplicatePrompt({ open: false, message: '', detail: null, payload: null })}
      />
    </div>
  );
}
