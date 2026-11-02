package dao;

import database.DBConnection;
import model.Token;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;

// TokenDAO contains all database operations for the token table
public class TokenDAO {

    // Create a new token for today and return its token number
    public int generateToken(int patientId, int doctorId) throws SQLException {
        // Get the last token number for today
        // (MAX gives the biggest number; it is NULL, so getInt returns 0, if there is no token today)
        String maxSql = "SELECT MAX(token_number) FROM token WHERE date = CURDATE()";

        // Save the new token. CURDATE() is today's date in MySQL.
        String insertSql = "INSERT INTO token (patient_id, doctor_id, token_number, date, status) "
                         + "VALUES (?, ?, ?, CURDATE(), 'Waiting')";

        int newTokenNumber = 1;

        try (Connection con = DBConnection.getConnection()) {

            PreparedStatement maxStatement = con.prepareStatement(maxSql);
            ResultSet rs = maxStatement.executeQuery();

            int lastTokenNumber = 0;
            if (rs.next()) {
                lastTokenNumber = rs.getInt(1);
            }

            // Increase it by 1 for the new patient.
            // On a new day there are no tokens yet, so the number starts again from 1.
            newTokenNumber = lastTokenNumber + 1;

            PreparedStatement insertStatement = con.prepareStatement(insertSql);
            insertStatement.setInt(1, patientId);
            insertStatement.setInt(2, doctorId);
            insertStatement.setInt(3, newTokenNumber);
            insertStatement.executeUpdate();
        }
        return newTokenNumber;
    }

    // Get all of today's tokens. JOIN connects the token table with the patient and doctor
    // tables using patient_id and doctor_id, so we can show names instead of just numbers.
    public ArrayList<Token> getTodayTokens() throws SQLException {
        String sql = "SELECT t.token_id, t.patient_id, p.name AS patient_name, "
                   + "t.doctor_id, d.name AS doctor_name, t.token_number, t.date, t.status "
                   + "FROM token t "
                   + "JOIN patient p ON t.patient_id = p.patient_id "
                   + "JOIN doctor d ON t.doctor_id = d.doctor_id "
                   + "WHERE t.date = CURDATE() "
                   + "ORDER BY t.token_number";
        ArrayList<Token> tokens = new ArrayList<Token>();

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ResultSet rs = ps.executeQuery();

            while (rs.next()) {
                Token token = new Token(
                        rs.getInt("token_id"),
                        rs.getInt("patient_id"),
                        rs.getString("patient_name"),
                        rs.getInt("doctor_id"),
                        rs.getString("doctor_name"),
                        rs.getInt("token_number"),
                        rs.getString("date"),
                        rs.getString("status"));
                tokens.add(token);
            }
        }
        return tokens;
    }

    // Change the status of a token (Waiting, Completed or Cancelled)
    public void updateStatus(int tokenId, String newStatus) throws SQLException {
        String sql = "UPDATE token SET status = ? WHERE token_id = ?";

        try (Connection con = DBConnection.getConnection();
             PreparedStatement ps = con.prepareStatement(sql)) {

            ps.setString(1, newStatus);
            ps.setInt(2, tokenId);
            ps.executeUpdate();
        }
    }
}
