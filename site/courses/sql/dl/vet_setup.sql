-- SQL practice: 01_veterinary
-- Dialect: SQL Server (T-SQL); setup and solutions also use SQLite-compatible syntax.
-- Run in a dedicated empty practice database. No existing tables are deleted.
-- Execute each question independently against the initial data.
-- To undo an individual exercise in SQL Server: BEGIN TRANSACTION; ... ROLLBACK;

CREATE TABLE Pets (
    PetID VARCHAR(4) PRIMARY KEY,
    PetName VARCHAR(30) NOT NULL,
    Species VARCHAR(20) NOT NULL,
    OwnerPhone VARCHAR(20)
);
INSERT INTO Pets (PetID, PetName, Species, OwnerPhone) VALUES
('P101', 'Luna', 'Cat', '0501111111'),
('P102', 'Rex', 'Dog', '0502222222'),
('P103', 'Milo', 'Cat', NULL),
('P104', 'Bella', 'Dog', '0504444444'),
('P105', 'Kiwi', 'Bird', '0505555555'),
('P106', 'Nala', 'Cat', '0506666666');

CREATE TABLE Treatments (
    TreatmentID VARCHAR(4) PRIMARY KEY,
    TreatmentName VARCHAR(40) NOT NULL,
    StandardFee DECIMAL(8,2) NOT NULL
);
INSERT INTO Treatments (TreatmentID, TreatmentName, StandardFee) VALUES
('T01', 'Vaccination', 120),
('T02', 'Dental Cleaning', 450),
('T03', 'Checkup', 180),
('T04', 'X-Ray', 350);

CREATE TABLE Visits (
    VisitID INT PRIMARY KEY,
    PetID VARCHAR(4) NOT NULL REFERENCES Pets(PetID),
    TreatmentID VARCHAR(4) NOT NULL REFERENCES Treatments(TreatmentID),
    VisitDate DATE NOT NULL,
    PaidAmount DECIMAL(8,2)
);
INSERT INTO Visits (VisitID, PetID, TreatmentID, VisitDate, PaidAmount) VALUES
(1, 'P101', 'T01', '2026-09-01', 120),
(2, 'P102', 'T02', '2026-09-02', 450),
(3, 'P101', 'T03', '2026-09-03', 180),
(4, 'P103', 'T03', '2026-09-04', NULL),
(5, 'P104', 'T04', '2026-09-05', 300),
(6, 'P102', 'T01', '2026-09-06', 120),
(7, 'P105', 'T03', '2026-09-07', 180),
(8, 'P104', 'T03', '2026-09-08', 150);
