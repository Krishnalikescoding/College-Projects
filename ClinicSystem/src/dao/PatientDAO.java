package dao;

import database.DBConnection;
import model.Patient;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

// PatientDAO contains all database operations for the patient table.
// Note: "try (...)" below closes the connection automatically when the work is finished.
// Each method "throws SQLException", so the screen (GUI) decides which error message to show.
public class PatientDAO {

    // Insert a new patient into the database
    public void addPatient(Patient patient) throws SQLException {
        String sql = "INSERT INTO patient (name, age, gender, phone, address) VALUES (?, ?, ?, ?, ?)";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            // PreparedStatement puts the values into the ? marks safely (prevents SQL injection)
            ps.setString(1, patient.getName());
            ps.setInt(2, patient.getAge());
            ps.setString(3, patient.getGender());
            ps.setString(4, patient.getPhone());
            ps.setString(5, patient.getAddress());

            ps.executeUpdate();   // runs INSERT / UPDATE / DELETE queries
        }
    }

    // SQL query to find a patient using their patient ID. Returns null if not found.
    public Patient searchPatient(int patientId) throws SQLException {
        String sql = "SELECT * FROM patient WHERE patient_id = ?";
        Patient patient = null;

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, patientId);
            ResultSet rs = ps.executeQuery();   // runs SELECT queries

            if (rs.next()) {
                patient = makePatient(rs);
            }
        }
        return patient;
    }

    // Find patients whose name contains the given text (LIKE means "similar to")
    public ArrayList<Patient> searchPatientsByName(String name) throws SQLException {
        String sql = "SELECT * FROM patient WHERE name LIKE ? ORDER BY patient_id";
        ArrayList<Patient> patients = new ArrayList<Patient>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, "%" + name + "%");
            ResultSet rs = ps.executeQuery();

            while (rs.next()) {
                patients.add(makePatient(rs));
            }
        }
        return patients;
    }

    // Update the details of an existing patient. Returns false if the patient ID does not exist.
    public boolean updatePatient(Patient patient) throws SQLException {
        String sql = "UPDATE patient SET name = ?, age = ?, gender = ?, phone = ?, address = ? "
                   + "WHERE patient_id = ?";
        int rowsUpdated = 0;

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, patient.getName());
            ps.setInt(2, patient.getAge());
            ps.setString(3, patient.getGender());
            ps.setString(4, patient.getPhone());
            ps.setString(5, patient.getAddress());
            ps.setInt(6, patient.getPatientId());

            rowsUpdated = ps.executeUpdate();   // number of rows that were changed
        }
        return rowsUpdated > 0;
    }

    // Get all patients from the database
    public ArrayList<Patient> getAllPatients() throws SQLException {
        String sql = "SELECT * FROM patient ORDER BY patient_id";
        ArrayList<Patient> patients = new ArrayList<Patient>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ResultSet rs = ps.executeQuery();

            // Each rs.next() moves to the next row of the result
            while (rs.next()) {
                patients.add(makePatient(rs));
            }
        }
        return patients;
    }

    // Small helper: turns the current row of the ResultSet into a Patient object
    private Patient makePatient(ResultSet rs) throws SQLException {
        return new Patient(
                rs.getInt("patient_id"),
                rs.getString("name"),
                rs.getInt("age"),
                rs.getString("gender"),
                rs.getString("phone"),
                rs.getString("address"));
    }
}
