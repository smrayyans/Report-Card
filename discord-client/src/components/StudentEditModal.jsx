import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

const modalVariants = {
    hidden: { opacity: 0, scale: 0.95 },
    visible: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
};

const backdropVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
    exit: { opacity: 0 },
};

const statusOptions = ['Active', 'Left', 'Inactive'];

export default function StudentEditModal({
    open,
    student,
    onClose,
    onSave,
    loading,
    onDelete,
    deleteLoading,
}) {
    const [formData, setFormData] = useState({
        student_name: '',
        father_name: '',
        current_class_sec: '',
        current_session: '',
        status: 'Active',
        date_of_birth: '',
        joining_date: '',
        left_date: '',
        left_reason: '',
        contact_number_resident: '',
        contact_number_neighbour: '',
        contact_number_relative: '',
        contact_number_other1: '',
        contact_number_other2: '',
        contact_number_other3: '',
        contact_number_other4: '',
        address: '',
    });

    const [errors, setErrors] = useState({});

    useEffect(() => {
        if (student) {
            setFormData({
                student_name: student.student_name || '',
                father_name: student.father_name || '',
                current_class_sec: student.current_class_sec || '',
                current_session: student.current_session || '',
                status: student.status || 'Active',
                date_of_birth: student.date_of_birth || '',
                joining_date: student.joining_date || '',
                left_date: student.left_date || '',
                left_reason: student.left_reason || '',
                contact_number_resident: student.contact_number_resident || '',
                contact_number_neighbour: student.contact_number_neighbour || '',
                contact_number_relative: student.contact_number_relative || '',
                contact_number_other1: student.contact_number_other1 || '',
                contact_number_other2: student.contact_number_other2 || '',
                contact_number_other3: student.contact_number_other3 || '',
                contact_number_other4: student.contact_number_other4 || '',
                address: student.address || '',
            });
            setErrors({});
        }
    }, [student]);

    useEffect(() => {
        if (open) {
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
    }, [open]);

    const handleChange = (field, value) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
        // Clear error for this field
        if (errors[field]) {
            setErrors((prev) => ({ ...prev, [field]: null }));
        }
    };

    const validate = () => {
        const newErrors = {};

        if (!formData.student_name?.trim()) {
            newErrors.student_name = 'Student name is required';
        }

        if (!formData.father_name?.trim()) {
            newErrors.father_name = 'Father name is required';
        }

        if (!formData.current_class_sec?.trim()) {
            newErrors.current_class_sec = 'Class/Section is required';
        }

        if (formData.status === 'Left') {
            if (!formData.left_date?.trim()) {
                newErrors.left_date = 'Left date is required when status is Left';
            }
        }

        setErrors(newErrors);
        return Object.keys(newErrors).length === 0;
    };

    const handleSubmit = (e) => {
        e.preventDefault();
        if (validate()) {
            // Only send fields that have changed
            const updates = {};
            Object.keys(formData).forEach((key) => {
                if (formData[key] !== (student[key] || '')) {
                    updates[key] = formData[key];
                }
            });

            onSave(updates);
        }
    };

    if (!open) return null;

    return (
        <AnimatePresence>
            {open && (
                <div style={{ position: 'fixed', inset: 0, display: 'grid', placeItems: 'center', overflow: 'hidden', zIndex: 20 }}>
                    <motion.div
                        className="modal-backdrop"
                        variants={backdropVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        transition={{ duration: 0.2 }}
                        onClick={onClose}
                    />
                    <motion.div
                        className="modal-panel student-edit-modal"
                        variants={modalVariants}
                        initial="hidden"
                        animate="visible"
                        exit="exit"
                        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <div className="modal-header">
                            <div>
                                <h2>Edit Student Details</h2>
                                <p className="muted">G.R No: {student?.gr_no}</p>
                            </div>
                            <button className="btn btn-text" onClick={onClose} disabled={loading}>
                                Close
                            </button>
                        </div>

                        <form onSubmit={handleSubmit} className="modal-content">
                            {/* Basic Information */}
                            <section className="form-section">
                                <h3>Basic Information</h3>
                                <div className="form-grid">
                                    <div className="form-field">
                                        <label htmlFor="student_name">
                                            Student Name <span className="required">*</span>
                                        </label>
                                        <input
                                            id="student_name"
                                            type="text"
                                            className={`input ${errors.student_name ? 'input-error' : ''}`}
                                            value={formData.student_name}
                                            onChange={(e) => handleChange('student_name', e.target.value)}
                                            disabled={loading}
                                        />
                                        {errors.student_name && <span className="error-text">{errors.student_name}</span>}
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="father_name">
                                            Father Name <span className="required">*</span>
                                        </label>
                                        <input
                                            id="father_name"
                                            type="text"
                                            className={`input ${errors.father_name ? 'input-error' : ''}`}
                                            value={formData.father_name}
                                            onChange={(e) => handleChange('father_name', e.target.value)}
                                            disabled={loading}
                                        />
                                        {errors.father_name && <span className="error-text">{errors.father_name}</span>}
                                    </div>
                                </div>
                            </section>

                            {/* Academic Details */}
                            <section className="form-section">
                                <h3>Academic Details</h3>
                                <div className="form-grid">
                                    <div className="form-field">
                                        <label htmlFor="current_class_sec">
                                            Class/Section <span className="required">*</span>
                                        </label>
                                        <input
                                            id="current_class_sec"
                                            type="text"
                                            className={`input ${errors.current_class_sec ? 'input-error' : ''}`}
                                            value={formData.current_class_sec}
                                            onChange={(e) => handleChange('current_class_sec', e.target.value)}
                                            disabled={loading}
                                        />
                                        {errors.current_class_sec && <span className="error-text">{errors.current_class_sec}</span>}
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="current_session">Current Session</label>
                                        <input
                                            id="current_session"
                                            type="text"
                                            className="input"
                                            value={formData.current_session}
                                            onChange={(e) => handleChange('current_session', e.target.value)}
                                            placeholder="e.g., 2024-2025"
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="status">Status</label>
                                        <select
                                            id="status"
                                            className="input"
                                            value={formData.status}
                                            onChange={(e) => handleChange('status', e.target.value)}
                                            disabled={loading}
                                        >
                                            {statusOptions.map((status) => (
                                                <option key={status} value={status}>
                                                    {status}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                </div>
                            </section>

                            {/* Timeline */}
                            <section className="form-section">
                                <h3>Timeline</h3>
                                <div className="form-grid">
                                    <div className="form-field">
                                        <label htmlFor="date_of_birth">Date of Birth</label>
                                        <input
                                            id="date_of_birth"
                                            type="date"
                                            className="input"
                                            value={formData.date_of_birth}
                                            onChange={(e) => handleChange('date_of_birth', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="joining_date">Joining Date</label>
                                        <input
                                            id="joining_date"
                                            type="date"
                                            className="input"
                                            value={formData.joining_date}
                                            onChange={(e) => handleChange('joining_date', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    {formData.status === 'Left' && (
                                        <>
                                            <div className="form-field">
                                                <label htmlFor="left_date">
                                                    Left Date {formData.status === 'Left' && <span className="required">*</span>}
                                                </label>
                                                <input
                                                    id="left_date"
                                                    type="date"
                                                    className={`input ${errors.left_date ? 'input-error' : ''}`}
                                                    value={formData.left_date}
                                                    onChange={(e) => handleChange('left_date', e.target.value)}
                                                    disabled={loading}
                                                />
                                                {errors.left_date && <span className="error-text">{errors.left_date}</span>}
                                            </div>

                                            <div className="form-field">
                                                <label htmlFor="left_reason">Left Reason</label>
                                                <input
                                                    id="left_reason"
                                                    type="text"
                                                    className="input"
                                                    value={formData.left_reason}
                                                    onChange={(e) => handleChange('left_reason', e.target.value)}
                                                    placeholder="Reason for leaving"
                                                    disabled={loading}
                                                />
                                            </div>
                                        </>
                                    )}
                                </div>
                            </section>

                            {/* Contact Information */}
                            <section className="form-section">
                                <h3>Contact Information</h3>
                                <div className="form-grid">
                                    <div className="form-field">
                                        <label htmlFor="contact_number_resident">Resident Contact</label>
                                        <input
                                            id="contact_number_resident"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_resident}
                                            onChange={(e) => handleChange('contact_number_resident', e.target.value)}
                                            placeholder="Primary contact number"
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_neighbour">Neighbour Contact</label>
                                        <input
                                            id="contact_number_neighbour"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_neighbour}
                                            onChange={(e) => handleChange('contact_number_neighbour', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_relative">Relative Contact</label>
                                        <input
                                            id="contact_number_relative"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_relative}
                                            onChange={(e) => handleChange('contact_number_relative', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_other1">Other Contact 1</label>
                                        <input
                                            id="contact_number_other1"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_other1}
                                            onChange={(e) => handleChange('contact_number_other1', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_other2">Other Contact 2</label>
                                        <input
                                            id="contact_number_other2"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_other2}
                                            onChange={(e) => handleChange('contact_number_other2', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_other3">Other Contact 3</label>
                                        <input
                                            id="contact_number_other3"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_other3}
                                            onChange={(e) => handleChange('contact_number_other3', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>

                                    <div className="form-field">
                                        <label htmlFor="contact_number_other4">Other Contact 4</label>
                                        <input
                                            id="contact_number_other4"
                                            type="text"
                                            className="input"
                                            value={formData.contact_number_other4}
                                            onChange={(e) => handleChange('contact_number_other4', e.target.value)}
                                            disabled={loading}
                                        />
                                    </div>
                                </div>
                            </section>

                            {/* Address */}
                            <section className="form-section">
                                <h3>Address</h3>
                                <div className="form-field">
                                    <label htmlFor="address">Full Address</label>
                                    <textarea
                                        id="address"
                                        className="input textarea"
                                        value={formData.address}
                                        onChange={(e) => handleChange('address', e.target.value)}
                                        rows={3}
                                        placeholder="Complete residential address"
                                        disabled={loading}
                                    />
                                </div>
                            </section>

                            {/* Actions */}
                            <div className="modal-actions modal-actions--split">
                                <div className="modal-actions__support">
                                    <button
                                        type="button"
                                        className="btn btn-secondary"
                                        onClick={onClose}
                                        disabled={loading || deleteLoading}
                                    >
                                        Cancel
                                    </button>
                                    {onDelete && (
                                        <button
                                            type="button"
                                            className="btn btn-danger"
                                            onClick={onDelete}
                                            disabled={loading || deleteLoading}
                                        >
                                            {deleteLoading ? 'Deleting...' : 'Delete Student'}
                                        </button>
                                    )}
                                </div>
                                <button type="submit" className="btn btn-primary" disabled={loading || deleteLoading}>
                                    {loading ? 'Saving...' : 'Save Changes'}
                                </button>
                            </div>
                        </form>
                    </motion.div>
                </div>
            )}
        </AnimatePresence>
    );
}
