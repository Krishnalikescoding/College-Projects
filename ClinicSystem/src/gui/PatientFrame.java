package gui;

import dao.PatientDAO;
import model.Patient;
import java.awt.*;
import java.awt.event.*;
import java.sql.SQLException;
import java.util.ArrayList;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;

// Screen to add, search, update and view patients
public class PatientFrame extends JFrame {

    JTextField idField = new JTextField();
    JTextField nameField = new JTextField();
    JTextField ageField = new JTextField();
    JComboBox<String> genderBox = new JComboBox<String>(new String[] {"Male", "Female", "Other"});
    JTextField phoneField = new JTextField();
    JTextField addressField = new JTextField();

    JTable patientTable;
    DefaultTableModel tableModel;

    // The DAO object does all the database work for us
    PatientDAO patientDAO = new PatientDAO();

    public PatientFrame() {
        setTitle("Patient Management");
        setSize(800, 550);
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);   // closes only this window
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        // Form with labels and input fields
        JPanel formPanel = new JPanel(new GridLayout(6, 2, 5, 5));
        formPanel.add(new JLabel("Patient ID (automatic for new patients):"));
        formPanel.add(idField);
        formPanel.add(new JLabel("Name:"));
        formPanel.add(nameField);
        formPanel.add(new JLabel("Age:"));
        formPanel.add(ageField);
        formPanel.add(new JLabel("Gender:"));
        formPanel.add(genderBox);
        formPanel.add(new JLabel("Phone:"));
        formPanel.add(phoneField);
        formPanel.add(new JLabel("Address:"));
        formPanel.add(addressField);

        // Buttons
        JButton addButton = new JButton("Add Patient");
        JButton updateButton = new JButton("Update Patient");
        JButton searchButton = new JButton("Search Patient");
        JButton viewButton = new JButton("View All Patients");
        JButton clearButton = new JButton("Clear");

        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.add(addButton);
        buttonPanel.add(updateButton);
        buttonPanel.add(searchButton);
        buttonPanel.add(viewButton);
        buttonPanel.add(clearButton);

