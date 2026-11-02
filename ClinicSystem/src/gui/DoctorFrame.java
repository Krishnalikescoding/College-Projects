package gui;

import dao.DoctorDAO;
import model.Doctor;
import java.awt.*;
import java.awt.event.*;
import java.sql.SQLException;
import java.util.ArrayList;
import javax.swing.*;
import javax.swing.table.DefaultTableModel;

// Screen to add doctors, view doctors and change a doctor's availability
public class DoctorFrame extends JFrame {

    JTextField idField = new JTextField();
    JTextField nameField = new JTextField();
    JTextField specializationField = new JTextField();
    JComboBox<String> availabilityBox = new JComboBox<String>(new String[] {"Available", "Not Available"});

    JTable doctorTable;
    DefaultTableModel tableModel;

    DoctorDAO doctorDAO = new DoctorDAO();

    public DoctorFrame() {
        setTitle("Doctor Management");
        setSize(700, 500);
        setDefaultCloseOperation(JFrame.DISPOSE_ON_CLOSE);
        setLocationRelativeTo(null);
        setLayout(new BorderLayout(10, 10));

        JPanel formPanel = new JPanel(new GridLayout(4, 2, 5, 5));
        formPanel.add(new JLabel("Doctor ID (automatic for new doctors):"));
        formPanel.add(idField);
        formPanel.add(new JLabel("Doctor Name:"));
        formPanel.add(nameField);
        formPanel.add(new JLabel("Specialization:"));
        formPanel.add(specializationField);
        formPanel.add(new JLabel("Availability:"));
        formPanel.add(availabilityBox);

        JButton addButton = new JButton("Add Doctor");
        JButton updateButton = new JButton("Update Availability");
        JButton viewButton = new JButton("View Doctors");
        JButton clearButton = new JButton("Clear");

        JPanel buttonPanel = new JPanel(new FlowLayout());
        buttonPanel.add(addButton);
        buttonPanel.add(updateButton);
        buttonPanel.add(viewButton);
        buttonPanel.add(clearButton);

        JPanel topPanel = new JPanel(new BorderLayout(5, 5));
        topPanel.setBorder(BorderFactory.createEmptyBorder(10, 10, 0, 10));
        topPanel.add(formPanel, BorderLayout.CENTER);
        topPanel.add(buttonPanel, BorderLayout.SOUTH);

        String[] columns = {"Doctor ID", "Name", "Specialization", "Availability"};
        tableModel = new DefaultTableModel(columns, 0);
        doctorTable = new JTable(tableModel);
        doctorTable.setDefaultEditor(Object.class, null);

        add(topPanel, BorderLayout.NORTH);
        add(new JScrollPane(doctorTable), BorderLayout.CENTER);

        addButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                addDoctor();
            }
        });

        updateButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                updateAvailability();
            }
        });

        viewButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                loadDoctors();
            }
        });

        clearButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                clearFields();
            }
        });

        // Clicking a row copies that doctor into the form
        doctorTable.addMouseListener(new MouseAdapter() {
            public void mouseClicked(MouseEvent e) {
                fillFieldsFromTable();
            }
        });

        setVisible(true);
        loadDoctors();
    }

    private void addDoctor() {
        String name = nameField.getText().trim();
        String specialization = specializationField.getText().trim();
        String availability = availabilityBox.getSelectedItem().toString();

        if (name.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter doctor name.");
            return;
        }
        if (specialization.isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please enter specialization.");
            return;
        }

        Doctor doctor = new Doctor(0, name, specialization, availability);

        try {
            doctorDAO.addDoctor(doctor);
            JOptionPane.showMessageDialog(this, "Doctor added successfully.");
            clearFields();
            loadDoctors();
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Change availability of the doctor whose ID is in the Doctor ID field
    private void updateAvailability() {
        if (idField.getText().trim().isEmpty()) {
            JOptionPane.showMessageDialog(this, "Please select a doctor from the table first.");
            return;
        }

        int doctorId = 0;
        try {
            doctorId = Integer.parseInt(idField.getText().trim());
        } catch (NumberFormatException e) {
            JOptionPane.showMessageDialog(this, "Doctor ID must be a number.");
            return;
        }

        String availability = availabilityBox.getSelectedItem().toString();

        try {
            boolean updated = doctorDAO.updateAvailability(doctorId, availability);
            if (updated) {
                JOptionPane.showMessageDialog(this, "Availability updated.");
                loadDoctors();
            } else {
                JOptionPane.showMessageDialog(this, "Doctor not found.");
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    // Get all doctors from the database and show them in the table
    private void loadDoctors() {
        try {
            ArrayList<Doctor> doctors = doctorDAO.getAllDoctors();
            tableModel.setRowCount(0);

            for (int i = 0; i < doctors.size(); i++) {
                Doctor d = doctors.get(i);
                Object[] row = {d.getDoctorId(), d.getName(), d.getSpecialization(), d.getAvailability()};
                tableModel.addRow(row);
            }
        } catch (SQLException e) {
            JOptionPane.showMessageDialog(this, "Database error: " + e.getMessage());
        }
    }

    private void fillFieldsFromTable() {
        int row = doctorTable.getSelectedRow();
        if (row == -1) {
            return;
        }

        idField.setText(tableModel.getValueAt(row, 0).toString());
        nameField.setText(tableModel.getValueAt(row, 1).toString());
        specializationField.setText(tableModel.getValueAt(row, 2).toString());
        availabilityBox.setSelectedItem(tableModel.getValueAt(row, 3).toString());
    }

    private void clearFields() {
        idField.setText("");
        nameField.setText("");
        specializationField.setText("");
        availabilityBox.setSelectedIndex(0);
    }
}
