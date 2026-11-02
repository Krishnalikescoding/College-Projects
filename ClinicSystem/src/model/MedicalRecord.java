package model;

// Stores one medical record (one visit of a patient to a doctor)
public class MedicalRecord {
    private int recordId;
    private int patientId;
    private String patientName;
    private int doctorId;
    private String doctorName;
    private String date;
    private String symptoms;
    private String diagnosis;
    private String prescription;

    // Used when we READ a record from the database (names come from joined tables)
    public MedicalRecord(int recordId, int patientId, String patientName, int doctorId,
                         String doctorName, String date, String symptoms,
                         String diagnosis, String prescription) {
        this.recordId = recordId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.doctorId = doctorId;
        this.doctorName = doctorName;
        this.date = date;
        this.symptoms = symptoms;
        this.diagnosis = diagnosis;
        this.prescription = prescription;
    }

    // Used when we SAVE a new record (record ID is created by MySQL)
    public MedicalRecord(int patientId, int doctorId, String date,
                         String symptoms, String diagnosis, String prescription) {
        this.patientId = patientId;
        this.doctorId = doctorId;
        this.date = date;
        this.symptoms = symptoms;
        this.diagnosis = diagnosis;
        this.prescription = prescription;
    }

    public int getRecordId() { return recordId; }
    public int getPatientId() { return patientId; }
    public String getPatientName() { return patientName; }
    public int getDoctorId() { return doctorId; }
    public String getDoctorName() { return doctorName; }
    public String getDate() { return date; }
    public String getSymptoms() { return symptoms; }
    public String getDiagnosis() { return diagnosis; }
    public String getPrescription() { return prescription; }
}
