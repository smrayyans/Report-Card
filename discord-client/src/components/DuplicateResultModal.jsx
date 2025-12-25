import { AnimatePresence, motion } from 'framer-motion';
import { useEffect } from 'react';

export default function DuplicateResultModal({ open, message, onOverwrite, onView, onClose }) {
  useEffect(() => {
    if (open) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [open]);

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
                <p className="eyebrow">Duplicate Result</p>
                <h3>Result already exists</h3>
              </div>
              <button className="btn btn-text" onClick={onClose}>
                Close
              </button>
            </header>
            <p className="muted">{message || 'This result already exists for the selected term and session.'}</p>
            <footer className="modal-footer">
              <button className="btn btn-ghost" onClick={onClose}>
                Cancel
              </button>
              <button className="btn btn-secondary" onClick={onView}>
                View Result
              </button>
              <button className="btn btn-danger" onClick={onOverwrite}>
                Overwrite
              </button>
            </footer>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
