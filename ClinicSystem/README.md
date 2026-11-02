# Clinic Token & Patient Record System

Java + Swing + MySQL + JDBC. No frameworks.

## Setup
1. Install MySQL, then run `database/clinic.sql` (creates `clinic_system` and sample data).
2. Open `src/database/DBConnection.java` and set your MySQL username and password.
3. Download the MySQL Connector/J jar (the JDBC driver) and keep it next to the project.

## Compile and run
Windows:
    javac -d out src/model/*.java src/database/*.java src/dao/*.java src/gui/*.java
    java -cp "out;mysql-connector-j-8.x.x.jar" gui.LoginFrame

Mac / Linux (use `:` instead of `;`):
    java -cp "out:mysql-connector-j-8.x.x.jar" gui.LoginFrame

In Eclipse / IntelliJ / NetBeans: add the connector jar to the project libraries, then run `LoginFrame`.

Sample login: **admin** / **admin123**
