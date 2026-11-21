-- SQL practice: 02_museum
-- Dialect: SQL Server (T-SQL); setup and solutions also use SQLite-compatible syntax.
-- Run in a dedicated empty practice database. No existing tables are deleted.
-- Execute each question independently against the initial data.
-- To undo an individual exercise in SQL Server: BEGIN TRANSACTION; ... ROLLBACK;

CREATE TABLE Artists (
    ArtistID VARCHAR(4) PRIMARY KEY,
    ArtistName VARCHAR(40) NOT NULL,
    Country VARCHAR(30)
);
INSERT INTO Artists (ArtistID, ArtistName, Country) VALUES
('A01', 'Maya Levi', 'Israel'),
('A02', 'Leo Rossi', 'Italy'),
('A03', 'Nora Klein', 'Germany'),
('A04', 'Omar Aziz', NULL),
('A05', 'Eva Berg', 'Sweden');

CREATE TABLE Halls (
    HallID VARCHAR(4) PRIMARY KEY,
    HallName VARCHAR(40) NOT NULL,
    FloorNumber INT NOT NULL
);
INSERT INTO Halls (HallID, HallName, FloorNumber) VALUES
('H01', 'Modern Art', 1),
('H02', 'Sculpture', 0),
('H03', 'Photography', 2),
('H04', 'Guest Gallery', 1);

CREATE TABLE Artworks (
    ArtworkID INT PRIMARY KEY,
    Title VARCHAR(40) NOT NULL,
    ArtistID VARCHAR(4) NOT NULL REFERENCES Artists(ArtistID),
    HallID VARCHAR(4) REFERENCES Halls(HallID),
    CreationYear INT NOT NULL,
    InsuranceValue DECIMAL(12,2)
);
INSERT INTO Artworks (ArtworkID, Title, ArtistID, HallID, CreationYear, InsuranceValue) VALUES
(1, 'Blue Morning', 'A01', 'H01', 2020, 12000),
(2, 'Stone Wave', 'A02', 'H02', 2018, 25000),
(3, 'Silent Street', 'A03', 'H03', 2021, 8000),
(4, 'Desert Light', 'A04', 'H03', 2022, NULL),
(5, 'City Lines', 'A01', 'H01', 2019, 15000),
(6, 'Bronze Bird', 'A02', 'H02', 2015, 32000),
(7, 'Night Window', 'A03', NULL, 2023, 9500),
(8, 'Golden Sand', 'A04', 'H01', 2020, 11000);
