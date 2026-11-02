package gui;

import dao.DoctorDAO;
import dao.PatientDAO;
import dao.TokenDAO;
import model.Doctor;
import model.Patient;
import model.Token;
import java.awt.*;
import java.awt.event.*;
import java.sql.SQLException;
import java.util.ArrayList;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;

// Screen to generate tokens and manage today's patient queue
public class TokenFrame extends JFrame {

    JTextField patientIdField = new JTextField(10);
    JComboBox<String> doctorBox = new JComboBox<String>();

    JTable tokenTable;
    DefaultTableModel tableModel;

    // These lists keep the same order as the combo box / table rows,
    // so row number 2 in the table is tokenList.get(2)
    ArrayList<Doctor> doctorList = new ArrayList<Doctor>();
    ArrayList<Token> tokenList = new ArrayList<Token>();

    PatientDAO patientDAO = new PatientDAO();
    DoctorDAO doctorDAO = new DoctorDAO();
    TokenDAO tokenDAO = new TokenDAO();

    public TokenFrame() {
        setTitle("Token Management");
        setSize(850, 520);
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        // First row: patient ID and doctor selection
        JPanel inputPanel = new JPanel(new FlowLayout());
        inputPanel.add(new JLabel("Patient ID:"));
        inputPanel.add(patientIdField);
        inputPanel.add(new JLabel("Doctor:"));
        inputPanel.add(doctorBox);

        // Second row: buttons
        JButton generateButton = new JButton("Generate Token");
        JButton callNextButton = new JButton("Call Next Patient");
        JButton completeButton = new JButton("Complete Token");
        JButton cancelButton = new JButton("Cancel Token");
        JButton refreshButton = new JButton("Refresh");

        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.add(generateButton);
        buttonPanel.add(callNextButton);
        buttonPanel.add(completeButton);
        buttonPanel.add(cancelButton);
        buttonPanel.add(refreshButton);

        JPanel topPanel = new JPanel(new GridLayout(2, 1));
        topPanel.add(inputPanel);
        topPanel.add(buttonPanel);

        String[] columns = {"Token", "Patient ID", "Patient", "Doctor", "Date", "Status"};
        tableModel = new DefaultTableModel(columns, 0);
        tokenTable = new JTable(tableModel);
        tokenTable.setDefaultEditor(Object.class, null);

        JScrollPane scrollPane = new JScrollPane(tokenTable);
        scrollPane.setBorder(BorderFactory.createTitledBorder("Today's Tokens"));

        add(topPanel, BorderLayout.NORTH);
        add(scrollPane, BorderLayout.CENTER);

        generateButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                generateToken();
            }
        });

        callNextButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                callNextPatient();
            }
        });

        completeButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                changeStatus("Completed");
            }
        });

        cancelButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                changeStatus("Cancelled");
            }
        });

        refreshButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                loadDoctors();
                loadTokens();
            }
        });

        setVisible(true);
        loadDoctors();
        loadTokens();
    }

    // Generate a new token for the patient and doctor that were selected
    private void generateToken() {
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

        // The selected position in the combo box is the same position in doctorList
        Doctor doctor = doctorList.get(doctorBox.getSelectedIndex());
        if (!doctor.getAvailability().equals("Available")) {
            JOptionPane.showMessageDialog(this, "This doctor is not available. Please select another doctor.");
            return;
        }

        try {
            // Make sure the patient exists before creating a token
            Patient patient = patientDAO.searchPatient(patientId);
            if (patient == null) {
                JOptionPane.showMessageDialog(this, "Patient not found. Please register the patient first.");
                return;
            }

            int tokenNumber = tokenDAO.generateToken(patientId, doctor.getDoctorId());
            JOptionPane.showMessageDialog(this, "Token " + tokenNumber + " generated for " + patient.getName() + ".");

            patientIdField.setText("");
            loadTokens();
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Token generation error: " + e.getMessage());
        }
    }

    // Find the first token (lowest number) that is still Waiting and select it in the table
    private void callNextPatient() {
        for (int i = 0; i < tokenList.size(); i++) {
            Token token = tokenList.get(i);

            if (token.getStatus().equals("Waiting")) {
                tokenTable.setRowSelectionInterval(i, i);   // highlight this row
                JOptionPane.showMessageDialog(this, "Now calling token " + token.getTokenNumber()
                        + ": " + token.getPatientName() + " (" + token.getDoctorName() + ")");
                return;
            }
        }
        JOptionPane.showMessageDialog(this, "No patients are waiting.");
    }

    // Used by both the Complete and Cancel buttons
    private void changeStatus(String newStatus) {
        int row = tokenTable.getSelectedRow();
        if (row == -1) {
            JOptionPane.showMessageDialog(this, "Please select a token from the table first.");
            return;
        }

        Token token = tokenList.get(row);
        if (!token.getStatus().equals("Waiting")) {
            JOptionPane.showMessageDialog(this, "Only tokens with status Waiting can be changed.");
            return;
        }

        try {
            tokenDAO.updateStatus(token.getTokenId(), newStatus);
            loadTokens();
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
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

    // Show today's tokens in the table
    private void loadTokens() {
        try {
            tokenList = tokenDAO.getTodayTokens();
            tableModel.setRowCount(0);

            for (int i = 0; i < tokenList.size(); i++) {
                Token t = tokenList.get(i);
                // %03d shows the number with 3 digits, for example 1 becomes 001
                String tokenText = String.format("%03d", t.getTokenNumber());
                Object[] row = {tokenText, t.getPatientId(), t.getPatientName(),
                                t.getDoctorName(), t.getDate(), t.getStatus()};
                tableModel.addRow(row);
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }
}
