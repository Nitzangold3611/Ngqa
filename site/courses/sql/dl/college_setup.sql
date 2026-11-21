-- NGQA · SQL לבודקי תוכנה · תרגיל מסכם College
-- הריצו את הקובץ במסד נתונים חדש (למשל CREATE DATABASE College; USE College;)

create table Student
(ID char(4), First char(10), Last char(10));

insert into Student
(ID, First, Last)
values
('S103', 'John', 'Smith'),
('S104', 'Mary', 'Jones'),
('S105', 'Jane', 'Doe'),
('S106', 'Mark', 'Brown'),
('S107', 'John', 'Good');

create table Course
(Code char(3), Title char(20));

insert into Course
(Code, Title)
values
('DBS', 'Database Systems'),
('PR1', 'Programming 1'),
('PR2', 'Programming 2'),
('PM', 'Project Mgmt');

create table Grade
(ID char(4), Code char(4), Grade tinyint);

insert into Grade
(ID, Code, Grade)
values
('S103', 'DBS', 88),
('S103', 'PM', 90),
('S104', 'PR1', 55),
('S104', 'PM', 89),
('S106', 'PR2', 94),
('S107', 'PR1', 98),
('S107', 'PR2', 84),
('S107', 'PM', 83);
