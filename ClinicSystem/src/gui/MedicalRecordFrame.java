package gui;

import dao.DoctorDAO;
import dao.MedicalRecordDAO;
import dao.PatientDAO;
import model.Doctor;
import model.MedicalRecord;
import model.Patient;
import java.awt.*;
import java.awt.event.*;
import java.sql.SQLException;
import java.time.LocalDate;
import java.util.ArrayList;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;

// Screen to save medical records and to see the medical history of a patient
public class MedicalRecordFrame extends JFrame {

    JTextField recordIdField = new JTextField();
    JTextField patientIdField = new JTextField();
    JComboBox<String> doctorBox = new JComboBox<String>();
    JTextField dateField = new JTextField(LocalDate.now().toString());   // today, like 2026-10-24
    JTextField symptomsField = new JTextField();
    JTextField diagnosisField = new JTextField();
    JTextField prescriptionField = new JTextField();

    JLabel historyLabel = new JLabel("Showing: all medical records");
    JTable recordTable;
    DefaultTableModel tableModel;

    ArrayList<Doctor> doctorList = new ArrayList<Doctor>();

    PatientDAO patientDAO = new PatientDAO();
    DoctorDAO doctorDAO = new DoctorDAO();
    MedicalRecordDAO recordDAO = new MedicalRecordDAO();

