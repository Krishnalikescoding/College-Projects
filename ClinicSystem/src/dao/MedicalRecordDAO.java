package dao;

import database.DBConnection;
import model.MedicalRecord;
import java.sql.Connection;
import java.sql.Date;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

// MedicalRecordDAO contains all database operations for the medical_record table
public class MedicalRecordDAO {

    // Save a new medical record
    public void addRecord(MedicalRecord record) throws SQLException {
        String sql = "INSERT INTO medical_record (patient_id, doctor_id, date, symptoms, diagnosis, prescription) "
                   + "VALUES (?, ?, ?, ?, ?, ?)";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, record.getPatientId());
            ps.setInt(2, record.getDoctorId());
            ps.setDate(3, Date.valueOf(record.getDate()));   // text "2026-10-24" -> SQL date
            ps.setString(4, record.getSymptoms());
            ps.setString(5, record.getDiagnosis());
            ps.setString(6, record.getPrescription());
            ps.executeUpdate();
        }
    }

    // Get the medical history of ONE patient (newest visit first).
    // patient_id in medical_record is connected to patient_id in the patient table.
    public ArrayList<MedicalRecord> getRecordsByPatient(int patientId) throws SQLException {
        String sql = "SELECT r.record_id, r.patient_id, p.name AS patient_name, "
                   + "r.doctor_id, d.name AS doctor_name, "
                   + "DATE_FORMAT(r.date, '%d/%m/%Y') AS record_date, "
                   + "r.symptoms, r.diagnosis, r.prescription "
                   + "FROM medical_record r "
                   + "JOIN patient p ON r.patient_id = p.patient_id "
                   + "JOIN doctor d ON r.doctor_id = d.doctor_id "
                   + "WHERE r.patient_id = ? "
                   + "ORDER BY r.date DESC, r.record_id DESC";
        ArrayList<MedicalRecord> records = new ArrayList<MedicalRecord>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setInt(1, patientId);
            ResultSet rs = ps.executeQuery();

            while (rs.next()) {
                records.add(makeRecord(rs));
            }
        }
        return records;
    }

    // Get all medical records of all patients
    public ArrayList<MedicalRecord> getAllRecords() throws SQLException {
        String sql = "SELECT r.record_id, r.patient_id, p.name AS patient_name, "
                   + "r.doctor_id, d.name AS doctor_name, "
                   + "DATE_FORMAT(r.date, '%d/%m/%Y') AS record_date, "
                   + "r.symptoms, r.diagnosis, r.prescription "
                   + "FROM medical_record r "
                   + "JOIN patient p ON r.patient_id = p.patient_id "
                   + "JOIN doctor d ON r.doctor_id = d.doctor_id "
                   + "ORDER BY r.date DESC, r.record_id DESC";
        ArrayList<MedicalRecord> records = new ArrayList<MedicalRecord>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ResultSet rs = ps.executeQuery();

            while (rs.next()) {
                records.add(makeRecord(rs));
            }
        }
        return records;
    }

    // Small helper: turns the current row of the ResultSet into a MedicalRecord object
    private MedicalRecord makeRecord(ResultSet rs) throws SQLException {
        return new MedicalRecord(
                rs.getInt("record_id"),
                rs.getInt("patient_id"),
                rs.getString("patient_name"),
                rs.getInt("doctor_id"),
                rs.getString("doctor_name"),
                rs.getString("record_date"),
                rs.getString("symptoms"),
                rs.getString("diagnosis"),
                rs.getString("prescription")
            );
    }
}
