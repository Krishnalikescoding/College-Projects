package model;

// Stores the data of one doctor (one row of the doctor table)
public class Doctor {
    private int doctorId;
    private String name;
    private String specialization;
    private String availability;

    public Doctor(int doctorId, String name, String specialization, String availability) {
        this.doctorId = doctorId;
        this.name = name;
        this.specialization = specialization;
        this.availability = availability;
    }

    public int getDoctorId() { return doctorId; }
    public String getName() { return name; }
    public String getSpecialization() { return specialization; }
    public String getAvailability() { return availability; }
}
