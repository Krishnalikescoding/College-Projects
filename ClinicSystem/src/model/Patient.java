package model;

// Stores the data of one patient (one row of the patient table)
public class Patient {
    private int patientId;
    private String name;
    private int age;
    private String gender;
    private String phone;
    private String address;

    public Patient(int patientId, String name, int age, String gender, String phone, String address) {
        this.patientId = patientId;
        this.name = name;
        this.age = age;
        this.gender = gender;
        this.phone = phone;
        this.address = address;
    }

    public int getPatientId() { return patientId; }
    public String getName() { return name; }
    public int getAge() { return age; }
    public String getGender() { return gender; }
    public String getPhone() { return phone; }
    public String getAddress() { return address; }
}
