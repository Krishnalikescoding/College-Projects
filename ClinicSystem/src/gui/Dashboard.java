package gui;

import java.awt.*;
import java.awt.event.*;
import javax.swing.*;

// Main menu. Each button opens one of the other windows.
public class Dashboard extends JFrame {

    JButton patientButton = new JButton("Patient Management");
    JButton doctorButton = new JButton("Doctor Management");
    JButton tokenButton = new JButton("Token Management");
    JButton recordButton = new JButton("Medical Records");
    JButton logoutButton = new JButton("Logout");

    public Dashboard() {
        setTitle("Clinic System - Dashboard");
        setSize(350, 350);
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setLocationRelativeTo(null);

        JPanel panel = new JPanel(new GridLayout(5, 1, 10, 10));
        panel.setBorder(BorderFactory.createEmptyBorder(20, 40, 20, 40));
        panel.add(patientButton);
        panel.add(doctorButton);
        panel.add(tokenButton);
        panel.add(recordButton);
        panel.add(logoutButton);
        add(panel);

        // Each button creates (opens) the matching window
        patientButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                new PatientFrame();
            }
        });

        doctorButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                new DoctorFrame();
            }
        });

        tokenButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                new TokenFrame();
            }
        });

        recordButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                new MedicalRecordFrame();
            }
        });

        // Logout closes the dashboard and goes back to the login screen
        logoutButton.addActionListener(new ActionListener() {
            public void actionPerformed(ActionEvent e) {
                dispose();
                new LoginFrame();
            }
        });

        setVisible(true);
    }
}
