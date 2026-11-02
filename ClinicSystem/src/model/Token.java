package model;

// Stores one token. We also keep the patient name and doctor name
// (taken from the other tables) so the screen can show them in the table.
public class Token {
    private int tokenId;
    private int patientId;
    private String patientName;
    private int doctorId;
    private String doctorName;
    private int tokenNumber;
    private String date;
    private String status;

    public Token(int tokenId, int patientId, String patientName, int doctorId,
                 String doctorName, int tokenNumber, String date, String status) {
        this.tokenId = tokenId;
        this.patientId = patientId;
        this.patientName = patientName;
        this.doctorId = doctorId;
        this.doctorName = doctorName;
        this.tokenNumber = tokenNumber;
        this.date = date;
        this.status = status;
    }

    public int getTokenId() { return tokenId; }
    public int getPatientId() { return patientId; }
    public String getPatientName() { return patientName; }
    public int getDoctorId() { return doctorId; }
    public String getDoctorName() { return doctorName; }
    public int getTokenNumber() { return tokenNumber; }
    public String getDate() { return date; }
    public String getStatus() { return status; }
}
