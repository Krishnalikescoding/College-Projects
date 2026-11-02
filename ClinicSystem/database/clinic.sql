-- Run this file once in MySQL to create the database, tables and sample data
CREATE DATABASE IF NOT EXISTS clinic_system;
USE clinic_system;

-- Staff who can log in
CREATE TABLE IF NOT EXISTS users (
    user_id  INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS patient (
    patient_id INT AUTO_INCREMENT PRIMARY KEY,
    name       VARCHAR(100) NOT NULL,
    age        INT NOT NULL,
    gender     VARCHAR(10) NOT NULL,
    phone      VARCHAR(15) NOT NULL,
    address    VARCHAR(200) NOT NULL
);

CREATE TABLE IF NOT EXISTS doctor (
    doctor_id      INT AUTO_INCREMENT PRIMARY KEY,
    name           VARCHAR(100) NOT NULL,
    specialization VARCHAR(100) NOT NULL,
    availability   VARCHAR(20) NOT NULL DEFAULT 'Available'
);

-- One row per token. patient_id and doctor_id link this table to the other tables.
CREATE TABLE IF NOT EXISTS token (
    token_id     INT AUTO_INCREMENT PRIMARY KEY,
    patient_id   INT NOT NULL,
    doctor_id    INT NOT NULL,
    token_number INT NOT NULL,
    date         DATE NOT NULL,
    status       VARCHAR(20) NOT NULL DEFAULT 'Waiting',
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctor(doctor_id)
);

CREATE TABLE IF NOT EXISTS medical_record (
    record_id    INT AUTO_INCREMENT PRIMARY KEY,
    patient_id   INT NOT NULL,
    doctor_id    INT NOT NULL,
    date         DATE NOT NULL,
    symptoms     TEXT NOT NULL,
    diagnosis    TEXT NOT NULL,
    prescription TEXT NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES patient(patient_id),
    FOREIGN KEY (doctor_id)  REFERENCES doctor(doctor_id)
);

-- Sample data so you can log in and test immediately
INSERT INTO users (username, password) VALUES ('admin', 'admin123');
INSERT INTO doctor (name, specialization, availability) VALUES
    ('Dr. Mehta', 'General Physician', 'Available'),
    ('Dr. Verma', 'Pediatrics', 'Available');
