-- SQL practice: 03_space
-- Dialect: SQL Server (T-SQL); setup and solutions also use SQLite-compatible syntax.
-- Run in a dedicated empty practice database. No existing tables are deleted.
-- Execute each question independently against the initial data.
-- To undo an individual exercise in SQL Server: BEGIN TRANSACTION; ... ROLLBACK;
-- Values in BudgetMillions are in millions of USD.

CREATE TABLE Spacecraft (
    CraftID VARCHAR(4) PRIMARY KEY,
    CraftName VARCHAR(40) NOT NULL,
    Agency VARCHAR(30)
);
INSERT INTO Spacecraft (CraftID, CraftName, Agency) VALUES
('C01', 'Aurora', 'NASA'),
('C02', 'Horizon', 'ESA'),
('C03', 'Pioneer', 'NASA'),
('C04', 'Comet', NULL),
('C05', 'Odyssey', 'JAXA');

CREATE TABLE Destinations (
    DestinationID VARCHAR(4) PRIMARY KEY,
    DestinationName VARCHAR(30) NOT NULL,
    DestinationType VARCHAR(20) NOT NULL
);
INSERT INTO Destinations (DestinationID, DestinationName, DestinationType) VALUES
('D01', 'Moon', 'Moon'),
('D02', 'Mars', 'Planet'),
('D03', 'Europa', 'Moon'),
('D04', 'Venus', 'Planet');

CREATE TABLE Missions (
    MissionID INT PRIMARY KEY,
    CraftID VARCHAR(4) NOT NULL REFERENCES Spacecraft(CraftID),
    DestinationID VARCHAR(4) NOT NULL REFERENCES Destinations(DestinationID),
    LaunchYear INT NOT NULL,
    DurationDays INT,
    BudgetMillions DECIMAL(10,2) NOT NULL
);
INSERT INTO Missions (MissionID, CraftID, DestinationID, LaunchYear, DurationDays, BudgetMillions) VALUES
(1, 'C01', 'D01', 2020, 30, 120),
(2, 'C02', 'D02', 2021, 210, 450),
(3, 'C03', 'D03', 2022, NULL, 600),
(4, 'C01', 'D02', 2023, 240, 500),
(5, 'C04', 'D01', 2024, 45, 90),
(6, 'C02', 'D01', 2025, 28, 110),
(7, 'C03', 'D02', 2024, 220, 480),
(8, 'C04', 'D03', 2026, NULL, 700);
