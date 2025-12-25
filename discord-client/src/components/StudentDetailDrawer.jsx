import { AnimatePresence, motion } from 'framer-motion';
import { useEffect } from 'react';

const drawerVariants = {
  hidden: { x: '100%', opacity: 0 },
  visible: { x: 0, opacity: 1 },
  exit: { x: '100%', opacity: 0 },
};

const backdropVariants = {
  hidden: { opacity: 0 },
  visible: { opacity: 1 },
  exit: { opacity: 0 },
};

export default function StudentDetailDrawer({
  open,
  detail,
  loading,
  history,
  historyLoading,
  onDownloadHistory,
  onClose,
  onDetailedView,
}) {
  useEffect(() => {
    if (open) {
      // Prevent body scrolling when drawer is open
      document.body.style.overflow = 'hidden';
    } else {
      // Restore body scrolling when drawer is closed
      document.body.style.overflow = '';
    }

    // Cleanup function to restore scrolling if component unmounts
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="drawer-backdrop"
            variants={backdropVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ duration: 0.2 }}
            onClick={onClose}
          />
          <motion.aside
            className="detail-drawer detail-drawer-solid"
            variants={drawerVariants}
            initial="hidden"
            animate="visible"
            exit="exit"
            transition={{ type: 'spring', stiffness: 240, damping: 24 }}
          >
            <div className="drawer-header">
              <div>
                <p className="eyebrow">Focused Student</p>
                <h2>{detail?.student_name || 'Loading…'}</h2>
                <p className="muted">{detail?.address || '—'}</p>
              </div>
              <button className="btn btn-text" onClick={onClose}>
                Close
              </button>
            </div>
            <div className="drawer-content">
              {loading ? (
                <div className="drawer-loading">Loading profile…</div>
              ) : detail ? (
                <>
                  <div className="drawer-section">
                    <h4>Snapshot</h4>
                    <div className="drawer-grid">
                      <div>
                        <p className="muted">G.R No</p>
                        <strong>{detail.gr_no}</strong>
                      </div>
                      <div>
                        <p className="muted">Father Name</p>
                        <strong>{detail.father_name}</strong>
                      </div>
                      <div>
                        <p className="muted">Class / Session</p>
                        <strong>
                          {detail.current_class_sec} · {detail.current_session}
                        </strong>
                      </div>
                      <div>
                        <p className="muted">Status</p>
                        <span className={`status-pill status-${detail.status?.toLowerCase()}`}>{detail.status}</span>
                      </div>
                    </div>
                  </div>

                  <div className="drawer-section">
                    <h4>Timeline</h4>
                    <div className="timeline">
                      <div>
                        <p className="muted">Joining Date</p>
                        <strong>{detail.joining_date_display}</strong>
                      </div>
                      <div>
                        <p className="muted">Years Studying</p>
                        <strong>{detail.years_studying}</strong>
                      </div>
                      <div>
                        <p className="muted">Date of Birth</p>
                        <strong>{detail.date_of_birth_display}</strong>
                      </div>
                      <div>
                        <p className="muted">Age</p>
                        <strong>{detail.age_display}</strong>
                      </div>
                    </div>
                  </div>

                  <div className="drawer-section">
                    <h4>Contacts</h4>
                    <div className="drawer-list">
                      {detail.contacts?.length ? (
                        detail.contacts.map((contact) => (
                          <div key={`${contact.label}-${contact.value}`}>
                            <p className="muted">{contact.label}</p>
                            <strong>{contact.value}</strong>
                          </div>
                        ))
                      ) : (
                        <p className="muted">No contacts on record.</p>
                      )}
                    </div>
                  </div>

                  <div className="drawer-section">
                    <h4>Past Results</h4>
                    {historyLoading ? (
                      <p className="muted">Loading results...</p>
                    ) : history?.length ? (
                      <div className="result-history">
                        {history.map((item) => (
                          <div key={item.id} className="result-history-row">
                            <div>
                              <strong>{item.term || 'Term'}</strong>
                              <p className="muted">{item.session || ''}</p>
                              {item.date && <p className="muted">{item.date}</p>}
                            </div>
                            <button className="btn btn-text" onClick={() => onDownloadHistory?.(item.id)}>
                              Download PDF
                            </button>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="muted">No results saved yet.</p>
                    )}
                  </div>

                  <div className="drawer-actions">
                    <button className="btn btn-primary" onClick={onDetailedView}>
                      Detailed View & Edit
                    </button>
                  </div>
                </>
              ) : (
                <div className="drawer-loading">Select a student to see details.</div>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
