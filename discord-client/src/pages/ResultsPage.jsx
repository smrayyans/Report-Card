import { useEffect, useMemo, useState } from 'react';
import useToast from '../hooks/useToast';
import api from '../services/api';

const makeKey = (prefix, ...parts) => `${prefix}:${parts.join('|')}`;

export default function ResultsPage() {
  const toast = useToast();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [openSessions, setOpenSessions] = useState(new Set());
  const [openClasses, setOpenClasses] = useState(new Set());
  const [openTerms, setOpenTerms] = useState(new Set());
  const [contextMenu, setContextMenu] = useState(null);

  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true);
      try {
        const response = await api.get('/reports/history');
        setItems(response.data.items || []);
      } catch (error) {
        toast({
          type: 'error',
          title: 'Load failed',
          message: error.response?.data?.detail || 'Unable to fetch saved results.',
        });
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, [toast]);

  useEffect(() => {
    if (!contextMenu) return;
    const handleClose = () => setContextMenu(null);
    window.addEventListener('click', handleClose);
    return () => window.removeEventListener('click', handleClose);
  }, [contextMenu]);

  const grouped = useMemo(() => {
    const tree = {};
    items.forEach((item) => {
      const session = item.session || 'Unknown Session';
      const classSec = item.class_sec || 'Unknown Class';
      const term = item.term || 'Term';
      if (!tree[session]) tree[session] = {};
      if (!tree[session][classSec]) tree[session][classSec] = {};
      if (!tree[session][classSec][term]) tree[session][classSec][term] = [];
      tree[session][classSec][term].push(item);
    });
    return tree;
  }, [items]);

  const toggleSet = (setter, key) => {
    setter((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleDownload = async (resultId) => {
    try {
      const response = await api.get(`/reports/history/${resultId}/pdf`);
      if (response.data?.file) {
        toast({
          type: 'success',
          title: 'Saved',
          message: `${response.data.file} saved to output folder.`,
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

  const handleTermBatchDownload = async (session, classSec, term) => {
    try {
      const response = await api.get('/reports/history-term', {
        params: { session, class_sec: classSec, term },
      });
      if (response.data?.file) {
        toast({
          type: 'success',
          title: 'Saved',
          message: `${response.data.file} saved to output folder.`,
          openOutput: true,
        });
      }
    } catch (error) {
      toast({
        type: 'error',
        title: 'Download failed',
        message: error.response?.data?.detail || 'Unable to generate term PDF.',
      });
    }
  };

  return (
    <div className="reports-page">
      <section className="panel glass-surface">
        <header className="panel-header">
          <div>
            <p className="eyebrow">Results Archive</p>
            <h3>All saved report cards</h3>
          </div>
        </header>
        {loading ? (
          <p className="muted">Loading results...</p>
        ) : Object.keys(grouped).length ? (
          <div className="results-tree">
            {Object.entries(grouped).map(([session, classes]) => {
              const sessionKey = makeKey('session', session);
              const sessionOpen = openSessions.has(sessionKey);
              return (
                <div key={session} className="results-group">
                  <button
                    className={`results-toggle ${sessionOpen ? 'is-open' : ''}`}
                    onClick={() => toggleSet(setOpenSessions, sessionKey)}
                  >
                    <span>{session}</span>
                    <span className="muted">{Object.keys(classes).length} classes</span>
                  </button>
                  {sessionOpen && (
                    <div className="results-children">
                      {Object.entries(classes).map(([classSec, terms]) => {
                        const classKey = makeKey('class', session, classSec);
                        const classOpen = openClasses.has(classKey);
                        return (
                          <div key={classKey} className="results-group">
                            <button
                              className={`results-toggle ${classOpen ? 'is-open' : ''}`}
                              onClick={() => toggleSet(setOpenClasses, classKey)}
                            >
                              <span>{classSec}</span>
                              <span className="muted">{Object.keys(terms).length} terms</span>
                            </button>
                            {classOpen && (
                              <div className="results-children">
                                {Object.entries(terms).map(([term, students]) => {
                                  const termKey = makeKey('term', session, classSec, term);
                                  const termOpen = openTerms.has(termKey);
                                  return (
                                    <div key={termKey} className="results-group">
                                      <button
                                        className={`results-toggle ${termOpen ? 'is-open' : ''}`}
                                        onClick={() => toggleSet(setOpenTerms, termKey)}
                                        onContextMenu={(event) => {
                                          event.preventDefault();
                                          setContextMenu({
                                            x: event.clientX,
                                            y: event.clientY,
                                            session,
                                            classSec,
                                            term,
                                          });
                                        }}
                                      >
                                        <span>{term}</span>
                                        <span className="muted">{students.length} students</span>
                                      </button>
                                      {termOpen && (
                                        <div className="results-children">
                                          {students.map((student) => (
                                            <div key={student.id} className="results-row">
                                              <div>
                                                <strong>{student.student_name}</strong>
                                                <p className="muted">{student.gr_no}</p>
                                              </div>
                                              <button className="btn btn-text" onClick={() => handleDownload(student.id)}>
                                                Download PDF
                                              </button>
                                            </div>
                                          ))}
                                        </div>
                                      )}
                                    </div>
                                  );
                                })}
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        ) : (
          <p className="muted">No results saved yet.</p>
        )}
        {contextMenu && (
          <div
            className="context-menu"
            style={{ top: contextMenu.y, left: contextMenu.x }}
            onClick={(event) => event.stopPropagation()}
          >
            <button
              className="btn btn-text"
              onClick={() => {
                handleTermBatchDownload(contextMenu.session, contextMenu.classSec, contextMenu.term);
                setContextMenu(null);
              }}
            >
              Download term PDF
            </button>
          </div>
        )}
      </section>
    </div>
  );
}
