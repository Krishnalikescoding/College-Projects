package database;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;

// This class creates the connection between our Java program and MySQL (using JDBC)
public class DBConnection {

    // Change these three values to match your own MySQL setup
    private static final String URL = "jdbc:mysql://localhost:3306/clinic_system";
    private static final String USERNAME = "root";
    private static final String PASSWORD = "dit123";

    // Every DAO calls this method whenever it needs to talk to the database.
    // If the connection fails, SQLException goes back to the screen, which shows an error message.
    public static Connection getConnection() throws SQLException {
        // Connect Java application to the MySQL database
        Connection con = DriverManager.getConnection(URL, USERNAME, PASSWORD);
        return con;
    }
}
