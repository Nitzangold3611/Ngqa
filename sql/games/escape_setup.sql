-- NGQA SQL escape room: "The Missing Diamond" (היהלום שנעלם)
-- Dialect: SQL Server (T-SQL). Run in a dedicated empty practice database.
-- Tables: Halls, Exhibits, Staff, AccessLog
-- Date-times are written as 'YYYY-MM-DDThh:mm:ss' (ISO 8601), which SQL Server reads the same way under any language setting.

CREATE TABLE Halls (
    HallID VARCHAR(4) PRIMARY KEY,
    HallName VARCHAR(30) NOT NULL,
    FloorNumber INT NOT NULL
);
INSERT INTO Halls (HallID, HallName, FloorNumber) VALUES
('H1', 'Entrance', 0),
('H2', 'Gems', 1),
('H3', 'Paintings', 1),
('H4', 'Sculptures', 0),
('H5', 'Archive', -1);

CREATE TABLE Exhibits (
    ExhibitID INT PRIMARY KEY,
    Title VARCHAR(40) NOT NULL,
    HallID VARCHAR(4) NOT NULL REFERENCES Halls(HallID),
    InsuranceValue INT NOT NULL,
    Status VARCHAR(15) NOT NULL
);
INSERT INTO Exhibits (ExhibitID, Title, HallID, InsuranceValue, Status) VALUES
(1, 'Blue Star Diamond', 'H2', 4200000, 'Missing'),
(2, 'Ruby Crown', 'H2', 1800000, 'OnDisplay'),
(3, 'Night Harbor', 'H3', 650000, 'OnDisplay'),
(4, 'Golden Owl', 'H2', 920000, 'OnDisplay'),
(5, 'Marble Runner', 'H4', 300000, 'OnDisplay'),
(6, 'Old Map', 'H5', 45000, 'Storage'),
(7, 'Emerald Ring', 'H2', 760000, 'Restoration'),
(8, 'Sunset Field', 'H3', 410000, 'OnDisplay');

CREATE TABLE Staff (
    StaffID VARCHAR(4) PRIMARY KEY,
    FirstName VARCHAR(20) NOT NULL,
    LastName VARCHAR(20) NOT NULL,
    Department VARCHAR(20) NOT NULL,
    JobTitle VARCHAR(20) NOT NULL,
    HireDate DATE NOT NULL,
    Salary INT NOT NULL
);
INSERT INTO Staff (StaffID, FirstName, LastName, Department, JobTitle, HireDate, Salary) VALUES
('S01', 'Dana', 'Cohen', 'Security', 'Guard', '2019-03-01', 9800),
('S02', 'Avi', 'Levi', 'Security', 'Guard', '2023-06-15', 9200),
('S03', 'Maya', 'Klein', 'Curatorial', 'Curator', '2015-09-01', 16500),
('S04', 'Ron', 'Azulai', 'Maintenance', 'Technician', '2021-01-10', 10400),
('S05', 'Lior', 'Ben-David', 'Security', 'ShiftManager', '2018-11-20', 13900),
('S06', 'Noa', 'Shapiro', 'Curatorial', 'Restorer', '2024-02-01', 12800),
('S07', 'Eitan', 'Mor', 'IT', 'SysAdmin', '2022-08-08', 17200),
('S08', 'Tal', 'Peretz', 'Security', 'Guard', '2025-01-05', 8900),
('S09', 'Yael', 'Golan', 'Maintenance', 'Cleaner', '2023-03-03', 7600),
('S10', 'Omer', 'Katz', 'IT', 'Developer', '2020-05-17', 15800);

CREATE TABLE AccessLog (
    LogID INT PRIMARY KEY,
    StaffID VARCHAR(4) NOT NULL REFERENCES Staff(StaffID),
    Door VARCHAR(10) NOT NULL,
    EntryTime DATETIME NOT NULL,
    ExitTime DATETIME NOT NULL
);
INSERT INTO AccessLog (LogID, StaffID, Door, EntryTime, ExitTime) VALUES
(1, 'S01', 'D-MAIN', '2026-11-20T21:00:00', '2026-11-21T06:00:00'),
(2, 'S02', 'D-GEMS', '2026-11-20T21:30:00', '2026-11-20T21:45:00'),
(3, 'S09', 'D-GEMS', '2026-11-20T22:10:00', '2026-11-20T22:40:00'),
(4, 'S04', 'D-GEMS', '2026-11-20T22:50:00', '2026-11-20T23:05:00'),
(5, 'S07', 'D-SERVER', '2026-11-20T22:05:00', '2026-11-20T23:50:00'),
(6, 'S06', 'D-GEMS', '2026-11-20T23:10:00', '2026-11-20T23:20:00'),
(7, 'S08', 'D-PAINT', '2026-11-20T22:30:00', '2026-11-20T22:45:00'),
(8, 'S05', 'D-GEMS', '2026-11-20T23:40:00', '2026-11-20T23:55:00'),
(9, 'S03', 'D-ARCH', '2026-11-19T10:00:00', '2026-11-19T12:00:00'),
(10, 'S09', 'D-PAINT', '2026-11-20T23:00:00', '2026-11-20T23:15:00'),
(11, 'S02', 'D-MAIN', '2026-11-20T21:00:00', '2026-11-21T06:00:00'),
(12, 'S06', 'D-ARCH', '2026-11-20T22:00:00', '2026-11-20T22:55:00');