        JPanel topPanel = new JPanel(new BorderLayout(5, 5));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));
        topPanel.add(formPanel, BorderLayout.CENTER);
        topPanel.add(buttonPanel, BorderLayout.SOUTH);

        // Table that shows the patients
        String[] columns = {"Patient ID", "Name", "Age", "Gender", "Phone", "Address"};
        tableModel = new DefaultTableModel(columns, 0);
        patientTable = new JTable(tableModel);
        patientTable.setDefaultEditor(Object.class, null);   // the table cannot be edited by typing

        add(topPanel, BorderLayout.NORTH);
        add(new JScrollPane(patientTable), BorderLayout.CENTER);

        // Button actions
        addButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                addPatient();
            }
        });

        updateButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                updatePatient();
            }
        });

        searchButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                searchPatient();
            }
        });

        viewButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                loadAllPatients();
            }
        });

        clearButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                clearFields();
            }
        });

        // When a row of the table is clicked, copy that patient into the form
        patientTable.addMouseListener(new MouseAdapter() {
            public void mouseClicked(MouseEvent e) {
                fillFieldsFromTable();
            }
        });

        setVisible(true);
        loadAllPatients();
    }

    // Read the form, check it, and save a new patient
    private void addPatient() {
        if (!isInputValid()) {
            return;
        }

        String name = nameField.getText().trim();
        int age = Integer.parseInt(ageField.getText().trim());
        String gender = genderBox.getSelectedItem().toString();
        String phone = phoneField.getText().trim();
        String address = addressField.getText().trim();

        // Patient ID is 0 here because MySQL creates the real ID automatically
        Patient patient = new Patient(0, name, age, gender, phone, address);

        try {
            patientDAO.addPatient(patient);
            JOptionPane.showMessageDialog(this, "Patient added successfully.");
            clearFields();
            loadAllPatients();
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Update the patient whose ID is in the Patient ID field
    private void updatePatient() {
        if (idField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please select a patient from the table (or enter Patient ID) to update.");
            return;
        }

        int patientId = 0;
        try {
            patientId = Integer.parseInt(idField.getText().trim());
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Patient ID must be a number.");
            return;
        }

        if (!isInputValid()) {
            return;
        }

        String name = nameField.getText().trim();
        int age = Integer.parseInt(ageField.getText().trim());
        String gender = genderBox.getSelectedItem().toString();
        String phone = phoneField.getText().trim();
        String address = addressField.getText().trim();

        Patient patient = new Patient(patientId, name, age, gender, phone, address);

        try {
            boolean updated = patientDAO.updatePatient(patient);
            if (updated) {
                JOptionPane.showMessageDialog(this, "Patient updated successfully.");
                loadAllPatients();
            } else {
                JOptionPane.showMessageDialog(this, "Patient not found.");
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Search by Patient ID if it is filled, otherwise search by name
    private void searchPatient() {
        String idText = idField.getText().trim();
        String nameText = nameField.getText().trim();

        try {
            ArrayList<Patient> result = new ArrayList<Patient>();

            if (!idText.isEmpty()) {
                int patientId = Integer.parseInt(idText);
                Patient patient = patientDAO.searchPatient(patientId);
                if (patient != null) {
                    result.add(patient);
                }
            } else if (!nameText.isEmpty()) {
                result = patientDAO.searchPatientsByName(nameText);
            } else {
                JOptionPane.showMessageDialog(this, "Please enter a Patient ID or a Name to search.");
                return;
            }

            if (result.size() == 0) {
                JOptionPane.showMessageDialog(this, "Patient not found.");
            }
            showPatientsInTable(result);

        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Patient ID must be a number.");
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Get all patients from the database and show them in the table
    private void loadAllPatients() {
        try {
            ArrayList<Patient> patients = patientDAO.getAllPatients();
            showPatientsInTable(patients);
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Remove old rows from the table and add one row for every patient in the list
    private void showPatientsInTable(ArrayList<Patient> patients) {
        tableModel.setRowCount(0);

        for (int i = 0; i < patients.size(); i++) {
            Patient p = patients.get(i);
            Object[] row = {p.getPatientId(), p.getName(), p.getAge(),
                            p.getGender(), p.getPhone(), p.getAddress()};
            tableModel.addRow(row);
        }
    }

    // Copy the clicked table row into the input fields
    private void fillFieldsFromTable() {
        int row = patientTable.getSelectedRow();
        if (row == -1) {
            return;
        }

        idField.setText(tableModel.getValueAt(row, 0).toString());
        nameField.setText(tableModel.getValueAt(row, 1).toString());
        ageField.setText(tableModel.getValueAt(row, 2).toString());
        genderBox.setSelectedItem(tableModel.getValueAt(row, 3).toString());
        phoneField.setText(tableModel.getValueAt(row, 4).toString());
        addressField.setText(tableModel.getValueAt(row, 5).toString());
    }

    private void clearFields() {
        idField.setText("");
        nameField.setText("");
        ageField.setText("");
        genderBox.setSelectedIndex(0);
        phoneField.setText("");
        addressField.setText("");
    }

    // Basic validation. Shows a message and returns false if something is wrong.
    private boolean isInputValid() {
        if (nameField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter patient name.");
            return false;
        }

        int age = 0;
        try {
            age = Integer.parseInt(ageField.getText().trim());
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Age must be a number.");
            return false;
        }
        if (age < 0 || age > 120) {
            JOptionPane.showMessageDialog(this, "Please enter a valid age (0 to 120).");
            return false;
        }

        // matches("[0-9]{10}") means: exactly 10 digits and nothing else
        String phone = phoneField.getText().trim();
        if (!phone.matches("[0-9]{10}")) {
            JOptionPane.showMessageDialog(this, "Phone number must contain exactly 10 digits.");
            return false;
        }

        if (addressField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter patient address.");
            return false;
        }

        return true;
    }
}