    public MedicalRecordFrame() {
        setTitle("Medical Records");
        setSize(950, 650);
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        recordIdField.setEditable(false);   // the record ID is created by MySQL

        JPanel formPanel = new JPanel(new GridLayout(7, 2, 5, 5));
        formPanel.add(new JLabel("Record ID (automatic):"));
        formPanel.add(recordIdField);
        formPanel.add(new JLabel("Patient ID:"));
        formPanel.add(patientIdField);
        formPanel.add(new JLabel("Doctor:"));
        formPanel.add(doctorBox);
        formPanel.add(new JLabel("Date (yyyy-mm-dd):"));
        formPanel.add(dateField);
        formPanel.add(new JLabel("Symptoms:"));
        formPanel.add(symptomsField);
        formPanel.add(new JLabel("Diagnosis:"));
        formPanel.add(diagnosisField);
        formPanel.add(new JLabel("Prescription:"));
        formPanel.add(prescriptionField);

        JButton saveButton = new JButton("Save Record");
        JButton searchButton = new JButton("Search by Patient ID");
        JButton viewAllButton = new JButton("View All Records");
        JButton clearButton = new JButton("Clear");

        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.add(saveButton);
        buttonPanel.add(searchButton);
        buttonPanel.add(viewAllButton);
        buttonPanel.add(clearButton);

        JPanel topPanel = new JPanel(new BorderLayout(5, 5));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));
        topPanel.add(formPanel, BorderLayout.CENTER);
        topPanel.add(buttonPanel, BorderLayout.SOUTH);

        String[] columns = {"Record ID", "Date", "Patient", "Doctor", "Symptoms", "Diagnosis", "Prescription"};
        tableModel = new DefaultTableModel(columns, 0);
        recordTable = new JTable(tableModel);
        recordTable.setDefaultEditor(Object.class, null);

        JPanel centerPanel = new JPanel(new BorderLayout(5, 5));
        centerPanel.setBorder(BorderFactory.createEmptyBorder(0, 10, 10, 10));
        centerPanel.add(historyLabel, BorderLayout.NORTH);
        centerPanel.add(new JScrollPane(recordTable), BorderLayout.CENTER);

        add(topPanel, BorderLayout.NORTH);
        add(centerPanel, BorderLayout.CENTER);

        saveButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                saveRecord();
            }
        });

        searchButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                searchHistory();
            }
        });

        viewAllButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                loadAllRecords();
            }
        });

        clearButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                clearFields();
            }
        });

        setVisible(true);
        loadDoctors();
        loadAllRecords();
    }

    // Check the form and save a new medical record
    private void saveRecord() {
        String idText = patientIdField.getText().trim();
        if (idText.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter Patient ID.");
            return;
        }

        int patientId = 0;
        try {
            patientId = Integer.parseInt(idText);
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Patient ID must be a number.");
            return;
        }

        if (doctorList.size() == 0) {
            JOptionPane.showMessageDialog(this, "No doctors found. Please add a doctor first.");
            return;
        }
        Doctor doctor = doctorList.get(doctorBox.getSelectedIndex());

        // Check that the date is written like 2026-10-24
        String date = dateField.getText().trim();
        try {
            java.sql.Date.valueOf(date);
        } catch (IllegalArgumentException e) {
            JOptionPane.showMessageDialog(this, "Please enter the date as yyyy-mm-dd, for example 2026-10-24.");
            return;
        }

        String symptoms = symptomsField.getText().trim();
        String diagnosis = diagnosisField.getText().trim();
        String prescription = prescriptionField.getText().trim();

        if (symptoms.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter symptoms.");
            return;
        }
        if (diagnosis.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter diagnosis.");
            return;
        }

        try {
            // Make sure the patient exists
            Patient patient = patientDAO.searchPatient(patientId);
            if (patient == null) {
                JOptionPane.showMessageDialog(this, "Patient not found.");
                return;
            }

            MedicalRecord record = new MedicalRecord(patientId, doctor.getDoctorId(),
                    date, symptoms, diagnosis, prescription);
            recordDAO.addRecord(record);

            JOptionPane.showMessageDialog(this, "Medical record saved for " + patient.getName() + ".");

            // Show this patient's history, which now includes the new record
            showHistory(patient);
            symptomsField.setText("");
            diagnosisField.setText("");
            prescriptionField.setText("");
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Search the medical history of the patient whose ID is typed in the Patient ID field
    private void searchHistory() {
        String idText = patientIdField.getText().trim();
        if (idText.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter Patient ID to search.");
            return;
        }

        int patientId = 0;
        try {
            patientId = Integer.parseInt(idText);
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Patient ID must be a number.");
            return;
        }

        try {
            Patient patient = patientDAO.searchPatient(patientId);
            if (patient == null) {
                JOptionPane.showMessageDialog(this, "Patient not found.");
                return;
            }
            showHistory(patient);
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Show all records of one patient (their medical history) in the table
    private void showHistory(Patient patient) throws SQLException {
        ArrayList<MedicalRecord> records = recordDAO.getRecordsByPatient(patient.getPatientId());
        historyLabel.setText("Medical history of: " + patient.getName() + " (ID " + patient.getPatientId() + ")");
        showRecordsInTable(records);

        if (records.size() == 0) {
            JOptionPane.showMessageDialog(this, "No medical records found for this patient.");
        }
    }

    private void loadAllRecords() {
        try {
            ArrayList<MedicalRecord> records = recordDAO.getAllRecords();
            historyLabel.setText("Showing: all medical records");
            showRecordsInTable(records);
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Remove old rows from the table and add one row for every record in the list
    private void showRecordsInTable(ArrayList<MedicalRecord> records) {
        tableModel.setRowCount(0);

        for (int i = 0; i < records.size(); i++) {
            MedicalRecord r = records.get(i);
            Object[] row = {r.getRecordId(), r.getDate(), r.getPatientName(), r.getDoctorName(),
                            r.getSymptoms(), r.getDiagnosis(), r.getPrescription()};
            tableModel.addRow(row);
        }
    }

    // Fill the doctor combo box from the database
    private void loadDoctors() {
        try {
            doctorList = doctorDAO.getAllDoctors();
            doctorBox.removeAllItems();

            for (int i = 0; i < doctorList.size(); i++) {
                Doctor d = doctorList.get(i);
                doctorBox.addItem(d.getName() + " (" + d.getSpecialization() + ")");
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    private void clearFields() {
        recordIdField.setText("");
        patientIdField.setText("");
        dateField.setText(LocalDate.now().toString());
        symptomsField.setText("");
        diagnosisField.setText("");
        prescriptionField.setText("");
    }
}
