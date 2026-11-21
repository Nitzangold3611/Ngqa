-- NGQA · SQL לבודקי תוכנה · תרגיל מסכם Party
-- הריצו את הקובץ במסד נתונים חדש (למשל CREATE DATABASE PartyDB; USE PartyDB;)

CREATE TABLE Party
(Name char(10), City char(10), Department char(10), Age tinyint, Gender char(1), Transport char(10), Food char(10), Drink1 char(10), Drink2 char(10));

INSERT INTO party (Name, City, Department, Age, Gender, Transport, Food, Drink1, Drink2)
VALUES 
('Inna', 'Holon', 'finance', 24, 'F', 'car', 'meat', 'Wine', 'Vodka'),
('Raz', 'Netanya', 'logistics', 33, 'F', 'train', 'dairy', 'Beer', 'Pepsi'),
('Yavgeni', 'Burgata', 'sales', 65, 'M', 'taxi', NULL, 'water', ''),
('Dudi', 'Gadera', 'sales', 43, 'M', 'bike', 'dairy', NULL, ''),
('Merav', 'Tel Aviv', 'sales', 29, 'F', 'car', 'meat', 'Pepsi', 'Wine'),
('Sagi', 'Netanya', 'sales', 73, 'F', 'car', 'meat', 'Pepsi', 'Wine'),
('Yuval', 'Tel Aviv', 'finance', 28, 'M', 'taxi', 'meat', 'Pepsi', 'Wine'),
('Hila', 'Netanya', 'sales', 32, 'F', 'taxi', 'dairy', 'Pepsi', 'Pepsi'),
('Yael', 'Netanya', 'sales', 34, 'M', 'car', 'meat', 'Pepsi', 'Pepsi'),
('Sofi', 'Beer Sheva', 'finance', 18, 'M', 'train', 'dairy', 'Pepsi', 'Vodka'),
('Iris', 'Tel Aviv', 'sales', 23, 'F', NULL, NULL, 'Pepsi', 'Wine'),
('Shoval', 'Gadera', 'logistics', 55, 'F', 'car', 'meat', 'Vodka', 'Wine'),
('Tamar', 'Tel Aviv', 'sales', 42, 'F', NULL, 'meat', 'Pepsi', 'Vodka'),
('Ido', 'Ramla', 'management', 17, 'M', NULL, NULL, 'Vodka', 'Water');
