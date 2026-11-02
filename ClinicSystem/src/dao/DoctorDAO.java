package dao;

import database.DBConnection;
import model.Doctor;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

// DoctorDAO contains all database operations for the doctor table
public class DoctorDAO {

    // Insert a new doctor
    public void addDoctor(Doctor doctor) throws SQLException {
        String sql = "INSERT INTO doctor (name, specialization, availability) VALUES (?, ?, ?)";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, doctor.getName());
            ps.setString(2, doctor.getSpecialization());
            ps.setString(3, doctor.getAvailability());
            ps.executeUpdate();
        }
    }

    // Get all doctors from the database
    public ArrayList<Doctor> getAllDoctors() throws SQLException {
        String sql = "SELECT * FROM doctor ORDER BY doctor_id";
        ArrayList<Doctor> doctors = new ArrayList<Doctor>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ResultSet rs = ps.executeQuery();

            while (rs.next()) {
                Doctor doctor = new Doctor(
                        rs.getInt("doctor_id"),
                        rs.getString("name"),
                        rs.getString("specialization"),
                        rs.getString("availability"));
                doctors.add(doctor);
            }
        }
        return doctors;
    }

    // Change the availability of one doctor. Returns false if the doctor ID does not exist.
    public boolean updateAvailability(int doctorId, String availability) throws SQLException {
        String sql = "UPDATE doctor SET availability = ? WHERE doctor_id = ?";
        int rowsUpdated = 0;

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, availability);
            ps.setInt(2, doctorId);
            rowsUpdated = ps.executeUpdate();
        }
        return rowsUpdated > 0;
    }
}
